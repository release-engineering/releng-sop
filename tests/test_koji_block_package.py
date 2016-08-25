#!/usr/bin/python
# -*- coding: utf-8 -*-


"""Tests of BlockPackageInRelease script.
"""


import unittest
import os
import sys

DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(DIR, ".."))

from releng_sop.common import Environment, Release  # noqa
from releng_sop.koji_block_package_in_release import get_parser  # noqa
from releng_sop.koji_block_package_in_release import KojiBlockPackageInRelease  # noqa

l = [["envHelp", "--env ENV"], ["commitHelp", "--commit "], ["helpReleaseId", "RELEASE_ID  "], ["helpPackage", "PACKAGE  "]]

RELEASES_DIR = os.path.join(DIR, "releases")
ENVIRONMENTS_DIR = os.path.join(DIR, "environments")


class TestKojiBlockPackage(unittest.TestCase):
    """Tests of methods from KojiBlockPackageInRelease class."""

    def setUp(self):
        """Set up variables before tests."""
        parser = get_parser()
        arguments = ['test-release', 'bash']
        args = parser.parse_args(arguments)
        env = Environment(args.env)
        self.clone = KojiBlockPackageInRelease(env, args.release_id, args.packages)

    def test_details(self):
        """Test return data of details method."""
        test = self.clone.details(commit=False)

        expectation = """Blocking packages in a release
 * env name:                default
 * env config:              /home/jcupova/.config/releng-sop/environments/test-env.json
 * release source           /home/jcupova/.config/releng-sop/releases/test-release.json
 * koji profile:            test
 * release_id:              test-release
 * tag:                     test
 * packages:
     bash
*** TEST MODE ***"""

        self.assertEqual(test, expectation, 'Method print_details has any mistakes.')

    def test_get_cmd(self):
        """Test return data of get_cmd method."""
        commit = False
        testCmd = self.clone.get_cmd(commit=False)

        expectation = []
        expectation.append("koji")
        expectation.append("--profile=test")
        expectation.append("block-pkg")
        expectation.append('test')
        expectation.append('bash')
        if not commit:
            expectation = ["echo"] + expectation

        self.assertEqual(testCmd, expectation, 'Method get_cmd has any mistakes.')


class TestKojiBlockPackageGetParser(unittest.TestCase):
    """Tests of arguments from get_parser function."""

    longMessage = True

    def setUp(self):
        """Set up variables before tests."""
        parser = get_parser()
        with open('test.txt', 'w') as f:
            parser.print_help(f)

    def tearDown(self):
        """Clean space after tests."""
        os.remove('test.txt')

    def test_commit_default(self):
        """Test whether --commit have default value False."""
        parser = get_parser()
        arguments = ['fedora-24', 'bash']
        args = parser.parse_args(arguments)
        self.assertTrue(hasattr(args, "commit"), 'commit argument is missing')
        self.assertFalse(args.commit, 'Default value for commit should be False')

    def test_commit_set(self):
        """Test whether --commit is set."""
        parser = get_parser()
        arguments = ['fedora-24', 'bash', "--commit"]
        args = parser.parse_args(arguments)
        self.assertTrue(args.commit, 'Value for commit should be True')

    def test_env_default(self):
        """Test whether --env have default value default."""
        parser = get_parser()
        arguments = ['fedora-24', 'bash']
        args = parser.parse_args(arguments)
        self.assertEqual("default", args.env, 'Default value for env should be default')

    def test_env_set(self):
        """Test whether --commit is set."""
        parser = get_parser()
        arguments = ['fedora-24', 'bash', "--env", "some_env"]
        args = parser.parse_args(arguments)
        self.assertTrue(hasattr(args, "env"), 'Env argument is set')


def test_generator_help_not_empty(a):
    """Test generator whether some help is empty."""
    def test(self):
        with open('test.txt', 'r') as f:
            for line in f:
                if a in line:
                    helpAtr = line.replace(a, '').strip()
        self.assertNotEqual(len(helpAtr), 0, 'Help in %s argument is empty.' % a)
    return test

if __name__ == "__main__":
    for t in l:
        test_name = 'test_%s' % t[0]
        test = test_generator_help_not_empty(t[1])
        setattr(TestKojiBlockPackageGetParser, test_name, test)
    unittest.main()
