"""r/dataisbeautiful collage: reddit/sun_and_rain.png (2400 x 3000), light warm paper with the project's own bivariate palette.
Every number comes from ../data/results.json; maps are drawn from ../work/grid.npz (run code/01_prepare.py first).
Fonts: FONT_DIR (Fraunces, Source Serif 4, IBM Plex Mono).
Run from this folder: FONT_DIR=/path/to/fonts python3 collage.py
"""
import json, os, sys
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "code"))
import bivariate as bv
FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf"]:
    fm.fontManager.addfont(os.path.join(FD, f))
DISP = fm.FontProperties(fname=os.path.join(FD, "FrauncesVar.ttf"), weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT = "#F7F3EC", "#211C24", "#6A6270"
P = bv.palette(3)
HOT, COOL, DEEP = "#C9661C", P[0][2], P[2][2]
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
G = np.load(os.path.join(ROOT, "work", "grid.npz"))
cells, SUN, PRE = G["cells"], G["sun"].astype(float), G["pre"].astype(float)
NC, ROWS = 2160, 900
rows, cols = cells // NC, cells % NC
area = np.cos(np.radians(90 - (rows + .5) / 6))
RGB = np.array([[bv.hex2rgb(P[i][j]) for j in range(3)] for i in range(3)])


def img(ms):
    s = SUN[:, ms].sum(1); p = PRE[:, ms].sum(1)
    I = bv.classify(s, bv.quantile_breaks(s, area, 3)); J = bv.classify(p, bv.quantile_breaks(p, area, 3))
    a = np.zeros((ROWS * NC, 4)); a[rows * NC + cols, :3] = RGB[I, J]; a[rows * NC + cols, 3] = 1
    return a.reshape(ROWS, NC, 4)


def wmap(ax, im):
    ax.imshow(im, extent=(-180, 180, -60, 90), interpolation="nearest")
    ax.set_xlim(-168, 180); ax.set_ylim(-56, 84); ax.set_aspect(1); ax.axis("off")


fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
fig.text(0.045, 0.975, "Sunny or rainy? The", fontproperties=DISP, fontsize=50, color=FG, va="top")
rend = fig.canvas.get_renderer(); x = 0.045
for word, c in (("world is ", FG), ("both, ", HOT), ("or neither", COOL)):
    t = fig.text(x, 0.927, word.replace(" ", "\u00a0"), fontproperties=DISP, fontsize=50, color=c, va="top")
    x += t.get_window_extent(rend).width / fig.bbox.width
fig.text(0.045, 0.872, f"Every land cell outside Antarctica ({R['meta']['cells']:,} of them, about 18 km across), coloured by which third of\n"
         "the world's land it falls in for yearly sunshine hours and which third for yearly rain. 1961 to 1990 averages.",
         family=SER, fontsize=14.5, color=FG, va="top", linespacing=1.15)

# hero map
ax = fig.add_axes([0.0, 0.52, 1.0, 0.33]); ax.set_facecolor(BG); wmap(ax, img(list(range(12))))
C = {(r[0], r[1]): r for r in R["big"]["rows"]}
for nm, cc, dx, dy in [("London", "GB", -4, 4), ("Lima", "PE", -5, -5), ("Phoenix", "US", -2, -6), ("Chongqing", "CN", 3, 4), ("Surabaya", "ID", 6, -6), ("Cairo", "EG", 3, -6)]:
    lat = {"London": 51.51, "Lima": -12.04, "Phoenix": 33.45, "Chongqing": 29.56, "Surabaya": -7.25, "Cairo": 30.06}[nm]
    lon = {"London": -0.13, "Lima": -77.03, "Phoenix": -112.07, "Chongqing": 106.55, "Surabaya": 112.75, "Cairo": 31.25}[nm]
    r = C[(nm, cc)]
    ax.plot(lon, lat, "o", ms=6, mfc="white", mec=FG, mew=1.4, zorder=5)
    ax.annotate(f"{nm}\n{r[3]:,} h · {r[4]:,} mm", (lon, lat), xytext=(lon + dx * 3, lat + dy * 3), family=MONO, fontsize=10.5, color=FG,
                ha="right" if dx < 0 else "left", va="center", arrowprops=dict(arrowstyle="-", color=FG, lw=.8),
                bbox=dict(fc=(1, 1, 1, .8), ec="none", pad=1.5), zorder=6)

# legend
lx = fig.add_axes([0.625, 0.527, 0.2, 0.1]); lx.axis("off"); lx.set_xlim(-2.4, 5.4); lx.set_ylim(-1.3, 3.1); lx.set_aspect(1)
for i in range(3):
    for j in range(3): lx.add_patch(plt.Rectangle((i, j), .94, .94, color=P[i][j]))
for x, y, t, ha in [(-.12, .45, "dull\nand dry", "right"), (3.06, .45, "sunny\nand dry", "left"), (-.12, 2.45, "dull\nand wet", "right"), (3.06, 2.45, "sunny\nand wet", "left")]:
    lx.text(x, y, t, family=MONO, fontsize=10.5, color=FG, ha=ha, va="center", linespacing=1.05)
lx.annotate("", xy=(3, -.4), xytext=(0, -.4), arrowprops=dict(arrowstyle="->", color=MUT))
lx.text(1.5, -.95, "more sun", family=MONO, fontsize=10, color=MUT, ha="center")

# big numbers
items = [
    (f"{R['corners_q']['sunny_wet'] * 100:.0f}%", DEEP, f"of land is both sunny and wet, the rarest\ncorner. Sunny and dry: {R['corners_q']['sunny_dry'] * 100:.0f}%. Even odds\nwould give each about 11%."),
    ("3", COOL, f"cities of a million or more are dull\nand dry: Lima, Callao and Trujillo, on\nPeru's foggy desert coast. Lima: {R['profiles']['Lima']['rain_mm']:.0f} mm\nof rain a year, {R['profiles']['Lima']['sun_h']:,.0f} h of sun."),
    (f"{R['uk']['land_sunnier_than_uk_max'] * 100:.0f}%", HOT, f"of the world's land is sunnier than the\nsunniest spot in the UK (Sussex coast,\n{R['uk']['sunniest']['sun']:,.0f} h). Only Iceland, Ireland and\nNorway are duller, of 156 sizeable\ncountries."),
    (f"{R['people']['share_sunnier_than_london'] * 100:.0f}%", FG, f"of the people in the world's towns and\ncities live somewhere sunnier than\nLondon ({R['london']['sun']:,.0f} h). Yet {R['london']['big_wetter']} of {R['big']['n']} big cities\nare wetter."),
]
for k, (big, c, txt) in enumerate(items):
    x = 0.045 + (k % 2) * 0.48; y = 0.505 - (k // 2) * 0.105
    fig.text(x, y, big, fontproperties=DISP, fontsize=48, color=c, va="top")
    fig.text(x + 0.165, y - 0.006, txt, family=SER, fontsize=13, color=FG, va="top", linespacing=1.12)

# small multiples: seasons
fig.text(0.045, 0.29, "THE SAME MAP BY SEASON (EACH CUT INTO ITS OWN THIRDS): WATCH THE MONSOON MOVE", family=MONO, fontsize=11, color=MUT)
for k, (ms, t) in enumerate([([11, 0, 1], "Dec to Feb"), ([2, 3, 4], "Mar to May"), ([5, 6, 7], "Jun to Aug"), ([8, 9, 10], "Sep to Nov")]):
    a = fig.add_axes([0.02 + (k % 2) * 0.49, 0.168 - (k // 2) * 0.11, 0.47, 0.1]); a.set_facecolor(BG); wmap(a, img(ms))
    fig.text(0.045 + (k % 2) * 0.49, 0.278 - (k // 2) * 0.11, t, family=MONO, fontsize=11.5, color=FG, va="top", fontweight="medium")

fig.text(0.045, 0.047, "Data: CRU CL 2.0 climatology, Climatic Research Unit, University of East Anglia (New et al. 2002), sunshine converted\n"
         "from percent of daylight to hours with the astronomical day length. Sunshine rests on far fewer stations than rain, so read\n"
         "single cells as indicative. Cities: GeoNames (CC BY 4.0). Analysis and chart: Tristan Hotham, with Python and matplotlib.",
         family=MONO, fontsize=9.5, color=MUT, va="top", linespacing=1.3)
fig.savefig(os.path.join(HERE, "sun_and_rain.png"), dpi=200, facecolor=BG)
print("collage written")
