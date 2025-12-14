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
import yaml


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
    find the yaml file "date_corrections.yaml" automatically.

    Auto-correction can be disabled completely with the option -b in which case
    the date will be based on pure, uncorrected EXIF data.

    The date_corrections.yaml must follow the syntax:

        - file_name_filter: ".*"
          exif_filters:
            - tag: "Model"
              filter: "Canon PowerShot G9 X"
          correction:
            minutes: -10
            seconds: -1
    """) + common.info_text


def _add_prefix(file: Path, prefix: str,
                delimiter: str = common.tag_name_delimiter):
    newname = file.parent / common.prefix_str(file.name, prefix, delimiter)
    logger.debug(f"{file} => {newname}")
    file.rename(newname)


def _remove_prefix(file: Path, delimiter: str = common.tag_name_delimiter):
    newname = common.unprefix_str(file.name, delimiter)
    newname = file.parent / newname
    logger.debug(f"{file} => {newname}")
    file.rename(newname)


def _get_exif_info(file: Path):
    try:
        img = Image.open(file)
        exif_info = img.getexif()
        assert len(exif_info) > 0
        exif_data = {ExifTags.TAGS.get(t, t): v for t, v in exif_info.items()}
    except Exception:
        logger.error(f"Unable to get EXIF data for: {file}")
        return None

    return exif_data


def _parse_date_str_from_exif(exif_data):
    date_str = exif_data["DateTime"]
    dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
    return dt


def _parse_camera_str_from_exif(exif_data):
    camera = exif_data["Model"]
    camera_clean = ""
    for c in camera:
        if re.match(rf"[{common.legal_characters}]", c):
            camera_clean += c
    return camera_clean


def _find_corrections_file(file: Path):

    while file != common.pwf_root_path and file != Path("/"):

        yaml_file = file / "date_corrections.yaml"

        if file.is_dir() and yaml_file.exists():
            return yaml_file

        file = file.parent


def _get_corrections_def(file: Path):

    corr_file = _find_corrections_file(file)
    if corr_file is not None:
        logger.debug(corr_file)
        with open(corr_file, "r") as f:
            corr_def = yaml.safe_load(f)
        return corr_def


def _get_time_delta(file: Path, exif_info, corr_defs):

    for corr_def in corr_defs:
        correction_found = True

        if not re.match(corr_def["file_name_filter"], file.name):
            correction_found = False
            continue

        for exif_filter in corr_def["exif_filters"]:
            if re.match(exif_filter["filter"],
                        exif_info[exif_filter["tag"]]) is None:
                correction_found = False
                break

        if correction_found:
            correction = corr_def["correction"]
            days = correction.get("days", 0)
            hours = correction.get("hours", 0)
            minutes = correction.get("minutes", 0)
            seconds = correction.get("seconds", 0)
            return timedelta(days=days, hours=hours, minutes=minutes,
                             seconds=seconds)

    return timedelta(0)


def main(path: Path, is_undo: bool = False, is_bare: bool = False,
         add_camera: bool = False, camera_first: bool = False) -> None:

    if path.is_file():
        files = [path]
    else:
        files = list(path.glob("*.*"))

    if is_undo:
        for file in files:
            _remove_prefix(file, delimiter=common.tag_name_delimiter)
        return

    corr_defs = _get_corrections_def(path)
    logger.debug(corr_defs)

    for file in files:

        exif_info = _get_exif_info(file)
        if exif_info is None:
            continue  # reporting already done

        delta = _get_time_delta(file, exif_info, corr_defs)

        dt = _parse_date_str_from_exif(exif_info) + delta
        dt_str = dt.strftime("%Y%m%d-%H%M%S")
        camera = _parse_camera_str_from_exif(exif_info)

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
