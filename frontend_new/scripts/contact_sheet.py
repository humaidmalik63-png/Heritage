"""Build one labelled contact sheet from the downloaded monument images.

Used to confirm by eye that each fetched file actually depicts its monument -
filename matching and keyword filters are not proof, sight is.

    C:/Users/humai/AppData/Local/Python/bin/python frontend_new/scripts/contact_sheet.py

Writes to the scratch directory (never into the project) and prints the path.
"""
from __future__ import annotations

import json
import os

from PIL import Image, ImageDraw

FRONTEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MONUMENTS_DIR = os.path.join(FRONTEND, "assets", "images", "monuments")
MANIFEST = os.path.join(MONUMENTS_DIR, "image_manifest.json")
OUT_DIR = os.environ.get("TMPDIR") or os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Temp"
)

COLS = 5
CELL_W, CELL_H = 320, 240
LABEL_H = 34


def main() -> None:
    if not os.path.isfile(MANIFEST):
        raise SystemExit(f"no manifest at {MANIFEST}")
    with open(MANIFEST, encoding="utf-8") as fh:
        manifest = json.load(fh)
    entries = manifest.get("images") or {}

    items = []
    for site_id, entry in sorted(entries.items()):
        files = entry.get("files") or []
        if not files:
            continue
        path = os.path.join(FRONTEND, files[0])
        if not os.path.isfile(path):
            continue
        items.append((site_id, entry.get("name", site_id), path))

    if not items:
        raise SystemExit("manifest lists no readable files")

    rows = (len(items) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * CELL_W, rows * (CELL_H + LABEL_H)), (12, 14, 20))
    draw = ImageDraw.Draw(sheet)

    for i, (site_id, name, path) in enumerate(items):
        col, row = i % COLS, i // COLS
        x, y = col * CELL_W, row * (CELL_H + LABEL_H)
        with Image.open(path) as opened:
            tile = opened.convert("RGB")
            tile.thumbnail((CELL_W, CELL_H), Image.LANCZOS)
            sheet.paste(tile, (x + (CELL_W - tile.width) // 2,
                               y + (CELL_H - tile.height) // 2))
        # index + site_id, so a mistake can be traced back to a manifest entry
        draw.text((x + 6, y + CELL_H + 4), f"{i + 1}. {site_id[:38]}", fill=(235, 240, 248))
        draw.text((x + 6, y + CELL_H + 18), name[:44], fill=(180, 190, 205))

    out = os.path.join(OUT_DIR, "monument_contact_sheet.jpg")
    sheet.save(out, "JPEG", quality=88)
    print(f"{len(items)} images -> {out}")
    print(f"size {sheet.width}x{sheet.height}")


if __name__ == "__main__":
    main()