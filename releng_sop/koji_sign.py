# -*- coding: utf-8 -*-


"""
This module implements signing RPMs in koji.

The overall workflow is:
* get rpm_info_list from koji (latest builds from a tag, specified builds) -> rpm_info_list
* find RPMs with cached/uncached signatures -> (cached, uncached)
* determine if cached RPMs have signed/unsigned copies -> (signed, unsigned)
* look for signed main copies -> (signed_main, unsigned_main)
* signing process:

    * RPM has signed copy on disk -> SKIP
    * RPM has signed header in sigcache -> (1) WRITE FROM SIGCACHE
    * RPM has signed main copy that matches sigkeys -> (2) IMPORT FROM MAIN COPY
    * RPM has unsigned main copy -> (3) SIGN TO TEMP, IMPORT TO SIGCACHE, WRITE FROM SIGCACHE
"""


from __future__ import print_function

import base64
import logging
import multiprocessing.dummy
import os
import shutil
import subprocess
import tempfile

import koji

from .common import get_logger


__all__ = (
    "KojiSignRPMs",
    "get_rpmsign_class",
)


class KojiSignRPMs(object):
    """
    Sign RPMs and import them to a koji instance.

    :param koji_profile: Koji profile name
    :type  koji_profile: str
    :param rpmsign_class: Reference to a class that implements signing
    :type  rpmsign_class: object
    :param logger: Custom logger
    :type  logger: logging.Logger
    :param log_level: Log level for default logger (when logger is not set)
    :type  log_level: int
    """

    def __init__(self, koji_profile, rpmsign_class, logger=None, log_level=logging.INFO):  # noqa: D102
        self.koji_profile = koji_profile
        self.koji_module = koji.get_profile_module(self.koji_profile)
        self.koji_session = koji.ClientSession(self.koji_module.config.server)
        self.rpmsign_class = rpmsign_class
        self._get_rpm_sighdr_sigkey_cache = {}
        self.logger = logger or get_logger(self, log_level)

        if self.koji_module.config.authtype == "kerberos":
            self.koji_session.krb_login()

    def log(self, level, msg, commit=False):
        """
        Logging wrapper that prepeds [TEST] if commit is False.

        :param level: Logging level (info, debug, ...)
        :type  level: str
        :param msg: Message
        :type  msg: str
        :param commit: Disable dry-run, apply changes for real.
        :type  commit: bool=False
        """
        func = getattr(self.logger, level)
        if not commit:
            msg = "[TEST] %s" % msg
        func(msg)

    def get_latest_tagged_rpms(self, tag_name, inherit=False):
        """
        Return rpm_info list for latest tagged builds in a tag.

        :param tag_name: A koji tag name
        :type  tag_name: str
        :param inherit: Follow tag inheritance
        :type  inherit: bool=False
        :return: List of koji rpm_info dictionaries
        :rtype:  list
        """
        rpm_info_list, build_info_list = self.koji_session.listTaggedRPMS(tag_name, latest=True, inherit=inherit, rpmsigs=False)
        builds_by_id = {}
        for build_info in build_info_list:
            build_info["name"] = build_info["package_name"]
            builds_by_id[build_info["id"]] = build_info
        for rpm_info in rpm_info_list:
            rpm_info["build"] = builds_by_id[rpm_info["build_id"]]
        return rpm_info_list

    def get_build_rpms(self, build_list):
        """
        Return rpm_info list for specified builds.

        :param build_list: List of koji builds (NVRs)
        :type  build_list: list
        :return: List of koji rpm_info dictionaries
        :rtype:  list
        """
        result = []
        for build in build_list:
            build_info = self.koji_session.getBuild(build, strict=True)
            rpm_info_list = self.koji_session.listRPMs(buildID=build_info["id"])
            for rpm_info in rpm_info_list:
                rpm_info["build"] = build_info
            result.extend(rpm_info_list)
        return result

    def filter_rpm_info_list_by_packages(self, rpm_info_list, package_list):
        """
        Return rpm_info list filtered by specified packages.

        :param rpm_info_list: List of koji rpm_info dictionaries
        :type  rpm_info_list: list
        :param package_list: List of koji packages (SRPM names)
        :type  package_list: list
        :return: List of koji rpm_info dictionaries
        :rtype:  list
        """
        # convert to set, list lookups are slow
        package_list = set(package_list)

        result = []
        for rpm_info in rpm_info_list:
            if rpm_info["build"]["name"] not in package_list:
                continue
            result.append(rpm_info)
        return result

    def get_rpm_sig_dict(self, rpm_info_list):
        """
        Read information about cached signatures from koji.

        :param rpm_info_list: List of koji rpm_info dictionaries
        :type  rpm_info_list: list
        :return: {rpm_id: {sigkey: sighash}}
        :rtype:  dict
        """
        result = {}

        self.koji_session.multicall = True
        for rpm_info in rpm_info_list:
            self.koji_session.queryRPMSigs(rpm_info["id"])
        data = self.koji_session.multiCall(strict=True)

        for [sig_list] in data:
            for sig in sig_list:
                rpm_id = sig["rpm_id"]
                sigkey = sig["sigkey"].lower()
                sighash = sig["sighash"]
                result.setdefault(rpm_id, {})[sigkey] = sighash
        return result

    def find_cached(self, rpm_info_list, rpm_sig_dict, sigkeys):
        """
        Split rpm_info_list into (cached, uncached) according to cached sigs found in koji.

        :param rpm_info_list: List of koji rpm_info dictionaries
        :type  rpm_info_list: list
        :param rpm_sig_dict: A dictionary obtained from get_rpm_sig_dict() method
        :type  rpm_sig_dict: dict
        :param sigkeys: List of sigkeys
        :type  sigkeys: list
        :return: (cached, uncached) with rpm_info lists
        :rtype:  tuple
        """
        cached = []
        uncached = []

        sigkeys = set([i.lower() for i in sigkeys])
        for rpm_info in rpm_info_list:
            existing_sigs = set(rpm_sig_dict.get(rpm_info["id"], []))
            if existing_sigs & sigkeys:
                cached.append(rpm_info)
            else:
                uncached.append(rpm_info)

        return cached, uncached

    def _get_rpm_path(self, rpm_info, sigkey):
        """
        Return path to a signed or unsigned copy of an RPM in koji.

        :param rpm_info: Koji rpm_info dictionary
        :type  rpm_info: dict
        :param sigkey: Sigkey. Empty string or None for unsigned.
        :type  sigkey: str
        :return: Path to an RPM
        :rtype:  str
        """
        if sigkey:
            # signed
            path = os.path.join(self.koji_module.pathinfo.build(rpm_info["build"]), self.koji_module.pathinfo.signed(rpm_info, sigkey))
        else:
            # unsigned
            path = os.path.join(self.koji_module.pathinfo.build(rpm_info["build"]), self.koji_module.pathinfo.rpm(rpm_info))
        return path

    def _find_rpms(self, rpm_info_list, func):
        """
        A generic method for RPM lookups.

        The lookups are done in threads using multiprocessing.dummy.Pool.

        :param rpm_info_list: List of koji rpm_info dictionaries
        :type  rpm_info_list: list
        :param func: A match function that takes 2 arguments: (rpm_info, matches_by_rpm_id)
        :type  func: function
        :return: (matched, unmatched) koji rpm_info dictionaries
        :rtype:  tuple
        """
        matched = []
        unmatched = []
        matches_by_rpm_id = {}

        def _wrapped_func(rpm_info):
            return func(rpm_info, matches_by_rpm_id)

        # this creates a *threading* pool
        pool = multiprocessing.dummy.Pool(10)
        pool.map(_wrapped_func, rpm_info_list)
        pool.close()
        # pool.join()  # doesn't work on py2.7

        for rpm_info in rpm_info_list:
            if matches_by_rpm_id[rpm_info["id"]]:
                matched.append(rpm_info)
            else:
                unmatched.append(rpm_info)

        assert len(rpm_info_list) == len(matched) + len(unmatched)
        return matched, unmatched

    def find_signed_rpms(self, rpm_info_list, sigkeys):
        """
        Find signed RPM copies with specified sigkeys in given order.

        :param rpm_info_list: List of koji rpm_info dictionaries
        :type  rpm_info_list: list
        :param sigkeys: List of sigkeys
        :type  sigkeys: list
        :return: (matched, unmatched) koji rpm_info dictionaries
        :rtype:  tuple
        """
        sigkeys = [i.lower() for i in sigkeys]

        def _find_signed_rpm(rpm_info, matches_by_rpm_id):
            for sigkey in sigkeys:
                path = self._get_rpm_path(rpm_info, sigkey)
                if os.path.isfile(path):
                    matches_by_rpm_id[rpm_info["id"]] = True
                    return
            matches_by_rpm_id[rpm_info["id"]] = False

        signed, unsigned = self._find_rpms(rpm_info_list, _find_signed_rpm)
        assert len(rpm_info_list) == len(signed) + len(unsigned)
        return signed, unsigned

    def find_signed_rpms_in_main_copies(self, rpm_info_list, sigkeys):
        """
        Find signed RPMs in main copies.

        Main (unsigned) copies of RPMs are typically unsigned.
        They can be signed in rare situations such as imported signed 3rd party packages.
        In such case re-use existing signature rather than sign the RPMs again.

        :param rpm_info_list: List of koji rpm_info dictionaries
        :type  rpm_info_list: list
        :param sigkeys: List of sigkeys
        :type  sigkeys: list
        :return: (matched, unmatched) koji rpm_info dictionaries
        :rtype:  tuple
        """
        sigkeys = [i.lower() for i in sigkeys]
        signed = []
        unsigned = []

        def _find_signed_rpm_in_main_copies(rpm_info, matches_by_rpm_id):
            path = self._get_rpm_path(rpm_info, None)
            try:
                _, sigkey = self._get_rpm_sighdr_sigkey(path)
            except:
                sigkey = None
            if sigkey in sigkeys:
                self.logger.debug("Found a main copy signed with '%s': %s" % (sigkey, path))
                matches_by_rpm_id[rpm_info["id"]] = True
            else:
                self.logger.debug("Unsigned main copy: %s" % path)
                matches_by_rpm_id[rpm_info["id"]] = False

        signed, unsigned = self._find_rpms(rpm_info_list, _find_signed_rpm_in_main_copies)
        return signed, unsigned

    def write_signed_rpms_from_sigcache(self, rpm_info_list, sigkey, commit=False):
        """
        Reconstruct RPMs in koji from existing signed headers in sigcache.

        :param rpm_info_list: List of koji rpm_info dictionaries
        :type  rpm_info_list: list
        :param sigkey: Sigkey
        :type  sigkey: str
        :param commit: Disable dry-run, apply changes for real.
        :type  commit: bool=False
        """
        if commit:
            self.koji_session.multicall = True

        for rpm_info in rpm_info_list:
            path = self._get_rpm_path(rpm_info, sigkey)

            msg = "Writing RPM from '%s' sigcache: %s" % (sigkey, path)
            self.log("info", msg, commit=commit)

            if commit:
                self.koji_session.writeSignedRPM(rpm_info, sigkey)

        if commit:
            self.koji_session.multiCall(strict=True)

    def _get_rpm_sighdr_sigkey(self, path):
        """
        Read header and sigkey from an RPM.

        :param path: Path to a RPM package
        :type  path: str
        :return: (sighdr, sigkey)
        :rtype:  tuple
        """
        # I/O is expensive, cache RPM headers and sigkeys
        result = self._get_rpm_sighdr_sigkey_cache.get(path)
        if result:
            return result

        sighdr = koji.rip_rpm_sighdr(path)
        rawhdr = koji.RawHeader(sighdr)

        sigpkt = rawhdr.get(koji.RPM_SIGTAG_GPG)
        if not sigpkt:
            sigpkt = rawhdr.get(koji.RPM_SIGTAG_PGP)

        sigkey = ""
        if sigpkt:
            sigkey = koji.get_sigpacket_key_id(sigpkt)
        sigkey = sigkey.lower()

        result = (sighdr, sigkey)
        self._get_rpm_sighdr_sigkey_cache[path] = result
        return result

    def split_rpm_info_list_by_size_and_files(self, rpm_info_list, max_size=500, max_files=20):
        """
        Split rpm_info_list into chunks by max file size or file count.

        That should keep /tmp utilization in reasonable limits.

        :param rpm_info_list: List of koji rpm_info dictionaries
        :type  rpm_info_list: list
        :param max_size: Maximal size of files to be signed at once
        :type  max_size: int=500
        :param max_files: Maximal count of files to be signed at once
        :type  max_files: int=20
        :return: [[rpm_info, ...], ...]
        :rtype:  list
        """
        # make a copy, don't modify original
        rpm_info_list = rpm_info_list[:]

        while rpm_info_list:
            size = 0
            files = 0
            result = []

            while rpm_info_list:
                rpm_info = rpm_info_list.pop(0)
                result.append(rpm_info)
                size += rpm_info["size"]
                files += 1

                if max_files and files >= max_files:
                    break
                if max_size and size >= max_size * 1024 ** 2:
                    break

            yield result

    def copy_rpms_to_temp(self, rpm_info_list, commit=False):
        """
        The RPMs are signed in-place, that's why we need to work on copies in a temp directory.

        :param rpm_info_list: List of koji rpm_info dictionaries
        :type  rpm_info_list: list
        :param commit: Disable dry-run, apply changes for real.
        :type  commit: bool=False
        :return: (temp_dir, paths)
        :rtype:  tuple
        """
        temp_dir = None
        paths = []

        if not commit:
            return temp_dir, paths

        temp_dir = tempfile.mkdtemp(prefix="sign_rpms_")
        self.logger.info("Workdir: %s" % temp_dir)

        for rpm_info in rpm_info_list:
            src_path = self._get_rpm_path(rpm_info, None)
            dst_path = os.path.join(temp_dir, os.path.basename(src_path))
            shutil.copyfile(src_path, dst_path)
            paths.append(dst_path)

        return temp_dir, paths

    def sign_rpms_in_temp(self, sigkey, paths, commit=False):
        """
        Sign RPMs in temp (copies!) with a sigkey.

        The signing procedure is determined by self.rpmsign_class instance.

        :param sigkey: Sigkey
        :type  sigkey: str
        :param paths: Paths to RPM packages
        :type  paths: list
        :param commit: Disable dry-run, apply changes for real.
        :type  commit: bool=False
        """
        if not commit:
            return
        sign = self.rpmsign_class()
        sign.sign(sigkey, paths)

    def clean_temp(self, temp_dir, paths, commit=False):
        """
        Remove signed RPMs from temp, then remove the temp dir.

        :param temp_dir: Path to a temp directory with signer RPMs
        :type  temp_dir: str
        :param paths: Paths to RPM packages
        :type  paths: list
        :param commit: Disable dry-run, apply changes for real.
        :type  commit: bool=False
        """
        if not commit:
            return

        # remove only files and dirs we created; shutil.rmtree might be dangerous
        for path in paths:
            os.remove(path)
        os.rmdir(temp_dir)

    def import_signed_rpms(self, rpm_info_list, paths, sigkey, rpm_sig_dict=None, commit=False):
        """
        Import signed RPMs from temp to koji.

        :param rpm_info_list: List of koji rpm_info dictionaries
        :type  rpm_info_list: list
        :param paths: Paths to RPM packages
        :type  paths: list
        :param sigkey: Sigkey
        :type  sigkey: str
        :param rpm_sig_dict: A dictionary obtained from get_rpm_sig_dict() method
        :type  rpm_sig_dict: dict
        :param commit: Disable dry-run, apply changes for real.
        :type  commit: bool=False
        """
        if not commit:
            return

        # check if lists are equally long
        if len(rpm_info_list) != len(paths):
            raise ValueError("Arguments 'rpm_info_list' and 'paths' must be equally long")

        # check if filenames match at each position
        for rpm_info, path in zip(rpm_info_list, paths):
            rpm_info_fn = os.path.basename(self._get_rpm_path(rpm_info, None))
            path_fn = os.path.basename(path)
            if rpm_info_fn != path_fn:
                raise ValueError("File names in 'rpm_info' and 'path' do not match: %s vs %s" % (rpm_info_fn, path_fn))

        if not rpm_sig_dict:
            rpm_sig_dict = self.get_rpm_sig_dict(rpm_info_list)

        for (rpm_info, path) in zip(rpm_info_list, paths):
            rpm_sighdr, rpm_sigkey = self._get_rpm_sighdr_sigkey(path)
            if rpm_sigkey != sigkey:
                raise ValueError("Expected sigkey: %s; RPM is signed with '%s': %s" % (sigkey, rpm_sigkey, path))
            rpm_sighdr_base64 = base64.encodestring(rpm_sighdr)
            self.koji_session.addRPMSig(rpm_info["id"], rpm_sighdr_base64)

    def sign(self, rpm_info_list, sigkeys, just_sign=False, just_write=False, commit=False):
        """
        This method implements the signing workflow.

        It takes rpm_info_list as an argument to abstract
        getting RPMs from koji which can be:
          * RPMs of all tagged builds in a tag (& --inherit)
          * RPMs of latest tagged builds in a tag (& --inherit)
          * RPMs of specified builds
          * etc.

        :param rpm_info_list: List of koji rpm_info dictionaries
        :type  rpm_info_list: list
        :param sigkeys: List of sigkeys
        :type  sigkeys: list
        :param just_sign: Just sign RPMs, don't write RPMs from sigcache.
        :type  just_sign: bool=False
        :param just_write: Just write RPMs from sigcache, don't sign anything.
        :type  just_write: bool=False
        :param commit: Disable dry-run, apply changes for real.
        :type  commit: bool=False
        """
        # pick the first sigkey for signing
        sigkey = sigkeys[0]

        num_builds = len(set([i["build"]["id"] for i in rpm_info_list]))
        self.logger.info("Builds found: %s" % num_builds)
        self.logger.info("RPMs found:   %s" % len(rpm_info_list))

        # read known package signatures from koji and rearrange them into:
        # {rpm_id: {sigkey: sighash}}
        self.logger.info("Reading known package signatures from koji")
        rpm_sig_dict = self.get_rpm_sig_dict(rpm_info_list)

        # find RPMs with cached/uncached signatures
        cached, uncached = self.find_cached(rpm_info_list, rpm_sig_dict, sigkeys)
        self.logger.info("RPMs with cached signature:    %s" % len(cached))
        self.logger.info("RPMs without cached signature: %s" % len(uncached))

        # determine if cached RPMs have signed/unsigned copies
        signed, unsigned = self.find_signed_rpms(cached, sigkeys)
        self.logger.info("RPMs with cached signature and signed RPM:   %s" % len(signed))
        self.logger.info("RPMs with cached signature and unsigned RPM: %s" % len(unsigned))

        self.logger.info("Looking for signed main copies")
        if unsigned:
            signed_main, unsigned_main = self.find_signed_rpms_in_main_copies(unsigned, sigkeys)
            # signed_main, unsigned_main = self.find_signed_rpms_in_main_copies(unsigned, sigkeys)
            self.logger.info("RPMs with signed main copies:    %s" % len(signed_main))
            self.logger.info("RPMs without signed main copies: %s" % len(unsigned_main))
        else:
            signed_main = []
            unsigned_main = []
            self.logger.info("- Nothing to do")

        # Signing process:
        # RPM has signed copy on disk -> SKIP
        # RPM has signed header in sigcache -> (1) WRITE FROM SIGCACHE
        # RPM has signed main copy that matches sigkeys -> (2) IMPORT FROM MAIN COPY
        # RPM has unsigned main copy -> (3) SIGN TO TEMP, IMPORT TO SIGCACHE, WRITE FROM SIGCACHE

        # (1) write from sigcache
        if not just_sign:
            self.log("info", "Writing RPMs from sigcache", commit=commit)
            if unsigned:
                self.write_signed_rpms_from_sigcache(unsigned, sigkey, commit=commit)
            else:
                self.logger.info("- Nothing to do")

        # refresh signatures
        msg = "Reading known package signatures from koji (refresh)"
        self.logger.info(msg)
        rpm_sig_dict = self.get_rpm_sig_dict(rpm_info_list)

        # (2) import from main copy
        if signed_main:
            self.log("info", "Importing signed RPMs from main copies", commit=commit)
            for rpm_info in signed_main:
                # process one RPM at a time, they can be signed with different sigkeys
                # shouldn't have performance impact since this use case is quite rare

                # import sigs to koji
                paths = [self._get_rpm_path(i, None) for i in signed_main]
                path = self._get_rpm_path(i, None)
                rpm_sigkey = self._get_rpm_sighdr_sigkey(path)[1]
                self.import_signed_rpms([rpm_info], [path], rpm_sigkey, rpm_sig_dict, commit=commit)

                # write signed RPM
                if not just_sign:
                    self.write_signed_rpms_from_sigcache([rpm_info], sigkey, commit=commit)

        if not just_write:
            # (3) sign to temp, import to sigcache, write from sigcache
            self.log("info", "Signing and importing RPMs", commit=commit)
            if uncached:
                signed_count = 0
                for rpm_info_chunk in self.split_rpm_info_list_by_size_and_files(uncached, max_size=2):
                    # copy RPMs to temp
                    temp_dir, paths = self.copy_rpms_to_temp(rpm_info_chunk, commit=commit)

                    # sign RPMs in temp
                    self.sign_rpms_in_temp(sigkey, paths, commit=commit)

                    # import sigs to koji
                    self.import_signed_rpms(rpm_info_chunk, paths, sigkey, rpm_sig_dict, commit=commit)

                    # clean temp
                    self.clean_temp(temp_dir, paths, commit=commit)

                    # write signed RPMs
                    if not just_sign:
                        self.write_signed_rpms_from_sigcache(rpm_info_chunk, sigkey, commit=commit)

                    signed_count += len(rpm_info_chunk)
                    msg = "Signed %s/%s RPMs" % (signed_count, len(uncached))
                    self.log("info", msg, commit=commit)
            else:
                self.logger.info("- Nothing to do")

        msg = "All RPMs signed."
        self.log("info", msg, commit=commit)


