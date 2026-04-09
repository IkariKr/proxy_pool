# -*- coding: utf-8 -*-

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helper.proxy import Proxy
from helper.quality import apply_validation_result, extract_exit_ip, is_better_proxy, merge_proxy_state


class ProxyQualityTests(unittest.TestCase):

    def test_extract_exit_ip(self):
        self.assertEqual(extract_exit_ip({"origin": "1.1.1.1, 2.2.2.2"}), "1.1.1.1")

    def test_proxy_qualifies_after_two_successes(self):
        proxy = Proxy("1.2.3.4:80", source="freeProxy12")
        proxy = apply_validation_result(proxy, True, True, "8.8.8.8", "2026-04-08 22:00:00", "test", 2)
        self.assertFalse(proxy.qualified)

        proxy = apply_validation_result(proxy, True, True, "8.8.8.8", "2026-04-08 22:00:01", "test", 2)
        self.assertTrue(proxy.qualified)
        self.assertEqual(proxy.http_success_streak, 2)
        self.assertEqual(proxy.https_success_streak, 2)

    def test_better_proxy_prefers_qualified_higher_score(self):
        current_proxy = Proxy("1.2.3.4:80", score=6, success_streak=2, http_success_streak=2,
                              https_success_streak=2, qualified=True, https=True)
        stored_proxy = Proxy("5.6.7.8:81", score=1, success_streak=1, http_success_streak=1,
                             qualified=False, https=False)
        self.assertTrue(is_better_proxy(current_proxy, stored_proxy))

    def test_merge_proxy_state_keeps_current_proxy_type(self):
        current_proxy = Proxy("1.2.3.4:80", source="freeProxy13", proxy_type="socks5")
        stored_proxy = Proxy("1.2.3.4:80", source="freeProxy12", proxy_type="http", score=5)

        merged_proxy = merge_proxy_state(current_proxy, stored_proxy)

        self.assertEqual(merged_proxy.proxy_type, "socks5")
        self.assertEqual(merged_proxy.score, 5)
        self.assertIn("freeProxy12", merged_proxy.source)


if __name__ == '__main__':
    unittest.main()
