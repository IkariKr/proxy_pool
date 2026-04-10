# -*- coding: utf-8 -*-

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetcher.proxyFetcher import ProxyFetcher


class ProxyFetcherGithubListTests(unittest.TestCase):

    def test_parse_plain_proxy_lines_filters_invalid_and_dedupes(self):
        proxy_lines = [
            "1.2.3.4:80",
            " 1.2.3.4:80 ",
            "5.6.7.8:1080",
            "socks5://9.9.9.9:1080",
            "invalid-line",
            "",
        ]

        proxies = list(ProxyFetcher._parse_plain_proxy_lines(proxy_lines, proxy_type="socks5"))

        self.assertEqual(proxies, [
            {"proxy": "1.2.3.4:80", "proxy_type": "socks5"},
            {"proxy": "5.6.7.8:1080", "proxy_type": "socks5"},
        ])


if __name__ == '__main__':
    unittest.main()
