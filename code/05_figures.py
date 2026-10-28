"""Step 5. Static figures for the paper (release/paper/f_*.png) and the blog post (release/blog/b_*.png),
plus work/header_map.png used by step 4.

Maps are drawn from the grid itself (plate carree, 90N to 60S), no web tiles. Values come from work/grid.npz (step 1),
data/results.json and data/cities.csv. Fonts: FONT_DIR (Fraunces, Source Serif 4, IBM Plex Mono).
Run: FONT_DIR=/path/to/fonts python3 code/05_figures.py
"""
import json, os, sys
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import bivariate as bv

FD = os.environ.get("FONT_DIR", "")
if FD:
    for f in ["IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf"]:
        fm.fontManager.addfont(os.path.join(FD, f))
    plt.rcParams["font.family"] = "IBM Plex Mono"
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
C = pd.read_csv(os.path.join(ROOT, "data", "cities.csv"), keep_default_na=False, na_values=[""])
G = np.load(os.path.join(ROOT, "work", "grid.npz"))
cells, SUN, PRE, WC = G["cells"], G["sun"].astype(float), G["pre"].astype(float), G["wc_ann"]
NC, ROWS = 2160, 900
rows, cols = cells // NC, cells % NC
lat = 90 - (rows + .5) / 6
area = np.cos(np.radians(lat))
PO = os.path.join(ROOT, "release", "paper"); BO = os.path.join(ROOT, "release", "blog"); WO = os.path.join(ROOT, "work")
for d in (PO, BO): os.makedirs(d, exist_ok=True)
BG, FG, MUT, RULE, NOD = "#F7F3EC", "#211C24", "#6A6270", "#DED6C9", "#E4DED3"
HOT, COOL = "#C9661C", "#2E8F8C"
P3 = bv.palette(3)
MON = R["months"]


def style(ax, grid="both"):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(MUT)
    ax.tick_params(colors=FG, length=0)
    if grid: ax.grid(axis=grid, color=RULE, lw=.8); ax.set_axisbelow(True)


def save(fig, name, blog):
    if blog: fig.savefig(os.path.join(BO, f"b_{name}.png"), dpi=160, facecolor=fig.get_facecolor())
    else: fig.savefig(os.path.join(PO, f"f_{name}.png"), dpi=200, facecolor="white")
    plt.close(fig)


def class_image(months=range(12), n=3, breaks=None, bg=(1, 1, 1, 0)):
    ms = list(months); s = SUN[:, ms].sum(1); p = PRE[:, ms].sum(1)
    if breaks is None: breaks = (bv.quantile_breaks(s, area, n), bv.quantile_breaks(p, area, n))
    P = bv.palette(n)
    rgb = np.array([[bv.hex2rgb(P[i][j]) for j in range(n)] for i in range(n)])
    I = bv.classify(s, breaks[0]); J = bv.classify(p, breaks[1])
    img = np.zeros((ROWS * NC, 4)); img[:] = bg
    img[rows * NC + cols, :3] = rgb[I, J]; img[rows * NC + cols, 3] = 1
    return img.reshape(ROWS, NC, 4), breaks


def legend(ax, n=3, P=None, fs=10):
    P = P or bv.palette(n)
    for i in range(n):
        for j in range(n):
            ax.add_patch(plt.Rectangle((i, j), .94, .94, color=P[i][j]))
    ax.set_xlim(-1.9, n + 1.9); ax.set_ylim(-1.1, n + .2); ax.set_aspect(1); ax.axis("off")
    kw = dict(fontsize=fs, color=FG, va="center")
    ax.text(-.12, .45, "dull\nand dry", ha="right", **kw); ax.text(n + .06, .45, "sunny\nand dry", ha="left", **kw)
    ax.text(-.12, n - .55, "dull\nand wet", ha="right", **kw); ax.text(n + .06, n - .55, "sunny\nand wet", ha="left", **kw)
    ax.annotate("", xy=(n, -.45), xytext=(0, -.45), arrowprops=dict(arrowstyle="->", color=MUT))
    ax.text(n / 2, -.85, "more sunshine", ha="center", fontsize=fs, color=MUT)


def worldmap(ax, img, bgc):
    ax.set_facecolor(bgc)
    ax.imshow(img, extent=(-180, 180, -60, 90), interpolation="nearest")
    ax.set_xlim(-170, 180); ax.set_ylim(-57, 84); ax.set_aspect(1); ax.axis("off")


