# -*- coding: utf-8 -*-

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import api.proxyApi as proxy_api


class ProxyApiTests(unittest.TestCase):

    def test_run_flask_disables_reloader_on_windows(self):
        with patch.object(proxy_api.platform, "system", return_value="Windows"), \
                patch.object(proxy_api.app, "run") as app_run:
            proxy_api.runFlask()

        app_run.assert_called_once_with(
            host=proxy_api.conf.serverHost,
            port=proxy_api.conf.serverPort,
            use_reloader=False
        )


if __name__ == '__main__':
    unittest.main()
