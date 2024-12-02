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
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#


from bin import common
from bin.common import compute_md5sum, pwf_path
from collections import defaultdict
from pathlib import Path
import argparse
import copy
import logging
import re
import stat


logger = logging.getLogger(__name__)


info_text =\
    """
Performs various checks against the given path. Checks can be disabled
individually (see IGNORELIST). The inverse logic is possible as well, by
enabling just what needs to be checked (see ONLYLIST).

Checking the path ensures that files and directory structure are
compliant to the assumptions made by the PWF scripts. It is particularly
important to keep the 1_original/ folder clean from violations.

IGNORELIST/ONLYLIST
    cs    MD5 checksums
    dup   duplicates
    miss  missing files (compared to md5 checksum file)
    name  name violations
    path  path structure
    prot  protection violations (for 1_original/)
    raw   RAW derivatives (with same name pattern)
    """ + common.loglevel_info_text + common.fzf_info_text


things_to_check = {"cs", "dup", "miss", "name", "path", "prot", "raw"}


def _check_names(path: Path):
    """
    Verifies that all files and subdirs (recursive!) in the path only contain
    legal characters (as per common.legal_characters).
    """
    logger.info("check names...")

    regex = rf"^[{common.legal_characters}]+$"
    found_any = False

    for p in [path] + list(path.glob("**/*")):
        logger.debug(f"name: {p.name}")
        if not re.match(regex, p.name):
            logger.info(f"Illegal: '{pwf_path(p)}'")
            found_any = True

    if found_any:
        raise AssertionError("Found illegal chars in file or folder names!")


def _fix_names(path: Path, is_nono: bool):
    """
    Tries to fix illegal names as per common.name_replacements.
    """
    logger.info("fix names...")

    regex = rf"^[{common.legal_characters}]+$"

    if is_nono:
        logger.info("Dry-run: would do the following:")

    files_to_fix = []
    paths = list(path.glob("**/*")) + [path]  # include path itself

    for p in sorted(paths, reverse=True):  # from subdirs to top...
        if not re.match(regex, p.name):
            files_to_fix.append(p)

    for p in files_to_fix:
        newname = p.name
        for r in common.name_replacements:
            newname = newname.replace(r[0], r[1])

        logger.info(f"rename: '{pwf_path(p)}' -> '{newname}'")

        if not is_nono:
            new_p = p.replace(p.parent / newname)
            if p == path:
                path = new_p


def _check_duplicates(path: Path):
    """
    Check that there are no duplicate files in all sub-paths of path.
    """
    logger.info("check duplicates...")

    # find potential duplicates by size (much faster!):
    by_size = defaultdict(list)

    for p in path.glob("**/*"):
        if p.is_file():
            by_size[p.stat().st_size].append(p)

    logger.debug(f"{by_size=}")

    # from potential duplicates, compute md5 sum:
    by_md5 = defaultdict(list)

    for paths in by_size.values():
        if len(paths) < 2:
            continue

        for p in paths:
            # optimized: is_partial=True ready only first 8k data!
            by_md5[compute_md5sum(p, is_partial=True)].append(p)

    logger.debug(f"{by_md5}")

    # identify and report duplicate files:
    found_any = False

    for paths in by_md5.values():
        if len(paths) < 2:
            continue

        found_any = True
        logger.info("Found identical files:")

        for p in paths:
            logger.info(f"    {pwf_path(p)}")

    if found_any:
        raise AssertionError("Found duplicate files!")


def _check_protection(path: Path):
    """
    Check if no files and no dirs have write rights set.
    """
    logger.info("check protection...")

    found_any = False

    for p in [path] + list(path.glob("**/*")):  # include path itself
        # linked files are allowed to be writable
        mode = p.stat(follow_symlinks=False).st_mode
        ogo_mode = oct(mode)[-3:]
        is_locked = ((int(ogo_mode, 16) & 0x222) == 0)

        if not is_locked:
            logger.info(f"Not protected: {stat.filemode(mode)} {pwf_path(p)}")
            found_any = True

    if found_any:
        raise AssertionError("Found unprotected files or directories!")


def _check_raw_derivatives(path: Path):
    """
    Checks that there are no files with names derived from original raw names.

    This check relies on common.get_orig_name()
    """
    logger.info("check raw derivatives...")

    found_any = False

    for ext in common.raw_file_extensions:
        for p in path.glob(f"**/*.{ext}"):
            stem = common.get_orig_name(p, with_extension=False)

            files_with_same_stem = list(path.glob(f"**/*{stem}*"))

            if len(files_with_same_stem) > 1:
                logger.info("Files with same name:")
                for p in sorted(files_with_same_stem):
                    logger.info(f"    {pwf_path(p)}")
                found_any = True

    if found_any:
        raise AssertionError("Found RAW derivatives!")


def _check_paths(path: Path):
    """
    Asserts that files with certain suffix are only in allowed folders.
    """
    logger.info("check paths...")

    found_any = False
    ignored: set[str] = set()

    for p in path.glob("**/*"):
        if not p.is_file():  # ignore dirs (TODO: what is with links?)
            continue

        suffix = p.suffix
        if suffix in common.valid_file_locations.keys():
            if p.parent.name != common.valid_file_locations[suffix]:
                logger.info(f"File in wrong location: {pwf_path(p)}")
                found_any = True
        else:
            ignored.add(suffix)

    if len(ignored) > 0:
        logger.warning(f"Ignored suffixes: {ignored}")

    if found_any:
        raise AssertionError("Found files in wrong locations!")


