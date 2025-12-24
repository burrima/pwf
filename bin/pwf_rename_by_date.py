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
from bin.corrections_definitions import CorrectionsDefinitions, get_corrections_definitions, \
    get_file_corrections


logger = logging.getLogger(__name__)


info_text: str = dedent(
    """
    Renames the image files in the given folder (or just the image itself if
    PATH is a file) by prefixing them with a date string. The purpose is to
    make the folder view sort the files properly.

    The option -s can be used to provide a shell script which takes the name of
    the picture and prints the date string. This is useful to apply a
    correction to the date/time (remember: original files are protected and
    must not be changed). This is for backwards-compatibility to old
    bash-scripts only.

    By default (=new way), the script traverses the directory tree upwards to
    find the yaml file "exif_corrections.yaml" automatically.

    Auto-correction can be disabled completely with the option -b in which case
    the date will be based on pure, uncorrected EXIF data.

    The exif_corrections.yaml must follow the syntax:

        - file_name_filter: ".*"
          exif_filters:
            - tag: "Model"
              filter: "Canon PowerShot G9 X"
          time_correction:
            days: 0
            hours: 0
            minutes: -10
            seconds: -1

    Any of days, hours, minutes or seconds can be left away as long as there is
    at least one of them.
    """) + common.info_text


def read_exif_tags(file: Path) -> dict[str, str] | None:
    """
    Reads and returns all EXIF tags from a file. If the file has no tag, None
    is returned. Uses PIL Image.getexif() which is good for reading, but not
    suitable for writing EXIF tags.
    """
    try:
        img = Image.open(file)
        pil_exif = img.getexif()
        assert len(pil_exif) > 0
        exif_tags = {
            str(ExifTags.TAGS.get(t, t)): str(v) for t, v in pil_exif.items()}
    except Exception:
        logger.error(f"Unable to read EXIF info of: {file}")
        return None

    return exif_tags


def _parse_date_from_exif(exif_tags: dict[str, str]) -> datetime:
    date_str = exif_tags["DateTime"]
    dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
    return dt


def _parse_camera_from_exif(exif_tags: dict[str, str]) -> str:
    camera = exif_tags["Model"]
    camera_clean = ""
    for c in camera:
        if re.match(rf"[{common.legal_characters}]", c):
            camera_clean += c
    return camera_clean


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


def _get_time_delta(filename: str, exif_tags: dict[str, str],
                    corr_defs: CorrectionsDefinitions) -> timedelta:
    """
    Given an file name, the extracted exif_info and the corrections
    definitions, this method determines the time delta to be applied.
    """
    corrections = get_file_corrections(corr_defs, filename, exif_tags)
    if corrections is not None:
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

    corr_defs = get_corrections_definitions(path)

    for file in files:

        exif_tags = read_exif_tags(file)
        if exif_tags is None:
            continue  # reporting already done

        delta = _get_time_delta(file.name, exif_tags, corr_defs)

        dt = _parse_date_from_exif(exif_tags) + delta
        dt_str = dt.strftime("%Y%m%d-%H%M%S")
        camera = _parse_camera_from_exif(exif_tags)

        if not add_camera:
            camera = None

        if camera is not None and camera_first:
            prefix = f"{camera}-{dt_str}"
        else:
            prefix = f"{dt_str}-{camera}" if camera is not None else dt_str

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
    parser.add_argument("-s", "--script",
                        help="script to get date correction (deprecated)",
                        default="")
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
