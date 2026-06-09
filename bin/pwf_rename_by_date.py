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
from PIL import Image, ExifTags
from textwrap import dedent
import argparse
import logging
from datetime import datetime, timedelta
import re
from bin.corrections_definitions import CorrectionsDefinitions, \
    get_corrections_definitions, get_file_corrections
import pyexiv2  # type: ignore


logger = logging.getLogger(__name__)


info_text: str = dedent(
    """
    Renames the image files in the given folder (or just the image itself if
    PATH is a file) by prefixing them with a date string. The purpose is to
    make the folder view sort the files properly.

    By default, the script traverses the directory tree upwards to find the
    yaml file "exif_corrections.yaml" automatically.

    Auto-correction can be disabled completely with the option -b in which case
    the date will be based on pure, uncorrected EXIF data.

    The exif_corrections.yaml must follow the syntax:

        - filter:
            filename: ".*"  # regex
            tags:
              - tag: "Model"
                value: "Canon PowerShot G9 X"  # regex
          corrections:
            time:
              days: 0
              hours: 0
              minutes: -10
              seconds: -1
            tags:
              - tag: Artist
                pattern: ".*"  # regex for re.sub()
                replacement: "Martin Burri"  # repl for re.sub()

    Any of days, hours, minutes or seconds can be left away as long as there is
    at least one of them.
    """) + common.info_text


def read_exif_info(file: Path) -> tuple[datetime, str]:
    """
    Reads and returns date and camera model from the file exif. Raises an
    Exception if anything goes wrong (e.g. no EXIF tag present).
    """
    metadata = pyexiv2.ImageMetadata(str(file))
    metadata.read()

    if len(metadata.exif_keys) == 0:
        raise RuntimeError(f"No EXIF info found in {file}")

    # Try to take DateTimeOriginal and fall-back to DateTime
    date_key = "Exif.Photo.DateTimeOriginal"
    if date_key not in metadata.exif_keys:
        logger.warning(f"Falling back to Exif.Image.DateTime in {file}")
        date_key = "Exif.Image.DateTime"

    date = metadata[date_key].value
    camera = metadata["Exif.Image.Model"].value

    camera_clean = ""
    for c in camera:
        if re.match(rf"[{common.legal_characters}]", c):
            camera_clean += c

    return (date, camera_clean)


def _add_prefix(file: Path, prefix: str,
                delimiter: str = common.tag_name_delimiter) -> None:
    """
    Add the prefix to a file. Uses common.prefix_str() to add the prefix to the
    file name.
    """
    newname = file.parent / common.prefix_str(file.name, prefix, delimiter)
    logger.debug(f"{file} => {newname}")
    file.rename(newname)


def _remove_prefix(file: Path,
                   delimiter: str = common.tag_name_delimiter) -> None:
    """
    Removes the prefix from a file. Uses common.unprefix_str() to remove the
    prefix from the file name.
    """
    newname = common.unprefix_str(file.name, delimiter)
    newname = file.parent / newname
    logger.debug(f"{file} => {newname}")
    file.rename(newname)


def _get_time_delta(file: Path,
                    corr_defs: list[CorrectionsDefinitions]) -> timedelta:
    """
    Given an file name, the extracted exif_info and the corrections
    definitions, this method determines the time delta to be applied.
    """
    corrections = get_file_corrections(corr_defs, file)
    if corrections is not None and corrections.time is not None:
        correction = corrections.time
        return timedelta(days=correction.days,
                         hours=correction.hours,
                         minutes=correction.minutes,
                         seconds=correction.seconds)
    return timedelta(0)


def main(path: Path, is_undo: bool = False, is_bare: bool = False,
         add_camera: bool = False, camera_first: bool = False) -> None:

    if path.is_file():
        files = [path]
    else:
        files = list(path.glob("*.*"))

    if is_undo:
        for file in files:
            try:
                _remove_prefix(file, delimiter=common.tag_name_delimiter)
            except Exception:
                logger.error(f"Cannot remove prefix from {file}")
        return

    if not is_bare:
        try:
            corr_defs = get_corrections_definitions(path)
        except FileNotFoundError:
            logger.warning("No corrections file found, doing no corrections")
            is_bare = True

    for file in files:

        try:
            date, camera = read_exif_info(file)
        except Exception as err:
            logger.error(f"Unable to read EXIF info of: {file} {err=}")
            continue

        if not is_bare:
            delta = _get_time_delta(file, corr_defs)
            date += delta

        date_str = date.strftime("%Y%m%d-%H%M%S")

        if add_camera and camera_first:
            prefix = f"{camera}-{date_str}"
        else:
            prefix = f"{date_str}-{camera}" if add_camera else date_str

        _add_prefix(file, prefix, delimiter=common.tag_name_delimiter)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=info_text)

    parser.add_argument("-u", "--undo",
                        help="remove the date from the name again",
                        action="store_true")
    parser.add_argument("-b", "--bare",
                        help="do not apply any EXIF corrections",
                        action="store_true")
    parser.add_argument("-c", "--camera",
                        help="add camera prefix",
                        action="store_true")
    parser.add_argument("-d", "--camerafirst",
                        help="add camera tag behind date tag",
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
        main(Path(args.path), args.undo, args.bare, args.camera,
             args.camerafirst)
    except Exception as ex:
        if args.loglevel.upper() == "DEBUG":
            raise
        logger.error(str(ex))
