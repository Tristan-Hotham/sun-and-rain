"""Step 7. Blog post (release/blog/post.html from code/blog_template.html), blog and Zenodo meta files,
and the Zenodo folder (paper, key CSVs, results.json and a code-and-data zip).
Image placeholders {{IMG|file|alt|caption}} are left for the uploader (numbers inside them are filled).
Run: python3 code/07_release.py
"""
import importlib.util, json, os, re, shutil, zipfile

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "03_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
t = open(os.path.join(HERE, "blog_template.html")).read()
t = re.sub(r"\{\{(?!IMG\|)([^}|]+)(\|(\w+))?\}\}", b.sub, t)
assert "{{" not in t.replace("{{IMG|", "")
vis = re.sub(r"<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--"): assert bad not in vis, bad
open(os.path.join(ROOT, "release", "blog", "post.html"), "w").write(t)
for m in re.findall(r"\{\{IMG\|([^|]+)\|", t):
    assert os.path.exists(os.path.join(ROOT, "release", "blog", m)), m
meta = dict(
    title="Sun and rain: the world's sunshine against its rainfall",
    slug="sun-and-rain",
    excerpt=(f"Sunny and dry, sunny and wet, dull and dry, dull and wet: a map of the world's sunshine against its rainfall. "
             f"Only {R['corners_q']['sunny_wet'] * 100:.0f}% of land is both sunny and wet, and {R['uk']['land_sunnier_than_uk_max'] * 100:.0f}% is sunnier than anywhere in the UK."),
    seo_description=f"A bivariate map of sunshine against rain for {R['meta']['cells']:,} land cells, with a city search and a weather twin finder.",
    tags=["climate", "sunshine", "rainfall", "maps", "bivariate map", "data visualisation", "weather", "data"],
    header_alt=(f"Title card reading 'Sun and rain' with 'Sun' in orange and 'rain' in teal on warm paper, above a world map coloured by a nine-colour key "
                f"of sunshine against rain, with the key's corners labelled dull and wet, sunny and wet, dull and dry, sunny and dry. Text: the world's sunshine "
                f"against its rainfall; only {R['corners_q']['sunny_wet'] * 100:.0f}% of land is both sunny and wet; {R['uk']['land_sunnier_than_uk_max'] * 100:.0f}% is sunnier than anywhere in the UK."))
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
for v in meta.values():
    for bad in ("—", "–", "--"): assert bad not in str(v)
json.dump(meta, open(os.path.join(ROOT, "release", "blog", "meta.json"), "w"), indent=2, ensure_ascii=False)

NAME = "Hotham_Sun_and_Rain"
pt = open(os.path.join(ROOT, "release", "paper", NAME + ".tex")).read()
ab = pt.split("\\begin{center}\\textbf{Abstract}\\end{center}")[1].split("\\textbf{Keywords:}")[0].strip()
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("$\\rho$", "rho").replace("km$^2$", "km2").replace("$-$", "-")
assert "\\" not in ab and "$" not in ab, ab
Z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(Z, exist_ok=True)
zmeta = dict(
    title="Sun and Rain: The World's Sunshine Against Its Rainfall. A Bivariate Reading of the CRU CL 2.0 Climatology, 1961 to 1990",
    description_html=f"<p>{ab}</p><p>Interactive version: https://tristan-hotham.github.io/sun-and-rain/. Data and code: https://github.com/Tristan-Hotham/sun-and-rain. Blog post: to follow.</p>"
                     "<p>Text, figures and derived data: CC BY 4.0; code: MIT. Climate data: CRU CL 2.0, Climatic Research Unit, University of East Anglia, New et al. (2002), shared as derived products with citation. Places: GeoNames (CC BY 4.0). Country outlines: Natural Earth (public domain). WorldClim 2.1 is used for summary statistics only and is not redistributed.</p>",
    keywords=["sunshine duration", "precipitation", "bivariate map", "climatology", "CRU CL 2.0", "WorldClim", "climate classification",
              "data visualisation", "weather twins", "United Kingdom"],
    licence="cc-by-4.0",
    related=[
        dict(identifier="https://github.com/Tristan-Hotham/sun-and-rain", relation="issupplementedby", resource_type="software"),
        dict(identifier="https://tristan-hotham.github.io/sun-and-rain/", relation="issupplementedby", resource_type="other"),
        dict(identifier="https://crudata.uea.ac.uk/cru/data/hrg/tmc/", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://doi.org/10.3354/cr021001", relation="isderivedfrom", resource_type="other"),
        dict(identifier="https://www.worldclim.org", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://download.geonames.org/export/dump/", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.naturalearthdata.com", relation="isderivedfrom", resource_type="dataset"),
    ])
json.dump(zmeta, open(os.path.join(Z, "meta.json"), "w"), indent=2, ensure_ascii=False)
shutil.copy(os.path.join(ROOT, "release", NAME + ".pdf"), Z)
for f in ["cities.csv", "countries.csv", "grid_annual_30min.csv", "results.json"]:
    shutil.copy(os.path.join(ROOT, "data", f), Z)
with zipfile.ZipFile(os.path.join(Z, "sun-and-rain_code_and_data.zip"), "w", zipfile.ZIP_DEFLATED) as zf:
    for sub in ("code", "data"):
        for f in sorted(os.listdir(os.path.join(ROOT, sub))):
            p = os.path.join(ROOT, sub, f)
            if os.path.isfile(p) and not f.endswith(".pyc"): zf.write(p, f"sun-and-rain/{sub}/{f}")
    for f in ("README.md", "LICENSE"): zf.write(os.path.join(ROOT, f), f"sun-and-rain/{f}")
words = len(re.sub(r"<[^>]+>", " ", re.sub(r"\{\{IMG\|.*?\}\}", "", t)).split())
print("release files written; post words:", words, "abstract words:", len(ab.split()))
