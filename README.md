# Sun and rain: the world's sunshine against its rainfall

A bivariate world map of annual sunshine hours against annual rainfall, 1961 to 1990, from the CRU CL 2.0 10 arc-minute climatology. The interactive page lets you re-cut the map by month or season, switch between three by three and four by four classes, choose equal-land (tercile or quartile) or fixed breaks or drag your own, hover over the legend to isolate a class, search 34,167 towns and cities, and find each place's "weather twins" anywhere on Earth.

**Interactive version:** https://tristan-hotham.github.io/sun-and-rain/

**Paper and archived release:** https://doi.org/10.5281/zenodo.23732580

A data study by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349).

## Headline results

- 566,262 land cells (all land outside Antarctica, 137 million km²) have both sunshine and rain. Annual sunshine runs from 310 hours (South Sandwich Islands) to 4,027 hours (Nubian Desert, northern Sudan); the land median is 2,474 hours. Rain runs from nothing to 9,700 mm (Khasi Hills, Meghalaya); the median is 553 mm.
- Sun and rain are negatively related across cells (Spearman's rho = -0.24). With tercile breaks, the sunny and dry corner holds 21.0% of land and the sunny and wet corner only 3.0%, against 11.1% each if they were unrelated. Dull and dry holds 7.3%, mostly subarctic; dull and wet 12.4%.
- People (in GeoNames places of 15,000 or more) concentrate in the dull and wet corner (26.1%); only 0.4% live in dull and dry. Of 573 cities of a million or more, only Lima, Callao and Trujillo, all on the desert coast of Peru, are dull and dry.
- Sunniest big city: Phoenix (3,817 h). Dullest: Guayaquil (1,154 h), then six cities of south-west China, then Birmingham (1,356 h).
- The UK averages 1,319 hours and 1,121 mm. Only Iceland, Ireland and Norway are duller among 156 countries with 20,000 km² of land or more. The sunniest UK cell (near Bognor Regis, 1,774 h) is outdone by 84% of the world's land; every UK cell is in the dullest tercile. London (1,454 h, 628 mm) is drier than 415 of the 573 big cities; 96% of the people in the study's places live somewhere sunnier.
- CRU and WorldClim 2.1 annual rain agree closely (Pearson's r = 0.977; same rain tercile on 93.5% of land). Sunshine could not be checked independently.

Every number is in `data/results.json`, which the page, paper, blog and collage are built from.

## Files

| Path | What it is |
|---|---|
| `index.html` | The interactive page. Results and `code/bivariate.js` are embedded; the monthly grids and the place list are loaded from `data/`. |
| `header.png` | Social card (1200 by 630). |
| `data/sun_q1.png` to `sun_q4.png`, `data/rain_q1.png` to `rain_q4.png` | The full 10 arc-minute monthly grids, 2160 by 900 pixels covering 90N to 60S (row 0 at 90N, column 0 at 180W, 1/6 degree per pixel). Each image holds three months in its red, green and blue channels (q1 = January to March, and so on). Value 0 = no data. Sunshine hours = (value - 1) × 2. Rain mm = ((value - 1) / 5)². |
| `data/cities.csv` | GeoNames places of 15,000 or more (34,167) with the nearest grid cell, distance to it, annual and monthly sunshine hours and rain. |
| `data/cities_page.json` | Compact place list for the page search. |
| `data/countries.csv` | Area-weighted annual sunshine and rain by country (Natural Earth outlines), with ranges. |
| `data/grid_annual_30min.csv` | Annual sunshine and rain on a half-degree grid (area-weighted means of three by three CRU cells). |
| `data/results.json` | Every number used anywhere. |
| `code/01_prepare.py` | Reads CRU CL 2.0 sunshine and precipitation, converts sunshine to hours, reads WorldClim precipitation for the cross-check, matches GeoNames places to cells. Writes `work/grid.npz` (temporary). |
| `code/02_analyse.py` | All statistics, country rasterisation, weather twins, page images and tables. |
| `code/bivariate.js` | Reusable bivariate map logic for the page (and the planned UK companion): OKLab corner palette, weighted quantile breaks, classing and painting, Web Mercator reprojection of a lat/lon raster, interactive legend with corner words, draggable break sliders, twelve-month profile distance. |
| `code/bivariate.py` | The same palette and break logic in Python, used by the figures, header and collage. |
| `code/03_build_site.py` | Fills `code/page_template.html` to make `index.html` and checks facts stated in words. |
| `code/04_header.py` | Renders `header.png` with Playwright (run after step 5). |
| `code/05_figures.py` | Static figures for the paper and blog. |
| `code/06_paper.py` | Builds the paper PDF from `code/paper_template.tex` with xelatex. |
| `code/07_release.py` | Blog post, blog and Zenodo metadata, Zenodo folder. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `release/` | Paper PDF and source, blog post and figures, Zenodo files. |

## Method in brief

- **Sunshine hours.** CRU percentage of possible sunshine ÷ 100 × mean astronomical day length for the month at the cell's latitude (FAO-56 equations, sun centre on the horizon) × days in the month.
- **Classes.** Default three by three, breaks at terciles of land area (cells weighted by area). Options: four by four (quartiles), fixed breaks (2,000 and 3,000 h; 500 and 1,000 mm a year, scaled for seasons and months), or breaks the reader drags.
- **Palette.** Four corners (dull and dry #EDE8DF, sunny and dry #EB8A2E, dull and wet #2E8F8C, sunny and wet #3B1D47), bilinear mixing in OKLab.
- **Places.** GeoNames cities15000, nearest land cell within three cells (median 6.7 km). Countries: Natural Earth 1:10m outlines by cell centre.
- **Weather twins.** Root mean square over twelve months of standardised differences in sunshine hours and in the square root of rain; optional six-month flip for the other hemisphere. Default limit 0.5.
- **Cross-check.** WorldClim 2.1 precipitation, 1970 to 2000, same grid.

## Known limits

- Sunshine rests on far fewer stations than rain and was filled from cloud cover where it was not observed (New et al. 2002). It is least certain in Africa, South America, central Asia and the Arctic, and there was no second sunshine grid to check against.
- 1961 to 1990 is a past climate. Sunshine and rain have changed since.
- 10 arc-minute cells (about 18 km) smooth mountains and coasts; coastal cities can pick up a cell a few kilometres inland.
- City-weighted shares use GeoNames populations of places of 15,000 or more; some districts are listed alongside their city.
- On the page, grids are stored as images: up to 9 hours and 25 mm of error in a cell's yearly total. Figures in the text and tables use exact values.

## Sources and licences

- CRU CL 2.0, Climatic Research Unit, University of East Anglia: New, M., Lister, D., Hulme, M. and Makin, I. (2002) A high-resolution data set of surface climate over global land areas. Climate Research 21: 1 to 25. https://crudata.uea.ac.uk/cru/data/hrg/tmc/ . No licence is stated with the files; this repository shares derived grids and aggregates with citation.
- WorldClim 2.1: Fick, S.E. and Hijmans, R.J. (2017) WorldClim 2. International Journal of Climatology 37(12): 4302 to 4315. Used for summary statistics only; not redistributed.
- GeoNames cities15000 (CC BY 4.0), https://download.geonames.org/export/dump/
- Natural Earth 1:10m admin 0 countries (public domain).
- Day length: Allen, R.G. et al. (1998) FAO Irrigation and Drainage Paper 56.
- Base map tiles on the page © Esri, HERE, Garmin, © OpenStreetMap contributors, and the GIS user community.

Text, figures and derived data: CC BY 4.0. Code: MIT (see `LICENSE`).

## How to rerun

Inputs are read in place from the paths at the top of each script (`DATA13` for the CRU, WorldClim and GeoNames files; `NE_DIR` for Natural Earth). Python 3 with numpy, pandas, scipy, matplotlib, Pillow and tifffile; Playwright for the header; xelatex for the paper.

```
python3 code/01_prepare.py
python3 code/02_analyse.py
python3 code/03_build_site.py
FONT_DIR=path/to/fonts python3 code/05_figures.py
FONT_DIR=path/to/fonts python3 code/04_header.py
python3 code/06_paper.py
python3 code/07_release.py
```

## Citation

Hotham, T. (2026) Sun and rain: the world's sunshine against its rainfall. A bivariate reading of the CRU CL 2.0 climatology, 1961 to 1990. Zenodo. https://doi.org/10.5281/zenodo.23732580

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
