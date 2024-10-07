import os
import time
import execjs
import feapder
import argparse
import configparser
import requests


class CQ(feapder.AirSpider):
    __custom_setting__ = dict(
        SPIDER_MAX_RETRY_TIMES=3,
        LOG_LEVEL="INFO",
    )

    def start_requests(self):
        # 使用新的登录 URL
        login_url = "https://ids.gzist.edu.cn/lyuapServer/login?service=https://portal.gzist.edu.cn"
        post_data = {
            "username": USERNAME,
            "password": self.encrypt_password(PASSWORD),
            # 这里如果有其他需要的字段，继续补充
        }
        yield feapder.Request(url=login_url, data=post_data, callback=self.parse_tryLogin)

    def parse_tryLogin(self, request, response):
        # 检查登录是否成功
        login_response = response.json
        try:
            # 如果登录成功，继续处理跳转后的请求
            params = {"ticket": login_response["ticket"]}  # 可能需要根据返回的实际字段进行调整
        except KeyError:
            # 处理登录失败的各种情况
            if login_response.get("data", {}).get("code") == 'NOUSER':
                print("用户名错误")
                send_data(f"{USERNAME}: 用户名错误")
                return
            elif login_response.get("data", {}).get("code") == 'PASSERROR':
                print("密码错误")
                send_data(f"{USERNAME}: 密码错误")
                return
            else:
                raise Exception("发生未知错误, 尝试重新运行")

        # 登录成功后跳转到系统主页（如果有跳转需要继续处理）
        jump_url = "https://xsfw.gzist.edu.cn/xsfw/sys/swmzncqapp/*default/index.do"
        yield feapder.Request(url=jump_url, callback=self.parse_getSelRoleConfig, params=params)

    def parse_getSelRoleConfig(self, request, response):
        url = "https://xsfw.gzist.edu.cn/xsfw/sys/swpubapp/MobileCommon/getSelRoleConfig.do"
        cookies = response.cookies
        json = {
            "APPID": "5405362541914944",
            "APPNAME": "swmzncqapp"
        }
        yield feapder.Request(url=url, callback=self.parse_done, cookies=cookies, json=json)

    def parse_done(self, request, response):
        url = "https://xsfw.gzist.edu.cn/xsfw/sys/swmzncqapp/modules/studentCheckController/uniFormSignUp.do"
        cookies = response.cookies
        yield feapder.Request(url=url, callback=self.parse, cookies=cookies)

    def parse(self, request, response):
        result = response.json["msg"]
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


def get_username_password_from_config(config_file, section):
    config = configparser.ConfigParser()
    config.read(config_file)
    if config.has_section(section):
        username = config.get(section, 'username')
        password = config.get(section, 'password')
        return username, password
    else:
        return None, None


def get_username_password_manually():
    username = input("请输入用户名: ")
    password = input("请输入密码: ")
    return username, password


def get_username_password():
    parser = argparse.ArgumentParser(description='获取用户名和密码')
    parser.add_argument('-e', '--env', action='store_true', help='从环境变量中获取用户名和密码')
    parser.add_argument('-c', '--config', type=str, help='读取配置文件获取用户名和密码')
    parser.add_argument('-u', '--username', type=str, help='命令行输入用户名')
    parser.add_argument('-p', '--password', type=str, help='命令行输入密码')
    args = parser.parse_args()

    if args.env:
        return get_username_password_from_env()
    elif args.config:
        return get_username_password_from_config(args.config, 'loginInfo')
    elif args.username and args.password:
        return args.username, args.password
    else:
        return get_username_password_manually()


def send_data(string):
    url = os.environ.get("keyUrl")
    data = {
        "msgtype": "text",
        "text": {
            "content": f"{time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))} {string}",
        }
    }
    requests.post(url, json=data)


if __name__ == '__main__':
    USERNAME, PASSWORD = get_username_password()
    print(f"当前时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}")
    CQ().start()
