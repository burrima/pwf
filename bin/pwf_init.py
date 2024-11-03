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

from pathlib import Path
import os


paths = (
    # path, size
    ("0_new/template/raw/", 0),
    ("0_new/template/jpg/", 0),
    ("0_new/template/audio/", 0),
    ("0_new/template/video/", 0),

    ("0_new/2024-10-30_example_event/jpg/DSC_1234.jpg", 20000),
    ("0_new/2024-10-30_example_event/jpg/DSC_1235.jpg", 21000),
    ("0_new/2024-10-30_example_event/jpg/DSC_1236.jpg", 22000),

    ("0_new/2024-10-30_example_event/raw/DSC_1237.NEF", 30000),
    ("0_new/2024-10-30_example_event/raw/DSC_1238.NEF", 31000),

    ("1_original/", 0),
    ("2_lab/", 0),
    ("3_album/", 0),
    ("4_print/", 0),
)


def create_dir(path):
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)


def create_file(path, size=0):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "wb") as f:
        f.write(os.urandom(size))


def create_initial_paths(root):
    root = Path(root)
    root.mkdir()  # fail if exists!

    for path, size in paths:
        if path[-1] == "/":
            create_dir(root / path)
        else:
            create_file(root / path, size)


if __name__ == "__main__":
    create_initial_paths("pictures")
