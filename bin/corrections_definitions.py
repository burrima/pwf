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
import logging
import re
import pyexiv2  # type: ignore

from dataclasses import dataclass, field
from typing import List
from dataclass_wizard import YAMLWizard


logger = logging.getLogger(__name__)


"""
Dataclass classes are generated with the following command:

  cat ~/temp/exif_corrections.yaml |\
  python3 -c \
  'import sys, yaml, json; print(json.dumps(yaml.safe_load(sys.stdin)))' |\
  wiz gs
"""


@dataclass
class Container:
    """
    Container dataclass

    """
    data: 'CorrectionsDefinitions'


@dataclass
class CorrectionsDefinitions(YAMLWizard):
    """
    CorrectionsDefinitions dataclass

    """
    filter: 'Filter'
    corrections: 'Corrections'


@dataclass
class Filter:
    """
    Filter dataclass

    """
    filename: str = ".*"
    tags: List['FilterTag'] = field(default_factory=lambda: [])


@dataclass
class FilterTag:
    """
    FilterTag dataclass

    """
    tag: str
    value: str


@dataclass
class Corrections:
    """
    Corrections dataclass

    """
    time: 'Time'
    tz_offset: str = "+02:00"
    tags: List['Tag'] = field(default_factory=lambda: [])


@dataclass
class Time:
    """
    Time dataclass

    """
    days: int = 0
    hours: int = 0
    minutes: int = 0
    seconds: int = 0


@dataclass
class Tag:
    """
    Tag dataclass

    """
    tag: str
    pattern: str
    replacement: str


def find_corrections_file(file: Path) -> Path:
    """
    Traverses the tree upwards to find the "exif_corrections.yaml" file.
    If the file is not found, None is returned.
    """
    while file != common.pwf_root_path and file != Path("/"):

        yaml_file = file / "exif_corrections.yaml"

        if file.is_dir() and yaml_file.exists():
            logger.debug(yaml_file)
            return yaml_file

        file = file.parent

    raise FileNotFoundError("Unable to find exif_corrections.yaml in tree!")


def get_corrections_definitions(file: Path) -> list[CorrectionsDefinitions]:
    """
    Finds and opens the file exif_corrections.yaml

    Raises FileNotFoundError if the file is not found

    NOTE: this method is also used by pwf_fix_exif.py
    """
    corr_file = find_corrections_file(file)
    cd = CorrectionsDefinitions.from_yaml_file(corr_file)
    if not isinstance(cd, list):
        cd = [cd]
    return cd


def get_file_corrections(corr_defs: list[CorrectionsDefinitions],
                         file: Path) -> Corrections | None:
    """
    Returns the corrections to be applied to given file name. Searches through
    given corr_defs. Returns None if no corrections are found for this file.

    One file can only have 1 set of corrections. If different filters match the
    same file, only the first one is selected.
    """
    corrections = None
    for corr_def in corr_defs:
        correction_found = True

        if not re.match(corr_def.filter.filename, file.name):
            correction_found = False
            continue

        metadata = pyexiv2.ImageMetadata(str(file))
        metadata.read()

        for tag_filter in corr_def.filter.tags:
            if re.match(tag_filter.value,
                        metadata[tag_filter.tag].raw_value) is None:
                correction_found = False
                break

        if correction_found:
            if corrections != None:
                raise RuntimeError(f"Found multiple corrections for {file=}")
            corrections = corr_def.corrections
    return corrections
