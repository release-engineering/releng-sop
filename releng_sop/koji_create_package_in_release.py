# -*- coding: utf-8 -*-
"""Create packages in a release.

Constructs the koji command

    koji --profile=KOJI_PROFILE add-pkg --owner=OWNER RELEASE_TAG PACKAGES...

KOJI_PROFILE is obtained from the environment settings.

RELEASE_TAG is the "tag_release" key from the release configuration
    corresponding to the release id.
"""

from __future__ import print_function
from __future__ import unicode_literals

import argparse

from .common import Environment, Release
from .kojibase import KojiBase


class KojiCreatePackageInRelease(KojiBase):
    """
    Create packages in a release.

    :param env:        Environment object to be used to execute the commands.
    :type env:         Environment

    :param release: Release object.
    :type release:  Release

    :param packages: name of package to be created in a release
    :type packages:  list of str

    :param owner:   package owner
    :type owner:    str
    """

    def __init__(self, env, release, packages, owner):
        """Adding packages for create and owner as an aditional member."""
        super(KojiCreatePackageInRelease, self).__init__(env, release)
        self.packages = sorted(packages)
        self.owner = owner

    def print_details(self, commit=False):
        """Print details of command execution.

        :param commit: Flag to indicate if the command will be actually executed.
                       Line indicating "test mode" is printed, if this is False.
        :type commit:  boolean; default False
        """
        print("Blocking packages in a release")
        print(" * env name:                %s" % self.env.name)
        print(" * env config:              %s" % self.env.config_path)
        print(" * release source           %s" % self.release.config_path)
        print(" * koji profile:            %s" % self.env["koji_profile"])
        print(" * release_id:              %s" % self.release_id)
        print(" * owner:                   %s" % self.owner)
        print(" * tag:                     %s" % self.release["koji"]["tag_release"])
        print(" * packages:")
        for i in self.packages:
            print("     %s" % i)
        if not commit:
            print("*** TEST MODE ***")

    def get_cmd(self, commit=False):
        """Construct the koji command.

        :param commit: Flag to indicate if the command will be actually executed.
                       "echo" is prepended to the command, if this is False.
        :type commit:  boolean; default False
        :returns:      Koji command.
        :rtype:        list of strings
        """
        cmd = []
        cmd.append("koji")
        cmd.append("--profile=%s" % self.env["koji_profile"])
        cmd.append("add-pkg")
        cmd.append("--owner=%s" % self.owner)
        cmd.append(self.release["koji"]["tag_release"])
        cmd.extend(self.packages)
        if not commit:
            cmd = ["echo"] + cmd
        return cmd


def get_parser():
    """Construct argument parser.

    :returns: ArgumentParser object with arguments set up.
    """
    parser = argparse.ArgumentParser(
        description="Block packages in a koji tag that maps to given release.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "release_id",
        metavar="RELEASE_ID",
        help="PDC release ID, for example 'fedora-24', 'fedora-24-updates'.",
    )
    parser.add_argument(
        "packages",
        metavar="PACKAGE",
        nargs="+",
        help="Koji package, for example 'bash', 'kernel'.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Program performs a dry-run by default. Enable this option to apply the changes.",
    )
    parser.add_argument(
        "--owner",
        required=True,
        default=argparse.SUPPRESS,
        help="Package owner",
    )
    parser.add_argument(
        "--env",
        default="default",
        help="Select environment in which the program will make changes.",
    )
    return parser


def main():
    """Main function."""
    parser = get_parser()
    args = parser.parse_args()
    env = Environment(args.env)
    release = Release(args.release_id)
    clone = KojiCreatePackageInRelease(env, release, args.packages, args.owner)
    clone.run(commit=args.commit)


if __name__ == "__main__":
    main()
