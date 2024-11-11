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


from bin import common
from collections import defaultdict
from pathlib import Path
import argparse
import copy
import logging
import re
import stat


logger = logging.getLogger(__name__)


info_text =\
    """
Links SRC file(s) into the DST_DIR directory.

SRC can be a file or a folder. Folders can be traversed recursively with
the option -r. A DST_DIR can be specified where to place the links. If
no destination is provided, the files will be placed where the script is
called from.

DST_DIR can be set to "@lab" to cause special behavior: In this case,
SRC must point to an event folder in the 1_original/ tree. All files are
then linked into the corresponding event folder in the 2_lab/ tree, into
sub- folders 2_original_{jpg,raw,audio,video} (implies option -r). RAW
and JPG images are only linked if a corresponding preview file is
present in the folder 1_preview/ of the lab event folder. This can be
bypassed with the option -a.
    """ + common.fzf_info_text

def _tag_to_path(pwf_src_path, tag):
    """
    Given a tag, try to determine dst_path automatically.
    
    This only works in certain conditions which are checked here. If any is not
    met, a ValueError is raised.
    """

    if tag not in common.tag_dirs.keys():
        raise ValueError(f"Tag '{tag}' is not valid!")

    src = str(pwf_src_path.path)
    dst = src.replace(common.state_dirs[pwf_src_path.state],
                      common.tag_dirs[tag])

    if pwf_src_path.state == common.State.LAB:
        # With tags, only allow to link to 3_final_xy folders!
        if "3_final_" not in src:
            raise ValueError("Not allowed to link from this src_path!")
        dst = dst.replace("3_final_", "")

    if tag == "@lab":
        # With tags, only allow to create links in 2_original_xy folders,
        # pointing to 1_original folders!
        if pwf_src_path.state != common.State.ORIGINAL:
            raise ValueError("Only allowed to link to 1_original/ folders!")
        # change destination sub-dir from raw->2_original_raw etc:
        found = False
        for ftype in common.type_dirs:
            if ftype in src:
                dst = dst.replace(ftype, f"2_original_{ftype}")
                found = True
                break
        if not found:
            raise ValueError(f"Cannot determine file type dir from src_path!")

    return Path(dst)


def _relative_to(src: Path, dst: Path) -> Path:
    """
    Returns the relative path from dst to src.

    The relative path is build in 2 steps:
        * relative path up to root (../../...)
        * relative path from root to src

    Python >=3.12 allows the following:

        return src.relative_to(dst.parent, walk_up=True)

    However, this is not going through the root path.
    """
    rel_src = src.relative_to(common.pwf_root_path)
    rel_dst = dst.relative_to(common.pwf_root_path)
    rel_root = Path("../" * (len(rel_dst.parents) - 1))
    return rel_root / rel_src


def _link_to_file(src_path, dst_path, is_forced=False):
    """
    Create a link to a single file (or symlink).

    Non-existing dst_path directory tree will be auto-generated.
    Links will be relative.
    With is_forced=True, existing files will be overwritten, else ignored.
    """

    if src_path.is_symlink():
        src_path = src_path.readlink()
    if is_forced and dst_path.exists(follow_symlinks=False):
        dst_path.unlink()
    try:
        rel_src = _relative_to(src_path, dst_path)
        logger.info(f"link: {dst_path} -> {rel_src}")
        dst_path.symlink_to(rel_src)
    except FileExistsError:
        logger.warning(f"Target file exists, not touched!")


def _link_to_files_in_dir(src_path, dst_path, is_forced=False, filt=None):
    """
    Create symlinks from dst_path to files in src_path directory.
    """

    dst_path.mkdir(parents=True, exist_ok=True)

    for p in src_path.glob("*.*"):
        if filt is not None:
            filt_matches = [f for f in filt if f in p]
            if len(filt_matches) > 1:
                logger.warning("More than 1 filter pattern match the file!")
            elif len(filt_matches) == 0:
                logger.info(f"Ignore due to not matching filter: {p}")
                continue
        dst = dst_path / p.name
        _link_to_file(p, dst, is_forced)


def main(src_path: Path, dst_path: Path, is_all: bool=False,
         is_forced: bool=False):

    link_name = None

    logger.info("pwf_link: ENTRY")

    # parse and check path:
    pwf_src_path = common.PwfPath(src_path, must_exist=True)

    if common.path_is_tag(dst_path):
        dst_path = _tag_to_path(pwf_src_path, str(dst_path))

    # parse and check path:
    pwf_dst_path = common.PwfPath(dst_path)

    logger.debug(f"{pwf_src_path=}, {pwf_dst_path=}, {is_all=}, {is_forced=}")

    # TODO: if destination is @lab, then use preview files to filter which
    # links are created!
    filt = None
    # if pwf_dst_path.state == common.State.LAB:
    #     for p in 

    if pwf_src_path.path.is_dir():
        _link_to_files_in_dir(
            pwf_src_path.path, pwf_dst_path.path, is_forced, filt)

    else:
        if pwf_dst_path.path.is_dir():
            dst_path = pwf_dst_path.path / pwf_src_path.path.name

        _link_to_file(pwf_src_path.path, pwf_dst_path.path, is_forced)

    logger.info("pwf_link: OK")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=info_text)

    parser.add_argument("-a", "--all",
                        help="link all files to lab, indept. of previews",
                        action="store_true")
    parser.add_argument("-f", "--forced",
                        help="overwrite existing links",
                        action="store_true")
    parser.add_argument("-l", "--loglevel",
                        help="log level to use",
                        default="INFO")
    parser.add_argument("src_path", nargs='?', default=Path.cwd())
    parser.add_argument("dst_path", nargs='?')
    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=args.loglevel.upper())
    logger.debug(f"{args=}")

    try:
        main(Path(args.src_path), Path(args.dst_path), args.all, args.forced)
    except Exception as ex:
        if args.loglevel.upper() == "DEBUG":
            raise
        logger.error(str(ex))
