"""Step 6. Build the paper PDF: fill code/paper_template.tex with numbers and tables from data/results.json,
write release/paper/Hotham_Sun_and_Rain.tex and compile it with xelatex (figures from step 5).
Run: python3 code/06_paper.py
"""
import json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
R["third"] = "11.1\\%"
R["cities_total"] = f"{R['meta']['cities'] + R['meta']['cities_unmatched']:,}"
R["big"]["n_q_sunny_wet"] = len(R["big"]["q_sunny_wet"])
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Sun_and_Rain"


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct": return f"{v * 100:.0f}\\%"
    if f == "pct1": return f"{v * 100:.1f}\\%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}".replace("-", "$-$")
    if f == "f3": return f"{v:.3f}"
    if f == "raw" and isinstance(v, str) and "\\" in v: return v
    return tex(str(v))


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


MA, MP = R["matrix"]["quant3_area"], R["matrix"]["quant3_pop"]
sl = ["Dull", "Middling", "Sunny"]
rows = ""
for i in (2, 1, 0):
    rows += f"{sl[i]} & " + " & ".join(f"{MA[i][j] * 100:.1f} ({MP[i][j] * 100:.1f})" for j in range(3)) + "\\\\\n"
TM = ("\\begin{table}[tbp]\\centering\\small\\caption{Share of land area (and, in brackets, of the people in matched GeoNames places) in each "
      "tercile class, whole year, per cent. Under independence each cell would hold 11.1\\%.}\\label{tab:matrix}"
      "\\begin{tabular}{lrrr}\\toprule Sunshine & Dry & Middling rain & Wet\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
fr = lambda r: f"{tex(r['name'])} & {tex(r['country'].replace("People's Republic of China", 'China').replace('United States of America', 'United States'))} & {r['sun_h']:,.0f} & {r['rain_mm']:,.0f}\\\\\n"
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{The sunniest and dullest of the " + f"{R['big']['n']}" + " GeoNames places with a million people "
      "or more, annual hours of sunshine and mm of rain, 1961 to 1990.}\\label{tab:cities}"
      "\\begin{tabular}{llrr}\\toprule Place & Country & Sunshine (h) & Rain (mm)\\\\\\midrule\n"
      "\\multicolumn{4}{l}{\\emph{Sunniest}}\\\\\n" + "".join(fr(r) for r in R["big"]["sunniest"][:8]) +
      "\\midrule\\multicolumn{4}{l}{\\emph{Dullest}}\\\\\n" + "".join(fr(r) for r in R["big"]["dullest"][:8]) + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(HERE, "paper_template.tex")).read()
t = re.sub(r"\{\{(?!TABLE_)(.+?)\}\}", sub, t).replace("{{TABLE_MATRIX}}", TM).replace("{{TABLE_CITIES}}", TC)
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.copy(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
print("paper written", r.returncode)
