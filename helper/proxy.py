# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name锛?    Proxy
   Description :   浠ｇ悊瀵硅薄绫诲瀷灏佽
   Author :        JHao
   date锛?         2019/7/11
-------------------------------------------------
   Change Activity:
                   2019/7/11: 浠ｇ悊瀵硅薄绫诲瀷灏佽
-------------------------------------------------
"""
__author__ = 'JHao'

import json


class Proxy(object):

    def __init__(self, proxy, fail_count=0, region="", anonymous="",
                 source="", check_count=0, last_status="", last_time="", https=False,
                 score=0, success_streak=0, http_success_streak=0, https_success_streak=0,
                 http_last_status=False, https_last_status=False, exit_ip="", qualified=False):
        self._proxy = proxy
        self._fail_count = fail_count
        self._region = region
        self._anonymous = anonymous
        self._source = source.split('/')
        self._check_count = check_count
        self._last_status = last_status
        self._last_time = last_time
        self._https = https
        self._score = score
        self._success_streak = success_streak
        self._http_success_streak = http_success_streak
        self._https_success_streak = https_success_streak
        self._http_last_status = http_last_status
        self._https_last_status = https_last_status
        self._exit_ip = exit_ip
        self._qualified = qualified

    @classmethod
    def createFromJson(cls, proxy_json):
        _dict = json.loads(proxy_json)
        return cls(proxy=_dict.get("proxy", ""),
                   fail_count=_dict.get("fail_count", 0),
                   region=_dict.get("region", ""),
                   anonymous=_dict.get("anonymous", ""),
                   source=_dict.get("source", ""),
                   check_count=_dict.get("check_count", 0),
                   last_status=_dict.get("last_status", ""),
                   last_time=_dict.get("last_time", ""),
                   https=_dict.get("https", False),
                   score=_dict.get("score", 0),
                   success_streak=_dict.get("success_streak", 0),
                   http_success_streak=_dict.get("http_success_streak", 0),
                   https_success_streak=_dict.get("https_success_streak", 0),
                   http_last_status=_dict.get("http_last_status", False),
                   https_last_status=_dict.get("https_last_status", False),
                   exit_ip=_dict.get("exit_ip", ""),
                   qualified=_dict.get("qualified", False)
                   )

    @property
    def proxy(self):
        """ 浠ｇ悊 ip:port """
        return self._proxy

    @property
    def fail_count(self):
        """ 妫€娴嬪け璐ユ鏁?"""
        return self._fail_count

    @property
    def region(self):
        """ 鍦扮悊浣嶇疆(鍥藉/鍩庡競) """
        return self._region

    @property
    def anonymous(self):
        """ 鍖垮悕 """
        return self._anonymous

    @property
    def source(self):
        """ 浠ｇ悊鏉ユ簮 """
        return '/'.join(filter(None, self._source))

    @property
    def check_count(self):
        """ 浠ｇ悊妫€娴嬫鏁?"""
        return self._check_count

    @property
    def last_status(self):
        """ 鏈€鍚庝竴娆℃娴嬬粨鏋? True -> 鍙敤; False -> 涓嶅彲鐢?"""
        return self._last_status

    @property
    def last_time(self):
        """ 鏈€鍚庝竴娆℃娴嬫椂闂?"""
        return self._last_time

    @property
    def https(self):
        """ 鏄惁鏀寔https """
        return self._https

    @property
    def score(self):
        return self._score

    @property
    def success_streak(self):
        return self._success_streak

    @property
    def http_success_streak(self):
        return self._http_success_streak

    @property
    def https_success_streak(self):
        return self._https_success_streak

    @property
    def http_last_status(self):
        return self._http_last_status

    @property
    def https_last_status(self):
        return self._https_last_status

    @property
    def exit_ip(self):
        return self._exit_ip

    @property
    def qualified(self):
        return self._qualified

    @property
    def to_dict(self):
        """ 灞炴€у瓧鍏?"""
        return {"proxy": self.proxy,
                "https": self.https,
                "fail_count": self.fail_count,
                "region": self.region,
                "anonymous": self.anonymous,
                "source": self.source,
                "check_count": self.check_count,
                "last_status": self.last_status,
                "last_time": self.last_time,
                "score": self.score,
                "success_streak": self.success_streak,
                "http_success_streak": self.http_success_streak,
                "https_success_streak": self.https_success_streak,
                "http_last_status": self.http_last_status,
                "https_last_status": self.https_last_status,
                "exit_ip": self.exit_ip,
                "qualified": self.qualified}

    @property
    def to_json(self):
        """ 灞炴€son鏍煎紡 """
        return json.dumps(self.to_dict, ensure_ascii=False)

    @fail_count.setter
    def fail_count(self, value):
        self._fail_count = value

    @check_count.setter
    def check_count(self, value):
        self._check_count = value

    @last_status.setter
    def last_status(self, value):
        self._last_status = value

    @last_time.setter
    def last_time(self, value):
        self._last_time = value

    @https.setter
    def https(self, value):
        self._https = value

    @region.setter
    def region(self, value):
        self._region = value

    @score.setter
    def score(self, value):
        self._score = value

    @success_streak.setter
    def success_streak(self, value):
        self._success_streak = value

    @http_success_streak.setter
    def http_success_streak(self, value):
        self._http_success_streak = value

    @https_success_streak.setter
    def https_success_streak(self, value):
        self._https_success_streak = value

    @http_last_status.setter
    def http_last_status(self, value):
        self._http_last_status = value

    @https_last_status.setter
    def https_last_status(self, value):
        self._https_last_status = value

    @exit_ip.setter
    def exit_ip(self, value):
        self._exit_ip = value

    @qualified.setter
    def qualified(self, value):
        self._qualified = value

    def add_source(self, source_str):
        if source_str:
            self._source.append(source_str)
            self._source = list(set(filter(None, self._source)))
