
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import hashlib
import logging
import re
import os


logger = logging.getLogger(__name__)


legal_characters = r"\wäöüÄÖÜé~._-"


pwf_home_dir=Path(os.getenv("PWF_HOME"))


name_replacements = (
    (" ", "_"),
    ("&", "und"),
    ("-_", ""))


raw_file_extensions = ("NEF", "NRW", "CR2")


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


fzf_info_text=\
    """
FZF: Any path can be specified either by by normal means of bash (e.g. with tab
completion) or by using the FZF tool. Type **<tab> to bring the FZF tool to 
front where you can select the desired path much faster (see man fzf for 
more details). Paths are automatically bound to the pwf folder structure,
so this script can be used from anywhere whith consistent behavior.
    """


class State(Enum):
    NEW = 0
    ORIGINAL = 1
    LAB = 2
    ALBUM = 3
    PRINT = 4


@dataclass(init=False)
class PwfPath():
    path: Path
    state: State = None
    is_event_dir: bool = False
    year: int = None
    event: str = None
    is_file: bool = False
    filename: str = None

    def __init__(self, path):

        # TODO: required?
        self.path = Path.cwd() if path is None or path == "." else Path(path)

        if self.path.is_file():
            self.is_file = True
            self.filename = path.name

        parts = path.parts
        logger.debug(f"PwfPath: {parts=}")

        for part in parts:

            if re.match("\d{4}-\d{2}-\d{2}_.*", part):
                self.event = part
                if part == parts[-1]:
                    self.is_event_dir = True
            elif re.match("\d{4}", part):
                self.year = int(part)
            elif self.state is None:
                match(part):
                    case "0_new":
                        self.state = State.NEW
                    case "1_original":
                        self.state = State.ORIGINAL
                    case "2_lab":
                        self.state = State.LAB
                    case "3_album":
                        self.state = State.ALBUM
                    case "4_print":
                        self.state = State.PRINT
                    case _:
                        self.state = None

        if self.year is None and self.event is not None:
            self.year = int(self.event[:4])

        if self.state is None:
            raise ValueError("Cannot parse state from path!")


def md5sum(path, is_partial=False):
    # if is_partial=True, read only first 8k data (which should be fine for
    # pictures).
    # TODO: read chunked for big files (memory issue)
    with open(path, "rb") as f:
        data = f.read(8000 if is_partial else None)
        md5sum = hashlib.md5(data).hexdigest()
    return md5sum


