"""Step 2. All statistics. Reads work/grid.npz and data/cities.csv (step 1).

Writes:
  data/results.json           every number used in the page, paper, blog and collage
  data/countries.csv          area-weighted annual sunshine and rain by country (Natural Earth outlines)
  data/grid_annual_30min.csv  annual sunshine and rain on a half-degree grid (3 by 3 blocks of CRU cells)
  data/sun_q{1..4}.png, data/rain_q{1..4}.png   the full 10-minute monthly grids for the page (see README for the encoding)
  data/cities_page.json       the GeoNames place list for the page search
Run: python3 code/02_analyse.py
"""
import json, os
import numpy as np, pandas as pd
from PIL import Image
from matplotlib.path import Path
from scipy.stats import spearmanr

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
NE = os.environ.get("NE_DIR", "/home/claude/hist/_data3/ne/geojson")
DATA = os.path.join(ROOT, "data")
NR, NC, ROWS = 1080, 2160, 900       # page images cover 90N to 60S (CRU CL 2.0 has no Antarctica)
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
G = np.load(os.path.join(ROOT, "work", "grid.npz"))
cells, SUN, PRE, SUNP, WC = G["cells"], G["sun"].astype(np.float64), G["pre"].astype(np.float64), G["sunp"], G["wc_ann"]
rows, cols = cells // NC, cells % NC
lat = 90 - (rows + .5) / 6; lon = -180 + (cols + .5) / 6
# cell area in km2 on a sphere of radius 6371.0 km
Rk = 6371.0; dl = np.radians(1 / 6)
area = Rk ** 2 * dl * (np.sin(np.radians(lat + 1 / 12)) - np.sin(np.radians(lat - 1 / 12)))
s_ann, p_ann = SUN.sum(1), PRE.sum(1)
C = pd.read_csv(os.path.join(DATA, "cities.csv"), keep_default_na=False, na_values=[""])  # keep Namibia (NA)
R = {}


def wq(x, w, q):
    o = np.argsort(x); cw = np.cumsum(w[o]); cw /= cw[-1]
    return [float(x[o][min(np.searchsorted(cw, qq), len(x) - 1)]) for qq in q]


def wpct(x, w, v):
    """share of weight with value below v"""
    return float(w[x < v].sum() / w.sum())


# == basics
R["meta"] = dict(cells=int(len(cells)), area_km2=float(area.sum()), lat_min=float(lat.min()), lat_max=float(lat.max()),
                 n_sun_rows=int(G["n_sun_rows"]), n_pre_rows=int(G["n_pre_rows"]), cities=int(len(C)),
                 city_pop=float(C["pop"].sum()), period="1961 to 1990", crossval_period="1970 to 2000",
                 cities_unmatched=34191 - int(len(C)), city_cell_km_median=float(C.cell_km.median()),
                 city_cell_km_p95=float(C.cell_km.quantile(.95)))
q = wq(s_ann, area, [.01, .1, .25, 1 / 3, .5, 2 / 3, .75, .9, .99])
qr = wq(p_ann, area, [.01, .1, .25, 1 / 3, .5, 2 / 3, .75, .9, .99])
R["sun"] = dict(min=float(s_ann.min()), max=float(s_ann.max()), p01=q[0], p10=q[1], q1=q[2], t1=q[3], median=q[4], t2=q[5], q3=q[6], p90=q[7], p99=q[8],
                mean=float((s_ann * area).sum() / area.sum()))
R["rain"] = dict(min=float(p_ann.min()), max=float(p_ann.max()), p01=qr[0], p10=qr[1], q1=qr[2], t1=qr[3], median=qr[4], t2=qr[5], q3=qr[6], p90=qr[7], p99=qr[8],
                 mean=float((p_ann * area).sum() / area.sum()))
R["corr"] = dict(spearman=float(spearmanr(s_ann, p_ann)[0]))
imx, imn = int(np.argmax(s_ann)), int(np.argmin(s_ann))


def cellinfo(i):
    d = np.hypot(C.cell_lat - lat[i], (C.cell_lon - lon[i]) * np.cos(np.radians(lat[i])))
    j = int(np.argmin(d.values)); r = C.iloc[j]
    return dict(lat=float(lat[i]), lon=float(lon[i]), sun=float(s_ann[i]), rain=float(p_ann[i]), near=r["name"], near_country=r["country"],
                near_km=float(d.values[j] * 111.2))


