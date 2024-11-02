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
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
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
from bin import pwf_check
from bin import common
from pathlib import Path
import shutil
import os
import logging


root_path = "test/pictures"


def create_paths(extra_paths):
    for path, size in extra_paths:
        if path[-1] == "/":
            pwf_init.create_dir(path)
        else:
            pwf_init.create_file(path, size)


@pytest.fixture
def initial_paths():
    pwf_init.create_initial_paths(root_path)

    create_paths((
        (f"{root_path}/1_original/2024/2024-10-30_event_1/", 0),
        (f"{root_path}/1_original/2024/2024-10-30_event_1/jpg/", 0),
        (f"{root_path}/1_original/2024/2024-10-30_event_1/jpg/DSC_1000.jpg", 10000),
        (f"{root_path}/1_original/2024/2024-10-30_event_1/jpg/DSC_1001.jpg", 10000),
        (f"{root_path}/1_original/2024/2024-10-30_event_1/jpg/DSC_1002.jpg", 10000),
        (f"{root_path}/3_album/2024/", 0),
        (f"{root_path}/4_print/2024/", 0),
    ))

    for p in sorted(Path(f"{root_path}/1_original").glob("**/*"), reverse=True):
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


def test_normal(initial_paths):
    logging.info(">>> check 0_new")
    pwf_check.check(Path(f"{root_path}/0_new"))
    logging.info(">>> check 1_original")
    pwf_check.check(Path(f"{root_path}/1_original/2024"))
    logging.info(">>> check 2_lab")
    pwf_check.check(Path(f"{root_path}/2_lab"))
    logging.info(">>> check 3_album")
    pwf_check.check(Path(f"{root_path}/3_album/2024"))
    logging.info(">>> check 4_print")
    pwf_check.check(Path(f"{root_path}/4_print/2024"))


def test_cs(initial_paths):
    # TODO: implement!
    pass


def test_dup(initial_paths):
    logging.info(">>> create 2 files of same size in 0_new")
    p1 = f"{root_path}/0_new/2024-10-30_example_event/jpg/a.jpg"
    p2 = f"{root_path}/0_new/2024-10-30_example_event/jpg/b.jpg"
    pwf_init.create_file(p1)
    pwf_init.create_file(p2)
    for p in (p1, p2):
        with open(p, "wb") as f:
            data = os.urandom(15000)
            f.write(data)

    pwf_check.check(Path(f"{root_path}/0_new"))

    logging.info(">>> create 2 identical files in 0_new")
    data = os.urandom(15000)
    for p in (p1, p2):
        with open(p, "wb") as f:
            f.write(data)

    with pytest.raises(AssertionError) as exception:
        pwf_check.check(Path(f"{root_path}/0_new"))

    assert str(exception.value) == "Found duplicate files!"


def test_miss(initial_paths):
    # TODO: implement!
    pass


def test_name(initial_paths, caplog):
    logging.info(">>> create directory and files with wrong characters")
    create_paths ((
        (f"{root_path}/0_new/2024-10-30_event & space/", 0),
        (f"{root_path}/0_new/2024-10-30_event & space/jpg/my file.jpg", 512),
    ))

    logging.info(">>> check for name violations")
    with pytest.raises(AssertionError) as exception:
        pwf_check.check(Path(f"{root_path}/0_new"), onlylist={"name",})

    assert str(exception.value) == "Found illegal chars in file or folder names!"

    p = f"{root_path}/0_new/"
    assert f"Illegal: '{p}2024-10-30_event & space'" in caplog.text
    assert f"Illegal: '{p}2024-10-30_event & space/jpg/my file.jpg'" in caplog.text


def test_fix_name_nono(initial_paths, caplog):
    logging.info(">>> create directory and files with wrong characters")
    create_paths ((
        (f"{root_path}/0_new/2024-10-30_event & space/", 0),
        (f"{root_path}/0_new/2024-10-30_event & space/jpg/my file.jpg", 512),
    ))

    logging.info(">>> fix name violations - dry-run")
    pwf_check.check(Path(f"{root_path}/0_new"), onlylist={"name",}, do_fix=True, is_nono=True)

    assert "Dry-run: would do the following:" in caplog.text
    assert "'my file.jpg' -> 'my_file.jpg'" in caplog.text
    assert "'2024-10-30_event & space' -> '2024-10-30_event_und_space'" in caplog.text


def test_fix_name(initial_paths, caplog):
    logging.info(">>> create directory and files with wrong characters")
    create_paths ((
        (f"{root_path}/0_new/2024-10-30_event & space/", 0),
        (f"{root_path}/0_new/2024-10-30_event & space/jpg/my file.jpg", 512),
    ))

    logging.info(">>> fix name violations")
    pwf_check.check(Path(f"{root_path}/0_new"), onlylist={"name",}, do_fix=True)

    assert "Dry-run: would do the following:" not in caplog.text
    assert "'my file.jpg' -> 'my_file.jpg'" in caplog.text
    assert "'2024-10-30_event & space' -> '2024-10-30_event_und_space'" in caplog.text


