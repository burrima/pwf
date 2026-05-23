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


from bin import common, pwf_check, pwf_import, pwf_statistics, \
    pwf_extract_previews, pwf_rename_by_date, pwf_link, pwf_fix_exif, \
    pwf_downsize
from pathlib import Path
from textwrap import dedent
import argparse
import logging
import shutil
import yaml
from enum import Enum, auto


class State(Enum):
    INITIAL = auto(),
    IMPORT = auto(),
    ORIGINAL = auto(),
    LAB_PREPARE = auto(),
    LAB_FIX_SORTING = auto(),
    LAB_IMPORT_ORIGINALS = auto(),
    LAB_PROCESS = auto(),
    ALBUM = auto(),

    FINAL = auto(),


__state_handlers = { x: f"handle_state_{x.name.lower()}" for x in State }


default_corrections: str = dedent(
    """
    - filter:
        filename: ".*"
        tags:
          - tag: "Exif.Image.Model"
            value: "TODO"
      corrections:
        time:
          days: 0
          hours: 0
          minutes: 0
          seconds: 0
        tags:
          - tag: "TODO"
            pattern: "^.*$"
            replacement: "TODO"
    """)


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


def _user_info(text: str | list[str]) -> None:
    if type(text) is str:
        text = [text]

    logger.info("-" * 80)
    for line in text:
        logger.info(line)


def _user_confirm(text: str | list[str]) -> str:
    if type(text) is str:
        text = [text]

    logger.info("-" * 80)
    for line in text:
        logger.info(line)

    logger.info("Press ENTER to continue, CTRL-C to exit...")
    return input()


def _user_ask_yes_no(text: str | list[str]) -> bool:
    if type(text) is str:
        text = [text]

    logger.info("-" * 80)
    for line in text:
        logger.info(line)

    logger.info("Press y/n to continue, CTRL-C to exit...")
    return input() == "y"


def _user_choice(choices: list[str], default: int=0) -> int:
    logger.info("-" * 80)
    logger.info("What do you want to do?")
    for i, choice in enumerate(choices):
        logger.info(f"{i}: {choice}" + (" [default]" if i==default else ""))

    logger.info("Make your choice, press ENTER to continue, CTRL-C to exit...")
    choice = input()
    if choice == "":
        return default
    return int(choice)


def _save_last_state(path_info: common.Pwf_path_info, state: State) -> None:
    state_file = common.pwf_root_path / "2_lab" / str(path_info.year) / \
        str(path_info.event) / "interactive_state.yaml"

    with open(state_file, "w") as f:
        f.write(f"lastState: {state.name}")


def _load_last_state(path_info: common.Pwf_path_info) -> State:
    last_state = State.INITIAL
    state_file = common.pwf_root_path / "2_lab" / str(path_info.year) / \
        str(path_info.event) / "interactive_state.yaml"

    if not state_file.exists():
        logger.debug(f"last_state=INITIAL")
        return State.INITIAL

    with open(state_file, "r") as f:
        last_state = State[yaml.safe_load(f)["lastState"]]

    logger.debug(f"{last_state=}")
    return last_state


def handle_state_initial(path_info: common.Pwf_path_info) -> State:
    logger.info("STATE: INITIAL")
    logger.info("Welcome to the interactive PWF workflow.")

    _user_confirm([
        f"Working on {path_info.year}/{path_info.event}",
        "Is this correct?"])

    logger.info("Determining last active state and entering it...")

    return _load_last_state(path_info)


def handle_state_import(path_info: common.Pwf_path_info) -> State:
    logger.info("STATE: IMPORT")

    _save_last_state(path_info, State.IMPORT)

    if not _user_ask_yes_no("Do you want to import any files?"):
        return State.ORIGINAL

    path = common.pwf_root_path / "0_new" / str(path_info.event)

    if not path.exists():
        logger.info(f"Creating empty folder structure in {path}...")
        path.mkdir(parents=True, exist_ok=False)
        (path / "jpg").mkdir()
        (path / "raw").mkdir()
        (path / "audio").mkdir()
        (path / "video").mkdir()

    _user_confirm(f"Please ensure that all files to import are in {path}")

    if not path.exists():
        raise RuntimeError(f"Path {path} does not exist!")

    try:
        pwf_check.main(path)
    except Exception as e:
        _user_info([
            f"Checks failed with error: {e}",
            "Fix the issue(s), then re-run this script"])
        raise

    try:
        pwf_import.main(path)
    except Exception as e:
        _user_info([
            f"Import failed with error: {e}",
            "Fix the issue, then re-run this script"])
        raise

    return State.ORIGINAL


