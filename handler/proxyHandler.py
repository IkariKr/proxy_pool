# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name锛?    ProxyHandler.py
   Description :
   Author :       JHao
   date锛?         2016/12/3
-------------------------------------------------
   Change Activity:
                   2016/12/03:
                   2020/05/26: 鍖哄垎http鍜宧ttps
-------------------------------------------------
"""
__author__ = 'JHao'

from helper.proxy import Proxy
from db.dbClient import DbClient
from handler.configHandler import ConfigHandler


class ProxyHandler(object):
    """ Proxy CRUD operator"""

    def __init__(self):
        self.conf = ConfigHandler()
        self.db = DbClient(self.conf.dbConn)
        self.db.changeTable(self.conf.tableName)

    def get(self, https=False):
        """
        return a proxy
        Args:
            https: True/False
        Returns:
        """
        proxy = self.db.get(https, qualified_only=True)
        return Proxy.createFromJson(proxy) if proxy else None

    def pop(self, https):
        """
        return and delete a useful proxy
        :return:
        """
        proxy = self.db.pop(https)
        if proxy:
            return Proxy.createFromJson(proxy)
        return None

    def put(self, proxy):
        """
        put proxy into use proxy
        :return:
        """
        self.db.put(proxy)

    def delete(self, proxy):
        """
        delete useful proxy
        :param proxy:
        :return:
        """
        return self.db.delete(proxy.proxy)

    def getAll(self, https=False, qualified_only=True):
        """
        get all proxy from pool as Proxy list
        :return:
        """
        proxies = self.db.getAll(https, qualified_only=qualified_only)
        return [Proxy.createFromJson(_) for _ in proxies]

    def exists(self, proxy):
        """
        check proxy exists
        :param proxy:
        :return:
        """
        return self.db.exists(proxy.proxy)

    def getByProxy(self, proxy_str):
        proxy = self.db.getByKey(proxy_str)
        return Proxy.createFromJson(proxy) if proxy else None

    def findByExitIp(self, exit_ip, exclude_proxy=None):
        for proxy in self.getAll(qualified_only=True):
            if proxy.proxy == exclude_proxy:
                continue
            if proxy.exit_ip == exit_ip:
                return proxy
        return None

    def getCount(self):
        """
        return raw_proxy and use_proxy count
        :return:
        """
        qualified_count = self.db.getCount(qualified_only=True)
        total_count = self.db.getCount(qualified_only=False)
        return {'count': qualified_count, 'candidate_count': total_count}
