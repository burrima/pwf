#!/usr/bin/env python3
# Copyright 2024 Martin Burri
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from collections import defaultdict
from pathlib import Path
import argparse
import common
import copy
import logging
import re
import stat


logger = logging.getLogger(__name__)


info_text=\
    """
IGNORELIST
    cs    ignore wrong checksums
    dup   ignore duplicates
    miss  ignore missing files (compared to md5 checksum file)
    name  ignore name violations (not allowed!)
    path  ingore path violations
    prot  ignore protection violations
    raw   ignore RAW derivatives

Performs various checks against the given folder:
    * file and folder names
    * duplicates
    * RAW derivatives (files other than RAW but with same name pattern)
    * file and folder protection (useful only for 1_original/ folders)
    * MD5 checksums (useful only for 1_original/ folders)
    * Missing files (compared to MD5 checksum file) - not done when MD5
      checking is enabled (is covered by MD5 checking)
    * file and folder structure (path)
Checks can be disabled individually, see OPTIONS above.
    """ + common.fzf_info_text

things_to_check = {"cs", "dup", "miss", "name", "path", "prot", "raw"}


def _check_names(pwf_path: common.PwfPath):
    logger.info("check names...")

    regex = rf"^[{common.legal_characters}]+$"
    found_any = False

    for p in [pwf_path.path] + list(pwf_path.path.glob("**/*")):
        logger.debug(f"  {p.name}")
        if not re.match(regex, p.name):
            logger.info(f"Illegal: '{p.name}'")
            found_any = True

    if found_any:
        raise AssertionError("Found illegal chars in file or folder names!")


def _fix_names(pwf_path: common.PwfPath, isNono: bool):
    logger.info("fix names...")

    regex = rf"^[{common.legal_characters}]+$"
    name_replacements = [
        (" ", "_"),
        ("&", "und"),
        ("-_", "")]

    if isNono:
        logger.info("Dry-run: would do the following:")

    files_to_fix = []
    for p in list(pwf_path.path.glob("**/*")) + [pwf_path.path]:
        logger.debug(f"  {p.name}")
        if not re.match(regex, p.name):
            files_to_fix.append(p)

    for p in files_to_fix:
        newname = p.name
        for r in name_replacements:
            newname = newname.replace(r[0], r[1])
        logger.info(f"  '{p.name}' -> '{newname}'")
        if not isNono:
            new_p = p.replace(p.parent / newname)
            if p == pwf_path.path:
                pwf_path.path = new_p


def _check_duplicates(pwf_path: common.PwfPath):
    logger.info("check duplicates...")

    # find potential duplicates by size (much faster!):
    by_size = defaultdict(list)
    for p in pwf_path.path.glob("**/*"):
        if p.is_file():
            by_size[p.stat().st_size].append(p)
    logger.debug(by_size)

    # from potential duplicates, compute md5 sum:
    by_md5 = defaultdict(list)
    for paths in by_size.values():
        if len(paths) < 2:
            continue
        for p in paths:
            # optimized: is_partial=True ready only first 8k data!
            by_md5[common.md5sum(p, is_partial=True)].append(p)
    logger.debug(by_md5)

    # identify and report duplicate files:
    found_any = False
    for paths in by_md5.values():
        if len(paths) < 2:
            continue
        found_any = True
        logger.info("Found identical files:")
        for p in paths:
            logger.info(f"    {p}")

    if found_any:
        raise AssertionError("Found duplicate files!")


def _check_protection(pwf_path: common.PwfPath):
    logger.info("check protection...")

    found_any = False

    for p in [pwf_path.path] + list(pwf_path.path.glob("**/*")):
        mode = p.stat(follow_symlinks=False).st_mode
        ogo_mode = oct(mode)[-3:]
        is_locked = ((int(ogo_mode, 16) & 0x222) == 0)
        if not is_locked:
            logger.info(f"Not protected: {stat.filemode(mode)} {p}")
            found_any = True

    if found_any:
        raise AssertionError("Found unprotected files or directories!")


def _check_raw_derivates(pwf_path: common.PwfPath):
    logger.info("check raw derivatives...")


def _check_paths(pwf_path: common.PwfPath):
    logger.info("check paths...")


def _check_checksums(pwf_path: common.PwfPath):
    logger.info("check checksums...")


def _check_missing_files(pwf_path: common.PwfPath):
    logger.info("check missing files...")


def check(path: Path, ignorelist: set=None, onlylist: set=None,
          doFix: bool=False, isNono: bool=False):
    logger.info("pwf-check: ENTRY")

    if ignorelist is None:
        ignorelist = set()
    if onlylist is None:
        onlylist = set()

    # parse and check path:
    pwf_path = common.PwfPath(path)

    if "name" in ignorelist:
        logger.warning("WARNING: Ignoring name violations is strongly discouraged!")

    if pwf_path.state == common.State.NEW:
        if "dup" in ignorelist:
            raise ValueError("Ignoring duplicate violations is not allowed!")
        if "path" in ignorelist:
            raise ValueError("Ignoring path violations is not allowed!")

    if pwf_path.state == common.State.NEW:
        ignorelist.update({"cs", "miss", "prot"})
    elif pwf_path.state == common.State.LAB:
        ignorelist.update({"cs", "miss", "prot", "path"})

    checklist = copy.copy(things_to_check) if len(onlylist) == 0 else onlylist
    checklist -= ignorelist

    logger.debug(f"{pwf_path=}, {checklist=}, {doFix=}, {isNono=}")

    if "name" in checklist:
        if doFix:
            _fix_names(pwf_path, isNono)
            # update pwf_path because path might have changed:
            pwf_path = common.PwfPath(pwf_path.path)
        _check_names(pwf_path)

    if "dup" in checklist:
        _check_duplicates(pwf_path)

    if "prot" in checklist:
        _check_protection(pwf_path)

    if "raw" in checklist:
        _check_raw_derivates(pwf_path)

    if "path" in checklist:
        _check_paths(pwf_path)

    if "cs" in checklist:
        _check_checksums(pwf_path)

    if "miss" in checklist:
        _check_missing_files(pwf_path)

    logger.info("pwf-check: OK")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=info_text)

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-i", "--ignorelist",
                       help="ignore check by list of comma-separated items")
    group.add_argument("-o", "--onlylist",
                       help="check only the things listed (see IGNORELIST)")

    parser.add_argument("-f", "--fix",
                        help="auto-fix wrong names if possible",
                        action="store_true")
    parser.add_argument("-n", "--nono",
                        help="nono, dry-run, only print what would be done",
                        action="store_true")
    parser.add_argument("-l", "--loglevel",
                        help="log level to use",
                        default="INFO")
    parser.add_argument("path", nargs='?', default=Path.cwd())
    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=args.loglevel.upper())
    logger.debug(f"{args=}")

    ignorelist = None
    if args.ignorelist is not None:
        ignorelist = set(args.ignorelist.split(","))
        if not ignorelist.issubset(things_to_check):
            raise ValueError("Invalid IGNORELILST provided!")

    onlylist=None
    if args.onlylist is not None:
        onlylist = set(args.onlylist.split(","))
        if not onlylist.issubset(things_to_check):
            raise ValueError("Invalid ONLYLIST provided!")

    check(args.path, ignorelist, onlylist, args.fix, args.nono)
