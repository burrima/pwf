#!/usr/bin/env python3
# Copyright 2025 Martin Burri
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
from bin import pwf_rename_by_date
from bin.corrections_definitions import Corrections, \
    get_corrections_definitions, get_file_corrections
from datetime import datetime, timedelta
from pathlib import Path
from textwrap import dedent
import argparse
import logging
import re
import pyexiv2  # type: ignore
import shutil


logger = logging.getLogger(__name__)


info_text: str = dedent(
    """
    Fixes the EXIF entries of each image in given folder (or given file if SRC
    is a file). The fixes are made based on exif_corrections.yaml which must be
    present in any of the parent folders (the algorithm traverses upwards to
    look for these files).

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
            tz_offset: +02:00
            tags:
              - tag: Artist
                pattern: ".*"  # regex for re.sub()
                replacement: "Martin Burri"  # repl for re.sub()

    Each tag can be accessed individually and replacements are done with the
    python method re.sub(), which takes a pattern and a replacement. The part
    in the EXIF tag matching the pattern will be replaced by replacement. This
    provides fine-granular control.

    Any yaml tag can generally be left away, as long as it makes sense. The
    tool will complain if it does not understand anything. It will also
    complain if multiple filters match an image.
    """) + common.info_text


def apply_time_correction_to_tags(
        exif_tags: dict[str, str], file: Path, corr_defs: object) -> None:

    return


def apply_string_corrections_to_tags(
        exif_tags: dict[str, str], file: Path, corr_defs: object):
    # Not yet implemented!
    return

def apply_corrections(file: Path, corrections: Corrections) -> None:
    time_corr = corrections.time
    delta = timedelta(days=time_corr.days,
                      hours=time_corr.hours,
                      minutes=time_corr.minutes,
                      seconds=time_corr.seconds)

    metadata = pyexiv2.ImageMetadata(str(file))
    metadata.read()

    try:
        dt = metadata["Exif.Image.DateTime"].value
        dt_orig = metadata["Exif.Photo.DateTimeOriginal"].value

        if dt == dt_orig or (dt_orig + delta) > dt:
            logger.info(f"Overwrite {dt=} with {(dt_orig+delta)=} in {file}")
            dt = metadata["Exif.Image.DateTime"].value = dt_orig + delta

        metadata["Exif.Photo.DateTimeOriginal"].value += delta
        metadata["Exif.Photo.DateTimeDigitized"].value += delta

        for tag_corr in corrections.tags:
            value = metadata[tag_corr.tag].raw_value
            value = re.sub(tag_corr.pattern, tag_corr.replacement, value)
            metadata[tag_corr.tag] = value

        tz_offset = corrections.tz_offset
        # metadata["Exif.Image.OffsetTime"].value = tz_offset
        metadata["Exif.Photo.OffsetTimeOriginal"] = tz_offset
        metadata["Exif.Photo.OffsetTimeDigitized"] = tz_offset

    except Exception as err:
        logger.error(f"Unable to correct EXIF in {file} {err=}")
        return

    if file.is_symlink():
        real_file = file.resolve()
        file.unlink()
        shutil.copyfile(real_file, file)
        metadata2 = pyexiv2.ImageMetadata(str(file))
        metadata2.read()
        metadata.copy(metadata2)

    metadata.write()

def main(path: Path) -> None:

    if path.is_file():
        files = [path]
    else:
        files = list(path.glob("*.*"))

    corr_defs = get_corrections_definitions(path)

    for file in files:

        try:
            corrections = get_file_corrections(corr_defs, file)
            if corrections is None:   # no corrections to be applied
                continue
            apply_corrections(file, corrections)
        except KeyError:
            logger.warning(f"No EXIF tag found: {file}")
            continue


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=info_text)

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
    except Exception as ex:
        if args.loglevel.upper() == "DEBUG":
            raise
        logger.error(str(ex))
