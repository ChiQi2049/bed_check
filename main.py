import os
import execjs
import feapder
import requests


class CQ(feapder.AirSpider):
    __custom_setting__ = dict(
        SPIDER_MAX_RETRY_TIMES=3,
        LOG_LEVEL="INFO",
    )

    def start_requests(self):
        # 登录 URL
        login_url = "https://ids.gzist.edu.cn/lyuapServer/login?service=https://portal.gzist.edu.cn"

        # 模拟登录表单数据
        post_data = {
            "username": USERNAME,
            "password": self.encrypt_password(PASSWORD),
            # 如果需要其他字段，继续补充
        }

        # 模拟浏览器的请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",  # 必须是表单提交
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-cache",
            "Referer": "https://ids.gzist.edu.cn/lyuapServer/login",  # 设置登录页面的 Referer
            "Origin": "https://ids.gzist.edu.cn",  # 添加 Origin 头部
        }

        # 尝试使用 POST 方法发起请求
        yield feapder.Request(url=login_url, method="POST", data=post_data, headers=headers, callback=self.parse_tryLogin)

    def parse_tryLogin(self, request, response):
        # 检查响应状态码
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")  # 打印响应内容以调试
            return

        # 打印响应内容以检查是否为 JSON 格式
        print(f"响应内容: {response.text}")

        try:
            # 尝试解析 JSON 响应
            login_response = response.json()
        except Exception as e:
            print(f"解析 JSON 失败: {str(e)}")
            return

        try:
            # 检查是否登录成功
            params = {"ticket": login_response["ticket"]}  # 根据实际返回字段调整
        except KeyError:
            # 处理登录失败的情况
            if login_response.get("data", {}).get("code") == 'NOUSER':
                print("用户名错误")
                send_data(f"{USERNAME}: 用户名错误")
            elif login_response.get("data", {}).get("code") == 'PASSERROR':
                print("密码错误")
                send_data(f"{USERNAME}: 密码错误")
            else:
                print("发生未知错误")
            return

        # 登录成功后跳转到系统主页
        jump_url = "https://xsfw.gzist.edu.cn/xsfw/sys/swmzncqapp/*default/index.do"
        yield feapder.Request(url=jump_url, method="GET", callback=self.parse_getSelRoleConfig, params=params)

    def parse_getSelRoleConfig(self, request, response):
        url = "https://xsfw.gzist.edu.cn/xsfw/sys/swpubapp/MobileCommon/getSelRoleConfig.do"
        cookies = response.cookies
        json = {
            "APPID": "5405362541914944",
            "APPNAME": "swmzncqapp"
        }

        # 设置请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36",
            "X-Content-Type-Options": "nosniff",
            "Content-Type": "application/json"
        }

        yield feapder.Request(url=url, method="POST", callback=self.parse_done, cookies=cookies, json=json, headers=headers)

    def parse_done(self, request, response):
        url = "https://xsfw.gzist.edu.cn/xsfw/sys/swmzncqapp/modules/studentCheckController/uniFormSignUp.do"
        cookies = response.cookies

        # 发起请求继续流程
        yield feapder.Request(url=url, method="GET", callback=self.parse, cookies=cookies)

    def parse(self, request, response):
        result = response.json()["msg"]
        print(f"查寝结果：{result}")
        send_data(f"{USERNAME}查寝结果：{result}")

    # 加密密码
    def encrypt_password(self, password):
        # 编译加载js字符串
        context1 = execjs.compile(self.js_from_file('./login.js'))
        encrypted_password = context1.call("encrypt", password)
        return encrypted_password

    @staticmethod
    def js_from_file(file_name):
        # 读取JS文件
        with open(file_name, 'r', encoding='UTF-8') as file:
            result = file.read()
        return result


def get_username_password_from_env():
    username = os.environ.get("loginUserName")
    password = os.environ.get("loginPassword")
    if username and password:
        return username, password
    else:
        return None, None


def send_data(string):
    url = os.environ.get("keyUrl")
    data = {
        "msgtype": "text",
        "text": {
            "content": string,
        }
    }
    requests.post(url, json=data)


if __name__ == '__main__':
    USERNAME, PASSWORD = get_username_password_from_env()
    CQ().start()
