# -*- coding: utf-8 -*-
"""Base class for koji commands."""
import subprocess


class KojiBase(object):
    """Base class for koji commands.

    :param env:        Environment object to be used to execute the commands.
    :type env:         str

    :param rel: Release object.
    :type rel:  str
    """

    def __init__(self, env, rel):  # noqa: D102
        self.env = env
        self.release_id = rel.name
        self.release = rel

    def run(self, commit=False):
        """Print command details, get command and run it."""
        self.print_details(commit=commit)
        cmd = self.get_cmd(commit=commit)
        print(cmd)
        subprocess.check_output(cmd)
