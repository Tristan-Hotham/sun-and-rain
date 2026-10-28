"""Step 1. Read the CRU CL 2.0 10-minute climatology (sunshine percent and precipitation, 1961 to 1990), convert
sunshine percent to hours with the astronomical day length, cross-check precipitation against WorldClim 2.1,
and match GeoNames cities (population 15,000 or more) to their nearest grid cell.

Writes work/grid.npz (land cells only; a temporary file used by the later steps) and data/cities.csv.
Run: python3 code/01_prepare.py
Inputs (read in place, not copied):
  CRU CL 2.0  grid_10min_sunp.dat.gz, grid_10min_pre.dat.gz  (New et al. 2002)
  WorldClim 2.1 wc2.1_10m_prec.zip (Fick and Hijmans 2017), cross-check only, never redistributed
  GeoNames cities15000.zip (CC BY 4.0)
  Natural Earth 1:10m admin 0 countries (public domain), for country names
"""
import gzip, io, json, os, zipfile
import numpy as np, pandas as pd, tifffile

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
D13 = os.environ.get("DATA13", "/home/claude/hist/_data13")
NE = os.environ.get("NE_DIR", "/home/claude/hist/_data3/ne/geojson")
WORK = os.path.join(ROOT, "work"); os.makedirs(WORK, exist_ok=True)
NR, NC = 1080, 2160          # 10 arc-minute global grid, row 0 at 90N, col 0 at 180W
DAYS = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])


def read_cru(name, ncol):
    with gzip.open(os.path.join(D13, name), "rt") as f:
        a = np.loadtxt(f, dtype=np.float32, usecols=range(ncol))
    r = np.floor((90 - a[:, 0]) * 6).astype(int); c = np.floor((a[:, 1] + 180) * 6).astype(int)
    return r * NC + c, a[:, 2:14]


def day_length(lat):
    """Mean astronomical day length (hours) for each calendar month at each latitude (FAO-56 equations 24, 25, 34).
    Sunrise and sunset are taken when the sun's centre is on the horizon, as in FAO-56."""
    lat = np.radians(np.asarray(lat, dtype=np.float64))[:, None]
    out = np.zeros((lat.shape[0], 12))
    doy0 = np.cumsum(np.r_[0, DAYS[:-1]])
    for m in range(12):
        acc = np.zeros(lat.shape[0])
        nd = int(round(DAYS[m])) if m != 1 else 28
        for d in range(nd):
            J = doy0[m] + d + 1
            dec = 0.409 * np.sin(2 * np.pi / 365 * J - 1.39)
            x = np.clip(-np.tan(lat[:, 0]) * np.tan(dec), -1, 1)
            acc += 24 / np.pi * np.arccos(x)
        out[:, m] = acc / nd
    return out


print("reading CRU sunshine ...")
idx_s, sunp = read_cru("grid_10min_sunp.dat.gz", 14)
print("reading CRU precipitation ...")
idx_p, pre = read_cru("grid_10min_pre.dat.gz", 14)
assert len(np.unique(idx_s)) == len(idx_s) and len(np.unique(idx_p)) == len(idx_p)
cells = np.intersect1d(idx_s, idx_p)
os_ = np.argsort(idx_s); op = np.argsort(idx_p)
sunp = sunp[os_][np.searchsorted(idx_s[os_], cells)]
pre = pre[op][np.searchsorted(idx_p[op], cells)]
rows, cols = cells // NC, cells % NC
lat = 90 - (rows + .5) / 6; lon = -180 + (cols + .5) / 6
N = day_length(lat)                                   # hours of possible sunshine per day
sun_h = (np.clip(sunp, 0, 100) / 100 * N * DAYS).astype(np.float32)  # hours of sunshine per month
pre = np.clip(pre, 0, None).astype(np.float32)
print(len(idx_s), "sunshine cells,", len(idx_p), "precipitation cells,", len(cells), "with both")

