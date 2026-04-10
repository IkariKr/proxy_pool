# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     proxyFetcher
   Description :
   Author :        JHao
   date：          2016/11/25
-------------------------------------------------
   Change Activity:
                   2016/11/25: proxyFetcher
-------------------------------------------------
"""
__author__ = 'JHao'

import re
import json
from time import sleep
from urllib.parse import urlparse

from util.webRequest import WebRequest


class ProxyFetcher(object):
    """
    proxy getter
    """

    @staticmethod
    def _parse_plain_proxy_lines(proxy_lines, proxy_type="http"):
        seen = set()
        for raw_line in proxy_lines:
            proxy = raw_line.strip()
            if not proxy:
                continue

            if not re.match(r"^\d{1,3}(?:\.\d{1,3}){3}:\d+$", proxy):
                continue

            key = "%s|%s" % (proxy_type, proxy)
            if key in seen:
                continue

            seen.add(key)
            yield {"proxy": proxy, "proxy_type": proxy_type}

    @staticmethod
    def _parse_proxifly_proxy_lines(proxy_lines):
        seen = set()
        for raw_line in proxy_lines:
            proxy_line = raw_line.strip()
            if not proxy_line:
                continue

            parsed = urlparse(proxy_line)
            if parsed.scheme not in ("http", "https", "socks5"):
                continue

            if not parsed.hostname or not parsed.port:
                continue

            proxy = "%s:%s" % (parsed.hostname, parsed.port)
            key = "%s|%s" % (parsed.scheme, proxy)
            if key in seen:
                continue

            seen.add(key)
            yield {"proxy": proxy, "proxy_type": "socks5" if parsed.scheme == "socks5" else "http"}

    @staticmethod
    def freeProxy01():
        """
        站大爷 https://www.zdaye.com/dayProxy.html
        """
        start_url = "https://www.zdaye.com/dayProxy.html"
        html_tree = WebRequest().get(start_url, verify=False).tree
        latest_page_time = html_tree.xpath("//span[@class='thread_time_info']/text()")[0].strip()
        from datetime import datetime
        interval = datetime.now() - datetime.strptime(latest_page_time, "%Y/%m/%d %H:%M:%S")
        if interval.seconds < 300:  # 只采集5分钟内的更新
            target_url = "https://www.zdaye.com/" + html_tree.xpath("//h3[@class='thread_title']/a/@href")[0].strip()
            while target_url:
                _tree = WebRequest().get(target_url, verify=False).tree
                for tr in _tree.xpath("//table//tr"):
                    ip = "".join(tr.xpath("./td[1]/text()")).strip()
                    port = "".join(tr.xpath("./td[2]/text()")).strip()
                    yield "%s:%s" % (ip, port)
                next_page = _tree.xpath("//div[@class='page']/a[@title='下一页']/@href")
                target_url = "https://www.zdaye.com/" + next_page[0].strip() if next_page else False
                sleep(5)

    @staticmethod
    def freeProxy02():
        """
        代理66 http://www.66ip.cn/
        """
        url = "http://www.66ip.cn/"
        resp = WebRequest().get(url, timeout=10).tree
        for i, tr in enumerate(resp.xpath("(//table)[3]//tr")):
            if i > 0:
                ip = "".join(tr.xpath("./td[1]/text()")).strip()
                port = "".join(tr.xpath("./td[2]/text()")).strip()
                yield "%s:%s" % (ip, port)

    @staticmethod
    def freeProxy03():
        """ 开心代理 """
        target_urls = ["http://www.kxdaili.com/dailiip.html", "http://www.kxdaili.com/dailiip/2/1.html"]
        for url in target_urls:
            tree = WebRequest().get(url).tree
            for tr in tree.xpath("//table[@class='active']//tr")[1:]:
                ip = "".join(tr.xpath('./td[1]/text()')).strip()
                port = "".join(tr.xpath('./td[2]/text()')).strip()
                yield "%s:%s" % (ip, port)

    @staticmethod
    def freeProxy04():
        """ FreeProxyList https://www.freeproxylists.net/zh/ """
        url = "https://www.freeproxylists.net/zh/?c=CN&pt=&pr=&a%5B%5D=0&a%5B%5D=1&a%5B%5D=2&u=50"
        tree = WebRequest().get(url, verify=False).tree
        from urllib import parse

        def parse_ip(input_str):
            html_str = parse.unquote(input_str)
            ips = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', html_str)
            return ips[0] if ips else None

        for tr in tree.xpath("//tr[@class='Odd']") + tree.xpath("//tr[@class='Even']"):
            ip = parse_ip("".join(tr.xpath('./td[1]/script/text()')).strip())
            port = "".join(tr.xpath('./td[2]/text()')).strip()
            if ip:
                yield "%s:%s" % (ip, port)

    @staticmethod
    def freeProxy05(page_count=1):
        """ 快代理 https://www.kuaidaili.com """
        url_pattern = [
            'https://www.kuaidaili.com/free/inha/{}/',
            'https://www.kuaidaili.com/free/intr/{}/'
        ]
        url_list = []
        for page_index in range(1, page_count + 1):
            for pattern in url_pattern:
                url_list.append(pattern.format(page_index))

        for url in url_list:
            tree = WebRequest().get(url).tree
            proxy_list = tree.xpath('.//table//tr')
            sleep(1)  # 必须sleep 不然第二条请求不到数据
            for tr in proxy_list[1:]:
                yield ':'.join(tr.xpath('./td/text()')[0:2])

    @staticmethod
    def freeProxy06():
        """ 冰凌代理 https://www.binglx.cn """
        url = "https://www.binglx.cn/?page=1"
        try:
            tree = WebRequest().get(url).tree
            proxy_list = tree.xpath('.//table//tr')
            for tr in proxy_list[1:]:
                yield ':'.join(tr.xpath('./td/text()')[0:2])
        except Exception as e:
            print(e)

    @staticmethod
    def freeProxy07():
        """ 云代理 """
        urls = ['http://www.ip3366.net/free/?stype=1', "http://www.ip3366.net/free/?stype=2"]
        for url in urls:
            r = WebRequest().get(url, timeout=10)
            proxies = re.findall(r'<td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>[\s\S]*?<td>(\d+)</td>', r.text)
            for proxy in proxies:
                yield ":".join(proxy)

    @staticmethod
    def freeProxy08():
        """ 小幻代理 """
        urls = ['https://ip.ihuan.me/address/5Lit5Zu9.html']
        for url in urls:
            r = WebRequest().get(url, timeout=10)
            proxies = re.findall(r'>\s*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*?</a></td><td>(\d+)</td>', r.text)
            for proxy in proxies:
                yield ":".join(proxy)

    @staticmethod
    def freeProxy09(page_count=1):
        """ 免费代理库 """
        for i in range(1, page_count + 1):
            url = 'http://ip.jiangxianli.com/?country=中国&page={}'.format(i)
            html_tree = WebRequest().get(url, verify=False).tree
            for index, tr in enumerate(html_tree.xpath("//table//tr")):
                if index == 0:
                    continue
                yield ":".join(tr.xpath("./td/text()")[0:2]).strip()

    @staticmethod
    def freeProxy10():
        """ 89免费代理 """
        r = WebRequest().get("https://www.89ip.cn/index_1.html", timeout=10)
        proxies = re.findall(
            r'<td.*?>[\s\S]*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[\s\S]*?</td>[\s\S]*?<td.*?>[\s\S]*?(\d+)[\s\S]*?</td>',
            r.text)
        for proxy in proxies:
            yield ':'.join(proxy)

    @staticmethod
    def freeProxy11():
        """ 稻壳代理 https://www.docip.net/ """
        r = WebRequest().get("https://www.docip.net/data/free.json", timeout=10)
        try:
            for each in r.json['data']:
                yield each['ip']
        except Exception as e:
            print(e)

    @staticmethod
    def freeProxy12():
        """ Proxifly https://github.com/proxifly/free-proxy-list """
        # 中文：国内网络访问 raw.githubusercontent.com 经常超时，这里增加 jsDelivr 回退，避免单源失败导致整批抓取失效。
        # English: raw.githubusercontent.com often times out on CN networks, so we add a jsDelivr fallback to avoid losing the whole batch on a single upstream failure.
        urls = [
            "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all/data.txt",
            "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.txt",
        ]
        for url in urls:
            r = WebRequest().get(url, timeout=15)
            if not r.text:
                continue

            for proxy in ProxyFetcher._parse_proxifly_proxy_lines(r.text.splitlines()):
                yield proxy
            return

    @staticmethod
    def freeProxy13():
        """ IPlocate https://github.com/iplocate/free-proxy-list """
        # 中文：优先走 GitHub Raw，失败后回退到 jsDelivr；同时合并 http/https 清单，交给后续校验流程判定真实协议能力。
        # English: Prefer GitHub Raw and fall back to jsDelivr; merge the http/https lists and let downstream validation determine actual protocol capability.
        urls = [
            "https://raw.githubusercontent.com/iplocate/free-proxy-list/main/protocols/http.txt",
            "https://raw.githubusercontent.com/iplocate/free-proxy-list/main/protocols/https.txt",
            "https://raw.githubusercontent.com/iplocate/free-proxy-list/main/protocols/socks5.txt",
            "https://cdn.jsdelivr.net/gh/iplocate/free-proxy-list@main/protocols/http.txt",
            "https://cdn.jsdelivr.net/gh/iplocate/free-proxy-list@main/protocols/https.txt",
            "https://cdn.jsdelivr.net/gh/iplocate/free-proxy-list@main/protocols/socks5.txt",
        ]
        seen = set()
        for url in urls:
            r = WebRequest().get(url, timeout=15)
            if not r.text:
                continue

            proxy_type = "socks5" if "socks5" in url else "http"
            for raw_line in r.text.splitlines():
                proxy = raw_line.strip()
                key = "%s|%s" % (proxy_type, proxy)
                if not proxy or key in seen:
                    continue
                seen.add(key)
                yield {"proxy": proxy, "proxy_type": proxy_type}

    @staticmethod
    def freeProxy14():
        """ ProxyScraper https://github.com/ProxyScraper/ProxyScraper """
        urls = [
            "https://raw.githubusercontent.com/ProxyScraper/ProxyScraper/main/http.txt",
            "https://raw.githubusercontent.com/ProxyScraper/ProxyScraper/main/socks5.txt",
            "https://cdn.jsdelivr.net/gh/ProxyScraper/ProxyScraper@main/http.txt",
            "https://cdn.jsdelivr.net/gh/ProxyScraper/ProxyScraper@main/socks5.txt",
        ]
        seen = set()
        for url in urls:
            r = WebRequest().get(url, timeout=15)
            if not r.text:
                continue

            proxy_type = "socks5" if "socks5" in url else "http"
            for proxy_item in ProxyFetcher._parse_plain_proxy_lines(r.text.splitlines(), proxy_type=proxy_type):
                key = "%s|%s" % (proxy_item["proxy_type"], proxy_item["proxy"])
                if key in seen:
                    continue
                seen.add(key)
                yield proxy_item

    @staticmethod
    def freeProxy15():
        """ TheSpeedX https://github.com/TheSpeedX/PROXY-List """
        urls = [
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
            "https://cdn.jsdelivr.net/gh/TheSpeedX/PROXY-List@master/http.txt",
            "https://cdn.jsdelivr.net/gh/TheSpeedX/PROXY-List@master/socks5.txt",
        ]
        seen = set()
        for url in urls:
            r = WebRequest().get(url, timeout=15)
            if not r.text:
                continue

            proxy_type = "socks5" if "socks5" in url else "http"
            for proxy_item in ProxyFetcher._parse_plain_proxy_lines(r.text.splitlines(), proxy_type=proxy_type):
                key = "%s|%s" % (proxy_item["proxy_type"], proxy_item["proxy"])
                if key in seen:
                    continue
                seen.add(key)
                yield proxy_item

    @staticmethod
    def freeProxy16():
        """ Fresh Proxy List https://github.com/fyvri/fresh-proxy-list """
        urls = [
            "https://raw.githubusercontent.com/fyvri/fresh-proxy-list/archive/storage/classic/http.txt",
            "https://raw.githubusercontent.com/fyvri/fresh-proxy-list/archive/storage/classic/https.txt",
            "https://raw.githubusercontent.com/fyvri/fresh-proxy-list/archive/storage/classic/socks5.txt",
            "https://cdn.jsdelivr.net/gh/fyvri/fresh-proxy-list@archive/storage/classic/http.txt",
            "https://cdn.jsdelivr.net/gh/fyvri/fresh-proxy-list@archive/storage/classic/https.txt",
            "https://cdn.jsdelivr.net/gh/fyvri/fresh-proxy-list@archive/storage/classic/socks5.txt",
        ]
        seen = set()
        for url in urls:
            r = WebRequest().get(url, timeout=15)
            if not r.text:
                continue

            proxy_type = "socks5" if "socks5" in url else "http"
            for proxy_item in ProxyFetcher._parse_plain_proxy_lines(r.text.splitlines(), proxy_type=proxy_type):
                key = "%s|%s" % (proxy_item["proxy_type"], proxy_item["proxy"])
                if key in seen:
                    continue
                seen.add(key)
                yield proxy_item

    # @staticmethod
    # def wallProxy01():
    #     """
    #     PzzQz https://pzzqz.com/
    #     """
    #     from requests import Session
    #     from lxml import etree
    #     session = Session()
    #     try:
    #         index_resp = session.get("https://pzzqz.com/", timeout=20, verify=False).text
    #         x_csrf_token = re.findall('X-CSRFToken": "(.*?)"', index_resp)
    #         if x_csrf_token:
    #             data = {"http": "on", "ping": "3000", "country": "cn", "ports": ""}
    #             proxy_resp = session.post("https://pzzqz.com/", verify=False,
    #                                       headers={"X-CSRFToken": x_csrf_token[0]}, json=data).json()
    #             tree = etree.HTML(proxy_resp["proxy_html"])
    #             for tr in tree.xpath("//tr"):
    #                 ip = "".join(tr.xpath("./td[1]/text()"))
    #                 port = "".join(tr.xpath("./td[2]/text()"))
    #                 yield "%s:%s" % (ip, port)
    #     except Exception as e:
    #         print(e)

    # @staticmethod
    # def freeProxy10():
    #     """
    #     墙外网站 cn-proxy
    #     :return:
    #     """
    #     urls = ['http://cn-proxy.com/', 'http://cn-proxy.com/archives/218']
    #     request = WebRequest()
    #     for url in urls:
    #         r = request.get(url, timeout=10)
    #         proxies = re.findall(r'<td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>[\w\W]<td>(\d+)</td>', r.text)
    #         for proxy in proxies:
    #             yield ':'.join(proxy)

    # @staticmethod
    # def freeProxy11():
    #     """
    #     https://proxy-list.org/english/index.php
    #     :return:
    #     """
    #     urls = ['https://proxy-list.org/english/index.php?p=%s' % n for n in range(1, 10)]
    #     request = WebRequest()
    #     import base64
    #     for url in urls:
    #         r = request.get(url, timeout=10)
    #         proxies = re.findall(r"Proxy\('(.*?)'\)", r.text)
    #         for proxy in proxies:
    #             yield base64.b64decode(proxy).decode()

    # @staticmethod
    # def freeProxy12():
    #     urls = ['https://list.proxylistplus.com/Fresh-HTTP-Proxy-List-1']
    #     request = WebRequest()
    #     for url in urls:
    #         r = request.get(url, timeout=10)
    #         proxies = re.findall(r'<td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>[\s\S]*?<td>(\d+)</td>', r.text)
    #         for proxy in proxies:
    #             yield ':'.join(proxy)


if __name__ == '__main__':
    p = ProxyFetcher()
    for _ in p.freeProxy06():
        print(_)

# http://nntime.com/proxy-list-01.htm
