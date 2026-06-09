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
from dataclasses import asdict
from datetime import datetime, timedelta
from fractions import Fraction
from pathlib import Path
from textwrap import dedent
import argparse
import logging
import re
import pyexiv2  # type: ignore
import shutil
from textwrap import indent
import yaml


logger = logging.getLogger(__name__)


info_text: str = dedent(
    """
    Fixes the EXIF entries of each image in given folder (or given file if SRC
    is a file). The fixes are made based on exif_corrections.yaml which must be
    present in any of the parent folders (the algorithm traverses upwards to
    look for these files).

    The exif_corrections.yaml must follow a specific syntax as shown in the
    following example:

        - corrections:  # default values for all pictures
            tz_offset: +02:00
            gps_lat_lng: "1.234, 5.678"

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

        - filter:
            filename: '^.*IMG_553[3-5].*$' # regex
          corrections:
            gps_lat_lng: "9.1011, 12.1314"  # overwrite

    Filter/correction pairs are listed in order from global to more specific.
    Each level can overwrite corrections from the previous level. This makes it
    very powerful and flexible. The use of regex replacements also provides
    more fine-granular control.

    Any yaml tag can generally be left away, as long as it makes sense. The
    tool will complain if it does not understand anything. It will also
    print a warning for each re-defined value.
    """) + common.info_text


class MyDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)


def apply_time_correction_to_tags(
        exif_tags: dict[str, str], file: Path, corr_defs: object) -> None:

    return


def apply_string_corrections_to_tags(
        exif_tags: dict[str, str], file: Path, corr_defs: object):
    # Not yet implemented!
    return

def decimal_to_dms_fractions(decimal_coord):
    abs_coord = abs(float(decimal_coord))

    degrees = int(abs_coord)
    minutes_float = (abs_coord - degrees) * 60
    minutes = int(minutes_float)

    seconds = (minutes_float - minutes) * 60
    seconds_fraction = Fraction(seconds).limit_denominator(100)

    return [Fraction(degrees, 1), Fraction(minutes, 1), seconds_fraction]


def apply_corrections(file: Path, corrections: Corrections) -> None:
    time_corr = corrections.time
    delta = timedelta(days=time_corr.days,
                      hours=time_corr.hours,
                      minutes=time_corr.minutes,
                      seconds=time_corr.seconds)

    metadata = pyexiv2.ImageMetadata(str(file))
    metadata.read()

    try:
        # Try to take DateTimeOriginal and fall-back to DateTime
        date_key = "Exif.Photo.DateTimeOriginal"
        if date_key not in metadata.exif_keys:
            logger.warning(f"Falling back to Exif.Image.DateTime in {file}")
            date_key = "Exif.Image.DateTime"

        logger.debug(f"Add {delta=} to {file}")
        new_date = metadata[date_key].value + delta
        metadata["Exif.Image.DateTime"] = new_date
        metadata["Exif.Image.DateTimeOriginal"] = new_date
        metadata["Exif.Photo.DateTimeOriginal"] = new_date
        metadata["Exif.Photo.DateTimeDigitized"] = new_date

        for tag_corr in corrections.tags:
            if tag_corr.tag in metadata:
                if "Latitude" in tag_corr.tag or "Longitude" in tag_corr.tag:
                    logger.warning(f"Correcting GPS not supported in {file}!")
                    continue
                logger.debug(f"Correct {tag_corr.tag} in {file}")
                value = metadata[tag_corr.tag].raw_value
                value = re.sub(tag_corr.pattern, tag_corr.replacement, value)
                metadata[tag_corr.tag] = value
            else:
                logger.debug(f"Set {tag_corr.tag} in {file}")
                value = tag_corr.replacement
                if "Latitude" in tag_corr.tag:
                    lat_ref = "N" if float(value) > 0 else "S"
                    metadata["Exif.GPSInfo.GPSLatitudeRef"] = lat_ref
                    value = decimal_to_dms_fractions(float(value))
                if "Longitude" in tag_corr.tag:
                    lng_ref = "E" if float(value) > 0 else "W"
                    metadata["Exif.GPSInfo.GPSLongitudeRef"] = lng_ref
                    value = decimal_to_dms_fractions(float(value))
                metadata[tag_corr.tag] = value

        tz_offset = corrections.tz_offset
        # metadata["Exif.Image.OffsetTime"] = tz_offset
        metadata["Exif.Photo.OffsetTimeOriginal"] = tz_offset
        metadata["Exif.Photo.OffsetTimeDigitized"] = tz_offset

    except Exception as err:
        logger.error(f"Unable to correct EXIF in {file} {err=}")
        return

    if file.is_symlink():
        real_file = file.resolve()
        file.unlink()
        shutil.copyfile(real_file, file)

    metadata.write()

def main(path: Path, is_nono: bool) -> None:

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

            if is_nono:
                corr_str = yaml.dump(asdict(corrections), Dumper=MyDumper,
                                     allow_unicode=True, sort_keys=False)
                corr_str = indent(corr_str, "    ")
                logger.info(f"[NONO] Corrections for: {file}:\n{corr_str}")
            else:
                apply_corrections(file, corrections)
        except KeyError:
            logger.warning(f"No EXIF tag found: {file}")
            continue


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=info_text)

    parser.add_argument("-n", "--nono",
                        help="nono, dry-run, only print what would be done",
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
        main(Path(args.path), is_nono=args.nono)
    except Exception as ex:
        if args.loglevel.upper() == "DEBUG":
            raise
        logger.error(str(ex))