def get_gpg_name(sigkey, gnupghome=None):
    """
    Resolve GPG sigkey ID (keyid) to name (uid).

    For example: 81b46521 -> Fedora (24) <fedora-24-primary@fedoraproject.org>

    :param sigkey: Sigkey ID (hash)
    :type  sigkey: str
    :param gnupghome: Path to GNUPG home directory
    :type  gnupghome: str=None
    :return: GPG key name (uid)
    :rtype:  str
    """
    # To generate a custom/testing GPG key, run:
    # gpg --gen-key
    # gpg --list-keys

    import gnupg

    gpg = gnupg.GPG(gnupghome=gnupghome)
    public_keys = gpg.list_keys()

    sigkey = sigkey.lower()
    for i in public_keys:
        keyid = i["keyid"][-8:].lower()
        if keyid == sigkey:
            return i["uids"][0]
    return None


class LocalRPMSign(object):
    def _sigkey_to_gpg_name(self, sigkey):
        """
        Convert sigkey to _gpg_name for RPM signing.

        Override this method if you want to change 'gnupghome'
        or if maintain the mappings manually

        :param sigkey: Sigkey ID (hash)
        :type  sigkey: str
        """
        return get_gpg_name(sigkey)

    def _get_cmd(self, sigkey, paths):
        """
        Create a signing command.

        :param sigkey: Sigkey ID (hash)
        :type  sigkey: str
        :param paths: Paths to RPMs to be signed
        :type  paths: str
        """
        gpg_name = self._sigkey_to_gpg_name(sigkey)
        cmd = ["rpm"]
        cmd.extend(["--define", "_gpg_name %s" % gpg_name])
        cmd.extend(["--resign"])
        cmd.extend(paths)
        return cmd

    def sign(self, sigkey, paths):
        """
        Sign RPMs in specified paths with a sigkey.

        :param sigkey: Sigkey ID (hash)
        :type  sigkey: str
        :param paths: Paths to RPMs to be signed
        :type  paths: str
        """
        cmd = self._get_cmd(sigkey, paths)
        return subprocess.check_call(cmd)


def get_rpmsign_class(env):
    """
    Get signing class for KojiSignRPMs from environment settings.
    """
    class_path = env["rpmsign_class"]
    module_name, class_name = class_path.rsplit(".", 1)
    mod = __import__(module_name, globals(), locals(), [class_name], 0)
    cls = getattr(mod, class_name)
    return cls
