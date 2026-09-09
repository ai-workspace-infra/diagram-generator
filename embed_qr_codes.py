#!/usr/bin/env python3
"""Embed two QR code images into a reusable promotional background."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


# (x, y, width, height), expressed as fractions of the template dimensions.
# These defaults match the supplied 2564 x 902 promotional background.
DEFAULT_QR1_BOX = (0.748, 0.326, 0.060, 0.171)
DEFAULT_QR2_BOX = (0.884, 0.326, 0.060, 0.171)


def parse_box(value: str) -> tuple[int, int, int, int]:
    """Parse a box written as x,y,width,height."""
    try:
        parts = tuple(int(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Position must be x,y,width,height, for example 1915,295,155,155"
        ) from exc
    if len(parts) != 4 or parts[2] <= 0 or parts[3] <= 0:
        raise argparse.ArgumentTypeError(
            "Position must be x,y,width,height; width and height must be positive"
        )
    return parts  # type: ignore[return-value]


def fractional_box(
    template_size: tuple[int, int],
    box: tuple[float, float, float, float],
) -> tuple[int, int, int, int]:
    width, height = template_size
    x, y, box_width, box_height = box
    return (
        round(width * x),
        round(height * y),
        round(width * box_width),
        round(height * box_height),
    )


def dark_pixel_bbox(image: Image.Image, min_y: int) -> tuple[int, int, int, int] | None:
    """Find dark-pixel bounds while ignoring title text above the QR code."""
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    xs: list[int] = []
    ys: list[int] = []

    for y in range(max(0, min_y), rgba.height):
        for x in range(rgba.width):
            red, green, blue, alpha = pixels[x, y]
            if alpha > 20 and min(red, green, blue) < 180:
                xs.append(x)
                ys.append(y)

    if not xs:
        return None
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def crop_qr_subject(image: Image.Image, auto_crop: bool = True) -> Image.Image:
    """Crop a QR subject and add a small white quiet zone around it."""
    image = image.convert("RGBA")
    if not auto_crop:
        return image

    # The supplied QR images include a title above the code.
    bbox = dark_pixel_bbox(image, round(image.height * 0.12))
    if bbox is None:
        return image

    left, top, right, bottom = bbox
    subject_width = right - left
    subject_height = bottom - top
    if subject_width < image.width * 0.35 or subject_height < image.height * 0.35:
        # Avoid an accidental crop for an unusual QR design.
        return image

    side = max(subject_width, subject_height)
    margin = max(4, round(side * 0.03))
    side += margin * 2
    center_x = (left + right) / 2
    center_y = (top + bottom) / 2
    crop_left = round(center_x - side / 2)
    crop_top = round(center_y - side / 2)
    crop_left = max(0, min(crop_left, image.width - side))
    crop_top = max(0, min(crop_top, image.height - side))
    return image.crop((crop_left, crop_top, crop_left + side, crop_top + side))


def fit_qr_to_box(qr: Image.Image, box_size: tuple[int, int]) -> Image.Image:
    """Fit a QR image into a box without distorting its aspect ratio."""
    target_width, target_height = box_size
    scale = min(target_width / qr.width, target_height / qr.height)
    resized = qr.resize(
        (max(1, round(qr.width * scale)), max(1, round(qr.height * scale))),
        Image.Resampling.LANCZOS,
    )
    fitted = Image.new("RGBA", (target_width, target_height), (255, 255, 255, 255))
    fitted.alpha_composite(
        resized,
        ((target_width - resized.width) // 2, (target_height - resized.height) // 2),
    )
    return fitted


def embed_qr_codes(
    template_path: Path,
    qr1_path: Path,
    qr2_path: Path,
    output_path: Path,
    qr1_box: tuple[int, int, int, int] | None = None,
    qr2_box: tuple[int, int, int, int] | None = None,
    auto_crop: bool = True,
) -> None:
    """Embed two QR images into the template and save the result."""
    with Image.open(template_path) as source:
        canvas = source.convert("RGBA")
        template_size = canvas.size

    resolved_qr1_box = qr1_box or fractional_box(template_size, DEFAULT_QR1_BOX)
    resolved_qr2_box = qr2_box or fractional_box(template_size, DEFAULT_QR2_BOX)

    with Image.open(qr1_path) as source_qr1:
        qr1 = crop_qr_subject(source_qr1, auto_crop=auto_crop)
    with Image.open(qr2_path) as source_qr2:
        qr2 = crop_qr_subject(source_qr2, auto_crop=auto_crop)

    for qr, (x, y, width, height) in (
        (qr1, resolved_qr1_box),
        (qr2, resolved_qr2_box),
    ):
        if x < 0 or y < 0 or x + width > canvas.width or y + height > canvas.height:
            raise ValueError(f"QR position is outside the template: {x},{y},{width},{height}")
        canvas.alpha_composite(fit_qr_to_box(qr, (width, height)), (x, y))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() in {".jpg", ".jpeg"}:
        canvas.convert("RGB").save(output_path, format="JPEG", quality=95, optimize=True)
    else:
        canvas.save(output_path, format="PNG", optimize=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Embed two QR codes into a promotional background")
    parser.add_argument("template", type=Path, help="Template/background image")
    parser.add_argument("qr1", type=Path, help="First QR code image")
    parser.add_argument("qr2", type=Path, help="Second QR code image")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("qr_composite.png"),
        help="Output image (default: qr_composite.png)",
    )
    parser.add_argument("--qr1-box", type=parse_box, help="First QR box: x,y,width,height")
    parser.add_argument("--qr2-box", type=parse_box, help="Second QR box: x,y,width,height")
    parser.add_argument(
        "--no-auto-crop",
        action="store_true",
        help="Do not crop title text from the top of QR images",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    for path in (args.template, args.qr1, args.qr2):
        if not path.is_file():
            raise SystemExit(f"File not found: {path}")

    try:
        embed_qr_codes(
            args.template,
            args.qr1,
            args.qr2,
            args.output,
            qr1_box=args.qr1_box,
            qr2_box=args.qr2_box,
            auto_crop=not args.no_auto_crop,
        )
    except Exception as exc:
        raise SystemExit(f"Failed to create composite: {exc}") from exc
    print(f"Generated: {args.output}")


if __name__ == "__main__":
    main()
