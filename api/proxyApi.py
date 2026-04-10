# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""
-------------------------------------------------
   File Name：     ProxyApi.py
   Description :   WebApi
   Author :       JHao
   date：          2016/12/4
-------------------------------------------------
   Change Activity:
                   2016/12/04: WebApi
                   2019/08/14: 集成Gunicorn启动方式
                   2020/06/23: 新增pop接口
                   2022/07/21: 更新count接口
-------------------------------------------------
"""
__author__ = 'JHao'

import platform
from pathlib import Path
from werkzeug.wrappers import Response
from flask import Flask, jsonify, request, send_from_directory

from util.six import iteritems
from helper.proxy import Proxy
from handler.proxyHandler import ProxyHandler
from handler.configHandler import ConfigHandler

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ADMIN_DIST_DIR = PROJECT_ROOT / "web-admin" / "dist"

app = Flask(__name__)
conf = ConfigHandler()
proxy_handler = ProxyHandler()


class JsonResponse(Response):
    @classmethod
    def force_type(cls, response, environ=None):
        if isinstance(response, (dict, list)):
            response = jsonify(response)

        return super(JsonResponse, cls).force_type(response, environ)


app.response_class = JsonResponse

api_list = [
    {"url": "/get", "params": "type: ''https'|''", "desc": "get a proxy"},
    {"url": "/pop", "params": "", "desc": "get and delete a proxy"},
    {"url": "/delete", "params": "proxy: 'e.g. 127.0.0.1:8080'", "desc": "delete an unable proxy"},
    {"url": "/all", "params": "type: ''https'|''", "desc": "get all proxy from proxy pool"},
    {"url": "/count", "params": "", "desc": "return proxy count"}
    # 'refresh': 'refresh proxy pool',
]


def parse_proxy_type():
    request_type = request.args.get("type", "").lower()
    if request_type == 'socks5':
        return "socks5", False
    return "http", request_type == 'https'


@app.route('/')
def index():
    return {'url': api_list}


@app.route('/admin/')
@app.route('/admin/<path:asset_path>')
def admin(asset_path='index.html'):
    if not ADMIN_DIST_DIR.exists():
        return {
            "code": 0,
            "src": "admin page not built yet, run `npm install && npm run build` in web-admin"
        }, 404

    target_path = ADMIN_DIST_DIR / asset_path
    if asset_path != 'index.html' and target_path.exists() and target_path.is_file():
        return send_from_directory(str(ADMIN_DIST_DIR), asset_path)

    return send_from_directory(str(ADMIN_DIST_DIR), 'index.html')


@app.route('/get/')
def get():
    proxy_type, https = parse_proxy_type()
    proxy = proxy_handler.get(https, proxy_type=proxy_type)
    return proxy.to_dict if proxy else {"code": 0, "src": "no proxy"}


@app.route('/pop/')
def pop():
    proxy_type, https = parse_proxy_type()
    proxy = proxy_handler.pop(https, proxy_type=proxy_type)
    return proxy.to_dict if proxy else {"code": 0, "src": "no proxy"}


@app.route('/refresh/')
def refresh():
    # TODO refresh会有守护程序定时执行，由api直接调用性能较差，暂不使用
    return 'success'


@app.route('/all/')
def getAll():
    proxy_type, https = parse_proxy_type()
    qualified_only = request.args.get("scope", "").lower() != 'all'
    proxies = proxy_handler.getAll(https, qualified_only=qualified_only, proxy_type=proxy_type)
    return jsonify([_.to_dict for _ in proxies])


@app.route('/delete/', methods=['GET'])
def delete():
    proxy = request.args.get('proxy')
    request_type = request.args.get("type", "").lower()
    if request_type == "socks5":
        proxy_type = "socks5"
    elif request_type in ("http", "https"):
        proxy_type = "http"
    else:
        proxy_type = None
    status = proxy_handler.deleteByProxy(proxy, proxy_type=proxy_type)
    return {"code": 0, "src": status}


@app.route('/count/')
def getCount():
    proxies = proxy_handler.getAll(qualified_only=True, proxy_type="http") + proxy_handler.getAll(qualified_only=True, proxy_type="socks5")
    candidates = proxy_handler.getAll(qualified_only=False, proxy_type="http") + proxy_handler.getAll(qualified_only=False, proxy_type="socks5")
    http_type_dict = {}
    source_dict = {}
    for proxy in proxies:
        http_type = proxy.proxy_type if proxy.proxy_type == 'socks5' else ('https' if proxy.https else 'http')
        http_type_dict[http_type] = http_type_dict.get(http_type, 0) + 1
        for source in proxy.source.split('/'):
            source_dict[source] = source_dict.get(source, 0) + 1
    return {
        "http_type": http_type_dict,
        "source": source_dict,
        "count": len(proxies),
        "candidate_count": len(candidates),
        "qualified_count": len(proxies)
    }


def runFlask():
    if platform.system() == "Windows":
        # 中文：Windows 下显式关闭 reloader，避免开发服务器派生重复的 python 进程。
        # English: Disable the reloader on Windows explicitly to avoid duplicate Python worker processes.
        app.run(host=conf.serverHost, port=conf.serverPort, use_reloader=False)
    else:
        import gunicorn.app.base

        class StandaloneApplication(gunicorn.app.base.BaseApplication):

            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super(StandaloneApplication, self).__init__()

            def load_config(self):
                _config = dict([(key, value) for key, value in iteritems(self.options)
                                if key in self.cfg.settings and value is not None])
                for key, value in iteritems(_config):
                    self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        _options = {
            'bind': '%s:%s' % (conf.serverHost, conf.serverPort),
            'workers': 4,
            'accesslog': '-',  # log to stdout
            'access_log_format': '%(h)s %(l)s %(t)s "%(r)s" %(s)s "%(a)s"'
        }
        StandaloneApplication(app, _options).run()


if __name__ == '__main__':
    runFlask()
