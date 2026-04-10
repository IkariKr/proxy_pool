# -*- coding: utf-8 -*-

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import helper.scheduler as scheduler_module


class FakeScheduler(object):

    def __init__(self, logger=None, timezone=None):
        self.logger = logger
        self.timezone = timezone
        self.jobs = []
        self.configured = None
        self.started = False

    def add_job(self, func, trigger, **kwargs):
        self.jobs.append({
            "func": func,
            "trigger": trigger,
            "kwargs": kwargs
        })

    def configure(self, **kwargs):
        self.configured = kwargs

    def start(self):
        self.started = True


class SchedulerTests(unittest.TestCase):

    def test_run_scheduler_bootstraps_with_immediate_check_job(self):
        created = {}

        def build_scheduler(logger=None, timezone=None):
            scheduler = FakeScheduler(logger=logger, timezone=timezone)
            created["scheduler"] = scheduler
            return scheduler

        with patch.object(scheduler_module, "BlockingScheduler", side_effect=build_scheduler), \
                patch.object(scheduler_module, "LogHandler", return_value="scheduler-log"), \
                patch.object(scheduler_module, "ProcessPoolExecutor", return_value="process-pool"), \
                patch.object(scheduler_module.platform, "system", return_value="Linux"), \
                patch.object(scheduler_module, "ConfigHandler") as config_handler, \
                patch.object(scheduler_module, "__runProxyFetch") as run_proxy_fetch, \
                patch.object(scheduler_module, "__runProxyCheck") as run_proxy_check:
            config_handler.return_value.timezone = "Asia/Shanghai"

            scheduler_module.runScheduler()

        scheduler = created["scheduler"]
        self.assertTrue(scheduler.started)
        self.assertEqual(run_proxy_fetch.call_count, 0)
        self.assertEqual(run_proxy_check.call_count, 0)
        self.assertEqual(len(scheduler.jobs), 3)
        self.assertEqual(scheduler.jobs[0]["func"], run_proxy_check)
        self.assertEqual(scheduler.jobs[0]["trigger"], "date")
        self.assertEqual(scheduler.jobs[0]["kwargs"]["id"], "proxy_bootstrap_check")
        self.assertEqual(scheduler.jobs[1]["func"], run_proxy_fetch)
        self.assertEqual(scheduler.jobs[1]["trigger"], "interval")
        self.assertEqual(scheduler.jobs[2]["func"], run_proxy_check)
        self.assertEqual(scheduler.jobs[2]["trigger"], "interval")
        self.assertIn("processpool", scheduler.configured["executors"])

    def test_run_scheduler_skips_processpool_on_windows(self):
        created = {}

        def build_scheduler(logger=None, timezone=None):
            scheduler = FakeScheduler(logger=logger, timezone=timezone)
            created["scheduler"] = scheduler
            return scheduler

        with patch.object(scheduler_module, "BlockingScheduler", side_effect=build_scheduler), \
                patch.object(scheduler_module, "LogHandler", return_value="scheduler-log"), \
                patch.object(scheduler_module, "ProcessPoolExecutor", return_value="process-pool"), \
                patch.object(scheduler_module.platform, "system", return_value="Windows"), \
                patch.object(scheduler_module, "ConfigHandler") as config_handler, \
                patch.object(scheduler_module, "__runProxyFetch") as run_proxy_fetch, \
                patch.object(scheduler_module, "__runProxyCheck") as run_proxy_check:
            config_handler.return_value.timezone = "Asia/Shanghai"

            scheduler_module.runScheduler()

        scheduler = created["scheduler"]
        self.assertTrue(scheduler.started)
        self.assertEqual(run_proxy_fetch.call_count, 0)
        self.assertEqual(run_proxy_check.call_count, 0)
        self.assertNotIn("processpool", scheduler.configured["executors"])


if __name__ == '__main__':
    unittest.main()
