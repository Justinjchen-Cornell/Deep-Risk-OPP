# -*- coding: utf-8 -*-
from pathlib import Path
import base64
from playwright.sync_api import sync_playwright
from pypdf import PdfWriter, PdfReader

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "看板日志" / "reports" / "special"
ASSETS = OUT / "ai_bubble_assets"

def data_uri(name):
    p = ASSETS / name
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()

body_tpl = (BASE/"scripts"/"ai_bubble_plain_body.html").read_text(encoding="utf-8")
for fig in ASSETS.glob("*.png"):
    body_tpl = body_tpl.replace("{{FIG:%s}}" % fig.name, data_uri(fig.name))
body_html = OUT / "_abp_body_rendered.html"
body_html.write_text(body_tpl, encoding="utf-8")

cover_tpl = (BASE/"scripts"/"ai_bubble_plain_cover.html").read_text(encoding="utf-8")
cover_html = OUT / "_abp_cover_rendered.html"
cover_html.write_text(cover_tpl, encoding="utf-8")

cover_pdf = OUT / "_abp_cover.pdf"
body_pdf = OUT / "_abp_body.pdf"
final_pdf = OUT / "AI泡沫-人话版-风险-推演与二阶三阶机会-2026-11-03.pdf"

header = """<div style="width:100%;font-family:'Microsoft YaHei';font-size:6.8pt;color:#8A8F98;padding:0 18mm 2mm;display:flex;justify-content:space-between;letter-spacing:0.3pt;border-bottom:0.5pt solid #E3DED2;">
<span>DEEP-RISK-OPP · AI 泡沫：风险、推演与二阶/三阶机会</span><span>2026-11-03 更新版</span></div>"""
footer = """<div style="width:100%;font-family:'Microsoft YaHei';font-size:6.8pt;color:#8A8F98;padding:2mm 18mm 0;display:flex;justify-content:space-between;border-top:0.5pt solid #E3DED2;">
<span>研究框架，不构成投资建议。</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>"""

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page()
    page.goto(cover_html.resolve().as_uri())
    page.pdf(path=str(cover_pdf), format="A4", print_background=True,
             margin={"top":"0","bottom":"0","left":"0","right":"0"})
    page.goto(body_html.resolve().as_uri())
    page.pdf(path=str(body_pdf), format="A4", print_background=True,
             display_header_footer=True, header_template=header, footer_template=footer,
             margin={"top":"19mm","bottom":"17mm","left":"18mm","right":"18mm"})
    browser.close()

writer = PdfWriter()
for f in (cover_pdf, body_pdf):
    for pg in PdfReader(str(f)).pages:
        writer.add_page(pg)
writer.add_metadata({
    "/Title": "AI 泡沫：风险、推演与二阶/三阶机会",
    "/Author": "Deep-Risk-OPP",
    "/Subject": "人话版研究框架（2026-11-03 更新版）",
    "/Keywords": "AI bubble, capex, credit, GPU, power, second-order, third-order",
})
with open(final_pdf, "wb") as fh:
    writer.write(fh)
print("PDF:", final_pdf, final_pdf.stat().st_size, "bytes")
print("body pages:", len(PdfReader(str(body_pdf)).pages), "cover pages:", len(PdfReader(str(cover_pdf)).pages))
for f in (cover_pdf, body_pdf, body_html, cover_html):
    try:
        f.unlink()
    except Exception:
        pass
