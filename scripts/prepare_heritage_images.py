"""Create web-optimised copies of the project's own heritage images.

Reads from data/raw (project assets only) and writes JPEG derivatives into
frontend/public/heritage. Originals are never modified.
"""
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "frontend" / "public" / "heritage"

SITES = [
    "taj_mahal",
    "qutub_minar",
    "red_fort",
    "ajanta_caves",
    "konark_sun_temple",
]

MAX_W = 1800
QUALITY = 82


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    for site in SITES:
        src = RAW / site / f"{site}_01.jpg"
        if not src.exists():
            print(f"SKIP {site}: {src} missing")
            continue

        with Image.open(src) as im:
            im = im.convert("RGB")
            if im.width > MAX_W:
                h = round(im.height * MAX_W / im.width)
                im = im.resize((MAX_W, h), Image.LANCZOS)

            dest = OUT / f"{site}.jpg"
            im.save(dest, "JPEG", quality=QUALITY, optimize=True, progressive=True)
            kb = dest.stat().st_size / 1024
            print(f"OK   {dest.name:<28} {im.width}x{im.height}  {kb:6.0f} KB")

    return 0


if __name__ == "__main__":
    sys.exit(main())
