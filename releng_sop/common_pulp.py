# -*- coding: utf-8 -*-


"""
Common code for Pulp.
"""


import os

import pulp.client.admin.config
import xdg.BaseDirectory

from . import common


__all__ = (
    "PulpAdminConfig",
)


class PulpConfigBase(common.ConfigBase):
    config_suffix = ".conf"

    def _set_config_dirs(self, config_dirs=None):
        """
        Set list of config dirs in priority order.
        """
        self.config_dirs = []
        if config_dirs:
            # set user defined paths
            self.config_dirs += config_dirs
        else:
            # set userdir and system conf dirs
            self.config_dirs.append(os.path.join(xdg.BaseDirectory.xdg_config_home, "pulp", self.config_subdir))
            self.config_dirs.append(os.path.join("/etc", "pulp", self.config_subdir))

    def _read_config(self):
        """
        Read config file contents.
        """
        self.config_data = pulp.client.admin.config.read_config(paths=[self.config_path])


class PulpAdminConfig(PulpConfigBase):
    """
    Pulp admin configs are expected to be found in following locations.

    * ~/.config/pulp/admin/<name>.conf
    * /etc/pulp/admin/<name>.conf
    """

    config_subdir = "admin"
