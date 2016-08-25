# -*- coding: utf-8 -*-
"""Base class for koji commands."""
import subprocess


class KojiBase(object):
    """Base class for koji commands.

    :param env:        Environment object to be used to execute the commands.
    :type env:         str

    :param rel: Release object.
    :type rel:  str

    :param packages:   Koji packages.
    :type packages:    list of str
    """

    def __init__(self, env, rel, packages):  # noqa: D102
        self.env = env
        self.release_id = rel.name
        self.release = rel
        self.packages = sorted(packages)

    def run(self, commit=False):
        """Print command details, get command and run it."""
        self.print_details(commit=commit)
        cmd = self.get_cmd(commit=commit)
        print(cmd)
        subprocess.check_output(cmd)
