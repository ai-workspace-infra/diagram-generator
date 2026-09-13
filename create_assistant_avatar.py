#!/usr/bin/env python3
"""Create a compact, brand-safe avatar for the XWorktech assistant account."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


FONT_CANDIDATES = (
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).is_file():
            try:
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def create_avatar(output: Path, size: int = 1024) -> None:
    image = Image.new("RGBA", (size, size), (244, 248, 255, 255))
    pixels = image.load()
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * size)
            pixels[x, y] = (
                round(242 - 38 * t),
                round(248 - 20 * t),
                round(255 - 2 * t),
                255,
            )

    draw = ImageDraw.Draw(image)
    margin = round(size * 0.10)
    draw.ellipse((margin, margin, size - margin, size - margin), fill=(255, 255, 255, 245))

    # A simplified version of the XWorktech X mark, kept bold enough for a
    # small WeChat avatar and rendered with the existing blue/purple palette.
    center = size // 2
    arm = round(size * 0.17)
    width = round(size * 0.075)
    for offset, color in ((-round(size * 0.040), (55, 116, 236, 255)), (round(size * 0.040), (126, 75, 239, 255))):
        draw.line(
            (center - arm, center - arm + offset, center + arm, center + arm + offset),
            fill=color,
            width=width,
        )
        draw.line(
            (center - arm, center + arm + offset, center + arm, center - arm + offset),
            fill=color,
            width=width,
        )

    wordmark = "XWORK"
    font = load_font(round(size * 0.075))
    bbox = draw.textbbox((0, 0), wordmark, font=font)
    draw.text(((size - (bbox[2] - bbox[0])) // 2, round(size * 0.655)), wordmark, fill=(18, 39, 104, 255), font=font)
    subtitle = "XWorktech Assistant"
    subtitle_font = load_font(round(size * 0.040))
    bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    draw.text(((size - (bbox[2] - bbox[0])) // 2, round(size * 0.770)), subtitle, fill=(69, 91, 153, 255), font=subtitle_font)

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--size", type=int, default=1024)
    args = parser.parse_args()
    create_avatar(args.output, args.size)
    print(f"Generated: {args.output}")


if __name__ == "__main__":
    main()
