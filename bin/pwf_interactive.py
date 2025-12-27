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
from textwrap import dedent
import argparse
import logging
from enum import Enum, auto


class  State(Enum):
    INITIAL = auto(),
    CHECK_BEFORE_IMPORT = auto(),
    IMPORT = auto(),
    PREPARE_LAB = auto(),
    REMOVE_UNWANTED_PREVIEWS = auto(),
    DEFINE_EXIF_CORRECTIONS = auto(),
    DEVELOP_IMAGES = auto(),
    APPLY_EXIF_CORRECTIONS = auto(),
    EXPORT_TO_ALBUM = auto(),
    DOWNSIZE_IN_ALBUM = auto(),
    FINAL = auto()


__state_handlers = { x: f"handle_state_{x.name.lower()}" for x in State }


logger = logging.getLogger(__name__)


info_text: str = dedent(
    """
    Interactive helper for PWF.

    This script interactively guides the user through the work-flow, providing
    standard procedure for everyday use. It internally stores the current
    work-state in the corresponding lab folder. This means that the interactive
    workflow can be left and re-entered at any time later.

    src_path must be an event folder which can be in any of the pwf state
    folders, as long as it is possible to uniquely identify the year and the
    event from the path.
    """) + common.info_text


def handle_state_initial():
    logger.debug("STATE: INITIAL")
    return State.CHECK_BEFORE_IMPORT


def handle_state_check_before_import():
    logger.debug("STATE: CHECK_BEFORE_IMPORT")
    return State.IMPORT


def handle_state_import():
    logger.debug("STATE: IMPORT")
    return State.PREPARE_LAB


def handle_state(state: State) -> State:

    handler_func_str = __state_handlers[state]
    handler_func = globals()[handler_func_str]
    next_state = handler_func()
    return next_state


def main(src_path: Path):
    path_info = common.parse_path(src_path)

    if path_info.year is None:
        raise ValueError(f"Unable to parse year from {src_path=}")
    if path_info.event is None:
        raise ValueError(f"Unable to parse event from {src_path=}")

    state_file = Path("2_lab") / str(path_info.year) / path_info.event \
        / "interactive_state.yaml"

    state = State.INITIAL

    if state_file.exists():
        pass

    while state != State.FINAL:
        state = handle_state(state)



if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=info_text)

    parser.add_argument("-l", "--loglevel",
                        help="log level to use",
                        default="INFO")
    parser.add_argument("src_path", nargs='?')
    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=args.loglevel.upper())
    logger.debug(f"{args=}")

    try:
        main(Path(args.src_path))
    except Exception as ex:
        if args.loglevel.upper() == "DEBUG":
            raise
        logger.error(str(ex))
