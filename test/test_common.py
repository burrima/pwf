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

"""
This pytest module verifies the common.py script.
"""

from bin import common
from pathlib import Path
import pytest


def test_parse_valid_paths():
    p = Path("/home/user/pictures/0_new/2024-01-01_event1")
    info = common.parse_path(p)
    assert info.state == common.State.NEW
    assert info.is_event_dir is True
    assert info.event == "2024-01-01_event1"
    assert info.year == 2024
    assert info.file_type is None

    p = Path("/home/user/pictures/0_new/2024/2024-01-01_event1")
    # NOTE: this is accepted!
    info = common.parse_path(p)
    assert info.state == common.State.NEW
    assert info.is_event_dir is True
    assert info.event == "2024-01-01_event1"
    assert info.year == 2024
    assert info.file_type is None

    p = Path("/home/user/pictures/0_new/event1")
    info = common.parse_path(p)
    assert info.state == common.State.NEW
    assert info.is_event_dir is True
    assert info.event == "event1"
    assert info.year is None
    assert info.file_type is None

    p = Path("/home/user/pictures/0_new/event1/jpg/DSC_123.jpg")
    info = common.parse_path(p)
    assert info.state == common.State.NEW
    assert info.is_event_dir is False
    assert info.event == "event1"
    assert info.year is None
    assert info.file_type == "jpg"

    p = Path("/home/user/pictures/1_original/2024/2024-01-01_event1")
    info = common.parse_path(p)
    assert info.state == common.State.ORIGINAL
    assert info.is_event_dir is True
    assert info.event == "2024-01-01_event1"
    assert info.year == 2024
    assert info.file_type is None

    p = Path("/home/user/pictures/2_lab/2024/2024-01-01_event1/1_original_raw")
    info = common.parse_path(p)
    assert info.state == common.State.LAB
    assert info.is_event_dir is False
    assert info.event == "2024-01-01_event1"
    assert info.year == 2024
    assert info.file_type == "raw"


def test_parse_invalid_paths():
    with pytest.raises(ValueError) as ex:
        p = Path("/home/user/pictures/asdf/2024-01-01_event1")
        common.parse_path(p)
    assert str(ex.value) == "Cannot parse state from path!"

    with pytest.raises(ValueError) as ex:
        p = Path("/home/user/pictures/0_new/1_original/2024-01-01_event1")
        common.parse_path(p)
    assert str(ex.value) == "Path must not contain more than one state dir!"

    with pytest.raises(ValueError) as ex:
        p = Path("/home/user/pictures/0_new/event/2024-01-01_event1")
        common.parse_path(p)
    assert str(ex.value) == "Event dir must contain file_type dir!"

    with pytest.raises(ValueError) as ex:
        p = Path("/home/user/pictures/0_new/event/asdf/file.asdf")
        common.parse_path(p)
    assert str(ex.value) == "Event dir must contain file_type dir!"

    with pytest.raises(ValueError) as ex:
        p = Path("/home/user/pictures/0_new/2024/event/asdf/file.asdf")
        common.parse_path(p)
    assert str(ex.value) == "Event dir must contain file_type dir!"