def handle_state_original(path_info: common.Pwf_path_info) -> State:
    logger.info("STATE: ORIGINAL")
    _save_last_state(path_info, State.ORIGINAL)

    path = common.pwf_root_path / "1_original" / str(path_info.year) \
        / str(path_info.event)

    choice = _user_choice(choices=["Import further files",
                                   "Show statistics",
                                   "Prepare Lab"], default=1)
    match choice:
        case 0:
            return State.IMPORT
        case 1:
            pwf_statistics.main(path)
            return State.ORIGINAL
        case 2:
            return State.LAB_PREPARE
        case _:
            raise RuntimeError("Invalid choice!")

    return State.FINAL


def handle_state_lab_prepare(path_info: common.Pwf_path_info) -> State:
    logger.info("STATE: LAB_PREPARE")
    _save_last_state(path_info, State.LAB_PREPARE)

    src_path = common.pwf_root_path / "1_original" / str(path_info.year) \
        / str(path_info.event)
    dst_path = common.pwf_root_path / "2_lab" / str(path_info.year) \
        / str(path_info.event) / "1_preview"

    if dst_path.exists() and not _user_ask_yes_no([
            "WARNING: 1_preview exists!",
            "Do you want to re-create all previews? (n=no action)"]):
        return State.LAB_FIX_SORTING
    else:
        # TODO: if previews are date-tagged, they won't be recognized as
        # existing previews! Better delete all previews prior to generating new
        # ones? Or better fix pwf_extract_previews!
        shutil.rmtree(dst_path, ignore_errors=True)
        pwf_extract_previews.main(src_path, Path("@lab"))

    _user_confirm(["Now go through all previews and delete unwanted ones"])

    return State.LAB_FIX_SORTING


def handle_state_lab_fix_sorting(path_info: common.Pwf_path_info) -> State:
    logger.info("STATE: LAB_FIX_SORTING")
    _save_last_state(path_info, State.LAB_FIX_SORTING)

    path = common.pwf_root_path / "2_lab" / str(path_info.year) \
        / str(path_info.event) / "1_preview"

    logger.info("Create the file exif_corrections.yaml if needed.")
    corrections_file = path.parent / "exif_corrections.yaml"
    if corrections_file.exists():
        logger.info("Not needed (exists already)")
    else:
        with open(corrections_file, "w") as f:
            f.write(default_corrections)

    choice = _user_choice(choices=[
        "Re-create previews",
        "Rename previews by date",
        "Rename previews by date (ignore exif_corrections.yaml)",
        "Rename previews by date-camera",
        "Rename previews by camera-date",
        "Remove prefix from previews",
        "DONE"], default=6)
    match choice:
        case 0:  # re-create previews
            shutil.rmtree(path, ignore_errors=True)
            return State.LAB_PREPARE
        case 1:  # rename previews by date
            pwf_rename_by_date.main(path, add_camera=False)
        case 2:  # rename previews by date (ignore exif_corrections.yaml)
            pwf_rename_by_date.main(path, add_camera=False, is_bare=True)
        case 3:  # rename previews by date-camera
            pwf_rename_by_date.main(path, add_camera=True, camera_first=False)
        case 4:  # rename previews by camera-date
            pwf_rename_by_date.main(path, add_camera=True, camera_first=True)
        case 5:  # remove prefix from previews
            pwf_rename_by_date.main(path, is_undo=True)
        case 6:
            return State.LAB_IMPORT_ORIGINALS

    return State.LAB_FIX_SORTING


def handle_state_lab_import_originals(
    path_info: common.Pwf_path_info) -> State:

    logger.info("STATE: LAB_IMPORT_ORIGINALS")
    _save_last_state(path_info, State.LAB_IMPORT_ORIGINALS)

    src_path = common.pwf_root_path / "1_original" / str(path_info.year) \
        / str(path_info.event)
    path = common.pwf_root_path / "2_lab" / str(path_info.year) \
        / str(path_info.event)

    for file_type in common.type_dirs:
        try:
            pwf_link.main(src_path / file_type, Path("@lab"))
        except Exception as e:
            logger.info(f"Failed with error {e}")

    for file_type in {"raw", "jpg"}:
        try:
            pwf_rename_by_date.main(path / f"2_original_{file_type}")
        except Exception as e:
            logger.info(f"Failed with error {e}")

    return State.LAB_PROCESS


