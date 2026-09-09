#!/usr/bin/env python3
"""Create an XHS acquisition graphic with one to four QR codes.

The QR source images are kept as the source of truth. This script only removes
optional title text above a QR code, scales the code crisply, and lays it out in
a branded acquisition panel.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw

from embed_qr_codes import (
    crop_qr_subject,
    fit_font,
    load_font,
    parse_box,
)


# Default panel matches the right-hand QR-card area of the current 2564 x 902
# promotional background.
DEFAULT_PANEL_BOX = (0.706, 0.210, 0.279, 0.465)
DEFAULT_PORTRAIT_PANEL_BOX = (0.028, 0.783, 0.944, 0.190)
DEFAULT_TITLES = ("", "", "", "")
DEFAULT_VALUES = (
    "Xconnect-支持群",
    "AI-Native-交流群",
    "第三个群",
    "第四个群",
)


def fractional_box(
    template_size: tuple[int, int],
    box: tuple[float, float, float, float],
) -> tuple[int, int, int, int]:
    width, height = template_size
    x, y, box_width, box_height = box
    return round(width * x), round(height * y), round(width * box_width), round(height * box_height)


def fit_qr_crisp(qr: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Scale QR modules without introducing interpolation blur."""
    target_width, target_height = size
    scale = min(target_width / qr.width, target_height / qr.height)
    resized = qr.resize(
        (max(1, round(qr.width * scale)), max(1, round(qr.height * scale))),
        Image.Resampling.NEAREST,
    )
    fitted = Image.new("RGBA", (target_width, target_height), (255, 255, 255, 255))
    fitted.alpha_composite(
        resized,
        ((target_width - resized.width) // 2, (target_height - resized.height) // 2),
    )
    return fitted


def draw_panel_background(canvas: Image.Image, box: tuple[int, int, int, int]) -> None:
    x, y, width, height = box
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
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
    canvas.alpha_composite(layer)


def draw_single_panel(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    qr: Image.Image,
    title: str,
    value: str,
    font_path: str | None,
) -> None:
    x, y, width, height = box
    draw_panel_background(canvas, box)

    qr_size = min(round(height * 0.76), round(width * 0.47))
    qr_x = x + round(width * 0.055)
    qr_y = y + round((height - qr_size) / 2)
    canvas.alpha_composite(fit_qr_crisp(qr, (qr_size, qr_size)), (qr_x, qr_y))

    draw = ImageDraw.Draw(canvas)
    text_left = x + round(width * 0.53)
    text_width = round(width * 0.40)
    center_x = text_left + text_width // 2
    title_font = fit_font(draw, title, font_path, round(height * 0.12), text_width)
    value_font = fit_font(draw, value, font_path, round(height * 0.09), text_width)
    badge_font = fit_font(draw, "扫码加入", font_path, round(height * 0.07), text_width)

    def centered_text(text: str, font, center: int, top: int) -> None:
        text_width = draw.textbbox((0, 0), text, font=font)[2]
        draw.text((center - text_width // 2, top), text, fill=(17, 45, 105, 255), font=font)

    badge_top = y + round(height * 0.17)
    badge_width = draw.textbbox((0, 0), "扫码加入", font=badge_font)[2]
    draw.rounded_rectangle(
        (center_x - badge_width // 2 - 18, badge_top,
         center_x + badge_width // 2 + 18, badge_top + badge_font.size + 16),
        radius=18,
        fill=(232, 242, 255, 255),
    )
    centered_text("扫码加入", badge_font, center_x, badge_top + 8)
    centered_text(title, title_font, center_x, y + round(height * 0.39))
    centered_text(value, value_font, center_x, y + round(height * 0.60))


def draw_multi_panel(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    qrs: list[Image.Image],
    texts: list[tuple[str, str]],
    font_path: str | None,
) -> None:
    """Arrange two to four QR codes in a compact, future-ready grid."""
    x, y, width, height = box
    draw_panel_background(canvas, box)
    columns = 2
    rows = (len(qrs) + columns - 1) // columns
    cell_width = width // columns
    cell_height = height // rows
    draw = ImageDraw.Draw(canvas)

    for index, (qr, (title, value)) in enumerate(zip(qrs, texts)):
        row, column = divmod(index, columns)
        cell_x = x + column * cell_width
        cell_y = y + row * cell_height
        qr_size = min(round(cell_height * 0.57), round(cell_width * 0.72))
        qr_x = cell_x + (cell_width - qr_size) // 2
        qr_y = cell_y + 10
        canvas.alpha_composite(fit_qr_crisp(qr, (qr_size, qr_size)), (qr_x, qr_y))
        title_font = fit_font(draw, title, font_path, max(12, round(height * 0.055)), cell_width - 16)
        value_font = fit_font(draw, value, font_path, max(10, round(height * 0.045)), cell_width - 16)
        title_width = draw.textbbox((0, 0), title, font=title_font)[2]
        value_width = draw.textbbox((0, 0), value, font=value_font)[2]
        draw.text((cell_x + (cell_width - title_width) // 2, cell_y + round(cell_height * 0.66)), title, fill=(17, 45, 105, 255), font=title_font)
        draw.text((cell_x + (cell_width - value_width) // 2, cell_y + round(cell_height * 0.80)), value, fill=(17, 45, 105, 255), font=value_font)


def draw_portrait_two_panel(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    qrs: list[Image.Image],
    texts: list[tuple[str, str]],
    font_path: str | None,
) -> None:
    """Use the wide bottom card of the portrait template for two QR codes."""
    x, y, width, height = box
    draw_panel_background(canvas, box)
    cell_width = width // 2
    draw = ImageDraw.Draw(canvas)
    qr_size = min(round(height * 0.68), round(cell_width * 0.66))
    for index, (qr, (title, value)) in enumerate(zip(qrs, texts)):
        cell_x = x + index * cell_width
        qr_x = cell_x + (cell_width - qr_size) // 2
        qr_y = y + 12
        canvas.alpha_composite(fit_qr_crisp(qr, (qr_size, qr_size)), (qr_x, qr_y))
        value_font = fit_font(draw, value, font_path, max(11, round(height * 0.070)), cell_width - 18)
        value_width = draw.textbbox((0, 0), value, font=value_font)[2]
        if title:
            title_font = fit_font(draw, title, font_path, max(13, round(height * 0.090)), cell_width - 18)
            title_width = draw.textbbox((0, 0), title, font=title_font)[2]
            draw.text((cell_x + (cell_width - title_width) // 2, y + round(height * 0.71)), title, fill=(17, 45, 105, 255), font=title_font)
            value_y = y + round(height * 0.86)
        else:
            value_y = y + round(height * 0.76)
        draw.text((cell_x + (cell_width - value_width) // 2, value_y), value, fill=(17, 45, 105, 255), font=value_font)


def make_xhs_graphic(
    template_path: Path,
    qr_paths: list[Path],
    output_path: Path,
    panel_box: tuple[int, int, int, int] | None = None,
    titles: list[str] | None = None,
    values: list[str] | None = None,
    orientation: str = "auto",
    font_path: str | None = None,
    auto_crop: bool = True,
) -> None:
    if not 1 <= len(qr_paths) <= 4:
        raise ValueError("Use between one and four QR images")
    with Image.open(template_path) as source:
        canvas = source.convert("RGBA")
    is_portrait = orientation == "portrait" or (orientation == "auto" and canvas.height > canvas.width)
    box = panel_box or fractional_box(canvas.size, DEFAULT_PORTRAIT_PANEL_BOX if is_portrait else DEFAULT_PANEL_BOX)
    x, y, width, height = box
    if x < 0 or y < 0 or width <= 0 or height <= 0 or x + width > canvas.width or y + height > canvas.height:
        raise ValueError(f"Panel position is outside the template: {x},{y},{width},{height}")

    titles = titles or []
    values = values or []
    texts = [
        (
            titles[index] if index < len(titles) else DEFAULT_TITLES[index],
            values[index] if index < len(values) else DEFAULT_VALUES[index],
        )
        for index in range(len(qr_paths))
    ]
    qrs: list[Image.Image] = []
    for path in qr_paths:
        with Image.open(path) as source_qr:
            qrs.append(crop_qr_subject(source_qr, auto_crop=auto_crop))

    if len(qrs) == 1:
        draw_single_panel(canvas, box, qrs[0], texts[0][0], texts[0][1], font_path)
    elif is_portrait and len(qrs) == 2:
        draw_portrait_two_panel(canvas, box, qrs, texts, font_path)
    else:
        draw_multi_panel(canvas, box, qrs, texts, font_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() in {".jpg", ".jpeg"}:
        canvas.convert("RGB").save(output_path, format="JPEG", quality=95, optimize=True)
    else:
        canvas.save(output_path, format="PNG", optimize=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create an XHS acquisition graphic with one to four QR codes")
    parser.add_argument("template", type=Path, help="Template/background image")
    parser.add_argument("qr_images", nargs="+", type=Path, help="One to four actual QR code images")
    parser.add_argument("-o", "--output", type=Path, default=Path("xhs_qr.png"))
    parser.add_argument("--orientation", choices=("auto", "landscape", "portrait"), default="auto", help="Choose the default panel layout")
    parser.add_argument("--panel-box", type=parse_box, help="Acquisition panel: x,y,width,height")
    for index in range(1, 5):
        parser.add_argument(f"--card{index}-title", default=None, help=f"Card {index} title")
        parser.add_argument(f"--card{index}-value", default=None, help=f"Card {index} value/name")
    parser.add_argument("--font", dest="font_path", help="Font file for Chinese captions")
    parser.add_argument("--no-auto-crop", action="store_true", help="Do not remove title text above QR images")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if len(args.qr_images) > 4:
        raise SystemExit("Use between one and four QR images")
    for path in (args.template, *args.qr_images):
        if not path.is_file():
            raise SystemExit(f"File not found: {path}")

    titles = [getattr(args, f"card{index}_title") for index in range(1, 5)]
    values = [getattr(args, f"card{index}_value") for index in range(1, 5)]
    titles = [value for value in titles if value is not None]
    values = [value for value in values if value is not None]
    try:
        make_xhs_graphic(
            args.template,
            args.qr_images,
            args.output,
            panel_box=args.panel_box,
            titles=titles,
            values=values,
            orientation=args.orientation,
            font_path=args.font_path,
            auto_crop=not args.no_auto_crop,
        )
    except Exception as exc:
        raise SystemExit(f"Failed to create XHS graphic: {exc}") from exc
    print(f"Generated: {args.output}")


if __name__ == "__main__":
    main()
