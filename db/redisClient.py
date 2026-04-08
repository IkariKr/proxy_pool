# -*- coding: utf-8 -*-
"""
-----------------------------------------------------
   File Name锛?    redisClient.py
   Description :   灏佽Redis鐩稿叧鎿嶄綔
   Author :        JHao
   date锛?         2019/8/9
------------------------------------------------------
   Change Activity:
                   2019/08/09: 灏佽Redis鐩稿叧鎿嶄綔
                   2020/06/23: 浼樺寲pop鏂规硶, 鏀圭敤hscan鍛戒护
                   2021/05/26: 鍖哄埆http/https浠ｇ悊
------------------------------------------------------
"""
__author__ = 'JHao'

from redis.exceptions import TimeoutError, ConnectionError, ResponseError
from redis.connection import BlockingConnectionPool
from handler.logHandler import LogHandler
from random import choice
from redis import Redis
import json


class RedisClient(object):
    """
    Redis client

    Redis涓唬鐞嗗瓨鏀剧殑缁撴瀯涓篽ash锛?
    key涓篿p:port, value涓轰唬鐞嗗睘鎬х殑瀛楀吀;

    """

    def __init__(self, **kwargs):
        """
        init
        :param host: host
        :param port: port
        :param password: password
        :param db: db
        :return:
        """
        self.name = ""
        kwargs.pop("username")
        self.__conn = Redis(connection_pool=BlockingConnectionPool(decode_responses=True,
                                                                   timeout=5,
                                                                   socket_timeout=5,
                                                                   **kwargs))

    def _filtered_items(self, https=False, qualified_only=False):
        items = self.__conn.hvals(self.name)
        proxies = []
        for item in items:
            proxy_data = json.loads(item)
            if https and not proxy_data.get("https"):
                continue
            if qualified_only and not proxy_data.get("qualified"):
                continue
            proxies.append(item)
        return proxies

    def _choice_proxy(self, https=False, qualified_only=False):
        proxies = self._filtered_items(https=https, qualified_only=qualified_only)
        return choice(proxies) if proxies else None

    def get(self, https, qualified_only=True):
        """
        杩斿洖涓€涓唬鐞?
        :return:
        """
        return self._choice_proxy(https=https, qualified_only=qualified_only)

    def put(self, proxy_obj):
        """
        灏嗕唬鐞嗘斁鍏ash, 浣跨敤changeTable鎸囧畾hash name
        :param proxy_obj: Proxy obj
        :return:
        """
        data = self.__conn.hset(self.name, proxy_obj.proxy, proxy_obj.to_json)
        return data

    def pop(self, https):
        """
        寮瑰嚭涓€涓唬鐞?
        :return: dict {proxy: value}
        """
        proxy = self.get(https, qualified_only=True)
        if proxy:
            self.__conn.hdel(self.name, json.loads(proxy).get("proxy", ""))
        return proxy if proxy else None

    def delete(self, proxy_str):
        """
        绉婚櫎鎸囧畾浠ｇ悊, 浣跨敤changeTable鎸囧畾hash name
        :param proxy_str: proxy str
        :return:
        """
        return self.__conn.hdel(self.name, proxy_str)

    def exists(self, proxy_str):
        """
        鍒ゆ柇鎸囧畾浠ｇ悊鏄惁瀛樺湪, 浣跨敤changeTable鎸囧畾hash name
        :param proxy_str: proxy str
        :return:
        """
        return self.__conn.hexists(self.name, proxy_str)

    def getByKey(self, proxy_str):
        return self.__conn.hget(self.name, proxy_str)

    def update(self, proxy_obj):
        """
        鏇存柊 proxy 灞炴€?
        :param proxy_obj:
        :return:
        """
        return self.__conn.hset(self.name, proxy_obj.proxy, proxy_obj.to_json)

    def getAll(self, https=False, qualified_only=False):
        """
        瀛楀吀褰㈠紡杩斿洖鎵€鏈変唬鐞? 浣跨敤changeTable鎸囧畾hash name
        :return:
        """
        return self._filtered_items(https=https, qualified_only=qualified_only)

    def clear(self):
        """
        娓呯┖鎵€鏈変唬鐞? 浣跨敤changeTable鎸囧畾hash name
        :return:
        """
        return self.__conn.delete(self.name)

    def getCount(self, qualified_only=False):
        """
        杩斿洖浠ｇ悊鏁伴噺
        :return:
        """
        proxies = self.getAll(https=False, qualified_only=qualified_only)
        return {
            'total': len(proxies),
            'https': len(list(filter(lambda x: json.loads(x).get("https"), proxies))),
            'qualified': len(list(filter(lambda x: json.loads(x).get("qualified"), proxies))),
        }

    def changeTable(self, name):
        """
        鍒囨崲鎿嶄綔瀵硅薄
        :param name:
        :return:
        """
        self.name = name

    def test(self):
        log = LogHandler('redis_client')
        try:
            self.getCount()
        except TimeoutError as e:
            log.error('redis connection time out: %s' % str(e), exc_info=True)
            return e
        except ConnectionError as e:
            log.error('redis connection error: %s' % str(e), exc_info=True)
            return e
        except ResponseError as e:
            log.error('redis connection error: %s' % str(e), exc_info=True)
            return e
