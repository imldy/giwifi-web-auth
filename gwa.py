import builtins
import json
import time
import sys
import requests
import re
from requests import Response
from urllib.parse import urlparse
import urllib


class Util():
    @classmethod
    def get_datetime(cls):
        local_time = time.localtime()
        dt = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
        return dt


def print(str: str):
    builtins.print("{} - {}".format(Util.get_datetime(), str))


class Code():
    # 登陆失败
    login_error = 0
    # 已登录
    is_login = 1
    # 未登录
    not_login = 2


class Account():
    def __init__(self, phone, password):
        self.phone = phone
        self.username = phone
        self.password = password


class Client():
    '''
    包含客户端软件和客户端设备
    '''

    def __init__(self):
        self.version = ""
        self.ip = ""
        self.mac = ""
        # 认证状态 1：未登录 2：已登录
        self.auth_state = ""
        # 网关ID
        self.gw_id = ""
        # AP Mac
        self.ap_mac = ""
        # 访问类型
        self.access_type = ""
        # 在线时间
        self.online_time = ""
        #
        self.logout_reason = ""
        self.station_cloud = ""
        self.station_sn = ""
        # 网关IP地址
        self.gw_address = ""
        self.gw_port = ""

        self.btype = "pc"
        # 通过get_auth_state/登录页面获取
        self.ac_sign = ""
        # 通过解析登录页面获得
        self.sign = ""
        # 联系电话
        self.contact_phone = ""
        # 建议反馈电话
        self.suggest_phone = ""
        self.org_id = ""
        # 访问get_auth_state返回的时间戳
        self.timestamp = ""
        # 访问登录页面返回的时间戳
        self.page_timestamp = ""

        self.login_link = ""


