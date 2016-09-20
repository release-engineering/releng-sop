#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
Tests for Pulp common code.
"""


import unittest

import os
import sys

DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(DIR, ".."))


# ----------
# HACK: mock pulp.client.admin.config module to silence failing tests.
from tests.common import mock_module  # noqa: E402
import six.moves.configparser  # noqa: E402

mod = mock_module("pulp.client.admin.config")


def read_config(paths, *args, **kwargs):
    """
    Mock function for pulp.client.admin.config.read_config().
    """
    cp = six.moves.configparser.RawConfigParser()
    cp.read(paths[0])
    return cp._sections


mod.read_config = read_config
# ----------


from releng_sop.common_pulp import PulpAdminConfig  # noqa: E402


PULP_ADMIN_CONFIG_DIR = os.path.join(DIR, "pulp", "admin")


class TestPulpAdminConfig(unittest.TestCase):
    """Test Pulp admin configuration data found in PULP_ADMIN_CONFIG_DIR."""

    longMessage = True

    def _get_pulp_configs(self):
        result = []
        for fn in os.listdir(PULP_ADMIN_CONFIG_DIR):
            if not fn.endswith(PulpAdminConfig.config_suffix):
                continue
            result.append(fn[:-len(PulpAdminConfig.config_suffix)])
        return result

    def test_pulp_configs(self):
        """Read all config files from PULP_ADMIN_CONFIG_DIR, and check data structure."""
        configs = self._get_pulp_configs()
        for config_name in configs:
            context = "\n\nconfig_name: %s" % config_name
            conf = PulpAdminConfig(config_name, config_dirs=[PULP_ADMIN_CONFIG_DIR])

            self.assertTrue("server" in conf, context)
            self.assertTrue("client" in conf, context)

            self.assertEqual(conf["server"]["host"], "%s.example.com" % config_name, context)
            self.assertEqual(conf["client"]["role"], "admin", context)


if __name__ == "__main__":
    unittest.main()
