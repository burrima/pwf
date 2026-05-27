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


tag_name_delimiter: str = r"--"


pwf_root = os.getenv("PWF_ROOT_PATH")
if pwf_root is None:
    raise ValueError("PWF_ROOT_PATH is not defined. Is envstup.sh sourced?")
if re.match(rf"^[{legal_characters}]+$", pwf_root):
    raise ValueError("PWF_ROOT_PATH contains illegal characters!")
pwf_root_path = Path(pwf_root)


# Define which characters shall be replaced by pwf_check.py when fixing names:
name_replacements: set[tuple[str, str]] = {
    (" ", "_"),
    ("&", "_und_"),
    ("+", "_und_"),
    ("__", "_"),
    ("-_", "")}


# Define which file endings (extensions) shall be recognized as RAW files:
raw_file_extensions: set[str] = {"NEF", "NRW", "CR2"}


# Define which file endings (extensions) shall be recognized as JPG files:
jpg_file_extensions: set[str] = {"jpg", "JPG", "jpeg", "JPEG"}


# Define which file endings (extensions) shall be recognized as video files:
video_file_extensions: set[str] = {"MOV", "mp4", "MP4", "mpeg", "mov", "MOV"}


# Define which file endings (extensions) shall be recognized as audio files:
audio_file_extensions: set[str] = {"wav", "WAV", "mp3"}


# Define which directory names are valid for the different file types:
type_dirs: set[str] = {"raw", "jpg", "png", "audio", "video"}


# Define which file types are allowed to be stored in which type directory:
valid_file_locations: dict[str, str] = {
    ".NEF": "raw",
    ".NRW": "raw",
    ".CR2": "raw",
    ".jpg": "jpg",
    ".jpeg": "jpg",
    ".JPG": "jpg",
    ".JPEG": "jpg",
    ".PNG": "png",
    ".png": "png",
    ".MOV": "video",
    ".mp4": "video",
    ".MP4": "video",
    ".mpeg": "video",
    ".mov": "video",
    ".MOV": "video",
    ".wav": "audio",
    ".WAV": "audio",
    ".mp3": "audio"}


# Define general help text which is appended to each script's help output:
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


# Define PWF workflow states:
class State(Enum):
    NEW = 0
    ORIGINAL = 1
    LAB = 2
    ALBUM = 3
    PRINT = 4


# Define which PWF workflow state corresponds to which folder:
state_dirs: dict[State, str] = {
    State.NEW: "0_new",
    State.ORIGINAL: "1_original",
    State.LAB: "2_lab",
    State.ALBUM: "3_album",
    State.PRINT: "4_print",
}


# Define which tags can be used as shortcuts for state folders when calling
# scripts:
tags: set[str] = {"@new", "@original", "@lab", "@album", "@print"}


# Define which tag corresponds to which state folder:
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

    def __repr__(self):
        return (f"{self.state=}, {self.is_event_dir=}, {self.year=}, "
                f"{self.event=}, {self.file_type=}")


def parse_path(path: Path) -> Pwf_path_info:
    """
    Parses a path and returns a Pwf_path_info opject.

    Valid paths are, for example:
      - 0_new/2025-10-30_Event_1/jpg/IMG_1234.jpg   # standard
      - 0_new/2025_Topic1/jpg/IMG_5678.jpg
      - 1_original/2025/2025-10-20_Event_2/jgp/IMG_1234.jpg   # standard
      - 1_original/2008/2008_Topic1/raw/DSC_1234.NRW
      - 1_original/2008/Topic2/raw/DSC_1234.NRW
      - 2_lab/2025/2025-10-20_Event/1_original_raw

    They all follow the following schemes:
      - <state>/<year>/<event>/{jpg,raw,audio,video}/<file>.<ending>
      - 0_new/<event>/{jpg,raw,audio,video}/<file>.<ending>

    The algorithm traverses the parts of the path from root to leaf and tries
    to find the next information, given the already found out things.

    Caveats:
      * Only 1 state dir allowed in path (0_new, 1_original, ...)
      * State dir must be followed by year dir (or by event dir in 0_new)
      * Year dir must be followed by event dir
      * Event dir must be followed by file_type dir, where this can have a
        prefix ([prefix_]jpg, [prefix_]raw, ...)
    """
    info = Pwf_path_info()

    parts = path.parts
    logger.debug(f"parse_path: {parts=}")

    for idx, part in enumerate(parts):

        if info.state is None:
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
            continue

        if part in state_dirs.values():
            raise ValueError("Path must not contain more than one state dir!")

        # NOTE: year is optional!
        if info.year is None and re.match(r"\d{4}", part):
            info.year = int(part[:4])
            if len(part) == 4:  # is year-dir, else event-dir
                continue

        if info.event is None:
            info.event = part
            info.is_event_dir = True
            continue

        info.is_event_dir = False

        if info.file_type is None:
            if part.split("_")[-1] in type_dirs:
                info.file_type = part.split("_")[-1]
            elif part.split("_")[0] in type_dirs:
                info.file_type = part.split("_")[0]
            elif part == "1_preview":
                info.file_type = "jpg"
            else:
                # NOTE: this is restrictive but helps to filter many illegal
                # situations!
                raise ValueError("Event dir must contain file_type dir!")

    if info.state is None:
        raise ValueError("Cannot parse state from path!")

    return info


def prefix_str(file_name: str, prefix: str,
               delimiter: str = tag_name_delimiter):
    """
    Add given prefix to given file name (pure string operations).
    """
    return f"{prefix}{delimiter}{file_name}"


def unprefix_str(file_name: str, delimiter: str = tag_name_delimiter):
    """
    Remove prefix from file name (pure string operations).

    The method works with modern separators, but has a fallback for old
    bash-script based PWF tools where it just cuts-off the first 16 characters.
    """
    newname = None
    if delimiter in file_name:
        newname = file_name.split(delimiter)[-1]
    elif re.match(r"^[0-9]{8}-[0-9]{6}-.*", file_name):
        # backwards-compatibility
        newname = f"{file_name[16:]}"

    if newname is None:
        raise RuntimeError(f"Cannot determine new name: {file_name}")

    return newname


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

    try:
        name = unprefix_str(name)
    except RuntimeError:
        # In this case, the name had no prefix. Silently ignore it
        pass
    return name


def pwf_path(path: Path) -> Path:
    """
    Return path relative to pwf_root_path (shortcut used mostly for printing)

    Memoric: convert a path to a pwf-specific path (pwf_path)
    """
    return path.relative_to(pwf_root_path)
