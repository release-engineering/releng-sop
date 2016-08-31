#!/usr/bin/python
# -*- coding: utf-8 -*-


"""Tests of KojiCreatePackageInRelease script.
"""


import unittest
import os
import sys
from mock import Mock

DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(DIR, ".."))

from releng_sop.common import Environment, Release  # noqa
from releng_sop.koji_create_package_in_release import get_parser, KojiCreatePackageInRelease  # noqa
from tests.common import ParserTestBase  # noqa


class TestKojiCreatePackage(unittest.TestCase):
    """Tests of methods from KojiCreatePackageInRelease class."""

    env_spec = {
        'name': 'default',
        'config_path': 'some/file.json',
        'config_data': {
            'koji_profile': 'test'
        },
        '__getitem__': lambda self, item: self.config_data[item]
    }

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

    packages = ['bash']
    owner = 'test'

    # Expected details text
    details = """Creating packages in a release
 * env name:                {env[name]}
 * env config:              {env[config_path]}
 * release source           {release[config_path]}
 * koji profile:            {env[config_data][koji_profile]}
 * release_id:              {release[name]}
 * owner:                   {owner}
 * tag:                     {release[config_data][koji][tag_release]}
 * packages:
     {packages}
""".format(env=env_spec, owner=owner, release=release_spec, packages="\n     ".join(packages))

    # Expected command
    cmd = "koji --profile={profile} add-pkg --owner={owner} {release_tag} {packages}".format(
        profile=env_spec['config_data']['koji_profile'],
        owner=owner,
        release_tag=release_spec['config_data']['koji']['tag_release'],
        packages=" ".join(packages)).split()

    @classmethod
    def setUpClass(cls):
        """Set up variables before tests."""
        env = Mock(spec_set=list(cls.env_spec.keys()))
        env.configure_mock(**cls.env_spec)

        release = Mock(spec_set=list(cls.release_spec.keys()))
        release.configure_mock(**cls.release_spec)

        cls.clone = KojiCreatePackageInRelease(env, release, cls.packages, cls.owner)

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


class TestKojiCreatePackageParser(ParserTestBase, unittest.TestCase):
    """Set Arguments and Parser for Test generator."""

    ARGUMENTS = {
        'envHelp': {
            'arg': '--env ENV',
            'env_default': ['--owner=test', 'fedora-24', 'bash'],
            'env_set': ['--owner=test', 'fedora-24', 'bash', "--env", "some_env"],
        },
        'commitHelp': {
            'arg': '--commit',
            'commit_default': ['--owner=test', 'fedora-24', 'bash'],
            'commit_set': ['--owner=test', 'fedora-24', 'bash', '--commit'],
        },
        'helpReleaseId': {
            'arg': 'RELEASE_ID',
        },
        'helpPackage': {
            'arg': 'PACKAGE',
        },
        'helpOwner': {
            'arg': '--owner',
        },
    }

    PARSER = get_parser()

if __name__ == "__main__":
    unittest.main()
