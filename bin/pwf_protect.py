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
from pathlib import Path
import argparse
import hashlib
import logging


logger = logging.getLogger(__name__)


info_text =\
    """
Protects or unprotects a file or folder provided by PATH. Normally
only used against 1_original/YEAR, but can be used for any PATH.
Calls pwf_check.py before protection is applied (unless -f is set).

By default, only folders are unprotected, but files remain protected.
This allows to add or delete files, but modification is still not
allowed. With the flag -a all files can be unlocked too (use with
care!).
    """ + common.fzf_info_text


def compute_md5sum(path: Path, is_partial: bool = False) -> str:
    # if is_partial=True, read only first 8k data (which should be fine for
    # pictures).
    # TODO: read chunked for big files (memory issue)
    with open(path, "rb") as f:
        data = f.read(8000 if is_partial else None)
        md5sum = hashlib.md5(data).hexdigest()
    return md5sum


def unprotect(path: Path, is_all: bool = False):
    md5_file = path.parent / (path.name + ".md5")
    for p in sorted(path.glob("**/*")):
        if p.is_dir():
            p.chmod(0o775)
        elif is_all and p.is_file():
            p.lchmod(0o664)
    if md5_file.exists():
        md5_file.lchmod(0o664)


def protect(path: Path, is_forced: bool = False):
    md5_file = path.parent / (path.name + ".md5")
    if not is_forced:
        pwf_check.main(path, ignorelist={"prot", })
    for p in sorted(path.glob("**/*")):
        if p.is_dir():
            p.chmod(0o555)
        elif p.is_file():
            md5sum = compute_md5sum(p, is_partial=False)
            with open(md5_file, "a") as f:
                f.write(f"{md5sum} *{p.relative_to(path.parent)}")
            p.lchmod(0o444)


def main(path: Path, do_unprotect: bool = False, is_forced: bool = False,
         is_all: bool = False):

    logger.info("pwf_protect: ENTRY")

    if do_unprotect:
        unprotect(path, is_all)
    else:
        protect(path, is_forced)

    logger.info("pwf_protect: OK")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=info_text)

    parser.add_argument("-a", "--all",
                        help="all content of a directory (also files)",
                        action="store_true")
    parser.add_argument("-f", "--forced",
                        help="don't perform any checks",
                        action="store_true")
    parser.add_argument("-u", "--unprotect",
                        help="unprotect given path (default is to protect)",
                        action="store_true")
    parser.add_argument("-l", "--loglevel",
                        help="log level to use",
                        default="INFO")
    parser.add_argument("path", nargs='?', default=Path.cwd())
    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=args.loglevel.upper())
    logger.debug(f"{args=}")

    try:
        main(Path(args.path), do_unprotect=args.unprotect,
             is_forced=args.forced, is_all=args.all)
    except Exception as ex:
        if args.loglevel.upper() == "DEBUG":
            raise
        logger.error(str(ex))
