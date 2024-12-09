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

from enum import Enum
from pathlib import Path
from textwrap import dedent
import logging
import re
import os


logger = logging.getLogger(__name__)


legal_characters: str = r"\wäöüÄÖÜé~._-"


pwf_root = os.getenv("PWF_ROOT_PATH")
if pwf_root is None:
    raise ValueError("PWF_ROOT_PATH is not defined. Is envstup.sh sourced?")
if re.match(rf"^[{legal_characters}]+$", pwf_root):
    raise ValueError("PWF_ROOT_PATH contains illegal characters!")
pwf_root_path = Path(pwf_root)


name_replacements: set[tuple[str, str]] = {
    (" ", "_"),
    ("&", "und"),
    ("-_", "")}


raw_file_extensions: set[str] = {"NEF", "NRW", "CR2"}


jpg_file_extensions: set[str] = {"jpg", "JPG", "jpeg", "JPEG"}


video_file_extensions: set[str] = {"MOV", "mp4", "MP4", "mpeg", "mov", "MOV"}


audio_file_extensions: set[str] = {"wav", "WAV", "mp3"}


type_dirs: set[str] = {"raw", "jpg", "audio", "video"}  # TODO: add other/


valid_file_locations: dict[str, str] = {
    ".NEF": "raw",
    ".NRW": "raw",
    ".CR2": "raw",
    ".jpg": "jpg",
    ".jpeg": "jpg",
    ".JPG": "jpg",
    ".JPEG": "jpg",
    ".MOV": "video",
    ".mp4": "video",
    ".MP4": "video",
    ".mpeg": "video",
    ".mov": "video",
    ".MOV": "video",
    ".wav": "audio",
    ".WAV": "audio",
    ".mp3": "audio"}


info_text: str = dedent(
    """
    LOGLEVEL
        WARNING print warings and errors only (be quiet by default)
        INFO    default print level
        DEBUG   print additional info and give full exception trace log

    FZF PATH EXPANSION
        Any path can be specified either by by normal means of bash (e.g.  with
        tab completion) or by using the FZF tool. Type **<tab> to bring the FZF
        tool to front where you can select the desired path much faster (see
        man fzf for more details). Paths are automatically bound to the pwf
        folder structure, so this script can be used from anywhere with
        consistent behavior.
    """)


class State(Enum):
    NEW = 0
    ORIGINAL = 1
    LAB = 2
    ALBUM = 3
    PRINT = 4


state_dirs: dict[State, str] = {
    State.NEW: "0_new",
    State.ORIGINAL: "1_original",
    State.LAB: "2_lab",
    State.ALBUM: "3_album",
    State.PRINT: "4_print",
}


tags: set[str] = {"@new", "@original", "@lab", "@album", "@print"}


tag_dirs: dict[str, str] = {
    "@new": "0_new",
    "@original": "1_original",
    "@lab": "2_lab",
    "@album": "3_album",
    "@print": "4_print",
}


def path_is_tag(path: Path) -> bool:
    return str(path)[0] == "@"


class Pwf_path_info(object):
    state: State | None = None
    is_event_dir: bool = False
    year: int | None = None
    event: str | None = None
    file_type: str | None = None


def parse_path(path: Path) -> Pwf_path_info:
    info = Pwf_path_info()

    parts = path.parts
    logger.debug(f"parse_path: {parts=}")

    for part in parts:

        if re.match(r"\d{4}-\d{2}-\d{2}_.*", part):
            info.event = part
            if part == parts[-1]:
                info.is_event_dir = True
        elif re.match(r"\d{4}", part):
            info.year = int(part[:4])
        elif part.split("_")[-1] in type_dirs:
            info.file_type = part.split("_")[-1]
        elif info.state is None:
            match(part):
                case "0_new":
                    info.state = State.NEW
                case "1_original":
                    info.state = State.ORIGINAL
                case "2_lab":
                    info.state = State.LAB
                case "3_album":
                    info.state = State.ALBUM
                case "4_print":
                    info.state = State.PRINT
                case _:
                    info.state = None

    if info.year is None and info.event is not None:
        info.year = int(info.event[:4])

    if info.state is None:
        raise ValueError("Cannot parse state from path!")

    return info


def get_orig_name(path: Path, with_extension: bool = False) -> str:
    """
    Extract original file name from given path.

    Similar to Path.stem or Path.name, but with extra feature.

    Original name can be prefixed with date-time string and post-fixed
    with "-preview.jpg". The start of the original name is retrieved
    by searching for the first alpha-character.
    """
    name = path.name
    if name.endswith("-preview.jpg"):
        name = name.replace("-preview.jpg", "")  # remove preview ending

    if not with_extension:
        name = Path(name).stem

    match = re.search(r"[a-zA-Z]", name)
    if match is None:
        raise RuntimeError(f"Unable to determine orig name from {name=}")
    idx = match.start()
    name = name[idx:]
    return name


def pwf_path(path: Path) -> Path:
    """
    Return path relative to pwf_root_path (shortcut used mostly for printing)

    Memoric: convert a path to a pwf-specific path (pwf_path)
    """
    return path.relative_to(pwf_root_path)