# 1. the world map, whole year, terciles of land area
def fig_map(blog):
    bgc = BG if blog else "white"
    img, br = class_image()
    fig = plt.figure(figsize=(9.5, 5.6) if blog else (7.2, 4.4), facecolor=bgc)
    ax = fig.add_axes([0, .02, 1, .96]); worldmap(ax, img, bgc)
    lx = fig.add_axes([.0, .06, .27, .34]); legend(lx, fs=9 if blog else 7)
    for nm, cc in [("London", "GB"), ("Lima", "PE"), ("Phoenix", "US"), ("Chongqing", "CN"), ("Surabaya", "ID")]:
        r = C[(C.name == nm) & (C.cc == cc)].iloc[0]
        ax.plot(r.lon, r.lat, "o", ms=4, mfc="white", mec=FG, mew=1)
        ax.text(r.lon + 3, r.lat + 1.5, nm, fontsize=9 if blog else 7, color=FG,
                bbox=dict(fc=(1, 1, 1, .7), ec="none", pad=.6))
    save(fig, "map", blog)
    if blog:   # header map (no labels)
        fig = plt.figure(figsize=(8, 3.5), facecolor="none"); ax = fig.add_axes([0, 0, 1, 1]); worldmap(ax, img, (0, 0, 0, 0))
        fig.savefig(os.path.join(WO, "header_map.png"), dpi=150, transparent=True); plt.close(fig)


# 2. seasons: December to February and June to August, each with its own terciles
def fig_seasons(blog):
    bgc = BG if blog else "white"
    fig = plt.figure(figsize=(9.5, 8.2) if blog else (7.2, 6.4), facecolor=bgc)
    for k, (ms, t) in enumerate([([11, 0, 1], "December to February"), ([5, 6, 7], "June to August")]):
        img, br = class_image(ms)
        ax = fig.add_axes([0, .51 - k * .49, 1, .44]); worldmap(ax, img, bgc)
        ax.set_title(t + f": breaks at {br[0][0]:,.0f} and {br[0][1]:,.0f} h, {br[1][0]:,.0f} and {br[1][1]:,.0f} mm",
                     fontsize=10 if blog else 8, color=FG, loc="left", pad=3)
    save(fig, "seasons", blog)


# 3. scatter of big cities
def fig_scatter(blog):
    bgc = BG if blog else "white"
    fig, ax = plt.subplots(figsize=(9.5, 6.6) if blog else (7.2, 5.0), facecolor=bgc); ax.set_facecolor(bgc)
    b = R["breaks"]["quant3"]; xs = [900] + b["sun"] + [4000]; ys = [10] + b["rain"] + [5000]
    for i in range(3):
        for j in range(3):
            ax.add_patch(plt.Rectangle((xs[i], ys[j]), xs[i + 1] - xs[i], ys[j + 1] - ys[j], color=P3[i][j], alpha=.28, lw=0))
    rows_ = R["big"]["rows"]
    for r in sorted(rows_, key=lambda r: r[1] == "GB"):
        i = bv.classify([r[3]], b["sun"])[0]; j = bv.classify([r[4]], b["rain"])[0]; uk = r[1] == "GB"
        ax.scatter(r[3], max(r[4], 10), s=max(10, min(140, r[2] / 1e6 * 9)), c=P3[i][j], edgecolors=FG if uk else MUT, linewidths=1.6 if uk else .4, zorder=3)
    lab = {("London", "GB"): (8, 6), ("Birmingham", "GB"): (-12, -14), ("Lima", "PE"): (8, 0), ("Phoenix", "US"): (8, 4), ("Guayaquil", "EC"): (-10, -14),
           ("Chongqing", "CN"): (-12, 8), ("Surabaya", "ID"): (8, 2), ("Conakry", "GN"): (8, 2), ("Cairo", "EG"): (8, 0), ("Singapore", "SG"): (-12, 8)}
    for r in rows_:
        if (r[0], r[1]) in lab:
            dx, dy = lab[(r[0], r[1])]
            ax.annotate(r[0], (r[3], max(r[4], 10)), xytext=(dx, dy), textcoords="offset points", fontsize=10 if blog else 8, color=FG,
                        ha="left" if dx > 0 else "right", fontweight="medium")
    ax.set_yscale("log"); ax.set_xlim(900, 4000); ax.set_ylim(10, 5000)
    ax.set_yticks([10, 30, 100, 300, 1000, 3000]); ax.set_yticklabels(["10", "30", "100", "300", "1,000", "3,000"])
    ax.set_xticks(range(1000, 4001, 500)); ax.set_xticklabels([f"{v:,}" for v in range(1000, 4001, 500)])
    ax.set_xlabel("hours of sunshine a year", color=MUT); ax.set_ylabel("mm of rain a year (log scale)", color=MUT)
    style(ax); fig.tight_layout(); save(fig, "scatter", blog)


