# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""
-------------------------------------------------
   File Name锛?   DbClient.py
   Description :  DB宸ュ巶绫?
   Author :       JHao
   date锛?         2016/12/2
-------------------------------------------------
   Change Activity:
                   2016/12/02:   DB宸ュ巶绫?
                   2020/07/03:   鍙栨秷raw_proxy鍌ㄥ瓨
-------------------------------------------------
"""
__author__ = 'JHao'

import os
import sys

from util.six import urlparse, withMetaclass
from util.singleton import Singleton

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class DbClient(withMetaclass(Singleton)):
    """
    DbClient DB宸ュ巶绫?鎻愪緵get/put/update/pop/delete/exists/getAll/clean/getCount/changeTable鏂规硶


    鎶借薄鏂规硶瀹氫箟锛?
        get(): 闅忔満杩斿洖涓€涓猵roxy;
        put(proxy): 瀛樺叆涓€涓猵roxy;
        pop(): 椤哄簭杩斿洖骞跺垹闄や竴涓猵roxy;
        update(proxy): 鏇存柊鎸囧畾proxy淇℃伅;
        delete(proxy): 鍒犻櫎鎸囧畾proxy;
        exists(proxy): 鍒ゆ柇鎸囧畾proxy鏄惁瀛樺湪;
        getAll(): 杩斿洖鎵€鏈変唬鐞?
        clean(): 娓呴櫎鎵€鏈塸roxy淇℃伅;
        getCount(): 杩斿洖proxy缁熻淇℃伅;
        changeTable(name): 鍒囨崲鎿嶄綔瀵硅薄


        鎵€鏈夋柟娉曢渶瑕佺浉搴旂被鍘诲叿浣撳疄鐜帮細
            ssdb: ssdbClient.py
            redis: redisClient.py
            mongodb: mongodbClient.py

    """

    def __init__(self, db_conn):
        """
        init
        :return:
        """
        self.parseDbConn(db_conn)
        self.__initDbClient()

    @classmethod
    def parseDbConn(cls, db_conn):
        db_conf = urlparse(db_conn)
        cls.db_type = db_conf.scheme.upper().strip()
        cls.db_host = db_conf.hostname
        cls.db_port = db_conf.port
        cls.db_user = db_conf.username
        cls.db_pwd = db_conf.password
        cls.db_name = db_conf.path[1:]
        return cls

    def __initDbClient(self):
        """
        init DB Client
        :return:
        """
        __type = None
        if "SSDB" == self.db_type:
            __type = "ssdbClient"
        elif "REDIS" == self.db_type:
            __type = "redisClient"
        else:
            pass
        assert __type, 'type error, Not support DB type: {}'.format(self.db_type)
        self.client = getattr(__import__(__type), "%sClient" % self.db_type.title())(host=self.db_host,
                                                                                     port=self.db_port,
                                                                                     username=self.db_user,
                                                                                     password=self.db_pwd,
                                                                                     db=self.db_name)

    def get(self, https, **kwargs):
        return self.client.get(https, **kwargs)

    def put(self, key, **kwargs):
        return self.client.put(key, **kwargs)

    def update(self, key, value, **kwargs):
        return self.client.update(key, value, **kwargs)

    def delete(self, key, **kwargs):
        return self.client.delete(key, **kwargs)

    def exists(self, key, **kwargs):
        return self.client.exists(key, **kwargs)

    def getByKey(self, key, **kwargs):
        return self.client.getByKey(key, **kwargs)

    def pop(self, https, **kwargs):
        return self.client.pop(https, **kwargs)

    def getAll(self, https=False, **kwargs):
        return self.client.getAll(https, **kwargs)

    def clear(self):
        return self.client.clear()

    def changeTable(self, name):
        self.client.changeTable(name)

    def getCount(self, **kwargs):
        return self.client.getCount(**kwargs)

    def test(self):
        return self.client.test()
