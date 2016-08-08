#!/usr/bin/python
# -*- coding: utf-8 -*-


import unittest

import os
import sys

DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(DIR, ".."))

from releng_sop.common import Environment, Release  # noqa


RELEASES_DIR = os.path.join(DIR, "releases")
ENVIRONMENTS_DIR = os.path.join(DIR, "environments")


class TestReleaseData(unittest.TestCase):
    longMessage = True

    def _get_releases(self):
        result = []
        for fn in os.listdir(RELEASES_DIR):
            if not fn.endswith(".json"):
                continue
            result.append(fn[:-5])
        return result

    def test_releases(self):
        releases = self._get_releases()
        for release_id in releases:
            release = Release(release_id, config_dirs=[RELEASES_DIR])

            # check distgit data
            expected = [
                "branch",
            ]
            self.assertEqual(sorted(release["distgit"]), expected, "\n\nrelease_id: %s" % release_id)

            # check koji data
            expected = [
                "tag_bootstrap",
                "tag_build",
                "tag_buildrequires",
                "tag_candidate",
                "tag_compose",
                "tag_override",
                "tag_pending",
                "tag_release",
                "tag_temp_override",
                "target",
            ]
            self.assertEqual(sorted(release["koji"]), expected, "\n\nrelease_id: %s" % release_id)


class TestEnvironmentData(unittest.TestCase):
    longMessage = True

    def _get_environments(self):
        result = []
        for fn in os.listdir(ENVIRONMENTS_DIR):
            if not fn.endswith(".json"):
                continue
            result.append(fn[:-5])
        return result

    def test_environments(self):
        environments = self._get_environments()
        for env_id in environments:
            env = Environment(env_id, config_dirs=[ENVIRONMENTS_DIR])

            expected = [
                "distgit_server",
                "koji_profile",
            ]
            self.assertEqual(sorted(env), expected, "\n\nenv_id: %s" % env_id)


if __name__ == "__main__":
    unittest.main()
