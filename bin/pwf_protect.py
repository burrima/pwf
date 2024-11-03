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
from pathlib import Path
import argparse
import logging


logger = logging.getLogger(__name__)


info_text =\
    """
Protects or unprotects a file or folder provided by PATH. Normally only used
against 1_original/YEAR, but can be used for any PATH.  Calls pwf_check.py
before protection is applied (unless -f is set).

By default, only folders are unprotected, but files remain protected. This
allows to add or delete files, but modification is still not allowed. With the
flag -a all files can be unlocked too (use with care!).
    """ + common.fzf_info_text


def main(path: Path):
    pass


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
        main(Path(args.path))
    except ValueError as ex:
        logger.error(str(ex))
    except AssertionError as ex:
        logger.error(str(ex))
