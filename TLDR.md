# TL;DR

## What this repository does

This repository generates the platform architecture diagram and provides a
small utility for placing two dynamic QR codes and configurable group names
onto the promotional background.

## Install

```bash
pip3 install -r requirements.txt
python3 -m playwright install chromium
```

## Generate the architecture diagram

```bash
python3 generate.py
```

## Generate the QR composite

The command takes three image files in this order:

1. Background/template image
2. First QR code image
3. Second QR code image

```bash
python3 embed_qr_codes.py background.png qr1.png qr2.png \
  --output qr_composite.png
```

The default card captions are:

- `群聊` / `Xconnect-支持群`
- `群聊` / `AI-Native-交流群`

Override them when needed:

```bash
python3 embed_qr_codes.py background.png qr1.png qr2.png \
  --card1-title 群聊 --card1-value 新群名称1 \
  --card2-title 群聊 --card2-value 新群名称2 \
  --output qr_composite.png
```

## Layout parameters

The supplied promotional background uses proportional default positions. For
a different template, set pixel boxes as `x,y,width,height`:

```bash
python3 embed_qr_codes.py background.png qr1.png qr2.png \
  --qr1-box 1915,295,155,155 \
  --qr2-box 2263,295,155,155 \
  --text1-box 1838,492,320,83 \
  --text2-box 2188,492,320,83 \
  --output qr_composite.png
```

Use `--font /path/to/font.ttc` for a specific font and
`--no-auto-crop` when the QR files are already cropped to the QR subject.

Important: the second and third inputs must be the actual QR images. Small
screenshots containing only the caption text are not QR inputs; use
`--card1-value` and `--card2-value` to define those names instead.

## XHS acquisition script

Use `embed_xhs_qr.py` when the graphic is intended for Xiaohongshu customer
acquisition. One QR code is highlighted; two to four QR images use a compact
grid automatically:

```bash
python3 embed_xhs_qr.py background.png qr.png \
  --card1-title 小红书获客 \
  --card1-value Xconnect-支持群 \
  --output xhs_qr.png
```

For future QR destinations, append more actual QR image paths and define
`--card1-value` through `--card4-value`. The QR data is not regenerated or
changed by the script.