# 4. UK on the world's sunshine scale
def fig_uk(blog):
    bgc = BG if blog else "white"
    fig, ax = plt.subplots(figsize=(9.5, 4.4) if blog else (7.2, 3.4), facecolor=bgc); ax.set_facecolor(bgc)
    e = np.array(R["hist"]["sun_edges"]); h = np.array(R["hist"]["sun"]) * 100
    b = R["breaks"]["quant3"]["sun"]
    for k in range(len(h)):
        c = bv.classify([(e[k] + e[k + 1]) / 2], b)[0]
        ax.bar(e[k], h[k], width=100, align="edge", color=P3[c][0], edgecolor="#BDB4A6", lw=.4)
    top = h.max() * 1.05
    for c in R["uk_cities"]: ax.plot([c["sun_h"]] * 2, [0, top * .9], color="#3B1D47", lw=.8, alpha=.5)
    for nm, v, y in [(R["uk"]["dullest_city"]["name"], R["uk"]["dullest_city"]["sun_h"], 1.0), ("London", R["london"]["sun"], 1.1),
                     (R["uk"]["sunniest_city"]["name"], R["uk"]["sunniest_city"]["sun_h"], 1.2)]:
        ax.plot([v, v], [0, top * y], color=FG, lw=1)
        ax.text(v + (-25 if nm == R["uk"]["dullest_city"]["name"] else 25), top * y, f"{nm} {v:,.0f}", fontsize=10 if blog else 8,
                ha="right" if nm == R["uk"]["dullest_city"]["name"] else "left", va="center", color=FG)
    m = R["sun"]["median"]; ax.plot([m, m], [0, top * 1.0], color=FG, ls=(0, (3, 3)), lw=1)
    ax.text(m + 25, top * 1.0, f"world median {m:,.0f}", fontsize=10 if blog else 8, va="center", color=FG)
    ax.set_xlim(0, 4200); ax.set_ylim(0, top * 1.3); ax.set_xlabel("hours of sunshine a year", color=MUT)
    ax.set_ylabel("% of world land per 100 h", color=MUT)
    ax.set_xticks(range(0, 4001, 1000)); ax.set_xticklabels([f"{v:,}" for v in range(0, 4001, 1000)])
    style(ax, "y"); fig.tight_layout(); save(fig, "uk", blog)


# 5. monthly profiles
def fig_profiles(blog):
    bgc = BG if blog else "white"
    names = ["London", "Mumbai", "Lima", "Singapore"]
    fig, axs = plt.subplots(2, 2, figsize=(9.5, 6.4) if blog else (7.2, 5.0), facecolor=bgc)
    for ax, nm in zip(axs.ravel(), names):
        p = R["profiles"][nm]; ax.set_facecolor(bgc)
        ax2 = ax.twinx(); ax2.set_facecolor(bgc)
        ax2.bar(range(12), p["rain"], color=COOL, alpha=.6, width=.66); ax2.set_ylim(0, 1000)
        ax.plot(range(12), p["sun"], color=HOT, lw=2.4, marker="o", ms=3.5, zorder=5); ax.set_ylim(0, 400)
        ax.set_zorder(ax2.get_zorder() + 1); ax.patch.set_visible(False)
        ax.set_title(f"{nm}: {p['sun_h']:,.0f} h, {p['rain_mm']:,.0f} mm a year", fontsize=11 if blog else 8.5, loc="left", color=FG)
        ax.set_xticks(range(12)); ax.set_xticklabels([m[0] for m in MON])
        style(ax, "y"); ax2.spines[["top", "left", "bottom"]].set_visible(False); ax2.spines["right"].set_color(MUT)
        ax2.tick_params(colors=COOL, length=0); ax.tick_params(axis="y", colors=HOT)
    fig.text(.01, .005, "Orange line: sunshine, hours (left). Bars: rain, mm (right).", fontsize=9 if blog else 7.5, color=MUT)
    fig.tight_layout(rect=(0, .03, 1, 1)); save(fig, "profiles", blog)


# 6. CRU against WorldClim annual rain
def fig_wc(blog):
    ok = ~np.isnan(WC)
    fig, ax = plt.subplots(figsize=(5.6, 5.0), facecolor="white")
    x = np.log10(np.maximum(PRE.sum(1)[ok], 1)); y = np.log10(np.maximum(WC[ok], 1))
    hb = ax.hexbin(x, y, gridsize=70, bins="log", cmap="Greys", mincnt=1, linewidths=0)
    ax.plot([0, 4], [0, 4], color=HOT, lw=1)
    t = [1, 10, 100, 1000, 10000]
    ax.set_xticks(np.log10(t)); ax.set_xticklabels([f"{v:,}" for v in t]); ax.set_yticks(np.log10(t)); ax.set_yticklabels([f"{v:,}" for v in t])
    ax.set_xlim(0, 4.05); ax.set_ylim(0, 4.05)
    ax.set_xlabel("CRU CL 2.0, 1961 to 1990, mm a year"); ax.set_ylabel("WorldClim 2.1, 1970 to 2000, mm a year")
    cb = fig.colorbar(hb, ax=ax, shrink=.8); cb.set_label("cells")
    style(ax, None); fig.tight_layout(); save(fig, "wc", False)


for blog in (True, False):
    fig_map(blog); fig_seasons(blog); fig_scatter(blog); fig_uk(blog); fig_profiles(blog)
fig_wc(False)
print("figures written")