R["extremes"] = dict(sunniest=cellinfo(imx), dullest=cellinfo(imn), wettest=cellinfo(int(np.argmax(p_ann))))
# land with less than 1 mm a year at this resolution
R["rain"]["dry_area_share_lt50"] = float(area[p_ann < 50].sum() / area.sum())

# == default classes
FIX3 = dict(sun=[2000, 3000], rain=[500, 1000]); FIX4 = dict(sun=[1750, 2500, 3250], rain=[250, 750, 1500])
R["breaks"] = dict(fixed3=FIX3, fixed4=FIX4, quant3=dict(sun=[q[3], q[5]], rain=[qr[3], qr[5]]),
                   quant4=dict(sun=[q[2], q[4], q[6]], rain=[qr[2], qr[4], qr[6]]))


def classes(sb, rb, s=s_ann, p=p_ann):
    return np.digitize(s, sb), np.digitize(p, rb)


def matrix(sb, rb, w, s=s_ann, p=p_ann):
    S, P = classes(sb, rb, s, p); n = len(sb) + 1
    M = np.zeros((n, n))
    for i in range(n):
        for j in range(n): M[i, j] = w[(S == i) & (P == j)].sum()
    return (M / M.sum()).tolist()      # M[sun class][rain class]


R["matrix"] = dict(fixed3_area=matrix(FIX3["sun"], FIX3["rain"], area), quant3_area=matrix(R["breaks"]["quant3"]["sun"], R["breaks"]["quant3"]["rain"], area))
ci = C.cell.values; cpop = C["pop"].values.astype(float)
R["matrix"]["fixed3_pop"] = matrix(FIX3["sun"], FIX3["rain"], cpop, s_ann[ci], p_ann[ci])
R["matrix"]["quant3_pop"] = matrix(R["breaks"]["quant3"]["sun"], R["breaks"]["quant3"]["rain"], cpop, s_ann[ci], p_ann[ci])
M = np.array(R["matrix"]["fixed3_area"])
R["corners"] = dict(sunny_dry=M[2, 0], sunny_wet=M[2, 2], dull_dry=M[0, 0], dull_wet=M[0, 2])
MP = np.array(R["matrix"]["fixed3_pop"])
MQ = np.array(R["matrix"]["quant3_area"]); MQP = np.array(R["matrix"]["quant3_pop"])
R["corners_q"] = dict(sunny_dry=MQ[2, 0], sunny_wet=MQ[2, 2], dull_dry=MQ[0, 0], dull_wet=MQ[0, 2], middle=MQ[1, 1])
R["corners_q_pop"] = dict(sunny_dry=MQP[2, 0], sunny_wet=MQP[2, 2], dull_dry=MQP[0, 0], dull_wet=MQP[0, 2], middle=MQP[1, 1])
R["corners_pop"] = dict(sunny_dry=MP[2, 0], sunny_wet=MP[2, 2], dull_dry=MP[0, 0], dull_wet=MP[0, 2])

# == countries (rasterise Natural Earth 1:10m)
ne = json.load(open(os.path.join(NE, "ne_10m_admin_0_countries.geojson")))
ctry = np.full(len(cells), -1); names = []
pts = np.c_[lon, lat]
for k, f in enumerate(ne["features"]):
    p = f["properties"]; names.append((p.get("ADM0_A3"), p.get("NAME_EN") or p["NAME"], p.get("ISO_A2_EH") or p.get("ISO_A2")))
    geom = f["geometry"]
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        ring = np.array(poly[0])
        x0, y0 = ring.min(0); x1, y1 = ring.max(0)
        sel = np.where((ctry < 0) & (lon >= x0) & (lon <= x1) & (lat >= y0) & (lat <= y1))[0]
        if not len(sel): continue
        inside = Path(ring).contains_points(pts[sel])
        for hole in poly[1:]:
            inside &= ~Path(np.array(hole)).contains_points(pts[sel])
        ctry[sel[inside]] = k
