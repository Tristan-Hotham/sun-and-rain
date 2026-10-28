"""Step 4. Render header.png (1200x630 social card) with Playwright Chromium.

Uses work/header_map.png (the 3 x 3 world map drawn by step 5) and data/results.json.
Fonts: FONT_DIR holding FrauncesVar.ttf, SourceSerif4-Regular.ttf, IBMPlexMono-Regular.ttf, IBMPlexMono-Medium.ttf.
Run (after step 5): FONT_DIR=/path/to/fonts python3 code/04_header.py
"""
import base64, json, os, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import bivariate as bv
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
FD = os.environ.get("FONT_DIR", "")
mp = base64.b64encode(open(os.path.join(ROOT, "work", "header_map.png"), "rb").read()).decode()
P = bv.palette(3)
leg = "".join(f'<rect x="{i * 25}" y="{(2 - j) * 25}" width="23" height="23" fill="{P[i][j]}"/>' for i in range(3) for j in range(3))
ff = ""
if FD:
    ff = "".join(f"@font-face{{font-family:'{n}';src:url('file://{FD}/{f}');font-weight:{w};}}" for n, f, w in [
        ("Fraunces", "FrauncesVar.ttf", "100 900"), ("Source Serif 4", "SourceSerif4-Regular.ttf", "400"),
        ("IBM Plex Mono", "IBMPlexMono-Regular.ttf", "400"), ("IBM Plex Mono", "IBMPlexMono-Medium.ttf", "500")])
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff}
body{{margin:0;width:1200px;height:630px;background:#F7F3EC;color:#211C24;overflow:hidden;position:relative;font-family:'Source Serif 4',Georgia,serif}}
.k{{position:absolute;left:64px;top:52px;font:500 15px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#6A6270;display:flex;gap:12px;align-items:center}}
.k b{{background:#3B1D47;color:#fff;padding:7px 9px;font-weight:500}}
h1{{position:absolute;left:58px;top:84px;margin:0;font:900 112px/.9 Fraunces,Georgia,serif;letter-spacing:-.02em}}
h1 .s{{color:#C9661C}} h1 .r{{color:#2E8F8C}}
p{{position:absolute;left:64px;top:206px;width:560px;margin:0;font-size:24px;line-height:1.34}}
.map{{position:absolute;left:290px;top:296px;width:910px}}
.f{{position:absolute;left:64px;bottom:34px;font:400 14px/1 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#6A6270}}
.lg{{position:absolute;right:56px;top:56px;font:400 13px/1.25 'IBM Plex Mono',monospace;color:#6A6270}}
.lg svg{{display:block;margin:4px 0 4px 54px}}
</style></head><body>
<div class="k"><b>Data study</b><span>Climate · 1961 to 1990</span></div>
<h1><span class="s">Sun</span> and <span class="r">rain</span></h1>
<p>The world's sunshine against its rainfall. Only {R['corners_q']['sunny_wet'] * 100:.0f}% of land is both sunny and wet; {R['uk']['land_sunnier_than_uk_max'] * 100:.0f}% is sunnier than anywhere in the UK.</p>
<img class="map" src="data:image/png;base64,{mp}">
<div class="lg"><div style="margin-left:54px">dull and wet &nbsp; sunny and wet</div><svg width="75" height="75">{leg}</svg><div style="margin-left:54px">dull and dry &nbsp; sunny and dry</div></div>
<div class="f">Dr Tristan Hotham · Independent researcher</div>
</body></html>"""
tmp = os.path.join(ROOT, "work", "header.html"); open(tmp, "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto("file://" + os.path.abspath(tmp)); pg.wait_for_timeout(800)
    pg.screenshot(path=os.path.join(ROOT, "header.png")); b.close()
os.remove(tmp)
print("header.png written")
