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
from bin import pwf_protect
from test import common as test_common
from pathlib import Path
import shutil


root_path = test_common.root_path


@pytest.fixture
def initial_paths():
    pwf_init.create_initial_paths(root_path)

    test_common.create_paths((
        (f"{root_path}/1_original/2024/2024-10-30_ev_1/", 0),
        (f"{root_path}/1_original/2024/2024-10-30_ev_1/jpg/", 0),
        (f"{root_path}/1_original/2024/2024-10-30_ev_1/jpg/DSC_100.jpg", 9000),
        (f"{root_path}/1_original/2024/2024-10-30_ev_1/jpg/DSC_101.jpg", 9000),
        (f"{root_path}/1_original/2024/2024-10-30_ev_1/jpg/DSC_102.jpg", 9000),
        (f"{root_path}/3_album/2024/", 0),
        (f"{root_path}/4_print/2024/", 0),
    ))

    path = Path(f"{root_path}/1_original").glob("**/*")
    for p in sorted(path, reverse=True):
        p.chmod(0o555) if p.is_dir() else p.lchmod(0o444)
    for p in sorted(Path(f"{root_path}/3_album").glob("**/*"), reverse=True):
        p.chmod(0o555) if p.is_dir() else p.lchmod(0o444)
    for p in sorted(Path(f"{root_path}/4_print").glob("**/*"), reverse=True):
        p.chmod(0o555) if p.is_dir() else p.lchmod(0o444)

    yield

    for p in sorted(Path(f"{root_path}/1_original").glob("**/*")):
        p.chmod(0o775) if p.is_dir() else p.lchmod(0o664)
    for p in sorted(Path(f"{root_path}/3_album").glob("**/*")):
        p.chmod(0o775) if p.is_dir() else p.lchmod(0o664)
    for p in sorted(Path(f"{root_path}/4_print").glob("**/*")):
        p.chmod(0o775) if p.is_dir() else p.lchmod(0o664)

    shutil.rmtree(Path(root_path), ignore_errors=True)


def test_unprotect(initial_paths):
    pwf_protect.main(Path(f"{root_path}/1_original/2024"),
                     do_unprotect=True, is_all=True)
    pwf_protect.main(Path(f"{root_path}/1_original/2024"))
