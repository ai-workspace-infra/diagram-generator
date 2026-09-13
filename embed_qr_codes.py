#!/usr/bin/env python3
"""Embed one or two QR code images into a reusable promotional background."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image
from PIL import ImageDraw, ImageFont


# (x, y, width, height), expressed as fractions of the template dimensions.
# These defaults match the supplied 2564 x 902 promotional background.
DEFAULT_QR1_BOX = (0.748, 0.326, 0.060, 0.171)
DEFAULT_QR2_BOX = (0.884, 0.326, 0.060, 0.171)
DEFAULT_TEXT1_BOX = (0.716, 0.545, 0.126, 0.092)
DEFAULT_TEXT2_BOX = (0.853, 0.545, 0.126, 0.092)
DEFAULT_CARD1_TITLE = "群聊"
DEFAULT_CARD1_VALUE = "Xconnect-支持群"
DEFAULT_CARD2_TITLE = "群聊"
DEFAULT_CARD2_VALUE = "AI-Native-交流群"

FONT_CANDIDATES = (
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)


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


def load_font(font_path: str | None, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a user-selected font, falling back to common system fonts."""
    candidates = (font_path,) if font_path else FONT_CANDIDATES
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            try:
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: str | None,
    initial_size: int,
    max_width: int,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Reduce the font size until the text fits the card."""
    for size in range(max(8, initial_size), 7, -1):
        font = load_font(font_path, size)
        if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
            return font
    return load_font(font_path, 8)


def draw_centered_card_text(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    title: str,
    value: str,
    font_path: str | None,
    title_font_size: int,
    value_font_size: int,
    text_color: tuple[int, int, int, int] = (17, 45, 105, 255),
) -> None:
    """Replace a card's lower caption with configurable title and value text."""
    x, y, width, height = box
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((x, y, x + width, y + height), fill=(255, 255, 255, 255))

    title_font = fit_font(draw, title, font_path, title_font_size, width - 70)
    value_font = fit_font(draw, value, font_path, value_font_size, width - 16)
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    value_bbox = draw.textbbox((0, 0), value, font=value_font)
    title_width = title_bbox[2] - title_bbox[0]
    value_width = value_bbox[2] - value_bbox[0]
    title_x = x + (width - title_width) // 2
    value_x = x + (width - value_width) // 2

    title_y = y + 4
    value_y = y + height // 2
    line_y = title_y + max(11, (title_bbox[3] - title_bbox[1]) // 2)
    line_gap = 18
    line_width = max(12, min(46, (width - title_width) // 2 - line_gap))
    center_x = x + width // 2
    draw.line((x + 2, line_y, x + 2 + line_width, line_y), fill=text_color, width=2)
    draw.line((center_x + title_width // 2 + line_gap, line_y,
               center_x + title_width // 2 + line_gap + line_width, line_y),
              fill=text_color, width=2)
    draw.text((title_x, title_y), title, fill=text_color, font=title_font)
    draw.text((value_x, value_y), value, fill=text_color, font=value_font)


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

    # Phone screenshots can be close to 4:3 after export. Limit detection to
    # the central QR area so the account title and bottom hint are excluded.
    if image.height > image.width * 1.35:
        rgba = image.convert("RGBA")
        pixels = rgba.load()
        xs: list[int] = []
        ys: list[int] = []
        for y in range(round(rgba.height * 0.30), round(rgba.height * 0.80)):
            for x in range(rgba.width):
                red, green, blue, alpha = pixels[x, y]
                if alpha > 20 and min(red, green, blue) < 200:
                    xs.append(x)
                    ys.append(y)
        if xs:
            left, top, right, bottom = min(xs), min(ys), max(xs) + 1, max(ys) + 1
            subject_width = right - left
            subject_height = bottom - top
            if subject_width > rgba.width * 0.45 and subject_height > rgba.height * 0.25:
                side = max(subject_width, subject_height)
                margin = max(4, round(side * 0.03))
                side += margin * 2
                center_x = (left + right) / 2
                center_y = (top + bottom) / 2
                crop_left = max(0, min(round(center_x - side / 2), rgba.width - side))
                crop_top = max(0, min(round(center_y - side / 2), rgba.height - side))
                return rgba.crop((crop_left, crop_top, crop_left + side, crop_top + side))

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


def draw_single_panel(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    qr: Image.Image,
    title: str,
    value: str,
    font_path: str | None,
) -> None:
    """Draw one QR card with a short, configurable welcome message."""
    x, y, width, height = box
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        (x + 6, y + 10, x + width + 6, y + height + 10),
        radius=24,
        fill=(54, 76, 150, 35),
    )
    draw.rounded_rectangle(
        (x, y, x + width, y + height),
        radius=24,
        fill=(255, 255, 255, 255),
        outline=(212, 226, 250, 255),
        width=3,
    )
    qr_size = min(round(height * 0.80), round(width * 0.40))
    canvas.alpha_composite(
        fit_qr_to_box(qr, (qr_size, qr_size)),
        (x + round(width * 0.60), y + (height - qr_size) // 2),
    )

    text_left = x + round(width * 0.08)
    text_width = round(width * 0.40)
    center_x = text_left + text_width // 2
    title_font = fit_font(draw, title, font_path, round(height * 0.105), text_width)
    value_font = fit_font(draw, value, font_path, round(height * 0.085), text_width)
    for text, font, top in (
        (title, title_font, y + round(height * 0.32)),
        (value, value_font, y + round(height * 0.54)),
    ):
        text_width_px = draw.textbbox((0, 0), text, font=font)[2]
        draw.text(
            (center_x - text_width_px // 2, top),
            text,
            fill=(17, 45, 105, 255),
            font=font,
        )


def draw_qr_only_panel(canvas: Image.Image, box: tuple[int, int, int, int], qr: Image.Image) -> None:
    """Draw a single clean QR card without captions or promotional copy."""
    x, y, width, height = box
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        (x + 6, y + 10, x + width + 6, y + height + 10),
        radius=24,
        fill=(54, 76, 150, 35),
    )
    draw.rounded_rectangle(
        (x, y, x + width, y + height),
        radius=24,
        fill=(255, 255, 255, 255),
        outline=(212, 226, 250, 255),
        width=3,
    )
    qr_size = min(round(height * 0.84), round(width * 0.46))
    canvas.alpha_composite(
        fit_qr_to_box(qr, (qr_size, qr_size)),
        (x + (width - qr_size) // 2, y + (height - qr_size) // 2),
    )


def draw_qr_only_right_card(
    canvas: Image.Image,
    template_size: tuple[int, int],
    qr: Image.Image,
    qr_box: tuple[int, int, int, int],
) -> None:
    """Replace the old two-card area with one clean card and a right QR."""
    draw = ImageDraw.Draw(canvas)
    x, y, width, height = fractional_box(template_size, (0.706, 0.210, 0.279, 0.465))
    draw.rounded_rectangle(
        (x + 6, y + 10, x + width + 6, y + height + 10),
        radius=24,
        fill=(54, 76, 150, 35),
    )
    draw.rounded_rectangle(
        (x, y, x + width, y + height),
        radius=24,
        fill=(255, 255, 255, 255),
        outline=(212, 226, 250, 255),
        width=3,
    )

    x, y, card_width, card_height = fractional_box(
        template_size, (0.853, 0.210, 0.126, 0.465)
    )
    qr_size = min(round(card_height * 0.80), round(card_width * 0.82))
    canvas.alpha_composite(
        fit_qr_to_box(qr, (qr_size, qr_size)),
        (x + (card_width - qr_size) // 2, y + (card_height - qr_size) // 2),
    )


def embed_qr_codes(
    template_path: Path,
    qr1_path: Path,
    qr2_path: Path | None = None,
    output_path: Path = Path("qr_composite.png"),
    qr1_box: tuple[int, int, int, int] | None = None,
    qr2_box: tuple[int, int, int, int] | None = None,
    text1_box: tuple[int, int, int, int] | None = None,
    text2_box: tuple[int, int, int, int] | None = None,
    card1_title: str = DEFAULT_CARD1_TITLE,
    card1_value: str = DEFAULT_CARD1_VALUE,
    card2_title: str = DEFAULT_CARD2_TITLE,
    card2_value: str = DEFAULT_CARD2_VALUE,
    font_path: str | None = None,
    title_font_size: int = 28,
    value_font_size: int = 24,
    auto_crop: bool = True,
    qr_only: bool = False,
) -> None:
    """Embed one or two QR images into the template and save the result.

    With one QR input, the two original card positions are replaced by one
    wide assistant card. Two QR inputs keep the original two-card behavior.
    """
    with Image.open(template_path) as source:
        canvas = source.convert("RGBA")
        template_size = canvas.size

    resolved_qr1_box = qr1_box or fractional_box(template_size, DEFAULT_QR1_BOX)
    resolved_qr2_box = qr2_box or fractional_box(template_size, DEFAULT_QR2_BOX)
    resolved_text1_box = text1_box or fractional_box(template_size, DEFAULT_TEXT1_BOX)
    resolved_text2_box = text2_box or fractional_box(template_size, DEFAULT_TEXT2_BOX)

    with Image.open(qr1_path) as source_qr1:
        qr1 = crop_qr_subject(source_qr1, auto_crop=auto_crop)
    if qr2_path is None:
        if qr_only:
            draw_qr_only_right_card(canvas, template_size, qr1, resolved_qr2_box)
        else:
            panel_box = fractional_box(template_size, (0.706, 0.210, 0.279, 0.465))
            draw_single_panel(canvas, panel_box, qr1, card1_title, card1_value, font_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.suffix.lower() in {".jpg", ".jpeg"}:
            canvas.convert("RGB").save(output_path, format="JPEG", quality=95, optimize=True)
        else:
            canvas.save(output_path, format="PNG", optimize=True)
        return

    qrs_and_boxes = [(qr1, resolved_qr1_box)]
    with Image.open(qr2_path) as source_qr2:
        qr2 = crop_qr_subject(source_qr2, auto_crop=auto_crop)
    qrs_and_boxes.append((qr2, resolved_qr2_box))

    for qr, (x, y, width, height) in qrs_and_boxes:
        if x < 0 or y < 0 or x + width > canvas.width or y + height > canvas.height:
            raise ValueError(f"QR position is outside the template: {x},{y},{width},{height}")
        canvas.alpha_composite(fit_qr_to_box(qr, (width, height)), (x, y))

    scale = canvas.height / 902
    draw_centered_card_text(
        canvas, resolved_text1_box, card1_title, card1_value, font_path,
        round(title_font_size * scale), round(value_font_size * scale),
    )
    draw_centered_card_text(
        canvas, resolved_text2_box, card2_title, card2_value, font_path,
        round(title_font_size * scale), round(value_font_size * scale),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() in {".jpg", ".jpeg"}:
        canvas.convert("RGB").save(output_path, format="JPEG", quality=95, optimize=True)
    else:
        canvas.save(output_path, format="PNG", optimize=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Embed one or two QR codes into a promotional background")
    parser.add_argument("template", type=Path, help="Template/background image")
    parser.add_argument("qr1", type=Path, help="First QR code image")
    parser.add_argument("qr2", type=Path, nargs="?", help="Optional second QR code image")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("qr_composite.png"),
        help="Output image (default: qr_composite.png)",
    )
    parser.add_argument("--qr1-box", type=parse_box, help="First QR box: x,y,width,height")
    parser.add_argument("--qr2-box", type=parse_box, help="Second QR box: x,y,width,height")
    parser.add_argument("--text1-box", type=parse_box, help="First caption box: x,y,width,height")
    parser.add_argument("--text2-box", type=parse_box, help="Second caption box: x,y,width,height")
    parser.add_argument("--card1-title", default=DEFAULT_CARD1_TITLE, help="First card title")
    parser.add_argument("--card1-value", default=DEFAULT_CARD1_VALUE, help="First card name/value")
    parser.add_argument("--card2-title", default=DEFAULT_CARD2_TITLE, help="Second card title")
    parser.add_argument("--card2-value", default=DEFAULT_CARD2_VALUE, help="Second card name/value")
    parser.add_argument("--font", dest="font_path", help="Font file for captions, e.g. PingFang.ttc")
    parser.add_argument("--title-font-size", type=int, default=28, help="Caption title font size")
    parser.add_argument("--value-font-size", type=int, default=24, help="Caption value font size")
    parser.add_argument(
        "--no-auto-crop",
        action="store_true",
        help="Do not crop title text from the top of QR images",
    )
    parser.add_argument(
        "--qr-only",
        action="store_true",
        help="Use one clean QR card without captions or promotional copy",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    for path in (args.template, args.qr1, args.qr2):
        if path is None:
            continue
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
            text1_box=args.text1_box,
            text2_box=args.text2_box,
            card1_title=args.card1_title,
            card1_value=args.card1_value,
            card2_title=args.card2_title,
            card2_value=args.card2_value,
            font_path=args.font_path,
            title_font_size=args.title_font_size,
            value_font_size=args.value_font_size,
            auto_crop=not args.no_auto_crop,
            qr_only=args.qr_only,
        )
    except Exception as exc:
        raise SystemExit(f"Failed to create composite: {exc}") from exc
    print(f"Generated: {args.output}")


if __name__ == "__main__":
    main()
