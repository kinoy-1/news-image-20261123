#!/usr/bin/env python3
"""Entry point for the news-image-20261123 competition.

Standard library only. Copies the pre-rendered entry.png that sits
beside this file into $MAKEFUN_OUTPUT_DIR/entry.png (default
/output/entry.png), after checking it is a whole PNG within the
competition limits (at most 1 MiB, at most 1024 by 1024 pixels).

The image itself was drawn at build time (see draw.py) because the
grader runs with no network and standard library only, so no image
library is available there. draw.py is the build-time renderer; this
file is the delivery program the grader runs twice, and both runs
must write the same bytes — copying a fixed file guarantees that.
"""

import os
import shutil
import struct
import sys
import zlib

MAX_BYTES = 1048576
MAX_DIMENSION = 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _read_png_dimensions(path):
    """Return (width, height) of a PNG by parsing its IHDR chunk."""
    with open(path, "rb") as handle:
        header = handle.read(33)
    if len(header) < 33 or header[:8] != PNG_SIGNATURE:
        raise ValueError("not a PNG file")
    length, chunk_type = struct.unpack(">I4s", header[8:16])
    if chunk_type != b"IHDR" or length != 13:
        raise ValueError("missing IHDR chunk")
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def _validate_png_whole(path):
    """Walk every PNG chunk, checking lengths and CRCs, ending at IEND."""
    with open(path, "rb") as handle:
        data = handle.read()
    if data[:8] != PNG_SIGNATURE:
        raise ValueError("not a PNG file")
    pos = 8
    seen_iend = False
    while pos + 12 <= len(data):
        length, chunk_type = struct.unpack(">I4s", data[pos:pos + 8])
        end = pos + 8 + length + 4
        if end > len(data):
            raise ValueError("truncated %s chunk" % chunk_type.decode("latin1"))
        stored_crc = struct.unpack(">I", data[end - 4:end])[0]
        actual_crc = zlib.crc32(chunk_type + data[pos + 8:pos + 8 + length])
        if stored_crc != actual_crc & 0xFFFFFFFF:
            raise ValueError("bad CRC in %s chunk" % chunk_type.decode("latin1"))
        if chunk_type == b"IEND":
            seen_iend = True
            if end != len(data):
                raise ValueError("trailing bytes after IEND")
            break
        pos = end
    if not seen_iend:
        raise ValueError("missing IEND chunk")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    destination = os.path.join(out_dir, "entry.png")

    size = os.path.getsize(source)
    if size > MAX_BYTES:
        raise SystemExit("entry.png exceeds 1 MiB: %d bytes" % size)
    width, height = _read_png_dimensions(source)
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        raise SystemExit(
            "entry.png exceeds 1024x1024: %dx%d" % (width, height)
        )
    _validate_png_whole(source)

    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(source, destination)
    print("wrote %s (%d bytes, %dx%d)" % (destination, size, width, height))


if __name__ == "__main__":
    main()