# coastal cells whose centre misses every outline: take the most common country among neighbours (up to 2 cells)
full = np.full(NR * NC, -1); full[cells] = ctry
miss = np.where(ctry < 0)[0]
for i in miss:
    r, c = rows[i], cols[i]
    nb = full[np.clip(np.arange(r - 2, r + 3), 0, NR - 1)[:, None] * NC + (np.arange(c - 2, c + 3) % NC)[None, :]].ravel()
    nb = nb[nb >= 0]
    if len(nb): ctry[i] = np.bincount(nb).argmax()
R["meta"]["cells_no_country"] = int((ctry < 0).sum())
rows_c = []
for k, (a3, nm, a2) in enumerate(names):
    m = ctry == k
    if m.sum() == 0: continue
    w = area[m]
    rows_c.append(dict(a3=a3, iso2=a2, country=nm, cells=int(m.sum()), area_km2=round(float(w.sum())),
                       sun_h=round(float((s_ann[m] * w).sum() / w.sum())), rain_mm=round(float((p_ann[m] * w).sum() / w.sum())),
                       sun_min=round(float(s_ann[m].min())), sun_max=round(float(s_ann[m].max())),
                       rain_min=round(float(p_ann[m].min())), rain_max=round(float(p_ann[m].max()))))
CT = pd.DataFrame(rows_c).sort_values("sun_h", ascending=False)
CT.to_csv(os.path.join(DATA, "countries.csv"), index=False)
big = CT[CT.area_km2 >= 20000].reset_index(drop=True)
R["countries"] = dict(n=int(len(CT)), n_big=int(len(big)),
                      sunniest=big.head(8)[["country", "sun_h", "rain_mm"]].to_dict("records"),
                      dullest=big.tail(8).iloc[::-1][["country", "sun_h", "rain_mm"]].to_dict("records"),
                      wettest=big.sort_values("rain_mm", ascending=False).head(8)[["country", "sun_h", "rain_mm"]].to_dict("records"),
                      driest=big.sort_values("rain_mm").head(8)[["country", "sun_h", "rain_mm"]].to_dict("records"))
uk = CT[CT.a3 == "GBR"].iloc[0]
R["countries"]["uk_sun_rank"] = int((big.sun_h > uk.sun_h).sum() + 1)
R["countries"]["uk_rain_rank"] = int((big.rain_mm > uk.rain_mm).sum() + 1)

# == the UK
ku = [k for k, n in enumerate(names) if n[0] == "GBR"][0]
mu = ctry == ku; wu = area[mu]
iu = np.where(mu)[0]
R["uk"] = dict(cells=int(mu.sum()), sun_mean=float((s_ann[mu] * wu).sum() / wu.sum()), rain_mean=float((p_ann[mu] * wu).sum() / wu.sum()),
               sun_max=float(s_ann[mu].max()), sun_min=float(s_ann[mu].min()), rain_max=float(p_ann[mu].max()), rain_min=float(p_ann[mu].min()),
               sunniest=cellinfo(int(iu[np.argmax(s_ann[mu])])), dullest=cellinfo(int(iu[np.argmin(s_ann[mu])])),
               wettest=cellinfo(int(iu[np.argmax(p_ann[mu])])), driest=cellinfo(int(iu[np.argmin(p_ann[mu])])),
               sun_rank=R["countries"]["uk_sun_rank"], rain_rank=R["countries"]["uk_rain_rank"], n_big=R["countries"]["n_big"])
R["uk"]["land_sunnier_than_uk_max"] = 1 - wpct(s_ann, area, R["uk"]["sun_max"] + 1e-9) - float(area[s_ann == R["uk"]["sun_max"]].sum() / area.sum())
R["uk"]["land_sunnier_than_uk_mean"] = 1 - wpct(s_ann, area, R["uk"]["sun_mean"])
R["uk"]["land_wetter_than_uk_mean"] = 1 - wpct(p_ann, area, R["uk"]["rain_mean"])
R["uk"]["uk_sunmax_pct"] = wpct(s_ann, area, R["uk"]["sun_max"])
S3, P3 = classes(FIX3["sun"], FIX3["rain"])
R["uk"]["class_fixed3"] = {f"{a}{b}": float(wu[(S3[mu] == a) & (P3[mu] == b)].sum() / wu.sum()) for a in range(3) for b in range(3) if wu[(S3[mu] == a) & (P3[mu] == b)].sum() > 0}
SQ, PQ = classes(R["breaks"]["quant3"]["sun"], R["breaks"]["quant3"]["rain"])
R["uk"]["dull_tercile_share"] = float(wu[SQ[mu] == 0].sum() / wu.sum())
# months
um = (SUN[mu] * wu[:, None]).sum(0) / wu.sum(); ur = (PRE[mu] * wu[:, None]).sum(0) / wu.sum()
R["uk"]["sun_month"] = um.tolist(); R["uk"]["rain_month"] = ur.tolist()

