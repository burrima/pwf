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
from PIL import Image
import argparse
import copy
import logging


logger = logging.getLogger(__name__)


info_text =\
    """
TAGS
    UHD   3840x2160
    QHD   2560x1440
    FHD   1920x1080
    HD    1280x720

Make images or videos smaller in size to save space. Useful for web
presentation.

Files are down-scaled to fit into the bounding box. The box is always
aligned with the image orientation, so vertical images turned by 90° are
of the same size as horizontal images (from same camera with same
settings). This has no benefit on horizontal screen presentation - but
when printed, all images are of same resolution.
    """ + common.fzf_info_text


class Size():
    width: float = 0.0
    height: float = 0.0

    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height

    def get_int_size(self):
        return Size(int(self.width), int(self.height))

    def __str__(self):
        return f"Size({self.width}, {self.height})"

    def __repr__(self):
        return self.__str__()

    def is_landscape(self):
        return self.width > self.height

    def is_portrait(self):
        return self.width < self.height

    def rotate(self):
        self.width, self.height = self.height, self.width


tag_sizes = {
    "UHD": Size(3840, 2160),
    "QHD": Size(2560, 1440),
    "FHD": Size(1920, 1080),
    "HD": Size(1280, 720),
}


def _compute_inside_box(im_size: Size, box: Size, align: bool = True) -> Size:

    box = copy.copy(box)
    out_size = Size(im_size.width, im_size.height)

    if align and im_size.is_landscape() != box.is_landscape():
        box.rotate()

    if out_size.width > box.width:
        out_size.height *= box.width / out_size.width
        out_size.width = box.width

    if out_size.height > box.height:
        out_size.width *= box.height / out_size.height
        out_size.height = box.height

    return out_size.get_int_size()


def scale_image(src_path: Path, dst_path: Path,
                box: Size, align_box: bool = True):
    # convert -filter Sinc -resize "$SIZE" -quality 90 "$in_file" "$out_file"

    im = Image.open(src_path)
    size = _compute_inside_box(Size(im.width, im.height), box, align_box)

    im_hd = im.resize((size.width, size.height),
                      resample=Image.Resampling.BICUBIC,
                      reducing_gap=3.0)

    im_hd.save(dst_path,
               'jpeg',
               icc_profile=im.info.get('icc_profile'),
               exif=im.info.get('exif'),
               quality=80)


def scale_video(src_path: Path, dst_path: Path, box: set[int]):
    # ffmpeg -i $in_file -vf scale="$SIZE" -c:v libx265 $out_file
    pass


def main(path: Path, tag: str):

    logger.info("pwf_downsize: ENTRY")

    if tag not in tag_sizes:
        raise ValueError("Illegal tag provided!")
    box = tag_sizes[tag]

    files = []
    if path.is_dir():
        # glob = "**/*.*" if is_recursive else "*.*"
        glob = "*.*"
        files = list(path.glob(glob))
    else:
        files = [path]

    for file in files:
        dst_path = file.parent / tag
        dst_path.mkdir(parents=True, exist_ok=True)
        dst_file = dst_path / f"{file.stem}-{tag}{file.suffix}"

        if dst_file.exists():
            logger.info(f"Ignore (existing): {path}")
            continue

        logger.info(f"Downsize {path} -> {tag}/")

        if file.suffix[1:] in common.jpg_file_extensions:
            scale_image(file, dst_file, box, True)
        elif file.suffix in common.video_file_extensions:
            scale_video(file, dst_file, box, True)
        else:
            raise ValueError("Can only downsize jpg images and videos!")

    logger.info("pwf_downsize: OK")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=info_text)

    parser.add_argument("-t", "--tag",
                        help="specify output size by tag",
                        default="QHD")
    parser.add_argument("-l", "--loglevel",
                        help="log level to use",
                        default="INFO")
    parser.add_argument("path", nargs='?', default=Path.cwd())
    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=args.loglevel.upper())
    logger.debug(f"{args=}")

    try:
        main(Path(args.path), args.tag)
    except Exception as ex:
        if args.loglevel.upper() == "DEBUG":
            raise
        logger.error(str(ex))
