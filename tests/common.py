# -*- coding: utf-8 -*-


"""
Test generate script.
"""


import imp
import os
import sys
from six import with_metaclass


class HelpNotEmptyMeta(type):
    """Test generator whether some help is empty."""

    def __new__(meta, name, bases, dct):
        """Create new test."""
        def gen_test(a):
            def test(self):
                for line in self.HELPTEXT:
                    if line.strip().startswith(a):
                        helpAtr = line.replace(a, '').strip()
                        self.assertNotEqual(len(helpAtr), 0, 'Help in %s argument is empty.' % a)
                        return
                self.assertTrue(False, '%s not in help text.' % a)
            return test

        for tname, a in dct.get('ARGUMENTS', dict()).items():
            test_name = "test_%s" % tname
            dct[test_name] = gen_test(a["arg"])
        return type.__new__(meta, name, bases, dct)


class ParserTestBase(with_metaclass(HelpNotEmptyMeta), object):
    """SetUpClass and tearDownClass for test generator whether some help is empty."""

    @classmethod
    def setUpClass(cls):
        """Set up variables before tests."""
        with open('test.txt', 'w') as f:
            cls.PARSER.print_help(f)

        cls.HELPTEXT = open('test.txt').read().split('\n')
        os.remove('test.txt')

    def test_commit_default(self):
        """Test whether --commit have default value False."""
        arguments = self.ARGUMENTS["commitHelp"]["commit_default"]
        args = self.PARSER.parse_args(arguments)
        self.assertTrue(hasattr(args, "commit"), 'commit argument is missing')
        self.assertFalse(args.commit, 'Default value for commit should be False')

    def test_commit_set(self):
        """Test whether --commit is set."""
        arguments = self.ARGUMENTS["commitHelp"]["commit_set"]
        args = self.PARSER.parse_args(arguments)
        self.assertTrue(args.commit, 'Value for commit should be True')

    def test_env_default(self):
        """Test whether --env have default value default."""
        arguments = self.ARGUMENTS["envHelp"]["env_default"]
        args = self.PARSER.parse_args(arguments)
        self.assertEqual("default", args.env, 'Default value for env should be default')

    def test_env_set(self):
        """Test whether --commit is set."""
        arguments = self.ARGUMENTS["envHelp"]["env_set"]
        args = self.PARSER.parse_args(arguments)
        self.assertTrue(hasattr(args, "env"), 'Env argument is set')


def mock_module(module_name):
    """
    Create an empty module.

    Use this to mock modules for testing if there's
    no resonable way how to install the module via setup.py.
    """
    head = module_name.split(".")
    tail = []

    # lookup for the longest available module path
    parent_mod = None
    while head:
        name = ".".join(head)
        try:
            mod = __import__(name)
            parent_mod = mod
            break
        except ImportError:
            pass
        tail.insert(0, head.pop())

    # create missing modules
    while tail:
        head.append(tail.pop(0))
        name = ".".join(head)
        mod = imp.new_module(name)
        sys.modules[name] = mod
        if parent_mod:
            setattr(parent_mod, head[-1], mod)
        parent_mod = mod
    return parent_mod