def test_path(initial_paths, caplog):
    logging.info(">>> create files in wrong subdirs")
    create_paths ((
        (f"{root_path}/0_new/2024-10-30_example_event/raw/myFile.jpg", 512),
        (f"{root_path}/0_new/2024-10-30_example_event/jpg/myFile.NEF", 512),
    ))

    logging.info(">>> check path violations")
    with pytest.raises(AssertionError) as exception:
        pwf_check.check(Path(f"{root_path}/0_new"), onlylist={"path",})

    assert str(exception.value) == "Found files in wrong locations!"

    assert f"File in wrong location: {root_path}/0_new/2024-10-30_example_event/jpg/myFile.NEF" in caplog.text
    assert f"File in wrong location: {root_path}/0_new/2024-10-30_example_event/raw/myFile.jpg" in caplog.text


def test_prot(initial_paths, caplog):
    logging.info(">>> create unprotected file in protected folder structure")
    for p in sorted(Path(f"{root_path}/1_original").glob("**/*")):
        p.chmod(0o775) if p.is_dir() else p.lchmod(0o664)
    for p in sorted(Path(f"{root_path}/1_original").glob("**/*"), reverse=True):
        if "DSC_1000.jpg" in str(p):
            continue
        p.chmod(0o555) if p.is_dir() else p.lchmod(0o444)

    logging.info(">>> check file and folder protection")
    with pytest.raises(AssertionError) as exception:
        pwf_check.check(Path(f"{root_path}/1_original/2024"), onlylist={"prot",})

    assert str(exception.value) == "Found unprotected files or directories!"
    assert f"Not protected: -rw-rw-r-- {root_path}/1_original/2024/2024-10-30_event_1/jpg/DSC_1000.jpg" in caplog.text


def test_raw(initial_paths, caplog):
    create_paths ((
        (f"{root_path}/0_new/2024-10-30_example_event/jpg/DSC_1237.jpg", 300),
    ))

    logging.info(">>> check raw derivatives")
    with pytest.raises(AssertionError) as exception:
        pwf_check.check(Path(f"{root_path}/0_new/2024-10-30_example_event"), onlylist={"raw",})

    assert str(exception.value) == "Found RAW derivatives!"
    text = "Files with same name:\n"
    text += f"  {root_path}/0_new/2024-10-30_example_event/jpg/DSC_1237.jpg\n"
    text += f"  {root_path}/0_new/2024-10-30_example_event/raw/DSC_1237.NEF"
    assert text in caplog.text


def test_get_checklist_normal():
    assert pwf_check.things_to_check == {"cs", "dup", "miss", "name", "path", "prot", "raw"}

    logging.info(">>> assert default checklist for 0_new")
    p = common.PwfPath(Path(f"{root_path}/0_new/"))
    cl = pwf_check._get_checklist(p)
    assert cl == {"name", "raw", "path", "dup"}

    logging.info(">>> assert default checklist for 1_original")
    p = common.PwfPath(Path(f"{root_path}/1_original/"))
    cl = pwf_check._get_checklist(p)
    assert cl == pwf_check.things_to_check

    logging.info(">>> assert default checklist for 2_lab")
    p = common.PwfPath(Path(f"{root_path}/2_lab/"))
    cl = pwf_check._get_checklist(p)
    assert cl == {"name", "dup"}

    logging.info(">>> assert default checklist for 3_album")
    p = common.PwfPath(Path(f"{root_path}/3_album/"))
    cl = pwf_check._get_checklist(p)
    assert cl == pwf_check.things_to_check

    logging.info(">>> assert default checklist for 4_print")
    p = common.PwfPath(Path(f"{root_path}/4_print/"))
    cl = pwf_check._get_checklist(p)
    assert cl == pwf_check.things_to_check


def test_get_checklist_ignore(caplog):

    logging.info(">>> do not allow dup and path ignore in 0_new")

    with pytest.raises(ValueError) as exception:
        pwf_check.check(Path(f"{root_path}/0_new"), ignorelist={"dup",})
    assert str(exception.value) == "Ignoring duplicate violations is not allowed in 0_new!"

    with pytest.raises(ValueError) as exception:
        pwf_check.check(Path(f"{root_path}/0_new"), ignorelist={"path",})
    assert str(exception.value) == "Ignoring path violations is not allowed in 0_new!"

    logging.info(">>> exit when everything is ignored")
    p = common.PwfPath(Path(f"{root_path}/1_original/"))
    with pytest.raises(ValueError) as exception:
        pwf_check._get_checklist(p, ignorelist=pwf_check.things_to_check)
    assert str(exception.value) == "Everything ignored, nothing to check!"

    logging.info(">>> test normal ingorelist use case")
    cl = pwf_check._get_checklist(p, ignorelist={"cs", "dup"})
    assert cl == {"miss", "name", "path", "prot", "raw"}


def test_get_checklist_ignore_name(caplog):
    logging.info(">>> print warning when name check is ignored")
    p = common.PwfPath(Path(f"{root_path}/1_original/"))
    cl = pwf_check._get_checklist(p, ignorelist={"name"})
    assert cl == {"cs", "dup", "miss", "path", "prot", "raw"}
    assert "Ignoring name violations is strongly discouraged!" in caplog.text
