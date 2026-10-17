#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate Feishu setup QR codes (no secrets inside)."""
import os

try:
    import qrcode
except ImportError:
    raise SystemExit("pip install qrcode")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "docs", "assets")
os.makedirs(OUT, exist_ok=True)

TARGETS = {
    "feishu-setup-qr.png": "https://justinjchen-cornell.github.io/Deep-Risk-OPP/docs/feishu-setup.html",
    "feishu-secret-qr.png": "https://github.com/Justinjchen-Cornell/Deep-Risk-OPP/settings/secrets/actions/new",
}

for name, url in TARGETS.items():
    qr = qrcode.QRCode(version=None, box_size=10, border=2,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#182238", back_color="#FCFAF5")
    path = os.path.join(OUT, name)
    img.save(path)
    print("saved:", path, "->", url)
