# -*- coding: utf-8 -*-

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetcher.proxyFetcher import ProxyFetcher


def testParseProxiflyProxyLines():
    proxy_lines = [
        "http://1.2.3.4:80",
        " https://5.6.7.8:443 ",
        "socks5://9.9.9.9:1080",
        "invalid-line",
        "http://1.2.3.4:80",
        "",
    ]

    proxies = list(ProxyFetcher._parse_proxifly_proxy_lines(proxy_lines))

    assert proxies == [
        "1.2.3.4:80",
        "5.6.7.8:443",
    ]
