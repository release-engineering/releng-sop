# -*- coding: utf-8 -*-
"""Base class for koji commands."""
import subprocess

from .common import Release


class KojiBase(object):
    """Base class for koji commands.

    :param env:        Name of the environment to be used to execute the commands.
    :type env:         str

    :param release_id: PDC release ID.
    :type release_id:  str

    :param packages:   Koji packages.
    :type packages:    list of str
    """

    def __init__(self, env, release_id, packages):  # noqa: D102
        self.env = env
        self.release_id = release_id
        self.release = Release(self.release_id)
        self.packages = sorted(packages)

    def run(self, commit=False):
        """Print command details, get command and run it."""
        self.print_details(commit=commit)
        cmd = self.get_cmd(commit=commit)
        print(cmd)
        subprocess.check_output(cmd)
