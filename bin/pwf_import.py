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
from bin import pwf_check
from bin import pwf_protect
from pathlib import Path
import argparse
import logging
import shutil


logger = logging.getLogger(__name__)


info_text =\
    """
IGNORELIST
    See documentation of pwf_check.py -h

Import (i.e. move a new folder structure from 0_new into the
1_original/YEAR/ archive. The folder structure must contain files
sorted to raw/, jpg/, video/ and audio/ otherwise the script will exit
with an error.

If --keep-unprotected is specified, the destination path (year) will
kept unprotected after the import. The user is then responsible by
them own to call pwf_protect.py against the destination folder.

This script automates the following sequence:

  * pwf_check.py -i IGNORELLIST 0_new/EVENT/
  * pwf_protect.py -u 1_original/YEAR/
  * mv 0_new/EVENT 1_original/YEAR/EVENT
  * pwf_protect.py -f 1_original/YEAR/
    """ + common.fzf_info_text


def main(path: Path, ignorelist: set = None, year: int = None,
         keep_unprotected: bool = False, is_nono: bool = False):

    logger.info("pwf_import: ENTRY")

    # parse and check path:
    path_info = common.parse_path(path)

    logger.debug(f"{path=}, {ignorelist=}, {year=}, " +
                 "{keep_unprotected=}, {is_nono=}")

    if path_info.state != common.State.NEW or not path_info.is_event_dir:
        raise ValueError("Invalid path! pwf_import can only run against " +
                         "event dirs in 0_new!")

    if path_info.year is None:
        if year is None:
            raise RuntimeError(
                "Cannot auto-detect year and no year was provided with -y!")
        if year < 1900 or year > 2100:
            raise ValueError(
                "Invalid year provided! Must be between 1900 and 2100")
        path_info.year = year

    if ignorelist is not None:
        if ignorelist != {"raw", }:
            raise ValueError("Only allowed ignorelist item is 'raw'!")
        logger.warning(
            "Using --ignorelist is dangerous and strongly discouraged!")
        # logger.warning("Continue? [yes,no]")
        # val = input()
        # if val != "yes":
        #     raise ValueError("Stopped due to missing user confirmation")

    pwf_check.main(path, ignorelist=ignorelist, is_nono=is_nono)

    target_dir = common.pwf_root_path / "1_original" / str(path_info.year)

    if is_nono:
        logger.info("Dry-run, would do the following:")
        logger.info(
            f"  Move: {path} -> {target_dir}/{path_info.event}")
        return

    pwf_protect.unprotect(target_dir)

    logger.info(f"  Move: {path} -> {target_dir}/")
    shutil.move(path, target_dir)

    if not keep_unprotected:
        pwf_protect.protect(target_dir, is_forced=True)

    logger.info("pwf_import: OK")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=info_text)

    parser.add_argument("-i", "--ignorelist",
                        help="ignore check by list of comma-separated items")
    parser.add_argument("-k", "--keep-unprotected",
                        help="do not lock the destination year folder",
                        action="store_true")
    parser.add_argument("-n", "--nono",
                        help="nono, dry-run, only print what would be done",
                        action="store_true")
    parser.add_argument("-l", "--loglevel",
                        help="log level to use",
                        default="INFO")
    parser.add_argument("-y", "--year",
                        type=int,
                        help="year (if it unable to auto-parse by dir name)")
    parser.add_argument("path", nargs='?', default=Path.cwd())
    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=args.loglevel.upper())
    logger.debug(f"{args=}")

    ignorelist = None
    if args.ignorelist is not None:
        ignorelist = set(args.ignorelist.split(","))
        if not ignorelist.issubset(pwf_check.things_to_check):
            raise ValueError("Invalid IGNORELILST provided!")

    try:
        main(Path(args.path), ignorelist=ignorelist, year=args.year,
             keep_unprotected=args.keep_unprotected, is_nono=args.nono)
    except ValueError as ex:
        logger.error(str(ex))
    except AssertionError as ex:
        logger.error(str(ex))
