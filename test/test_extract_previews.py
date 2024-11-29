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
from bin import pwf_extract_previews
from bin import common
from test import common as test_common
from pathlib import Path
import shutil
import os
import logging


root = common.pwf_root_path


@pytest.fixture
def initial_paths():
    pwf_init.create_initial_paths(root)

    test_common.create_paths((
        (f"{root}/1_original/2024/2024-10-30_ev_1/", 0),
        (f"{root}/1_original/2024/2024-10-30_ev_1/jpg/", 0),
        (f"{root}/1_original/2024/2024-10-30_ev_1/jpg/DSC_100.jpg", 0),
        (f"{root}/1_original/2024/2024-10-30_ev_1/jpg/DSC_101.jpg", 0),
        (f"{root}/1_original/2024/2024-10-30_ev_1/jpg/DSC_102.jpg", 0),
        (f"{root}/2_lab/2024/2024-10-30_ev_1/", 0),
        (f"{root}/2_lab/2024/2024-10-30_ev_1/3_final_jpg/", 0),
        (f"{root}/2_lab/2024/2024-10-30_ev_1/3_final_jpg/DSC_100.jpg", 0),
        (f"{root}/2_lab/2024/2024-10-30_ev_1/3_final_jpg/DSC_101.jpg", 0),
        (f"{root}/2_lab/2024/2024-10-30_ev_1/3_final_jpg/DSC_102.jpg", 0),
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


def test_inplace_file(initial_paths, caplog):
    path = Path(f"{root}/2_lab/2024/2024-10-30_ev_1/3_final_jpg/DSC_100.jpg")
    pwf_extract_previews.main(path, is_nono=True)

    text = "NONO: 2_lab/2024/2024-10-30_ev_1/3_final_jpg/DSC_100.jpg -> " +\
           "2_lab/2024/2024-10-30_ev_1/3_final_jpg/DSC_100.jpg-preview.jpg"
    assert text in caplog.text


def test_inplace_dir(initial_paths, caplog):
    path = Path(f"{root}/2_lab/2024/2024-10-30_ev_1/3_final_jpg/")
    pwf_extract_previews.main(path, is_nono=True)

    for i in range(100, 103):
        text = \
            f"NONO: 2_lab/2024/2024-10-30_ev_1/3_final_jpg/DSC_{i}.jpg -> " +\
            f"2_lab/2024/2024-10-30_ev_1/3_final_jpg/DSC_{i}.jpg-preview.jpg"
        assert text in caplog.text


def test_src_file_to_dst_dir(initial_paths, caplog):
    test_common.create_paths((
        # dst_dir is not automatically created!
        (f"{root}/2_lab/2024/2024-10-30_ev_1/asdf/", 0),
    ))
    src_path = Path(
        f"{root}/2_lab/2024/2024-10-30_ev_1/3_final_jpg/DSC_100.jpg")
    dst_path = Path(f"{root}/2_lab/2024/2024-10-30_ev_1/asdf/")
    pwf_extract_previews.main(src_path, dst_path, is_nono=True)

    text = "NONO: 2_lab/2024/2024-10-30_ev_1/3_final_jpg/DSC_100.jpg -> " +\
           "2_lab/2024/2024-10-30_ev_1/asdf/DSC_100.jpg-preview.jpg"
    assert text in caplog.text


def test_src_file_to_dst_file(initial_paths, caplog):
    test_common.create_paths((
        # dst_dir is not automatically created!
        (f"{root}/2_lab/2024/2024-10-30_ev_1/asdf/", 0),
    ))
    src_path = Path(
        f"{root}/2_lab/2024/2024-10-30_ev_1/3_final_jpg/DSC_100.jpg")
    dst_path = Path(f"{root}/2_lab/2024/2024-10-30_ev_1/asdf/my.jpg")
    with pytest.raises(ValueError) as ex:
        pwf_extract_previews.main(src_path, dst_path, is_nono=True)
    assert str(ex.value) == "DST_PATH must be directory or '@lab'!"


def test_src_dir_to_dst_dir(initial_paths, caplog):
    test_common.create_paths((
        # dst_dir is not automatically created!
        (f"{root}/2_lab/2024/2024-10-30_ev_1/asdf/", 0),
    ))
    src_path = Path(f"{root}/2_lab/2024/2024-10-30_ev_1/3_final_jpg/")
    dst_path = Path(f"{root}/2_lab/2024/2024-10-30_ev_1/asdf/")
    pwf_extract_previews.main(src_path, dst_path, is_nono=True)

    for i in range(100, 103):
        text = \
            f"NONO: 2_lab/2024/2024-10-30_ev_1/3_final_jpg/DSC_{i}.jpg -> " +\
            f"2_lab/2024/2024-10-30_ev_1/asdf/DSC_{i}.jpg-preview.jpg"
        assert text in caplog.text


def test_src_dir_to_tag_lab(initial_paths, caplog):
    src_path = Path(f"{root}/1_original/2024/2024-10-30_ev_1/jpg/")
    dst_path = Path(f"{root}/2_lab/2024/2024-10-30_ev_1/1_preview/")
    pwf_extract_previews.main(src_path, "@lab", is_nono=True)

    text = f"NONO: Would create (if not existing): {dst_path}"
    assert text in caplog.text

    for i in range(100, 103):
        text = \
            f"NONO: 1_original/2024/2024-10-30_ev_1/jpg/DSC_{i}.jpg -> " +\
            f"2_lab/2024/2024-10-30_ev_1/1_preview/DSC_{i}.jpg-preview.jpg"
        assert text in caplog.text


def test_ignore_existing_file(initial_paths, caplog):
    test_common.create_paths((
        # dst_dir is not automatically created!
        (f"{root}/2_lab/2024/2024-10-30_ev_1/1_preview/" +
         "DSC_101.jpg-preview.jpg", 0),
    ))
    src_path = Path(f"{root}/1_original/2024/2024-10-30_ev_1/jpg/")
    dst_path = Path(f"{root}/2_lab/2024/2024-10-30_ev_1/1_preview/")
    pwf_extract_previews.main(src_path, "@lab", is_nono=True)

    text = f"NONO: Would create (if not existing): {dst_path}"
    assert text in caplog.text

    file = "1_original/2024/2024-10-30_ev_1/jpg/DSC_101.jpg"
    text = f"Ignore (exists): {file}"
    assert text in caplog.text

    for i in [100, 102]:
        text = \
            f"NONO: 1_original/2024/2024-10-30_ev_1/jpg/DSC_{i}.jpg -> " +\
            f"2_lab/2024/2024-10-30_ev_1/1_preview/DSC_{i}.jpg-preview.jpg"
        assert text in caplog.text


def test_unsupported_extension(initial_paths, caplog):
    file = f"{root}/2_lab/2024/2024-10-30_ev_1/hello.xyz"
    test_common.create_paths((
        (file, 0),
    ))
    src_path = Path(file)
    pwf_extract_previews.main(src_path, "@lab", is_nono=True)

    text = f"Ignored file due to unsupported extension: {file}"
    assert text in caplog.text
