#!/usr/bin/env python3
# Copyright 2026 Martin Burri
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

import pytest
from bin import pwf_init
from bin import common
from bin import corrections_definitions as cd
from test import common as test_common
import shutil
from pathlib import Path
import logging


root = common.pwf_root_path


@pytest.fixture
def initial_paths():
    pwf_init.create_initial_paths(root)

    yield

    shutil.rmtree(Path(root), ignore_errors=True)


yaml_strings = {
    """
- corrections:
    tz_offset: +02:00
    gps_lat_lng: "-26.715011, 27.103188"

- filter:
    tags:
      - tag: "Exif.Image.Model"
        value: "Canon PowerShot G9 X"
  corrections:
    time:
      hours: +1
      minutes: -3
      seconds: 0
    tags:
      - tag: "Exif.Image.Artist"
        replacement: "Fabienne Péquignot"

- filter:
    tags:
      - tag: "Exif.Image.Model"
        value: "NIKON D750"
  corrections:
    time:
      hours: +1
      minutes: +3
      seconds: 0
    """,
}


@pytest.mark.parametrize("yaml_str", yaml_strings)
def test_get_corrections_definitions(initial_paths, yaml_str):

    with open(root / "2_lab" / "exif_corrections.yaml", "w") as f:
        f.write(yaml_str)

    corr_defs = cd.get_corrections_definitions(root / "2_lab")
    logging.info(corr_defs)


#@pytest.mark.parametrize("yaml_str", yaml_strings)
#def test_get_file_corrections(initial_paths, yaml_str):
