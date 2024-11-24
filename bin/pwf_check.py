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


def _check_names(path: Path):
    logger.info("check names...")

    regex = rf"^[{common.legal_characters}]+$"
    found_any = False

    for p in [path] + list(path.glob("**/*")):
        logger.debug(f"  {p.name}")
        if not re.match(regex, p.name):
            logger.info(f"Illegal: '{p}'")
            found_any = True

    if found_any:
        raise AssertionError("Found illegal chars in file or folder names!")


def _fix_names(path: Path, is_nono: bool):
    logger.info("fix names...")

    regex = rf"^[{common.legal_characters}]+$"

    if is_nono:
        logger.info("Dry-run: would do the following:")

    files_to_fix = []
    paths = list(path.glob("**/*")) + [path]
    for p in sorted(paths, reverse=True):
        logger.debug(f"  {p.name}")
        if not re.match(regex, p.name):
            files_to_fix.append(p)

    for p in files_to_fix:
        newname = p.name
        for r in common.name_replacements:
            newname = newname.replace(r[0], r[1])
        logger.info(f"  '{p}' -> '{newname}'")
        if not is_nono:
            new_p = p.replace(p.parent / newname)
            if p == path:
                path = new_p


def _check_duplicates(path: Path):
    logger.info("check duplicates...")

    # find potential duplicates by size (much faster!):
    by_size = defaultdict(list)
    for p in path.glob("**/*"):
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


def _check_protection(path: Path):
    logger.info("check protection...")

    found_any = False

    for p in [path] + list(path.glob("**/*")):
        mode = p.stat(follow_symlinks=False).st_mode
        ogo_mode = oct(mode)[-3:]
        is_locked = ((int(ogo_mode, 16) & 0x222) == 0)
        if not is_locked:
            logger.info(f"Not protected: {stat.filemode(mode)} {p}")
            found_any = True

    if found_any:
        raise AssertionError("Found unprotected files or directories!")


def _check_raw_derivatives(path: Path):
    logger.info("check raw derivatives...")

    found_any = False

    for ext in common.raw_file_extensions:
        for p in path.glob(f"**/*.{ext}"):
            stem = common.get_orig_name(p, with_extension=False)

            files_with_same_stem = list(path.glob(f"**/*{stem}*"))
            if len(files_with_same_stem) > 1:
                files = "\n  ".join(
                    [str(p) for p in sorted(files_with_same_stem)])
                logger.info(f"Files with same name:\n  {files}")
                found_any = True

    if found_any:
        raise AssertionError("Found RAW derivatives!")


def _check_paths(path: Path):
    """
    Asserts that files with certain endings are only in allowed folders.
    """
    logger.info("check paths...")

    found_any = False
    n_ignored = 0

    for p in path.glob("**/*"):
        if not p.is_file():
            continue

        suffix = p.suffix[1:]
        if suffix in common.valid_file_locations.keys():
            if p.parent.name != common.valid_file_locations[suffix]:
                logger.info(f"File in wrong location: {p}")
                found_any = True
        else:
            n_ignored += 1

    if n_ignored > 0:
        logger.warning(f"Ignored {n_ignored} files in path verification!")

    if found_any:
        raise AssertionError("Found files in wrong locations!")


def _check_checksums(path: Path):
    logger.info("check checksums...")


def _check_missing_files(path: Path):
    logger.info("check missing files...")


def _get_checklist(path: Path, ignorelist: set = None, onlylist: set = None):
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

    checklist = copy.copy(things_to_check) if len(onlylist) == 0 else onlylist
    checklist -= ignorelist

    if "name" not in checklist:
        logger.warning("Ignoring name violations is strongly discouraged!")
    if checklist == set():
        raise ValueError("Everything ignored, nothing to check!")

    logger.info(f"Things to check: {checklist}")
    return checklist


def main(path: Path, ignorelist: set = None, onlylist: set = None,
         do_fix: bool = False, is_nono: bool = False):

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

    if "miss" in checklist:
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
