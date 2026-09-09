# Platform Diagram Generator

This tool provides an automated, stable way to generate the "Open Platform Toolkit" multi-cloud delivery architecture diagram.

Instead of manually editing shapes in a drawing tool, you modify the `config.yaml` file and run the Python script to render a pixel-perfect, high-resolution PNG using Web technologies (HTML/Tailwind CSS) and Playwright.

## Prerequisites

Ensure you have Python 3 installed. Then, install the required packages and the Playwright browser binaries:

```bash
pip3 install -r requirements.txt
python3 -m playwright install chromium
```

## Generating the Diagram

Run the generation script:

```bash
python3 generate.py
```

This will read `config.yaml`, inject it into `template.html`, and capture a high-resolution screenshot named `platform_architecture.png`.

## Customization

- **Change Text**: Edit `config.yaml`.
- **Change Colors**: Modify the `color` property under `hexagons.ring` in `config.yaml`. It uses Tailwind CSS gradient classes (e.g., `from-blue-500 to-cyan-400`).
- **Layout Tweaks**: If you want to change the size, spacing, or add real image icons, you can edit `template.html`.

## Embedding Dynamic QR Codes

Use `embed_qr_codes.py` when the same promotional background needs updated QR
code images. It automatically crops title text above the supplied QR codes,
preserves the QR aspect ratio, and places the codes in the two card positions
used by the supplied 2564 x 902 background:

```bash
python3 embed_qr_codes.py background.png qr-group.png qr-ai-native.png \
  --output qr_composite.png
```

The default positions are calculated as proportions of the background size.
For a different template, override the positions with pixel boxes in the form
`x,y,width,height`:

```bash
python3 embed_qr_codes.py background.png qr1.png qr2.png \
  --qr1-box 1915,295,155,155 \
  --qr2-box 2263,295,155,155 \
  --output qr_composite.png
```

If the QR files are already cropped to the QR subject, add `--no-auto-crop`.

The card captions are configurable as well. By default, the two cards are
labelled `Xconnect-支持群` and `AI-Native-交流群`:

```bash
python3 embed_qr_codes.py background.png qr1.png qr2.png \
  --card1-title 群聊 --card1-value Xconnect-支持群 \
  --card2-title 群聊 --card2-value AI-Native-交流群 \
  --output qr_composite.png
```

Use `--font /path/to/font.ttc` when a custom font is needed. Use `--text1-box`
and `--text2-box` to move or resize the caption areas for a different template.