def handle_state_lab_process(path_info: common.Pwf_path_info) -> State:
    logger.info("STATE: LAB_PROCESS")
    _save_last_state(path_info, State.LAB_PROCESS)

    path = common.pwf_root_path / "2_lab" / str(path_info.year) \
        / str(path_info.event)

    (path / "3_final_jpg").mkdir(exist_ok=True)

    _user_info(["It's time to process/develop the images",
                "Put final images into the folder 3_final_jpg/"])

    choice = _user_choice(choices=[
        "Re-import originals (overwrite)",
        "Copy unprocessed original jpg files to final folder",
        "Copy unprocessed original video & audio files to final folder",
        "Apply EXIF corrections to final images",
        "DONE"], default=4)
    match choice:
        case 0:  # re-import originals
            _user_confirm("Manually delete links to originals as needed")
            return State.LAB_IMPORT_ORIGINALS
        case 1:  # copy remaining, unprocessed jpg originals to final
            for ext in common.jpg_file_extensions:
                for f in (path / "2_original_jpg").glob(f"*.{ext}"):
                    if (path / "3_final_jpg" / f.name).exists():
                        continue
                    shutil.copy(f, path / "3_final_jpg", follow_symlinks=False)
        case 2:  # copy unprocessed video and audio to final
            for ext in common.video_file_extensions:
                for f in (path / "2_original_video").glob(f"*.{ext}"):
                    if (path / "3_final_video" / f.name).exists():
                        continue
                    shutil.copy(f, path / "3_final_video",
                                follow_symlinks=False)
            for ext in common.audio_file_extensions:
                for f in (path / "2_original_audio").glob(f"*.{ext}"):
                    if (path / "3_final_audio" / f.name).exists():
                        continue
                    shutil.copy(f, path / "3_final_audio",
                                follow_symlinks=False)
        case 3:  # apply exif corrections
            if _user_ask_yes_no([
                    "WARNING: corrections must only be applied once!",
                    "There is no built-in protection against multiple calls!",
                    "Apply corrections now?"]):
                pwf_fix_exif.main(path / "3_final_jpg")
                pwf_rename_by_date.main(path / f"3_final_jpg", is_undo=True)
                pwf_rename_by_date.main(path / f"3_final_jpg", is_bare=True)
        case 4:  # DONE
            for file_type in common.type_dirs:
                src_path = path / f"3_final_{file_type}"
                if src_path.exists():
                    pwf_link.main(src_path, Path("@album"))
            _user_confirm(
                "All final files have been linked to the default album.")
            return State.ALBUM

    return State.LAB_PROCESS


def handle_state_album(path_info: common.Pwf_path_info) -> State:
    logger.info("STATE: ALBUM")
    _save_last_state(path_info, State.ALBUM)

    path = common.pwf_root_path / "3_album" / str(path_info.year) \
        / str(path_info.event)

    choice = _user_choice(choices=[
        "Downsize images",
        "Downsize videos",
        "DONE"], default=2)
    match choice:
        case 0:  # downsize images
            path = path / "jpg"
        case 1:
            path = path / "video"
        case _:
            return State.FINAL

    size = _user_choice(choices=[
        "UHD   3840x2160",
        "QHD   2560x1440",
        "FHD   1920x1080",
        "HD    1280x720"], default=1)
    pwf_downsize.main(path, ["UHD", "QHD", "FHD", "HD"][size])

    return State.ALBUM


def handle_state(state: State, path_info: common.Pwf_path_info) -> State:

    handler_func_str = __state_handlers[state]
    handler_func = globals()[handler_func_str]
    next_state = handler_func(path_info)
    return next_state


def main(src_path: Path):
    path_info = common.parse_path(src_path)

    if path_info.year is None:
        raise ValueError(f"Unable to parse year from {src_path=}")
    if path_info.event is None:
        raise ValueError(f"Unable to parse event from {src_path=}")

    state = State.INITIAL

    while state != State.FINAL:
        new_state = handle_state(state, path_info)
        if new_state != None:
            state = new_state


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