class GiWiFiWebAuth():
    def __init__(self, client: Client, account: Account):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36 Edg/94.0.992.31"
        }
        self.session = requests.session()
        self.session.headers = headers
        self.client = client
        self.account = account

    def get_auth_state(self) -> Response:
        auth_state_url = "http://{}:{}/wifidog/get_auth_state".format(self.client.gw_address, self.client.gw_port)
        resp = self.session.get(auth_state_url)
        return resp

    def get_login_web(self) -> Response:
        login_web_url = "http://login.gwifi.com.cn/cmps/admin.php/api/login"
        resp = self.session.get(login_web_url)
        return resp

    def is_login_of_wifidog(self):
        # 先获取wifidog地址
        if self.client.gw_address == None or self.client.gw_address == "":
            try:
                self.client.gw_address = open("gw_address", encoding="utf-8").read().strip()
            except Exception as e:
                print("读取本地保存的网关地址发生错误：{}".format(e))
                return False
            self.client.gw_port = "8060"
        auth_state: dict = self.toJson(self.get_auth_state())
        if auth_state["data"]["auth_state"] == 2:
            return True
        else:
            return False

    def get_web_sign(self):
        resp: Response = self.get_login_web()
        url_obj = urllib.parse.urlparse(resp.url)
        if "login.gwifi.com.cn" in url_obj.netloc:
            print("未登录，开始获取sign、网关地址等信息")
            sign = re.findall('class="sign" name="sign" value="(.*?)"/>', resp.text)[0]
            self.client.sign = sign
            # 获取访问页面的时间
            page_time = re.findall('id="page_time" name="page_time" value="(.*?)" />', resp.text)[0]
            self.client.page_timestamp = page_time
            # 解析链接，获取参数信息
            query_arg = dict(urllib.parse.parse_qsl(url_obj.query))
            self.client.gw_address = query_arg["gw_address"]
            self.client.gw_port = query_arg["gw_port"]
            self.client.gw_id = query_arg["gw_id"]
            self.client.ip = query_arg["ip"]
            self.client.mac = query_arg["mac"]
            self.client.ap_mac = query_arg["apmac"]
            try:
                open("gw_address", encoding="utf-8", mode="w").write(self.client.gw_address)
                print("保存网关地址成功")
            except Exception:
                print("保存网关地址失败")
            return Code.not_login
        else:
            return Code.is_login

    def set_client(self):
        resp: Response = self.get_auth_state()
        resp_json: dict = self.toJson(resp)
        self.client.ac_sign = resp_json["data"]["sign"]
        self.client.gw_id = resp_json["data"]["gw_id"]
        self.client.access_type = resp_json["data"]["access_type"]
        self.client.station_sn = resp_json["data"]["station_sn"]
        self.client.ip = resp_json["data"]["client_ip"]
        self.client.mac = resp_json["data"]["client_mac"]
        self.client.online_time = resp_json["data"]["online_time"]
        self.client.logout_reason = resp_json["data"]["logout_reason"]
        self.client.contact_phone = resp_json["data"]["contact_phone"]
        self.client.suggest_phone = resp_json["data"]["suggest_phone"]
        self.client.station_cloud = resp_json["data"]["station_cloud"]
        self.client.org_id = resp_json["data"]["orgId"]
        self.client.timestamp = resp_json["data"]["timestamp"]

    def auth_account(self) -> bool:
        '''
        验证账户，获取带有token的链接，用于使AP(WiFiDog)接受客户端设备
        :return:
        '''
        login_url = "http://login.gwifi.com.cn/cmps/admin.php/api/loginaction?round=847"
        form = {
            "round": 847
        }
        data = {
            "gw_id": self.client.gw_id,
            "gw_address": self.client.gw_address,
            "gw_port": self.client.gw_port,
            "url": "http://www.baidu.com",
            "mac": self.client.mac,
            "btype": self.client.btype,
            "page_time": self.client.page_timestamp,
            "lastaccessurl": "",
            "user_agent": "",
            "devicemode": "",
            "client_ip": self.client.ip,
            "timestamp": self.client.timestamp,
            "access_type": self.client.access_type,
            "station_sn": self.client.station_sn,
            "client_mac": self.client.mac,
            "online_time": self.client.online_time,
            "logout_reason": self.client.logout_reason,
            "contact_phone": self.client.contact_phone,
            "suggest_phone": self.client.suggest_phone,
            "station_cloud": self.client.station_cloud,
            "acsign": self.client.ac_sign,
            "sign": self.client.sign,
            "name": self.account.phone,
            "password": self.account.password,
            "service_type": "1"
        }
        resp = self.session.post(url=login_url, data=data)
        resp_json: dict = resp.json()
        # 认证成功返回网关上的url，失败返回data中的url
        if resp_json["status"] == 1 and self.client.gw_address in resp_json["info"]:
            print("验证账户成功")
            self.client.login_link = resp_json["info"]
            return True
        else:
            print("验证账户失败：{}".format(resp_json))
            return False

    def requests_login_link(self):
        '''
        请求带有token的链接，使AP(WiFiDog)接受客户端设备
        :return:
        '''
        resp = self.session.get(self.client.login_link)
        print(resp.url)
        return True

    def out_login(self, reason='1'):
        url = 'http:/{}:{}/wifidog/userlogout'.format(self.client.gw_address, self.client.gw_port)
        # get方式url后面的数据
        url_data = {
            "ip": self.client.ip,
            "mac": self.client.mac,
            "reason": reason
        }
        ret = self.session.get(url, url_data)
        tojson = self.toJson(ret)
        # 调用get方法，并返回执行结果
        return tojson

    def toJson(self, HttpResponse: Response) -> dict:
        '''
        将HttpResponse中的内容转换成json，主要是处理json中值为字符型的字典
        :param HttpResponse:
        :return:
        '''
        # 解析返回的json信息
        ret = json.loads(HttpResponse.text.encode('utf8'))
        # 判断data数据是否存在
        if ret["data"] == '' or 'data' not in ret:
            return ret
        ret_data = json.loads(ret['data'])
        ret['data'] = ret_data
        return ret


def start(gwa: GiWiFiWebAuth):
    # 1、通过固定域名访问GiWiFi固定网站，判断是否已经登录，若未登录，则GiWiFi会跳转，可获取相关信息
    if gwa.get_web_sign() == Code.is_login:
        return True
    else:
        print("未登录，开始下一步")
        # 2、获取网关WiFiDog与本设备的链接信息，并设置为对象属性
        gwa.set_client()
        # 3、根据
        gwa.auth_account()
        if gwa.requests_login_link() and gwa.is_login_of_wifidog():
            return True
        else:
            return False


def cycle():
    cycle_flag = True
    max_cycle_num = 10
    now_cycle_num = max_cycle_num
    while cycle_flag and now_cycle_num >= 0:
        if now_cycle_num < max_cycle_num:
            print("正在尝试第{}次认证".format(max_cycle_num - now_cycle_num))
        try:
            now_cycle_num -= 1
            result = start(gwa)
            if result:
                print("当前认证状态为【已认证】")
                cycle_flag = False
        except Exception as e:
            print("出现异常：{}".format(e))
    print("认证结束")


if __name__ == '__main__':
    conf_file = open("conf.txt", encoding="utf-8")
    conf = conf_file.read().strip().split("\n")
    account = Account(conf[0].strip(), conf[1].strip())
    client = Client()
    gwa = GiWiFiWebAuth(account=account, client=client)
    cycle()