def _read_md5sums_file(path: Path):
    md5sums_file = path.parent / f"{path.name}.md5"
    md5sums = dict()

    with open(md5sums_file, "r") as f:
        for line in f.readlines():
            md5sum, path_str = line.strip().split(" ", 1)

            is_binary = path_str.startswith("*")
            file_path = path.parent / (path_str[1:] if is_binary else path_str)
            md5sums[md5sum] = (file_path, is_binary)

    return md5sums


def _check_checksums(path: Path):
    logger.info("check checksums...")

    md5sums = _read_md5sums_file(path)
    found_any = False

    for md5sum_exp, info in md5sums.items():
        file_path = info[0]
        is_binary = info[1]

        try:
            md5sum = common.compute_md5sum(file_path, is_binary=is_binary)
        except FileNotFoundError:
            logger.error(f"File missing: {pwf_path(file_path)}")
            found_any = True
            continue

        if md5sum != md5sum_exp:
            logger.error(f"MD5 sum error: {md5sum_exp} {pwf_path(file_path)}")
            found_any = True

    if found_any:
        raise AssertionError("Found missing files or files with wrong MD5 sum")


def _check_missing_files(path: Path):
    logger.info("check missing files...")

    md5sums = _read_md5sums_file(path)
    found_any = False

    for md5sum_exp, info in md5sums.items():
        file_path = info[0]

        if not file_path.exists():
            logger.error(f"File missing: {pwf_path(file_path)}")
            found_any = True

    if found_any:
        raise AssertionError("Found missing files")


def _get_checklist(path: Path, ignorelist: set | None = None,
                   onlylist: set | None = None):
    """
    Given ignorelist and pathlist, determine what to check
    """

    if ignorelist is None:
        ignorelist = set()
    if onlylist is None:
        onlylist = set()

    path_info = common.parse_path(path)
    if path_info.state == common.State.NEW:
        if "dup" in ignorelist:
            raise ValueError(
                "Ignoring duplicate violations is not allowed in 0_new!")

        if "path" in ignorelist:
            raise ValueError(
                "Ignoring path violations is not allowed in 0_new!")

    if path_info.state == common.State.NEW:
        ignorelist.update({"cs", "miss", "prot"})
    elif path_info.state == common.State.LAB:
        ignorelist.update({"cs", "miss", "prot", "path", "raw"})
    elif path_info.state != common.State.ORIGINAL:
        ignorelist.update({"cs", "prot", "miss"})

    checklist = copy.copy(things_to_check) if len(onlylist) == 0 else onlylist
    checklist -= ignorelist

    if "name" not in checklist:
        logger.warning("Ignoring name violations is strongly discouraged!")

    if checklist == set():
        raise ValueError("Everything ignored, nothing to check!")

    logger.info(f"Things to check: {checklist}")
    return checklist


def main(path: Path, ignorelist: set | None = None,
         onlylist: set | None = None, do_fix: bool = False,
         is_nono: bool = False):

    logger.info("pwf_check: ENTRY")

    # parse and check path:
    common.parse_path(path)

    # parse ignorelist and onlylist:
    checklist = _get_checklist(path, ignorelist, onlylist)

    logger.debug(f"{path=}, {checklist=}, {do_fix=}, {is_nono=}")

    if "name" in checklist:
        if do_fix:
            _fix_names(path, is_nono)
            if is_nono:
                return
        _check_names(path)

    if "dup" in checklist:
        _check_duplicates(path)

    if "prot" in checklist:
        _check_protection(path)

    if "raw" in checklist:
        _check_raw_derivatives(path)

    if "path" in checklist:
        _check_paths(path)

    if "cs" in checklist:
        _check_checksums(path)
    elif "miss" in checklist:
        # cs includes check for missing files!
        _check_missing_files(path)

    logger.info("pwf_check: OK")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=info_text)

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-i", "--ignorelist",
                       help="ignore check by list of comma-separated items")
    group.add_argument("-o", "--onlylist",
                       help="only check by list of comma-separated items")

    parser.add_argument("-f", "--fix",
                        help="auto-fix wrong names if possible",
                        action="store_true")
    parser.add_argument("-n", "--nono",
                        help="dry-run, only print what would be done",
                        action="store_true")
    parser.add_argument("-l", "--loglevel",
                        help="log level to use",
                        default="INFO")
    parser.add_argument("path")
    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=args.loglevel.upper())
    logger.debug(f"{args=}")

    ignorelist = None
    if args.ignorelist is not None:
        ignorelist = set(args.ignorelist.split(","))
        if not ignorelist.issubset(things_to_check):
            raise ValueError("Invalid IGNORELILST provided!")

    onlylist = None
    if args.onlylist is not None:
        onlylist = set(args.onlylist.split(","))
        if not onlylist.issubset(things_to_check):
            raise ValueError("Invalid ONLYLIST provided!")

    try:
        main(Path(args.path), ignorelist, onlylist, args.fix, args.nono)
    except Exception as ex:
        if args.loglevel.upper() == "DEBUG":
            raise
        logger.error(str(ex))