# == cities
C["sun_pct_land"] = [wpct(s_ann, area, v) for v in C.sun_h]   # share of land area duller than this city
C["rain_pct_land"] = [wpct(p_ann, area, v) for v in C.rain_mm]
BIG = C[C["pop"] >= 1_000_000].copy().reset_index(drop=True)
BIG["sun_rank"] = BIG.sun_h.rank(ascending=False, method="min").astype(int)
BIG["rain_rank"] = BIG.rain_mm.rank(ascending=False, method="min").astype(int)
R["big"] = dict(n=int(len(BIG)), min_pop=1_000_000)
cols_b = ["name", "country", "cc", "pop", "sun_h", "rain_mm", "lat", "lon"]
R["big"]["sunniest"] = BIG.sort_values("sun_h", ascending=False).head(10)[cols_b].to_dict("records")
R["big"]["dullest"] = BIG.sort_values("sun_h").head(10)[cols_b].to_dict("records")
R["big"]["wettest"] = BIG.sort_values("rain_mm", ascending=False).head(10)[cols_b].to_dict("records")
R["big"]["driest"] = BIG.sort_values("rain_mm").head(10)[cols_b].to_dict("records")
# corners among big cities (fixed 3 by 3 breaks)
bs, bp = classes(FIX3["sun"], FIX3["rain"], BIG.sun_h.values, BIG.rain_mm.values)
BIG["cls"] = [f"{a}{b}" for a, b in zip(bs, bp)]
qs, qp = classes(R["breaks"]["quant3"]["sun"], R["breaks"]["quant3"]["rain"], BIG.sun_h.values, BIG.rain_mm.values)
BIG["clsq"] = [f"{a}{b}" for a, b in zip(qs, qp)]
R["big"]["class_counts_q"] = BIG.clsq.value_counts().to_dict()
for key, cl, asc in (("q_sunny_wet", "22", False), ("q_sunny_dry", "20", False), ("q_dull_dry", "00", True), ("q_dull_wet", "02", True)):
    R["big"][key] = BIG[BIG.clsq == cl].sort_values("sun_h", ascending=asc)[cols_b].to_dict("records")
wetsun = BIG[BIG.rain_mm >= 1500].sort_values("sun_h", ascending=False)
drydull = BIG[BIG.rain_mm < 500].sort_values("sun_h")
R["big"]["sunny_wet"] = wetsun.head(8)[cols_b].to_dict("records"); R["big"]["n_wet1500"] = int(len(wetsun))
R["big"]["dull_dry"] = drydull.head(8)[cols_b].to_dict("records"); R["big"]["n_dry500"] = int(len(drydull))
R["big"]["n_sunny_wet_cls"] = int((BIG.cls == "22").sum()); R["big"]["n_dull_dry_cls"] = int((BIG.cls == "00").sum())
R["big"]["sunny_wet_cls"] = BIG[BIG.cls == "22"].sort_values("sun_h", ascending=False)[cols_b].to_dict("records")
R["big"]["dull_dry_cls"] = BIG[BIG.cls == "00"].sort_values("sun_h")[cols_b].to_dict("records")
R["big"]["class_counts"] = BIG.cls.value_counts().to_dict()
# all big cities for the scatter chart: [name, cc, pop, sun, rain]
R["big_cc"] = dict(zip(BIG.cc, BIG.country))
R["big"]["rows"] = [[r["name"], r["cc"], int(r["pop"]), int(r["sun_h"]), int(r["rain_mm"])] for _, r in BIG.iterrows()]
# London and UK cities
lon_ = BIG[(BIG.name == "London") & (BIG.cc == "GB")].iloc[0]
R["london"] = dict(sun=float(lon_.sun_h), rain=float(lon_.rain_mm), sun_rank=int(lon_.sun_rank), rain_rank=int(lon_.rain_rank),
                   sun_pct_land=float(lon_.sun_pct_land), rain_pct_land=float(lon_.rain_pct_land),
                   sun_month=C[(C.name == "London") & (C.cc == "GB")].iloc[0][[f"sun{m:02d}" for m in range(1, 13)]].astype(float).tolist(),
                   rain_month=C[(C.name == "London") & (C.cc == "GB")].iloc[0][[f"rain{m:02d}" for m in range(1, 13)]].astype(float).tolist())
