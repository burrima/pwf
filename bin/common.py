
from enum import Enum
from pathlib import Path
import hashlib
import logging
import re
import os


logger = logging.getLogger(__name__)


legal_characters = r"\wäöüÄÖÜé~._-"


pwf_root_path = Path(os.getenv("PWF_ROOT_PATH"))


name_replacements = (
    (" ", "_"),
    ("&", "und"),
    ("-_", ""))


raw_file_extensions = ("NEF", "NRW", "CR2")


jpg_file_extensions = ("jpg", "JPG", "jpeg", "JPEG")


video_file_extensions = ("MOV", "mp4", "MP4", "mpeg", "mov", "MOV")


audio_file_extensions = ("wav", "WAV", "mp3")


type_dirs = ("raw", "jpg", "audio", "video")


valid_file_locations = {
    "NEF": "raw",
    "NRW": "raw",
    "CR2": "raw",
    "jpg": "jpg",
    "jpeg": "jpg",
    "JPG": "jpg",
    "JPEG": "jpg",
    "MOV": "video",
    "mp4": "video",
    "MP4": "video",
    "mpeg": "video",
    "mov": "video",
    "MOV": "video",
    "wav": "audio",
    "WAV": "audio",
    "mp3": "audio"}


fzf_info_text =\
    """
FZF: Any path can be specified either by by normal means of bash (e.g.
with tab completion) or by using the FZF tool. Type **<tab> to bring the
FZF tool to front where you can select the desired path much faster (see
man fzf for more details). Paths are automatically bound to the pwf
folder structure, so this script can be used from anywhere whith
consistent behavior.
    """


class State(Enum):
    NEW = 0
    ORIGINAL = 1
    LAB = 2
    ALBUM = 3
    PRINT = 4


state_dirs = {
    State.NEW: "0_new",
    State.ORIGINAL: "1_original",
    State.LAB: "2_lab",
    State.ALBUM: "3_album",
    State.PRINT: "4_print",
}


tags = ("@new", "@original", "@lab", "@album", "@print")


tag_dirs = {
    "@new": "0_new",
    "@original": "1_original",
    "@lab": "2_lab",
    "@album": "3_album",
    "@print": "4_print",
}


def path_is_tag(path: Path):
    return str(path)[0] == "@"


class Pwf_path_info():
    state: State = None
    is_event_dir: bool = False
    year: int = None
    event: str = None
    file_type: str = None


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


def md5sum(path, is_partial=False):
    # if is_partial=True, read only first 8k data (which should be fine for
    # pictures).
    # TODO: read chunked for big files (memory issue)
    with open(path, "rb") as f:
        data = f.read(8000 if is_partial else None)
        md5sum = hashlib.md5(data).hexdigest()
    return md5sum


def get_orig_name(path: Path, with_extension: bool = False) -> str:
    """
    Extract original file name from given path.

    Similar to Path.stem or Path.name, but with extra feature.

    Original name can be prefixed with date-time string and post-fixed
    with "-preview.jpg". The start of the original name is retrieved by
    searching for the first alpha-character.
    """
    name = path.name
    if name.endswith("-preview.jpg"):
        name = name.replace("-preview.jpg", "")  # remove preview ending

    if not with_extension:
        name = Path(name).stem

    match = re.search(r"[a-zA-Z]", name)
    idx = match.start()
    name = name[idx:]
    return name
