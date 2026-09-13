#!/usr/bin/env python3
"""Render a text-safe, brand-aligned XHS product marketing series."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


SIZE = (1080, 1440)
NAVY = (16, 39, 103, 255)
BLUE = (42, 103, 230, 255)
PURPLE = (121, 68, 232, 255)
CYAN = (46, 174, 221, 255)
MUTED = (82, 104, 153, 255)
PALE = (234, 242, 255, 255)
WHITE = (255, 255, 255, 248)

FONT_CANDIDATES = (
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = FONT_CANDIDATES
    if bold:
        candidates = (
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            *FONT_CANDIDATES,
        )
    for path in candidates:
        if Path(path).is_file():
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def gradient_background() -> Image.Image:
    image = Image.new("RGBA", SIZE)
    pixels = image.load()
    for y in range(SIZE[1]):
        for x in range(SIZE[0]):
            top = y / SIZE[1]
            glow = max(0.0, 1.0 - math.hypot(x - 820, y - 280) / 900)
            pixels[x, y] = (
                round(248 - 18 * top - 4 * glow),
                round(251 - 22 * top - 5 * glow),
                round(255 - 2 * top),
                255,
            )
    return image


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill, outline=None, width=1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_background_detail(draw: ImageDraw.ImageDraw) -> None:
    for y in range(160, 1280, 90):
        draw.line((50, y, 1030, y), fill=(180, 207, 246, 45), width=1)
    for x in range(50, 1050, 90):
        draw.line((x, 130, x, 1300), fill=(180, 207, 246, 34), width=1)
    draw.ellipse((500, 180, 1240, 920), outline=(104, 160, 241, 45), width=2)
    draw.ellipse((590, 270, 1150, 830), outline=(144, 101, 238, 40), width=2)


def draw_mark(draw: ImageDraw.ImageDraw, center: tuple[int, int], scale: float = 1.0) -> None:
    cx, cy = center
    arm = round(52 * scale)
    width = max(12, round(20 * scale))
    draw.line((cx - arm, cy - arm, cx + arm, cy + arm), fill=BLUE, width=width)
    draw.line((cx - arm, cy + arm, cx + arm, cy - arm), fill=PURPLE, width=width)


def draw_brand(draw: ImageDraw.ImageDraw, y: int = 60) -> None:
    draw_mark(draw, (100, y + 28), 0.50)
    draw.text((142, y), "XWORK", fill=NAVY, font=font(34, bold=True))
    draw.text((144, y + 43), "Work · Connect · Control", fill=MUTED, font=font(16))


def text_width(draw: ImageDraw.ImageDraw, value: str, fnt) -> int:
    return draw.textbbox((0, 0), value, font=fnt)[2]


def centered(draw: ImageDraw.ImageDraw, value: str, y: int, fnt, fill=NAVY, center: int = 540) -> None:
    draw.text((center - text_width(draw, value, fnt) // 2, y), value, fill=fill, font=fnt)


def wrap_text(draw: ImageDraw.ImageDraw, value: str, fnt, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in value:
        candidate = current + char
        if current and text_width(draw, candidate, fnt) > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def body_text(draw: ImageDraw.ImageDraw, value: str, xy: tuple[int, int], max_width: int, size: int = 26, fill=MUTED, line_gap: int = 13) -> int:
    fnt = font(size)
    x, y = xy
    for line in wrap_text(draw, value, fnt, max_width):
        draw.text((x, y), line, fill=fill, font=fnt)
        y += size + line_gap
    return y


def pill(draw: ImageDraw.ImageDraw, value: str, xy: tuple[int, int], fill=PALE, text_fill=NAVY) -> None:
    fnt = font(20, bold=True)
    x, y = xy
    w = text_width(draw, value, fnt) + 34
    rounded(draw, (x, y, x + w, y + 44), 22, fill)
    draw.text((x + 17, y + 9), value, fill=text_fill, font=fnt)


def node(draw: ImageDraw.ImageDraw, center: tuple[int, int], label: str, fill, radius: int = 82) -> None:
    cx, cy = center
    rounded(draw, (cx - radius, cy - radius, cx + radius, cy + radius), 28, fill, outline=(255, 255, 255, 220), width=3)
    fnt = font(25, bold=True)
    centered(draw, label, cy - 15, fnt, fill=NAVY, center=cx)


def draw_footer(draw: ImageDraw.ImageDraw, index: int) -> None:
    draw.line((70, 1332, 1010, 1332), fill=(175, 200, 239, 120), width=2)
    draw.text((70, 1360), f"XWORKTECH  /  {index:02d}", fill=MUTED, font=font(17, bold=True))
    draw.text((770, 1360), "xworktech.com", fill=MUTED, font=font(17))


def base(title: str, subtitle: str, index: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = gradient_background()
    draw = ImageDraw.Draw(image)
    draw_background_detail(draw)
    draw_brand(draw)
    draw.text((70, 165), title, fill=NAVY, font=font(54, bold=True))
    body_text(draw, subtitle, (72, 242), 900, size=26)
    draw_footer(draw, index)
    return image, draw


def render_matrix() -> Image.Image:
    image, draw = base("One AI Workspace", "从对话到交付，把任务、知识、连接与结果放在同一条工作线上。", 1)
    cards = [
        ("XWorkmate", "AI 工作空间", BLUE, (82, 420, 510, 685)),
        ("XConnect", "安全连接", CYAN, (570, 420, 998, 685)),
        ("AI Workspace", "统一工作流", PURPLE, (82, 735, 510, 1000)),
        ("Open Platform", "开放基础设施", (75, 130, 220, 255), (570, 735, 998, 1000)),
    ]
    for title, label, color, box in cards:
        rounded(draw, box, 30, WHITE, outline=(202, 220, 247, 255), width=3)
        x, y, right, bottom = box
        draw.ellipse((x + 28, y + 28, x + 96, y + 96), fill=color)
        draw_mark(draw, (x + 62, y + 62), 0.28)
        draw.text((x + 28, y + 124), title, fill=NAVY, font=font(29, bold=True))
        draw.text((x + 28, y + 174), label, fill=MUTED, font=font(23))
        draw.line((x + 28, y + 222, right - 28, y + 222), fill=(203, 219, 245, 255), width=2)
        draw.text((x + 28, y + 238), "Plan  ·  Connect  ·  Deliver", fill=MUTED, font=font(17))
    rounded(draw, (148, 1050, 932, 1240), 42, (20, 47, 115, 245))
    centered(draw, "Work  ·  Connect  ·  Control", 1090, font(29, bold=True), fill=(255, 255, 255, 255))
    centered(draw, "从一个入口，连接完整的 AI 工作方式", 1150, font(23), fill=(209, 226, 255, 255))
    return image


def render_xworkmate() -> Image.Image:
    image, draw = base("XWorkmate", "从对话到交付，一个 AI 工作空间完成全部工作。", 2)
    pill(draw, "AI WORKSPACE", (72, 355), fill=(220, 235, 255, 255), text_fill=BLUE)
    rounded(draw, (72, 450, 1008, 1115), 42, (12, 35, 92, 245))
    draw.text((120, 505), "Your AI Workspace", fill=(255, 255, 255, 255), font=font(36, bold=True))
    draw.text((120, 560), "Connected. Productive. Yours.", fill=(171, 205, 255, 255), font=font(21))
    # Workflow rail.
    steps = [("01", "Plan", "把目标计划清楚"), ("02", "Connect", "连接模型、工具与数据"), ("03", "Deliver", "把结果可靠交付")]
    for index, (number, english, chinese) in enumerate(steps):
        x = 145 + index * 285
        if index < 2:
            draw.line((x + 72, 760, x + 285, 760), fill=(93, 141, 232, 180), width=5)
        draw.ellipse((x, 688, x + 144, 832), fill=(38, 92, 200, 255), outline=(112, 188, 255, 255), width=3)
        centered(draw, number, 715, font(22, bold=True), fill=(255, 255, 255, 255), center=x + 72)
        centered(draw, english, 870, font(27, bold=True), fill=(255, 255, 255, 255), center=x + 72)
        centered(draw, chinese, 920, font(19), fill=(187, 211, 255, 255), center=x + 72)
    rounded(draw, (120, 1010, 960, 1070), 30, (43, 78, 157, 255))
    centered(draw, "任务  ·  对话  ·  知识  ·  结果", 1025, font(22, bold=True), fill=(255, 255, 255, 255))
    return image


def render_xconnect() -> Image.Image:
    image, draw = base("XConnect", "为 AI Workspace 提供稳定、安全、可追踪的连接能力。", 3)
    pill(draw, "AI CONNECTIVITY", (72, 355), fill=(218, 250, 255, 255), text_fill=(16, 127, 170, 255))
    center = (540, 765)
    rounded(draw, (350, 575, 730, 955), 48, (18, 49, 116, 245), outline=(90, 191, 238, 255), width=4)
    draw_mark(draw, center, 1.25)
    centered(draw, "XConnect", 835, font(31, bold=True), fill=(255, 255, 255, 255), center=540)
    satellites = [
        ((210, 520), "Models", BLUE),
        ((870, 520), "Tools", PURPLE),
        ((210, 1020), "Data", CYAN),
        ((870, 1020), "Workspace", (73, 126, 220, 255)),
    ]
    for (cx, cy), label, color in satellites:
        draw.line((center[0], center[1], cx, cy), fill=(92, 163, 235, 180), width=4)
        draw.ellipse((cx - 88, cy - 88, cx + 88, cy + 88), fill=WHITE, outline=color, width=4)
        centered(draw, label, cy - 15, font(24, bold=True), fill=NAVY, center=cx)
    rounded(draw, (100, 1150, 980, 1240), 28, (227, 241, 255, 235))
    centered(draw, "Secure  ·  Observable  ·  Extensible", 1176, font(24, bold=True), fill=NAVY)
    return image


def render_workspace() -> Image.Image:
    image, draw = base("AI Workspace", "让任务、知识、连接和交付，在同一个上下文里持续推进。", 4)
    pill(draw, "ONE WORKSPACE", (72, 355), fill=(236, 228, 255, 255), text_fill=PURPLE)
    rounded(draw, (72, 455, 1008, 1110), 42, WHITE, outline=(201, 219, 247, 255), width=3)
    # Dashboard sidebar.
    rounded(draw, (105, 495, 310, 1070), 28, (19, 45, 106, 255))
    draw.text((140, 535), "AI Workspace", fill=(255, 255, 255, 255), font=font(25, bold=True))
    for i, label in enumerate(("Overview", "Tasks", "Knowledge", "Connections", "Deliverables")):
        y = 625 + i * 70
        if i == 0:
            rounded(draw, (125, y - 14, 290, y + 34), 18, (55, 104, 213, 255))
        draw.text((150, y), label, fill=(229, 239, 255, 255), font=font(19))
    # Main workspace content.
    draw.text((360, 525), "Today’s workspace", fill=NAVY, font=font(31, bold=True))
    draw.text((360, 580), "从目标开始，保留每一步上下文", fill=MUTED, font=font(22))
    mini = [
        ("Tasks", "3 active", BLUE, 650),
        ("Knowledge", "12 sources", PURPLE, 800),
        ("Connections", "8 ready", CYAN, 950),
    ]
    for label, value, color, y in mini:
        rounded(draw, (360, y, 935, y + 100), 24, (246, 249, 255, 255), outline=(211, 226, 248, 255), width=2)
        draw.ellipse((390, y + 28, 434, y + 72), fill=color)
        draw.text((465, y + 24), label, fill=NAVY, font=font(21, bold=True))
        draw.text((465, y + 57), value, fill=MUTED, font=font(18))
        draw.line((785, y + 50, 890, y + 50), fill=color, width=7)
    rounded(draw, (175, 1160, 905, 1240), 28, (19, 45, 106, 245))
    centered(draw, "Context stays with the work.", 1184, font(23, bold=True), fill=(255, 255, 255, 255))
    return image


def render_series(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    renders = (
        ("01-solution-matrix.png", render_matrix()),
        ("02-xworkmate.png", render_xworkmate()),
        ("03-xconnect.png", render_xconnect()),
        ("04-ai-workspace.png", render_workspace()),
    )
    paths: list[Path] = []
    for name, image in renders:
        path = output_dir / name
        image.save(path, format="PNG", optimize=True)
        paths.append(path)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("xhs_marketing_series"))
    args = parser.parse_args()
    for path in render_series(args.output_dir):
        print(f"Generated: {path}")


if __name__ == "__main__":
    main()