R["london"]["big_wetter"] = int((BIG.rain_mm > lon_.rain_mm).sum()); R["london"]["big_duller"] = int((BIG.sun_h < lon_.sun_h).sum())
GBc = C[(C.cc == "GB") & (C["pop"] >= 150_000)].copy()
R["uk_cities"] = GBc[["name", "pop", "sun_h", "rain_mm"]].to_dict("records")
R["uk"]["sunniest_city"] = GBc.sort_values("sun_h", ascending=False).iloc[0][["name", "sun_h"]].to_dict()
R["uk"]["dullest_city"] = GBc.sort_values("sun_h").iloc[0][["name", "sun_h"]].to_dict()
R["uk"]["wettest_city"] = GBc.sort_values("rain_mm", ascending=False).iloc[0][["name", "rain_mm"]].to_dict()
R["uk"]["driest_city"] = GBc.sort_values("rain_mm").iloc[0][["name", "rain_mm"]].to_dict()
# people (GeoNames cities of 15,000 or more) by sunshine
R["people"] = dict(pop=float(cpop.sum()), share_sunnier_than_london=float(cpop[C.sun_h.values > lon_.sun_h].sum() / cpop.sum()),
                   share_wetter_than_london=float(cpop[C.rain_mm.values > lon_.rain_mm].sum() / cpop.sum()),
                   median_sun=wq(C.sun_h.values.astype(float), cpop, [.5])[0], median_rain=wq(C.rain_mm.values.astype(float), cpop, [.5])[0])

# == seasons: where is the sunniest month not in summer?
peak = SUN.argmax(1)    # 0..11
north = lat >= 0
summer = np.where(north, (peak >= 3) & (peak <= 8), (peak <= 2) | (peak >= 9))
R["season"] = dict(peak_outside_summer=float(area[~summer].sum() / area.sum()),
                   peak_outside_summer_tropics=float(area[~summer & (np.abs(lat) < 23.44)].sum() / area[np.abs(lat) < 23.44].sum()),
                   peak_outside_summer_extra=float(area[~summer & (np.abs(lat) >= 23.44)].sum() / area[np.abs(lat) >= 23.44].sum()))
wetpeak = PRE.argmax(1)
R["season"]["wettest_is_dullest"] = float(area[wetpeak == SUN.argmin(1)].sum() / area.sum())
for nm, cc in [("Mumbai", "IN"), ("London", "GB"), ("Lima", "PE"), ("Kolkata", "IN"), ("Singapore", "SG"), ("Cairo", "EG")]:
    r = C[(C.name == nm) & (C.cc == cc)].iloc[0]
    R.setdefault("profiles", {})[nm] = dict(country=r.country, sun=[float(r[f"sun{m:02d}"]) for m in range(1, 13)],
                                             rain=[float(r[f"rain{m:02d}"]) for m in range(1, 13)], sun_h=float(r.sun_h), rain_mm=float(r.rain_mm))
mb = R["profiles"]["Mumbai"]
R["season"]["mumbai_peak_sun"] = MON[int(np.argmax(mb["sun"]))]; R["season"]["mumbai_jul_sun"] = mb["sun"][6]; R["season"]["mumbai_jul_rain"] = mb["rain"][6]
R["season"]["mumbai_max_sun"] = max(mb["sun"]); R["season"]["london_jul_sun"] = R["london"]["sun_month"][6]

# == similarity ("places like this"), same metric as the page
# features: monthly sunshine hours / SDs and square-root monthly rain / SDs; distance = root mean square over 12 months
sd_s = float(np.sqrt(np.average((SUN - np.average(SUN, weights=np.repeat(area[:, None], 12, 1))) ** 2, weights=np.repeat(area[:, None], 12, 1))))
RR = np.sqrt(PRE)
sd_r = float(np.sqrt(np.average((RR - np.average(RR, weights=np.repeat(area[:, None], 12, 1))) ** 2, weights=np.repeat(area[:, None], 12, 1))))
R["similar"] = dict(sd_sun=sd_s, sd_rootrain=sd_r, default_threshold=0.5)


