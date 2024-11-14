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
import logging
import filecmp


root = common.pwf_root_path


@pytest.fixture
def initial_paths():
    pwf_init.create_initial_paths(root)

    test_common.create_paths((
        (f"{root}/1_original/2024/2024-10-30_ev_1/", 0),
        (f"{root}/1_original/2024/2024-10-30_ev_1/jpg/", 0),
        (f"{root}/1_original/2024/2024-10-30_ev_1/jpg/DSC_100.jpg", 100),
        (f"{root}/1_original/2024/2024-10-30_ev_1/jpg/DSC_101.jpg", 100),
        (f"{root}/1_original/2024/2024-10-30_ev_1/jpg/DSC_102.jpg", 100),
        (f"{root}/1_original/2024/2024-10-30_ev_1/raw/DSC_103.NEF", 900),
        (f"{root}/1_original/2024/2024-10-30_ev_1/audio/track01.mp3", 75),
        (f"{root}/1_original/2024/2024-10-30_ev_1/video/birds.mpeg", 850),
        (f"{root}/3_album/2024/", 0),
        (f"{root}/4_print/2024/", 0),
    ))

    yield

    shutil.rmtree(Path(root), ignore_errors=True)


@pytest.fixture
def prepare_lab():
    pwf_link.main(Path(f"{root}/1_original/2024/2024-10-30_ev_1/jpg"),
                  Path("@lab"))
    pwf_link.main(Path(f"{root}/1_original/2024/2024-10-30_ev_1/raw"),
                  Path("@lab"))
    pwf_link.main(Path(f"{root}/1_original/2024/2024-10-30_ev_1/audio"),
                  Path("@lab"))
    pwf_link.main(Path(f"{root}/1_original/2024/2024-10-30_ev_1/video"),
                  Path("@lab"))


@pytest.mark.parametrize("tag", common.tags)
def test__tag_to_path(tag):
    """
    Test of method _tag_to_path() for all tags
    """
    src = Path(f"{root}/1_original/2024/")
    with pytest.raises(ValueError) as ex:
        pwf_link._tag_to_path(src, tag)
    assert str(ex.value) == \
        "Linking to tag only allowed from within event dirs!"

    # TODO: continue here!


def test__tag_to_path_invalid_tag():
    """
    Test of method _tag_to_path() with illegal tag
    """

    with pytest.raises(ValueError) as ex:
        pwf_link._tag_to_path(None, "@asdf")
    assert str(ex.value) == "Tag '@asdf' is not valid!"


def test__relative_to():
    """
    Test of method _relative_to()
    """

    vectors = [
        (f"{root}/a/b/c", f"{root}/a/b/d", "../../a/b/c"),
        (f"{root}/a/b/c/", f"{root}/a/b/d", "../../a/b/c"),
        (f"{root}/a/b/c/", f"{root}/a/b/d/x", "../../../a/b/c"),
    ]

    for vector in vectors:
        c = pwf_link._relative_to(Path(vector[0]), Path(vector[1]))
        assert c == Path(vector[2])


def test_lab_preparation(initial_paths, caplog):
    """
    Normal use case to prepare the lab

    TODO: test with/without preview filtering!
    """

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


@pytest.mark.parametrize("tag", common.tags)
@pytest.mark.parametrize("type_dir", common.type_dirs)
def test_lab_orig_to_tag(initial_paths, prepare_lab, tag, type_dir):
    """
    Linking from 1_original_ lab folder must be not allowed
    """

    logging.info(f">>># link from lab orig {type_dir} to {tag} must not work")

    with pytest.raises(ValueError) as ex:
        pwf_link.main(
            Path(f"{root}/2_lab/2024/2024-10-30_ev_1/2_original_{type_dir}"),
            Path(tag))
    assert str(ex.value) == "Not allowed to link from this src_path!"


@pytest.mark.parametrize("tag", common.tags)
def test_lab_final_to_tag(initial_paths, prepare_lab, tag):
    """
    Linking to a tag from lab 3_final_ folders must only be allowed for @album
    and @print (and not allowed otherwise)
    """
    test_common.create_paths((
        (f"{root}/2_lab/2024/2024-10-30_ev_1/3_final_jpg/DSC_200.jpg", 100),
        (f"{root}/2_lab/2024/2024-10-30_ev_1/3_final_jpg/DSC_201.jpg", 200),
        (f"{root}/2_lab/2024/2024-10-30_ev_1/3_final_audio/DSC_202.mp3", 210),
        (f"{root}/2_lab/2024/2024-10-30_ev_1/3_final_video/DSC_203.mpeg", 220),
    ))

    allowed_tags = ("@album", "@print")

    if tag in allowed_tags:
        pwf_link.main(
            Path(f"{root}/2_lab/2024/2024-10-30_ev_1/3_final_jpg"),
            Path(tag))
        pwf_link.main(
            Path(f"{root}/2_lab/2024/2024-10-30_ev_1/3_final_audio"),
            Path(tag))
        pwf_link.main(
            Path(f"{root}/2_lab/2024/2024-10-30_ev_1/3_final_video"),
            Path(tag))

        tag_dir = common.tag_dirs[tag]

        links = (
            f"{root}/{tag_dir}/2024/2024-10-30_ev_1/jpg/DSC_200.jpg",
            f"{root}/{tag_dir}/2024/2024-10-30_ev_1/jpg/DSC_201.jpg",
            f"{root}/{tag_dir}/2024/2024-10-30_ev_1/audio/DSC_202.mp3",
            f"{root}/{tag_dir}/2024/2024-10-30_ev_1/video/DSC_203.mpeg",
        )
        for link in links:
            assert Path(link).is_symlink()
            assert Path(link).exists()  # link points to correct target
    else:
        with pytest.raises(ValueError) as ex:
            pwf_link.main(
                Path(f"{root}/2_lab/2024/2024-10-30_ev_1/3_final_jpg"),
                Path(tag))
        assert str(ex.value) == "Not allowed to link to this tag!"
