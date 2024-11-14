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
Creates small preview images out of RAW and JPG files. For RAW files, the
preview images are extracted from the exif info. For JPG files, a smaller
version of the original is created.

SRC can be a file or a folder. Folders can be traversed recursively with the
option -r. A DST_DIR can be specified where to place the preview images. If no
destination is provided, the files will be placed where the script is called
from.

The option -f can be used to only create preview files if the source file name
is listed in the given filter file. This is used to restore cleaned-up lab
folders.

DST_DIR can be set to "@lab" to cause special behavior: In this case, SRC must
point to an event folder in the 1_original/ tree. A preview of all JPG and RAW
photos will be put into the corresponding event folder in the 2_lab/ tree, into
a subfolder 1_preview/ (implies option -r).
    """ + common.fzf_info_text


def extract_raw_preview(src: Path, dst: Path):
    pass


def extract_jpg_preview(src: Path, dst: Path):
    pass


def main(src_path: Path, dst_path: Path, is_recursive: bool = False,
         filter_file: Path = None):

    # TODO:
    # * if dst_path is None, use same dir
    # * if dst_path is @lab, do same as pwf-prepare-lab did (no extra script)
    # * use pwf_liknk src_dir @lab instead of pwf-prepare-lab

    logger.info("pwf_extract_previews: ENTRY")

    # parse and check path:
    common.parse_path(src_path)

    if dst_path is None:
        dst_path = src_path.parent
    if not dst_path.is_dir() and dst_path != "@lab":
        raise ValueError("DST_PATH must be directory or '@lab'!")

    files = []
    if src_path.is_dir():
        glob = "**/*.*" if is_recursive else "*.*"
        files = list(src_path.glob(glob))
    else:
        files = [src_path]

    for file in files:
        if file.suffix in common.jpg_file_extensions:
            extract_jpg_preview(src=file, dst=dst_path)
        elif file.suffix in common.raw_file_extensions:
            extract_raw_preview(src=file, dst=dst_path)
        else:
            logger.info(f"Ignored file: {file}")

    logger.info("pwf_extract_previews: OK")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=info_text)

    parser.add_argument("-r", "--recursive",
                        help="recursively search through dirs of given SRC",
                        action="store_true")
    parser.add_argument("-f", "--filter_file",
                        help="to only generate previews of listed files",
                        action="store_true")
    parser.add_argument("-l", "--loglevel",
                        help="log level to use",
                        default="INFO")
    parser.add_argument("src_path", nargs='?', default=Path.cwd())
    parser.add_argument("dst_path", nargs='?', default=None)
    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=args.loglevel.upper())
    logger.debug(f"{args=}")

    dst_path = Path(args.dst_path) if args.dst_path is not None else None

    try:
        main(Path(args.src_path), dst_path=dst_path,
             is_recursive=args.recursive, filter_file=args.filter_file)
    except ValueError as ex:
        logger.error(str(ex))
    except AssertionError as ex:
        logger.error(str(ex))