def dist(a_s, a_r, B_s, B_r, flip=False):
    if flip:
        a_s = np.roll(a_s, 6); a_r = np.roll(a_r, 6)
    return np.sqrt((((B_s - a_s) / sd_s) ** 2 + ((np.sqrt(B_r) - np.sqrt(a_r)) / sd_r) ** 2).mean(1))


def twins(name, cc, flip=True, thr=0.5, k=6):
    r = C[(C.name == name) & (C.cc == cc)].iloc[0]; i = int(r.cell)
    d0 = dist(SUN[i], PRE[i], SUN, PRE)
    d = np.minimum(d0, dist(SUN[i], PRE[i], SUN, PRE, True)) if flip else d0
    share = float(area[d <= thr].sum() / area.sum())
    dc = d[C.cell.values]
    cand = C.assign(d=dc)[(C.country != r.country) & (C["pop"] >= 300_000)].sort_values("d")  # nearest, whether or not under the threshold
    seen, out = set(), []
    for _, x in cand.iterrows():
        if x.country in seen: continue
        seen.add(x.country); out.append(dict(name=x["name"], country=x.country, d=float(x.d), pop=int(x["pop"]), flipped=bool(dist(SUN[i], PRE[i], SUN[[int(x.cell)]], PRE[[int(x.cell)]])[0] > x.d + 1e-9)))
        if len(out) >= k: break
    return dict(name=name, country=r.country, share_land=share, twins=out)


R["similar"]["examples"] = {e["name"]: e for e in [twins("London", "GB"), twins("Lima", "PE"), twins("Mumbai", "IN"), twins("Cairo", "EG"), twins("Singapore", "SG")]}

# == cross-check with WorldClim 2.1 precipitation (1970 to 2000)
ok = ~np.isnan(WC)
d = WC[ok] - p_ann[ok]
_, Pw = classes(R["breaks"]["quant3"]["sun"], R["breaks"]["quant3"]["rain"], s_ann[ok], WC[ok])
R["wc"] = dict(cells=int(ok.sum()), pearson=float(np.corrcoef(WC[ok], p_ann[ok])[0, 1]), spearman=float(spearmanr(WC[ok], p_ann[ok])[0]),
               median_diff=float(np.median(d)), median_absdiff=float(np.median(np.abs(d))),
               median_rel_absdiff=float(np.median(np.abs(d) / np.maximum(p_ann[ok], 1))),
               same_tercile=float(area[ok][Pw == PQ[ok]].sum() / area[ok].sum()),
               same_fixed=float(area[ok][np.digitize(WC[ok], FIX3["rain"]) == P3[ok]].sum() / area[ok].sum()),
               mean_cru=float((p_ann[ok] * area[ok]).sum() / area[ok].sum()), mean_wc=float((WC[ok] * area[ok]).sum() / area[ok].sum()))

# == page images: monthly grids as RGB PNGs (3 months each)
# sunshine code = 1 + round(hours / 2); rain code = 1 + round(5 * sqrt(mm)); 0 = no data
SC = np.clip(1 + np.round(SUN / 2), 1, 255).astype(np.uint8)
RC = np.clip(1 + np.round(5 * np.sqrt(PRE)), 1, 255).astype(np.uint8)
assert SUN.max() / 2 + 1 < 255.5 and 5 * np.sqrt(PRE.max()) + 1 < 255.5
ok_rows = rows < ROWS
assert ok_rows.all()
for var, code in (("sun", SC), ("rain", RC)):
    for qd in range(4):
        img = np.zeros((ROWS * NC, 3), np.uint8)
        img[rows * NC + cols] = code[:, qd * 3:qd * 3 + 3]
        Image.fromarray(img.reshape(ROWS, NC, 3), "RGB").save(os.path.join(DATA, f"{var}_q{qd + 1}.png"), optimize=True)
