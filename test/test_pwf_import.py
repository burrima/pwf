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

"""
This pytest module verifies the pwf_import.py script.

TODO: implement tests! There are no tests implemented yet!
"""

import pytest
import re
from bin import pwf_init
from bin import pwf_import
from bin import common
from test import common as test_common
from pathlib import Path
import shutil


root = common.pwf_root_path


@pytest.fixture
def initial_paths():
    pwf_init.create_initial_paths(root)

    test_common.create_paths((
        (f"{root}/0_new/2024-10-30_event_1/", 0),
        (f"{root}/0_new/2024-10-30_event_1/jpg/", 0),
        (f"{root}/0_new/2024-10-30_event_1/jpg/DSC_1000.jpg", 10000),
        (f"{root}/0_new/2024-10-30_event_1/jpg/DSC_1001.jpg", 10000),
        (f"{root}/0_new/2024-10-30_event_1/jpg/DSC_1002.jpg", 10000),
        (f"{root}/3_album/2024/", 0),
        (f"{root}/4_print/2024/", 0),
    ))

    for p in sorted(Path(f"{root}/1_original").glob("**/*"), reverse=True):
        p.chmod(0o555) if p.is_dir() else p.lchmod(0o444)

    yield

    for p in sorted(Path(f"{root}/1_original").glob("**/*")):
        p.chmod(0o775) if p.is_dir() else p.lchmod(0o664)

    shutil.rmtree(Path(root), ignore_errors=True)


def test_normal(initial_paths):
    pwf_import.main(Path(f"{root}/0_new/2024-10-30_event_1/"))


def test_path_not_in_new(initial_paths):
    test_common.create_paths((
        (f"{root}/4_print/2024/2024-10-30_event_2/", 0),
        (f"{root}/4_print/2024/2024-10-30_event_2/jpg/", 0),
        (f"{root}/4_print/2024/2024-10-30_event_2/jpg/DSC_1000.jpg", 0),
    ))
    with pytest.raises(ValueError) as ex:
        pwf_import.main(Path(f"{root}/4_print/2024/2024-10-30_event_2/"))

    assert str(ex.value) == \
        "Invalid path! Can only run against event dirs in 0_new!"


def test_path_is_no_event_dir(initial_paths):
    test_common.create_paths((
        (f"{root}/4_print/2024/2024-10-30_event_2/", 0),
        (f"{root}/4_print/2024/2024-10-30_event_2/jpg/", 0),
        (f"{root}/4_print/2024/2024-10-30_event_2/jpg/DSC_1000.jpg", 0),
    ))
    with pytest.raises(ValueError) as ex:
        pwf_import.main(Path(f"{root}/4_print/2024/"))

    assert str(ex.value) == \
        "Invalid path! Can only run against event dirs in 0_new!"


def test_event_without_year(initial_paths):
    test_common.create_paths((
        (f"{root}/0_new/2024_event_2/", 0),
        (f"{root}/0_new/2024_event_2/jpg/", 0),
        (f"{root}/0_new/2024_event_2/jpg/DSC_1000.jpg", 0),
        (f"{root}/0_new/event_3/", 0),
    ))
    pwf_import.main(Path(f"{root}/0_new/2024_event_2/"))

    with pytest.raises(ValueError) as ex:
        pwf_import.main(Path(f"{root}/0_new/event_3/"))
    assert str(ex.value) == \
        "Cannot detect year and no year was provided by argument!"


def test_add_images_to_existing_event(initial_paths):
    pwf_import.main(Path(f"{root}/0_new/2024-10-30_event_1/"))
    test_common.create_paths((
        (f"{root}/0_new/2024-10-30_event_1/jpg/DSC_1003.jpg", 1000),
        (f"{root}/0_new/2024-10-30_event_1/jpg/DSC_1004.jpg", 1000),
    ))
    files = ("DSC_1000.jpg", "DSC_1001.jpg", "DSC_1002.jpg", "DSC_1003.jpg",
             "DSC_1004.jpg")

    pwf_import.main(Path(f"{root}/0_new/2024-10-30_event_1/"))

    # assert that all files are at correct locations:
    for i, p in enumerate(
            sorted(Path(f"{root}/1_original/2024/").glob("**/*.*"))):
        print(p)
        assert str(p) == (
            f"{root}/1_original/2024/2024-10-30_event_1/jpg/{files[i]}")

    # assert that md5 checksum file is correct:
    with open(f"{root}/1_original/2024.md5", "r") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        print(line)
        assert re.match(
            r"[0-9a-f]+ \*2024/2024-10-30_event_1/jpg/" + files[i],
            line) is not None


def test_import_existing_file(initial_paths):
    pwf_import.main(Path(f"{root}/0_new/2024-10-30_event_1/"))
    test_common.create_paths((
        (f"{root}/0_new/2024-10-30_event_1/jpg/DSC_1000.jpg", 1000),
    ))

    with pytest.raises(RuntimeError) as ex:
        pwf_import.main(Path(f"{root}/0_new/2024-10-30_event_1/"))

    assert str(ex.value) == \
        "File jpg/DSC_1000.jpg exists in destination path!"
