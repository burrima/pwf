
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePath
import re

legal_characters = r"\wäöüÄÖÜé~._-"

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

        self.path = Path.cwd() if path is None or path == "." else Path(path)

        if self.path.is_file():
            self.is_file = True
            self.filename = PurePath(path).name

        parts = PurePath(path).parts
        print(f"PwfPath: {parts=}")

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




