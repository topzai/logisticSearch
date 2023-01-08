# 物流查询
import json
import re
import time

import requests
import yaml
from seleniumwire import webdriver
from selenium.webdriver import ChromeOptions


class Logistics(object):
    """
    查询快递信息，使用百度免费接口
    传入：compAndMun 列表[('快递单号'，'快递公司'),()]
    返回yield：详细快递信息
    """
    def __init__(self,compAndMun):
        """初始化方法"""
        # 传入快递公司名称和物流单号
        self.compAndMun = compAndMun
        # 百度用于查询快递的tokenV2
        self.tokenV2 = None
        # 请求头
        self.headers = None
        # 查询时网页中的payload
        self.payload = {
            'query_from_srcid': 'query_from_srcid',
            'isBaiduBoxApp': '10002',
            'isWisePc': "10020",
            'tokenV2': '',
            'cb': '',
            'appid': '4001',
            'com': 'ems',
            'nu': '11111111111',
            'qid': '',
            '_': '123123123100'
        }

    def WebConnect(self):
        """浏览器配置"""
        option = ChromeOptions()
        # 反爬虫
        option.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36")
        option.add_argument('--disable-blink-features=AutomationControlled')
        option.add_experimental_option('useAutomationExtension', False)
        option.add_argument('--headless')
        option.add_argument('--disable-gpu')  # 在linux下可以增加
        option.add_argument('--no-sandbox')  # root用户不加这条会无法运行
        driver = webdriver.Chrome('chromedriver.exe',options=option)
        driver.implicitly_wait(10)
        return driver

    def gettokenV2(self):
        """获取token和cookies并且更新到yml文件中"""
        try:
            driver = self.WebConnect()
            driver.get('https://www.baidu.com/s?tn=02003390_43_hao_pg&ie=utf-8&wd=%E5%BF%AB%E9%80%92')
            # 延迟
            time.sleep(3)
            # 获取cookies
            url1 = driver.requests
            cookies = dict(url1[1].headers)  # ['Cookie']
            try: # 有2种cookie
                cookies = cookies["cookie"]
            except:
                cookies = cookies["Cookie"]
            # 缓存网页
            html = driver.page_source
            # 查询网页中的tokenV2
            tv2 = re.findall(r'tokenV2=(.*?)",', html, re.S)

            self.tokenV2 = tv2[0]
            # 请求头
            self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
                'cookie': cookies,
            }
            # 关闭浏览器
            driver.close()
            driver.quit()
            self.updata_yaml('config2.yml',tokenV2=self.tokenV2,Cook=cookies,remainTime=49)
        except Exception as e:
            # 获取tokenV2失败
            print(e)
            self.tokenV2 = ''
            self.headers = None

    def updata_yaml(self,file,tokenV2,Cook,remainTime):
        """更新yml的数值"""
        old_data = self.read_yml('config2.yml')  # 读取文件数据
        old_data['tokenV2'] = tokenV2  # 修改读取的数据
        old_data['cookies'] = Cook  # 修改读取的数据
        old_data['lostTime'] = remainTime  # 修改读取的数据
        with open(file, "w", encoding="utf-8") as f:
            yaml.dump(old_data, f, encoding='utf-8', allow_unicode=True)

    def kuaidiComy(self,kuaidiCompy):
        """
        传入：kuaidiComy中文快递公司
        返回：Compy简称快递公司
        """
        if kuaidiCompy == "中通速递" or kuaidiCompy == "中通快递":
            Compy = "zhongtong"
        elif kuaidiCompy == "申通E物流":
            Compy = "shentong"
        elif kuaidiCompy == "京东快递":
            Compy = "jd"
        elif kuaidiCompy == "邮政标准快递EMS":
            Compy = "ems"
        else:
            Compy = None
        return Compy

    def LostTime(self,file):
        """更新yml的数值"""
        old_data = self.read_yml('config2.yml')  # 读取文件数据
        lostTime = old_data['lostTime']
        old_data['lostTime'] = lostTime-1  # 修改读取的数据
        with open(file, "w", encoding="utf-8") as f:
            yaml.dump(old_data, f, encoding='utf-8', allow_unicode=True)
        return lostTime

    def read_yml(self,file):
        """读取yml,传入文件路径file"""
        f = open(file, 'r', encoding="utf-8")  # 读取文件
        yml_config = yaml.load(f, Loader=yaml.FullLoader)  # Loader为了更加安全
        return yml_config

    def main(self):
        # 百度的快递查询接口
        url = "https://express.baidu.com/express/api/express?"
        configInfo=self.read_yml('config2.yml')
        self.tokenV2 = configInfo['tokenV2']
        # 模拟请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
            'cookie': configInfo['cookies'],
        }
        for Info in self.compAndMun:
            # 剩余可以直接查询次数
            remaining_times=self.LostTime('config2.yml')
            print("tokenV2剩余次数：",remaining_times)
            if remaining_times<1:
                # 更新剩余可用次数
                self.gettokenV2()
                print("tokenV2次数已更新")
            comp = Info[1]
            mun = Info[0]
            kuaidiCompy=self.kuaidiComy(comp)
            if kuaidiCompy is None:  # 如果未查询到公司简称不进入循环
                yield {'msg': '未输入正确快递公司名称',}
            else:
                self.payload['tokenV2'] = self.tokenV2
                self.payload['com'] = kuaidiCompy
                self.payload['nu'] = mun
                self.payload['nowTime'] = (str(time.time()).replace('.', ''))[0:12]
                data = requests.get(url, params=self.payload, headers=self.headers)
                wuliu_info = json.loads(data.text)
                if wuliu_info["status"] != '0' or wuliu_info["error_code"] != '0': # 如果状态码不和错误码等于0 证明可能查询失败
                    self.gettokenV2()  # 更新tokenV2
                    data = requests.get(url, params=self.payload, headers=self.headers)
                    wuliu_info = json.loads(data.text)
                yield wuliu_info


if __name__ == "__main__":
    # 快递单号，快递公司 请在   def kuaidiComy(self,kuaidiCompy): 中添加新的公司缩写
    kd = [('776337483107599','申通E物流'),('1234657903767','邮政标准快递EMS')]
    L = Logistics(kd)
    wuliu_info=L.main()
    for i in range(len(kd)):
        info=next(wuliu_info)
        # 打印快递信息
        print(info)
