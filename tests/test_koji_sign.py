#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
Tests for koji_sign module.
"""


import unittest

import os
import sys


# HACK: inject empty koji module to silence failing tests.
# We need to add koji to deps (currently not possible)
# or create a mock object for testing.
import imp
sys.modules["koji"] = imp.new_module("koji")


DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(DIR, ".."))

from releng_sop.common import Environment  # noqa: E402
from releng_sop.koji_sign import get_rpmsign_class, LocalRPMSign  # noqa: E402


RELEASES_DIR = os.path.join(DIR, "releases")
ENVIRONMENTS_DIR = os.path.join(DIR, "environments")


class TestRPMSignClass(unittest.TestCase):
    """
    Tests related to RPMSign classes.
    """

    longMessage = True

    def test_get_rpmsign_class(self):
        """Test if a RPMSign class can be properly loaded based on env settings."""
        env = Environment("test-env", config_dirs=[ENVIRONMENTS_DIR])
        cls = get_rpmsign_class(env)
        self.assertEqual(cls, LocalRPMSign)


if __name__ == "__main__":
    unittest.main()
