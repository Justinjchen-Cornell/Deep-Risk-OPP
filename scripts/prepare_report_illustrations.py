# -*- coding: utf-8 -*-
"""Resize illustrations and cover the bottom-right AI watermark without cutting content."""
from PIL import Image, ImageDraw
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "看板日志" / "reports" / "special" / "supercycle_report_en_assets" / "配图"
DST = BASE / "看板日志" / "reports" / "special" / "supercycle_report_en_assets" / "visuals"
DST.mkdir(parents=True, exist_ok=True)

for i, f in enumerate(sorted(SRC.glob("*.png")), 1):
    im = Image.open(f).convert("RGB")
    w, h = im.size
    im = im.resize((2000, int(h * 2000 / w)), Image.LANCZOS)
    w, h = im.size
    d = ImageDraw.Draw(im)
    # cover only the bottom-right watermark corner; keep the rest of the board intact
    d.rectangle([(1780, h - 46), (w, h)], fill=(250, 248, 242))
    out = DST / f"visual_{i:02d}.jpg"
    im.save(out, "JPEG", quality=92, optimize=True)
    print(out.name, im.size, out.stat().st_size)

print("done", DST)

