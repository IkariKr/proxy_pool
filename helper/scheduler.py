# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name:    proxyScheduler
   Description :
   Author :      JHao
   date:         2019/8/5
-------------------------------------------------
   Change Activity:
                   2019/08/05: proxyScheduler
                   2021/02/23: runProxyCheck 时, 剩余代理少于 POOL_SIZE_MIN 时执行抓取
-------------------------------------------------
"""
__author__ = 'JHao'

from datetime import datetime
import platform

from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler

from helper.check import Checker
from helper.fetch import Fetcher
from handler.configHandler import ConfigHandler
from handler.logHandler import LogHandler
from handler.proxyHandler import ProxyHandler
from util.six import Queue


def __runProxyFetch():
    proxy_queue = Queue()
    proxy_fetcher = Fetcher()

    for proxy in proxy_fetcher.run():
        proxy_queue.put(proxy)

    Checker("raw", proxy_queue)


def __runProxyCheck():
    proxy_handler = ProxyHandler()
    proxy_queue = Queue()
    if proxy_handler.db.getCount(qualified_only=True).get("total", 0) < proxy_handler.conf.poolSizeMin:
        __runProxyFetch()
    for proxy in proxy_handler.getAll(qualified_only=False, proxy_type="http") + \
            proxy_handler.getAll(qualified_only=False, proxy_type="socks5"):
        proxy_queue.put(proxy)
    Checker("use", proxy_queue)


def runScheduler():
    timezone = ConfigHandler().timezone
    scheduler_log = LogHandler("scheduler")
    scheduler = BlockingScheduler(logger=scheduler_log, timezone=timezone)

    # 中文：预热检查交给调度器立即执行，避免启动时同步抓取阻塞后续定时复检。
    # English: Let the scheduler trigger the bootstrap check immediately so startup fetches do not block recurring checks.
    scheduler.add_job(__runProxyCheck, 'date', run_date=datetime.now(), id="proxy_bootstrap_check",
                      name="proxy_bootstrap")
    scheduler.add_job(__runProxyFetch, 'interval', minutes=4, id="proxy_fetch", name="proxy_fetch")
    scheduler.add_job(__runProxyCheck, 'interval', minutes=2, id="proxy_check", name="proxy_check")
    executors = {
        'default': {'type': 'threadpool', 'max_workers': 20}
    }
    if platform.system() != "Windows":
        executors['processpool'] = ProcessPoolExecutor(max_workers=5)
    job_defaults = {
        'coalesce': False,
        'max_instances': 10
    }

    scheduler.configure(executors=executors, job_defaults=job_defaults, timezone=timezone)
    scheduler.start()


if __name__ == '__main__':
    runScheduler()