# WorldClim 2.1 annual precipitation on the same 10-minute grid (cross-check only)
wc = np.zeros(NR * NC, dtype=np.float64); ok = np.ones(NR * NC, bool)
with zipfile.ZipFile(os.path.join(D13, "wc2.1_10m_prec.zip")) as z:
    for m in range(12):
        a = tifffile.imread(io.BytesIO(z.read(f"wc2.1_10m_prec_{m + 1:02d}.tif"))).astype(np.float64).ravel()
        ok &= a > -30000; wc += np.where(a > -30000, a, 0)  # nodata is -32768 (int16)
wc_ann = np.where(ok, wc, np.nan)[cells].astype(np.float32)

np.savez_compressed(os.path.join(WORK, "grid.npz"), cells=cells, sunp=sunp, sun=sun_h, pre=pre, wc_ann=wc_ann,
                    daylen=N.astype(np.float32), n_sun_rows=len(idx_s), n_pre_rows=len(idx_p))

# Cities: GeoNames cities15000 (population 15,000 or more), nearest CRU cell with both variables
cols_g = ["geonameid", "name", "asciiname", "alt", "lat", "lon", "fclass", "fcode", "cc", "cc2", "a1", "a2", "a3", "a4",
          "pop", "elev", "dem", "tz", "mod"]
with zipfile.ZipFile(os.path.join(D13, "cities15000.zip")) as z:
    g = pd.read_csv(z.open("cities15000.txt"), sep="\t", header=None, names=cols_g, quoting=3, dtype={"cc": str, "a1": str},
                    keep_default_na=False, na_values=[""])
g = g[["geonameid", "name", "asciiname", "lat", "lon", "fcode", "cc", "pop", "dem", "tz"]].copy()
g["cc"] = g["cc"].fillna("NA")  # Namibia's ISO code is NA
grid = -np.ones(NR * NC, dtype=np.int64); grid[cells] = np.arange(len(cells))
gr = np.floor((90 - g.lat.values) * 6).astype(int).clip(0, NR - 1); gc = np.floor((g.lon.values + 180) * 6).astype(int) % NC
best = -np.ones(len(g), dtype=np.int64); bestd = np.full(len(g), np.inf)
coslat = np.cos(np.radians(g.lat.values))
for dr in range(-3, 4):          # search up to 3 cells (about 30 to 55 km) for a land cell, nearest by distance
    for dc in range(-3, 4):
        rr = (gr + dr).clip(0, NR - 1); cc = (gc + dc) % NC
        k = grid[rr * NC + cc]
        clat = 90 - (rr + .5) / 6; clon = -180 + (cc + .5) / 6
        dlon = (clon - g.lon.values + 540) % 360 - 180
        d = np.hypot((clat - g.lat.values), dlon * coslat) * 111.2
        upd = (k >= 0) & (d < bestd)
        best[upd] = k[upd]; bestd[upd] = d[upd]
g["cell"] = best; g["cell_km"] = bestd.round(1)
print("cities", len(g), "matched", (best >= 0).sum())
g = g[g.cell >= 0].copy()

# country names from Natural Earth (ISO A2; a few territories use ISO_A2_EH)
ne = json.load(open(os.path.join(NE, "ne_10m_admin_0_countries.geojson")))
cn = {}
for f in ne["features"]:
    p = f["properties"]
    for key in ("ISO_A2", "ISO_A2_EH", "WB_A2"):
        v = p.get(key)
        if v and v not in ("-99", "-1") and v not in cn: cn[v] = p.get("NAME_EN") or p["NAME"]
g["country"] = g.cc.map(cn).fillna(g.cc)
ci = g.cell.values
g["sun_h"] = sun_h[ci].sum(1).round(0); g["rain_mm"] = pre[ci].sum(1).round(0)
for m in range(12):
    g[f"sun{m + 1:02d}"] = sun_h[ci, m].round(1)
for m in range(12):
    g[f"rain{m + 1:02d}"] = pre[ci, m].round(1)
g["cell_lat"] = lat[ci].round(4); g["cell_lon"] = lon[ci].round(4)
g = g.sort_values("pop", ascending=False)
g.drop(columns=["asciiname"]).to_csv(os.path.join(ROOT, "data", "cities.csv"), index=False)
print("data/cities.csv", len(g))
