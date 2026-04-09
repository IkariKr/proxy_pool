# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name锛?    check
   Description :   鎵ц浠ｇ悊鏍￠獙
   Author :        JHao
   date锛?         2019/8/6
-------------------------------------------------
   Change Activity:
                   2019/08/06: 鎵ц浠ｇ悊鏍￠獙
                   2021/05/25: 鍒嗗埆鏍￠獙http鍜宧ttps
                   2022/08/16: 鑾峰彇浠ｇ悊Region淇℃伅
-------------------------------------------------
"""
__author__ = 'JHao'

from requests import get
from util.six import Empty
from threading import Thread
from datetime import datetime
from util.webRequest import WebRequest
from handler.logHandler import LogHandler
from helper.validator import ProxyValidator, HEADER
from helper.quality import extract_exit_ip, merge_proxy_state, apply_validation_result, is_better_proxy
from handler.proxyHandler import ProxyHandler
from handler.configHandler import ConfigHandler


class DoValidator(object):
    """ 鎵ц鏍￠獙 """

    conf = ConfigHandler()

    @classmethod
    def validator(cls, proxy, work_type):
        """
        鏍￠獙鍏ュ彛
        Args:
            proxy: Proxy Object
            work_type: raw/use
        Returns:
            Proxy Object
        """
        http_result = cls.httpValidator(proxy)
        https_result = cls.httpsValidator(proxy) if http_result.get("ok") else {"ok": False, "exit_ip": ""}
        exit_ip = https_result.get("exit_ip") or http_result.get("exit_ip") or proxy.exit_ip
        region = ""
        if http_result.get("ok") and cls.conf.proxyRegion:
            region = cls.regionGetter(exit_ip or proxy.proxy.split(':')[0])

        proxy = apply_validation_result(
            proxy=proxy,
            http_ok=http_result.get("ok"),
            https_ok=https_result.get("ok"),
            exit_ip=exit_ip,
            check_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            region=region if work_type == "raw" else proxy.region or region,
            qualify_success_streak=cls.conf.qualifySuccessStreak
        )
        return proxy

    @classmethod
    def _probe(cls, proxy_str, url, verify):
        return cls._probe_with_type(proxy_str, "http", url, verify)

    @classmethod
    def _probe_with_type(cls, proxy_str, proxy_type, url, verify):
        scheme = "socks5h" if proxy_type == "socks5" else "http"
        proxies = {
            "http": "{scheme}://{proxy}".format(scheme=scheme, proxy=proxy_str),
            "https": "{scheme}://{proxy}".format(scheme=scheme, proxy=proxy_str)
        }
        try:
            response = get(url, headers=HEADER, proxies=proxies, timeout=cls.conf.verifyTimeout, verify=verify)
            if response.status_code != 200:
                return {"ok": False, "exit_ip": ""}
            try:
                payload = response.json()
            except Exception:
                payload = response.text
            return {"ok": True, "exit_ip": extract_exit_ip(payload)}
        except Exception:
            return {"ok": False, "exit_ip": ""}

    @classmethod
    def httpValidator(cls, proxy):
        return cls._probe_with_type(proxy.proxy, proxy.proxy_type, cls.conf.httpUrl, verify=False)

    @classmethod
    def httpsValidator(cls, proxy):
        return cls._probe_with_type(proxy.proxy, proxy.proxy_type, cls.conf.httpsUrl, verify=False)

    @classmethod
    def preValidator(cls, proxy):
        for func in ProxyValidator.pre_validator:
            if not func(proxy):
                return False
        return True

    @classmethod
    def regionGetter(cls, ip):
        try:
            url = 'https://searchplugin.csdn.net/api/v1/ip/get?ip=%s' % ip
            r = WebRequest().get(url=url, retry_time=1, timeout=2).json
            return r['data']['address']
        except Exception:
            return 'error'


class _ThreadChecker(Thread):
    """ 澶氱嚎绋嬫娴?"""

    def __init__(self, work_type, target_queue, thread_name):
        Thread.__init__(self, name=thread_name)
        self.work_type = work_type
        self.log = LogHandler("checker")
        self.proxy_handler = ProxyHandler()
        self.target_queue = target_queue
        self.conf = ConfigHandler()

    def run(self):
        self.log.info("{}ProxyCheck - {}: start".format(self.work_type.title(), self.name))
        while True:
            try:
                proxy = self.target_queue.get(block=False)
            except Empty:
                self.log.info("{}ProxyCheck - {}: complete".format(self.work_type.title(), self.name))
                break

            stored_proxy = self.proxy_handler.getByProxy(proxy.proxy, proxy_type=proxy.proxy_type)
            if stored_proxy:
                proxy = merge_proxy_state(proxy, stored_proxy)

            was_qualified = proxy.qualified
            proxy = DoValidator.validator(proxy, self.work_type)
            if self.work_type == "raw":
                self.__ifRaw(proxy)
            else:
                self.__ifUse(proxy, was_qualified)
            self.target_queue.task_done()

    def __apply_exit_ip_dedup(self, proxy):
        if not proxy.qualified or not proxy.exit_ip:
            return proxy, None

        duplicate_proxy = self.proxy_handler.findByExitIp(proxy.exit_ip, exclude_proxy=proxy.proxy)
        if not duplicate_proxy:
            return proxy, None

        if is_better_proxy(proxy, duplicate_proxy):
            duplicate_proxy.qualified = False
            self.proxy_handler.put(duplicate_proxy)
            return proxy, duplicate_proxy

        proxy.qualified = False
        return proxy, duplicate_proxy

    def __ifRaw(self, proxy):
        if proxy.last_status:
            proxy, duplicate_proxy = self.__apply_exit_ip_dedup(proxy)
            if proxy.qualified:
                if duplicate_proxy:
                    self.log.info('RawProxyCheck - {}: {} promoted replace {}'.format(
                        self.name, proxy.proxy.ljust(23), duplicate_proxy.proxy.ljust(23)))
                else:
                    self.log.info('RawProxyCheck - {}: {} promoted score {} streak {}'.format(
                        self.name, proxy.proxy.ljust(23), proxy.score, proxy.success_streak))
            else:
                self.log.info('RawProxyCheck - {}: {} warmup score {} streak {}'.format(
                    self.name, proxy.proxy.ljust(23), proxy.score, proxy.success_streak))
            self.proxy_handler.put(proxy)
        else:
            proxy.qualified = False
            if proxy.fail_count > self.conf.candidateMaxFailCount:
                self.log.info('RawProxyCheck - {}: {} fail, count {} delete'.format(
                    self.name, proxy.proxy.ljust(23), proxy.fail_count))
                self.proxy_handler.delete(proxy)
            else:
                self.log.info('RawProxyCheck - {}: {} fail, count {} keep'.format(
                    self.name, proxy.proxy.ljust(23), proxy.fail_count))
                self.proxy_handler.put(proxy)

    def __ifUse(self, proxy, was_qualified):
        if proxy.last_status:
            proxy, duplicate_proxy = self.__apply_exit_ip_dedup(proxy)
            if proxy.qualified:
                if duplicate_proxy:
                    self.log.info('UseProxyCheck - {}: {} promoted replace {}'.format(
                        self.name, proxy.proxy.ljust(23), duplicate_proxy.proxy.ljust(23)))
                else:
                    self.log.info('UseProxyCheck - {}: {} pass score {} streak {}'.format(
                        self.name, proxy.proxy.ljust(23), proxy.score, proxy.success_streak))
            else:
                self.log.info('UseProxyCheck - {}: {} warmup score {} streak {}'.format(
                    self.name, proxy.proxy.ljust(23), proxy.score, proxy.success_streak))
            self.proxy_handler.put(proxy)
        else:
            proxy.qualified = False
            max_fail_count = self.conf.qualifiedMaxFailCount if was_qualified else self.conf.candidateMaxFailCount
            if proxy.fail_count > max_fail_count:
                self.log.info('UseProxyCheck - {}: {} fail, count {} delete'.format(
                    self.name, proxy.proxy.ljust(23), proxy.fail_count))
                self.proxy_handler.delete(proxy)
            else:
                self.log.info('UseProxyCheck - {}: {} fail, count {} keep'.format(
                    self.name, proxy.proxy.ljust(23), proxy.fail_count))
                self.proxy_handler.put(proxy)


def Checker(tp, queue):
    """
    run Proxy ThreadChecker
    :param tp: raw/use
    :param queue: Proxy Queue
    :return:
    """
    thread_list = list()
    for index in range(20):
        thread_list.append(_ThreadChecker(tp, queue, "thread_%s" % str(index).zfill(2)))

    for thread in thread_list:
        thread.setDaemon(True)
        thread.start()

    for thread in thread_list:
        thread.join()