dec_s = (SC.astype(float) - 1) * 2; dec_r = ((RC.astype(float) - 1) / 5) ** 2
R["encoding"] = dict(sun_max_err_month=float(np.abs(dec_s - SUN).max()), rain_max_err_month=float(np.abs(dec_r - PRE).max()),
                     sun_max_err_year=float(np.abs(dec_s.sum(1) - s_ann).max()), rain_max_err_year=float(np.abs(dec_r.sum(1) - p_ann).max()),
                     rain_med_rel_err_year=float(np.median(np.abs(dec_r.sum(1) - p_ann) / np.maximum(p_ann, 1))))

# == page place list
P = C[["name", "cc", "lat", "lon", "pop", "cell", "sun_h", "rain_mm"]].copy()
P["cell"] = (rows[P.cell.values] * NC + cols[P.cell.values])     # full-grid index (row * 2160 + col)
cn = dict(zip(C.cc, C.country))
json.dump(dict(cols=["name", "cc", "lat", "lon", "pop", "gridcell", "sun_h", "rain_mm"],
               rows=[[r.name.replace("\u2013", "-"), r.cc, round(r.lat, 3), round(r.lon, 3), int(r.pop), int(r.cell), int(r.sun_h), int(r.rain_mm)] for r in P.itertuples()],
               countries=cn), open(os.path.join(DATA, "cities_page.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# == half-degree grid CSV for reuse
b_r, b_c = rows // 3, cols // 3
key = b_r * (NC // 3) + b_c
df = pd.DataFrame(dict(key=key, a=area, s=s_ann * area, p=p_ann * area, n=1))
agg = df.groupby("key").sum()
agg["lat"] = 90 - ((agg.index // (NC // 3)) + .5) / 2; agg["lon"] = -180 + ((agg.index % (NC // 3)) + .5) / 2
agg["sun_h"] = (agg.s / agg.a).round(0).astype(int); agg["rain_mm"] = (agg.p / agg.a).round(0).astype(int)
agg[["lat", "lon", "n", "sun_h", "rain_mm"]].rename(columns=dict(n="cru_cells")).to_csv(os.path.join(DATA, "grid_annual_30min.csv"), index=False)

# == monthly world averages (area-weighted) for a chart
R["world_month"] = dict(sun=((SUN * area[:, None]).sum(0) / area.sum()).tolist(), rain=((PRE * area[:, None]).sum(0) / area.sum()).tolist())
# histograms of annual values (area share per bin) for the page's break sliders and the paper
R["hist"] = dict(sun_edges=list(range(0, 4201, 100)), rain_edges=[0, 50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 800, 900, 1000, 1200, 1400, 1600, 1800, 2000, 2500, 3000, 3500, 4000, 5000, 6000, 8000, 10000])
R["hist"]["sun"] = (np.histogram(s_ann, R["hist"]["sun_edges"], weights=area)[0] / area.sum()).tolist()
R["hist"]["rain"] = (np.histogram(p_ann, R["hist"]["rain_edges"], weights=area)[0] / area.sum()).tolist()
R["months"] = MON


def clean(o):
    if isinstance(o, dict): return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating, float)): return round(float(o), 4)
    return o


json.dump(clean(R), open(os.path.join(DATA, "results.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("results written")
for k in ("sun", "rain", "corr", "corners", "corners_pop", "uk", "london", "people", "season", "wc", "encoding"):
    v = R[k]
    if isinstance(v, dict): v = {a: b for a, b in v.items() if not isinstance(b, (list,))}
    print(k, json.dumps(clean(v))[:900])
print("extremes", R["extremes"])
for k in ("sunniest", "dullest", "wettest", "driest", "sunny_wet", "dull_dry"):
    print(k, [(r["name"], r["country"], r["sun_h"], r["rain_mm"]) for r in R["big"][k]])
print("cls", R["big"]["class_counts"], R["big"]["class_counts_q"], R["corners_q"], R["corners_q_pop"])
for k in ("q_sunny_wet","q_sunny_dry","q_dull_dry","q_dull_wet"): print(k, len(R["big"][k]), [(r["name"], r["country"], r["sun_h"], r["rain_mm"]) for r in R["big"][k][:8]])
print(R["uk_cities"])
print("countries", R["countries"]["sunniest"][:5], R["countries"]["dullest"][:5])
for e in R["similar"]["examples"].values():
    print(e["name"], round(e["share_land"], 3), [(t["name"], t["country"], round(t["d"], 2), t["flipped"]) for t in e["twins"]])
