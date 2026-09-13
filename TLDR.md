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

For the official assistant account, use one QR input. The single code is
placed in the right-hand card position. Add `--qr-only` to keep the image
focused on the QR code and put all guidance in the article copy:

```bash
python3 embed_qr_codes.py background.png assistant-qr.png \
  --qr-only \
  --output assistant-banner.png
```

Important: the second and third inputs must be the actual QR images. Small
screenshots containing only the caption text are not QR inputs; use
`--card1-value` and `--card2-value` to define those names instead.

## Mobile portrait QR script

Use `embed_xhs_qr.py` for a mobile portrait graphic. The assistant version
keeps one centered QR code position and no extra copy:

```bash
python3 embed_xhs_qr.py portrait-background.png assistant-qr.png \
  --orientation portrait \
  --qr-only \
  --output assistant-portrait.png
```

For the two-group version, use two QR codes at the bottom:

```bash
python3 embed_xhs_qr.py portrait-background.png qr1.png qr2.png \
  --orientation portrait \
  --card1-value Xconnect-支持群 \
  --card2-value AI-Native-交流群 \
  --output portrait_qr.png
```

The two QR images remain side by side and the output only displays the two
configured group names. For future expansion, append a third or fourth actual
QR image and define `--card3-value` or `--card4-value`. The QR data is not
regenerated or changed by the script.
