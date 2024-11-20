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
Provides statistics about the files contained in the given PATH.
    """ + common.fzf_info_text


def _get_stats(path: Path, extensions: set) -> set:
    files_grabbed = []
    for ext in extensions:
        files_grabbed.extend(path.glob(f"**/*.{ext}"))

    num_files = len(files_grabbed)
    total_size = 0

    for file in files_grabbed:
        size = file.stat().st_size
        total_size += size

    return num_files, total_size


def _size_to_str(size_bytes: int):

    unit = ("KiB", "MiB", "GiB", "TiB")

    size = size_bytes
    for i in range(len(unit)):
        if size < 1024:
            break

        size /= 1024

    return f"{round(size, 1)} {unit[i-1]}"


def main(path: Path):

    logger.info("pwf_statistics: ENTRY")

    ext_defs = (
        ("RAW images", common.raw_file_extensions),
        ("JPG images", common.jpg_file_extensions),
        ("Videos", common.video_file_extensions),
        ("Audio files", common.audio_file_extensions),
    )

    width = max([len(title) for title, _ in ext_defs]) + 1  # 1 for ":"

    logger.info(f"Folder:      {path}")

    for title, exts in ext_defs:
        num, size = _get_stats(path, exts)
        title_ljust = (title + ":").ljust(width)
        logger.info(f"{title_ljust} {num} ({_size_to_str(size)})")

    logger.info("pwf_statistics: OK")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=info_text)

    group = parser.add_mutually_exclusive_group(required=False)
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
