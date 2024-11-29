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
from pathlib import Path
import argparse
import logging


logger = logging.getLogger(__name__)


info_text: str =\
    """
Links SRC file(s) into the DST_DIR directory.

SRC can be a file or a folder. Folders can be traversed recursively
with the option -r. A DST_DIR can be specified where to place the
links. If no destination is provided, the files will be placed where
the script is called from.

DST_DIR can be set to "@lab" to cause special behavior: In this case,
SRC must point to an event folder in the 1_original/ tree. All files
are then linked into the corresponding event folder in the 2_lab/
tree, into sub- folders 2_original_{jpg,raw,audio,video} (implies
option -r). RAW and JPG images are only linked if a corresponding
preview file is present in the folder 1_preview/ of the lab event
folder. This can be bypassed with the option -a.
    """ + common.fzf_info_text


def _tag_to_path(src_path: Path, tag: str) -> Path:
    """
    Given a tag, try to determine dst_path automatically.

    This only works in certain conditions which are checked here. If any is not
    met, a ValueError is raised.
    """

    src = str(src_path)
    src_info = common.parse_path(src_path)

    if tag not in common.tags:
        raise ValueError("Invalid tag provided!")

    if src_info.event is None:
        raise ValueError("Linking to tag only allowed from within event dir!")

    if src_info.state is None:
        raise ValueError("Invalid src_path provided!")

    dst = src.replace(common.state_dirs[src_info.state], common.tag_dirs[tag])

    if src_info.state == common.State.LAB:
        # With tags, only allow to link to 3_final_xy folders!
        if "3_final_" not in src:
            raise ValueError("Not allowed to link from this src_path!")
        dst = dst.replace("3_final_", "")

    if tag == "@lab":
        ftype = src_info.file_type
        if ftype is None:
            raise ValueError("Cannot determine file type dir from src_path!")
        dst = dst.replace(ftype, f"2_original_{ftype}")

    return Path(dst)


def _check_is_allowed(src_path: Path, dst_path: Path):

    allowed_state_links = (  # (src, dst)
        (common.State.ORIGINAL, common.State.LAB),
        (common.State.ORIGINAL, common.State.ALBUM),
        (common.State.ORIGINAL, common.State.PRINT),
        (common.State.LAB, common.State.ALBUM),
        (common.State.LAB, common.State.PRINT),
    )

    src_info = common.parse_path(src_path)
    dst_info = common.parse_path(dst_path)

    if not src_path.exists():
        raise ValueError("src_path does not exist!")

    if (src_info.state, dst_info.state) not in allowed_state_links:
        raise ValueError("Not allowed to link from src_path to dst_path!")

    if src_info.state == common.State.LAB:
        # only allow to link from 3_final_xy folders!
        if "3_final_" not in str(src_path):
            raise ValueError("Not allowed to link from this src_path!")

    if dst_info.state == common.State.LAB:
        # only allow to link to 2_original_xy folders!
        if "2_original_" not in str(dst_path):
            raise ValueError("Not allowed to link to this dst_path!")


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


def _link_to_file(src_path: Path, dst_path: Path, is_forced: bool = False):
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
        logger.warning("Target file exists, not touched!")


def _link_to_files_in_dir(src_path: Path, dst_path: Path,
                          is_forced: bool = False,
                          filt: list[str] | None = None):
    """
    Create symlinks from dst_path to files in src_path directory.
    """

    dst_path.mkdir(parents=True, exist_ok=True)

    for p in src_path.glob("*.*"):
        if filt is not None:
            filt_matches = [f for f in filt if f in str(p)]
            if len(filt_matches) > 1:
                logger.warning("More than 1 filter pattern match the file!")
            elif len(filt_matches) == 0:
                logger.info(f"Ignore due to not matching filter: {p}")
                continue
        dst = dst_path / p.name
        _link_to_file(p, dst, is_forced)


def _get_filter_by_lab_preview(preview_path: Path) -> list[str]:
    filt: list[str] = []
    for p in preview_path.glob("*.jpg"):
        stem = common.get_orig_name(p, with_extension=True)
        filt.append(stem)
    return filt


def main(src_path: Path, dst_path: Path, is_all: bool = False,
         is_forced: bool = False):

    logger.info("pwf_link: ENTRY")

    # parse and check path:
    if common.path_is_tag(dst_path):
        dst_path = _tag_to_path(src_path, str(dst_path))

    _check_is_allowed(src_path, dst_path)

    logger.debug(f"{src_path=}, {dst_path=}, {is_all=}, {is_forced=}")

    src_info = common.parse_path(src_path)
    dst_info = common.parse_path(dst_path)

    # if destination is @lab, then use preview files to filter which
    # links are created!
    filt: list[str] | None = None
    if dst_info.state == common.State.LAB and not is_all \
       and src_info.file_type in {"raw", "jpg"}:

        if src_info.year is None:
            raise ValueError("src_path must contain year!")
        if src_info.event is None:
            raise ValueError("src_path must contain event dir!")

        path = common.pwf_root_path / "2_lab"
        path = path / str(src_info.year) / src_info.event / "1_preview/"
        filt = _get_filter_by_lab_preview(path)

    if src_path.is_dir():
        _link_to_files_in_dir(src_path, dst_path, is_forced, filt)

    else:
        if dst_path.is_dir():
            dst_path = dst_path / src_path.name

        _link_to_file(src_path, dst_path, is_forced)

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
