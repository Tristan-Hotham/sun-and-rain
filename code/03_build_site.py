"""Step 3. Build index.html from code/page_template.html.

Every number in the text is a {{path|format}} token filled from data/results.json, so the page cannot drift from the
analysis. Facts the template states in words are checked against the data below. code/bivariate.js is inlined, the
results are embedded, and the page fetches the monthly grids (data/sun_q*.png, data/rain_q*.png) and the place list
(data/cities_page.json).
Run: python3 code/03_build_site.py
"""
import json, os, re
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json"), encoding="utf-8"))


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(v):,}"
    if f == "pct": return f"{round(v * 100)}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}".replace("-", "−")
    if f == "f3": return f"{v:.3f}"
    raise ValueError(f)


def sub(m):
    return fmt(get(m.group(1)), m.group(3))


# facts stated in words (page, paper, blog, collage)
C = pd.read_csv(os.path.join(ROOT, "data", "cities.csv"), keep_default_na=False, na_values=[""])
city = lambda n, cc: C[(C.name == n) & (C.cc == cc)].iloc[0]
lima, london, sura, madrid = city("Lima", "PE"), city("London", "GB"), city("Surabaya", "ID"), city("Madrid", "ES")
assert lima.rain_mm < london.rain_mm * 14 / 365                     # less rain in a year than London in a fortnight
big = C[C["pop"] >= 1e6]
assert (big.sun_h < lima.sun_h).sum() < 25                          # "one of the dullest big cities"
assert sura.sun_h > madrid.sun_h and sura.rain_mm > 1500            # "soaked by the monsoon and still sunnier than Madrid"
assert R["extremes"]["sunniest"]["near_country"] == "Sudan" and R["extremes"]["sunniest"]["lat"] > 20
assert R["uk"]["sunniest"]["near"] == "Bognor Regis"
assert abs(R["uk"]["wettest"]["lat"] - 56.25) < .1 and abs(R["uk"]["wettest"]["lon"] + 4.92) < .1   # near Loch Lomond
assert R["uk"]["dull_tercile_share"] == 1.0                         # every bit of the UK in the dullest third
assert [c["country"] for c in R["countries"]["dullest"][:4]] == ["Iceland", "Ireland", "Norway", "United Kingdom"]
assert R["uk"]["sun_rank"] == R["uk"]["n_big"] - 3
d = R["big"]["dullest"]
assert d[0]["name"] == "Guayaquil" and all(x["country"] == "People's Republic of China" for x in d[1:7]) and d[7]["name"] == "Birmingham" and d[7]["cc"] == "GB"
assert R["big"]["sunniest"][0]["name"] == "Phoenix"
assert [r["name"] for r in R["big"]["q_dull_dry"]] == ["Lima", "Callao", "Trujillo"]
assert R["corners_q"]["sunny_dry"] > 1 / 9 > R["corners_q"]["sunny_wet"] and R["corners_q"]["dull_dry"] < 1 / 9
assert R["season"]["mumbai_peak_sun"] == "May"
assert max(R["london"]["sun_month"]) == R["london"]["sun_month"][5]   # peaks in June
assert R["corr"]["spearman"] < 0
for nm in ("London", "Lima", "Mumbai"): assert nm in R["profiles"] or nm in R["similar"]["examples"]

if __name__ == "__main__":
    tpl = open(os.path.join(HERE, "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", sub, tpl)
    bv = open(os.path.join(HERE, "bivariate.js"), encoding="utf-8").read()
    html = html.replace("/*BVJS*/", bv)
    html = html.replace("/*RESULTS*/", json.dumps(R, ensure_ascii=False, separators=(",", ":")))
    assert "{{" not in html
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--"):
        assert bad not in vis, bad
    # strings inside the scripts that are shown to readers
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        scr = re.sub(r"var\(--[\w-]+", "", scr)
        for bad in ("\u2014", "\u2013", "--"):
            assert bad not in scr.replace("\\u2014", ""), bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()), "bytes")
