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

import pytest
from bin import pwf_init
from bin import pwf_downsize
from bin import common
from test import common as test_common
from pathlib import Path
import shutil
import os
import logging


root = common.pwf_root_path


@pytest.mark.parametrize("im_size", (
    pwf_downsize.Size(500, 600),
    pwf_downsize.Size(5000, 2000),
    pwf_downsize.Size(2000, 5000),
))
@pytest.mark.parametrize("box", (
    pwf_downsize.Size(1024, 720),
    pwf_downsize.Size(720, 1024),
))
@pytest.mark.parametrize("align", (True, False))
def test__compute_inside_box(im_size, box, align):

    size = pwf_downsize._compute_inside_box(im_size, box, align=align)
    logging.info(f"{im_size=}, {box=}, {align=} => {size=}")

    assert type(size.width) is int
    assert type(size.height) is int

    if im_size.width <= box.width and im_size.height <= box.height:
        # image is already inside box, no change expected
        assert size.width == im_size.width
        assert size.height == im_size.height
        return

    if align is True:
        # bring im_size and box to landscape format
        if size.is_portrait():
            size.rotate()
        if box.is_portrait():
            box.rotate()

    # image must fit exactly into box
    assert size.width <= box.width
    assert size.height <= box.height
    assert size.width == box.width or size.height == box.height


def test_illegal_tag():
    with pytest.raises(ValueError) as ex:
        pwf_downsize.main(Path(), "asdf")
    assert str(ex.value) == "Illegal tag provided!"
