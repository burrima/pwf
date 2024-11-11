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
from bin import pwf_link
from bin import common
from test import common as test_common
from pathlib import Path
import shutil
import os
import logging
import filecmp


root = test_common.root_path


@pytest.fixture
def initial_paths():
    pwf_init.create_initial_paths(root)

    test_common.create_paths((
        (f"{root}/1_original/2024/2024-10-30_ev_1/", 0),
        (f"{root}/1_original/2024/2024-10-30_ev_1/jpg/", 0),
        (f"{root}/1_original/2024/2024-10-30_ev_1/jpg/DSC_100.jpg", 1000),
        (f"{root}/1_original/2024/2024-10-30_ev_1/jpg/DSC_101.jpg", 1000),
        (f"{root}/1_original/2024/2024-10-30_ev_1/jpg/DSC_102.jpg", 1000),
        (f"{root}/1_original/2024/2024-10-30_ev_1/raw/DSC_103.NEF", 9000),
        (f"{root}/3_album/2024/", 0),
        (f"{root}/4_print/2024/", 0),
    ))

    path = Path(f"{root}/1_original").glob("**/*")
    for p in sorted(path, reverse=True):
        p.chmod(0o555) if p.is_dir() else p.lchmod(0o444)
    for p in sorted(Path(f"{root}/3_album").glob("**/*"), reverse=True):
        p.chmod(0o555) if p.is_dir() else p.lchmod(0o444)
    for p in sorted(Path(f"{root}/4_print").glob("**/*"), reverse=True):
        p.chmod(0o555) if p.is_dir() else p.lchmod(0o444)

    yield

    for p in sorted(Path(f"{root}/1_original").glob("**/*")):
        p.chmod(0o775) if p.is_dir() else p.lchmod(0o664)
    for p in sorted(Path(f"{root}/3_album").glob("**/*")):
        p.chmod(0o775) if p.is_dir() else p.lchmod(0o664)
    for p in sorted(Path(f"{root}/4_print").glob("**/*")):
        p.chmod(0o775) if p.is_dir() else p.lchmod(0o664)

    shutil.rmtree(Path(root), ignore_errors=True)


def test__relative_to():

    vectors = [
        (f"{root}/a/b/c", f"{root}/a/b/d", "../../a/b/c"),
        (f"{root}/a/b/c/", f"{root}/a/b/d", "../../a/b/c"),
        (f"{root}/a/b/c/", f"{root}/a/b/d/x", "../../../a/b/c"),
    ]

    for vector in vectors:
        c = pwf_link._relative_to(Path(vector[0]), Path(vector[1]))
        assert c == Path(vector[2])


def test_lab_preparation(initial_paths, caplog):

    f1s = f"{root}/1_original/2024/2024-10-30_ev_1/jpg/DSC_100.jpg"
    f1d = f"{root}/2_lab/2024/2024-10-30_ev_1/2_original_jpg/DSC_100.jpg"

    f2s = f"{root}/1_original/2024/2024-10-30_ev_1/raw/DSC_103.NEF"
    f2d = f"{root}/2_lab/2024/2024-10-30_ev_1/2_original_raw/DSC_103.NEF"

    logging.info(">>># link jpg from 1_original to 2_lab")
    pwf_link.main(Path(f"{root}/1_original/2024/2024-10-30_ev_1/jpg"),
                  Path("@lab"))

    logging.info(">>># assert output text")
    text = "link: "
    text += f"{f1d} -> "
    text += "../../../../1_original/2024/2024-10-30_ev_1/jpg/DSC_100.jpg"
    assert text in caplog.text

    logging.info(">>># link raw from 1_original to 2_lab")
    pwf_link.main(Path(f"{root}/1_original/2024/2024-10-30_ev_1/raw"),
                  Path("@lab"))

    logging.info(">>># assert output text")
    text = "link: "
    text += f"{f2d} -> "
    text += "../../../../1_original/2024/2024-10-30_ev_1/raw/DSC_103.NEF"
    assert text in caplog.text

    logging.info(">>># assert linked files are equal")
    assert filecmp.cmp(f1s, f1d, shallow=False)
    assert filecmp.cmp(f2s, f2d, shallow=False)


def test_lab_orig_to_album(initial_paths):
    pass
