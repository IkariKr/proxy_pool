# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     testRedisClient
   Description :
   Author :        JHao
   date：          2020/6/23
-------------------------------------------------
   Change Activity:
                   2020/6/23:
-------------------------------------------------
"""
__author__ = 'JHao'

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.redisClient import RedisClient


def testRedisClient():
    from db.dbClient import DbClient
    from helper.proxy import Proxy

    uri = "redis://:pwd@127.0.0.1:6379"
    db = DbClient(uri)
    db.changeTable("use_proxy")
    proxy = Proxy.createFromJson('{"proxy": "118.190.79.36:8090", "https": false, "fail_count": 0, "region": "", "anonymous": "", "source": "freeProxy14", "check_count": 4, "last_status": true, "last_time": "2021-05-26 10:58:04"}')

    print("put: ", db.put(proxy))

    print("get: ", db.get(https=None))

    print("exists: ", db.exists("27.38.96.101:9797"))

    print("exists: ", db.exists("27.38.96.101:8888"))

    print("pop: ", db.pop(https=None))

    print("getAll: ", db.getAll(https=None))

    print("getCount", db.getCount())


class RedisClientKeyTests(unittest.TestCase):

    def test_resolve_keys_include_protocol_and_legacy_key(self):
        client = object.__new__(RedisClient)

        self.assertEqual(
            client._resolve_keys("1.2.3.4:80", proxy_type="socks5"),
            ["socks5|1.2.3.4:80", "1.2.3.4:80"]
        )
        self.assertEqual(
            client._resolve_keys("1.2.3.4:80"),
            ["http|1.2.3.4:80", "socks5|1.2.3.4:80", "1.2.3.4:80"]
        )


if __name__ == '__main__':
    unittest.main()
