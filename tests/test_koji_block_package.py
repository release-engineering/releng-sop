#!/usr/bin/python
# -*- coding: utf-8 -*-


"""Tests of KojiBlockPackageInRelease script.
"""


import unittest
import os
import sys
from mock import Mock

DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(DIR, ".."))

from releng_sop.common import Environment, Release  # noqa
from releng_sop.koji_block_package_in_release import get_parser, KojiBlockPackageInRelease  # noqa
from tests.common import ParserTestBase  # noqa


class TestKojiBlockPackage(unittest.TestCase):
    """Tests of methods from KojiBlockPackageInRelease class."""

    # Spec for fake Environment object
    env_spec = {
        'name': 'default',
        'config_path': 'some/file.json',
        'config_data': {
            'koji_profile': 'test'
        },
        '__getitem__': lambda self, item: self.config_data[item]
    }

    # Spec for fake Release object
    release_spec = {
        'name': 'test-release',
        'config_path': 'some.json',
        'config_data': {
            'koji': {
                'tag_release': 'test'
            },
        },
        '__getitem__': lambda self, item: self.config_data[item]
    }

    # Packages to be blocked
    packages = ['bash', 'vim']

    # Expected details text
    details = """Blocking packages in a release
 * env name:                {env[name]}
 * env config:              {env[config_path]}
 * release source           {release[config_path]}
 * koji profile:            {env[config_data][koji_profile]}
 * release_id:              {release[name]}
 * tag:                     {release[config_data][koji][tag_release]}
 * packages:
     {packages}
""".format(env=env_spec, release=release_spec, packages="\n     ".join(packages))

    # Expected command
    cmd = "koji --profile={profile} block-pkg {release_tag} {packages}".format(
        profile=env_spec['config_data']['koji_profile'],
        release_tag=release_spec['config_data']['koji']['tag_release'],
        packages=" ".join(packages)).split()

    @classmethod
    def setUpClass(cls):
        """Set up mocks and test object."""
        env = Mock(spec_set=list(cls.env_spec.keys()))
        env.configure_mock(**cls.env_spec)

        release = Mock(spec_set=list(cls.release_spec.keys()))
        release.configure_mock(**cls.release_spec)

        cls.clone = KojiBlockPackageInRelease(env, release, cls.packages)

    def test_details_no_commit(self):
        """Get details, while not commiting."""
        actual = self.clone.details()
        expected = self.details + "*** TEST MODE ***"
        self.assertEqual(actual, expected, self.test_details_no_commit.__doc__)

    def test_details_with_commit(self):
        """Get details when commiting."""
        actual = self.clone.details(commit=True)
        expected = self.details
        self.assertEqual(actual, expected, self.test_details_with_commit.__doc__)

    def test_get_cmd_no_commit(self):
        """Get command, while not commiting."""
        actual = self.clone.get_cmd()
        expected = ["echo"] + self.cmd
        self.assertEqual(actual, expected, self.test_get_cmd_no_commit.__doc__)

    def test_get_cmd_with_commit(self):
        """Get command when commiting."""
        actual = self.clone.get_cmd(commit=True)
        expected = self.cmd
        self.assertEqual(actual, expected, self.test_get_cmd_with_commit.__doc__)


class TestKojiBlockPackageParser(ParserTestBase, unittest.TestCase):
    """Set Arguments and Parser for Test generator."""

    ARGUMENTS = {
        'envHelp': {
            'arg': '--env ENV',
            'env_default': ['fedora-24', 'bash'],
            'env_set': ['fedora-24', 'bash', "--env", "some_env"],
        },
        'commitHelp': {
            'arg': '--commit',
            'commit_default': ['fedora-24', 'bash'],
            'commit_set': ['fedora-24', 'bash', "--commit"],
        },
        'helpReleaseId': {
            'arg': 'RELEASE_ID',
        },
        'helpPackage': {
            'arg': 'PACKAGE',
        },
    }

    PARSER = get_parser()


if __name__ == "__main__":
    unittest.main()
