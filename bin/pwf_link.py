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
Links SRC file(s) into the DST_DIR directory.

SRC can be a file or a folder. Folders can be traversed recursively with
the option -r. A DST_DIR can be specified where to place the links. If
no destination is provided, the files will be placed where the script is
called from.

DST_DIR can be set to "@lab" to cause special behavior: In this case,
SRC must point to an event folder in the 1_original/ tree. All files are
then linked into the corresponding event folder in the 2_lab/ tree, into
sub- folders 2_original_{jpg,raw,audio,video} (implies option -r). RAW
and JPG images are only linked if a corresponding preview file is
present in the folder 1_preview/ of the lab event folder. This can be
bypassed with the option -a.
    """ + common.fzf_info_text


def main(src_path: Path, dst_path: Path, is_all: bool=False,
         is_interactive: bool=False, is_recursive: bool=False):

    logger.info("pwf_link: ENTRY")

    # parse and check path:
    pwf_path = common.PwfPath(src_path)

    if str(dst_path) == "@lab":
        if not pwf_path.is_event_dir:
            raise ValueError("src_path must be event-dir when dst_path=@lab!")
        if pwf_path.state != common.State.ORIGINAL:
            raise ValueError("src_path must be in 1_original/!")

        dst_path = Path(str(src_path).replace("1_original", "2_lab"))

    logger.info("pwf_link: OK")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=info_text)

    parser.add_argument("-a", "--all",
                        help="link all files to lab, indept. of previews",
                        action="store_true")
    parser.add_argument("-i", "--interactive",
                        help="prompt whether to remove destinations (y/n)",
                        action="store_true")
    parser.add_argument("-r", "--recursive",
                        help="recursively traverse src_path",
                        action="store_true")
    parser.add_argument("src_path", nargs='?', default=Path.cwd())
    parser.add_argument("dst_path", nargs='?')
    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=args.loglevel.upper())
    logger.debug(f"{args=}")

    try:
        main(Path(args.src_path), Path(args.dst_path), is_all, is_interactive,
             is_recursive)
    except ValueError as ex:
        logger.error(str(ex))
    except AssertionError as ex:
        logger.error(str(ex))
