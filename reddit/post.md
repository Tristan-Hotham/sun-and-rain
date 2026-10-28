## Title

[OC] Sunshine against rain for every land cell on Earth, 1961 to 1990: only 3% of land is both sunny and wet, the only big cities that are dull and dry are all on Peru's foggy coast, and 84% of the world's land is sunnier than the sunniest spot in the UK

## Body (optional)

I coloured 566,262 land cells (about 18 km across) by which third of the world's land they fall in for yearly sunshine hours and which third for yearly rain. Because cloud brings rain and blocks sun, the corners fill unevenly: sunny and dry covers 21% of land, sunny and wet only 3%. Of 573 cities with a million people or more, just three are dull and dry: Lima, Callao and Trujillo. The UK is near the dull end of the world (only Iceland, Ireland and Norway are duller of 156 sizeable countries) but not especially wet: London is drier than 415 of those 573 cities.

Caveat: sunshine rests on far fewer weather stations than rain, so single cells in data-poor regions are indicative only, and this is a 1961 to 1990 climate.

Interactive version, where you can re-cut the map by month, drag the class breaks and find your town's weather twins: https://tristan-hotham.github.io/sun-and-rain/

## Source comment

Source: CRU CL 2.0 10-minute climatology of mean monthly sunshine (percent of possible) and precipitation, 1961 to 1990, Climatic Research Unit, University of East Anglia (New, Lister, Hulme and Makin 2002, Climate Research 21: 1 to 25; no licence stated, derived products shared with citation); sunshine converted to hours with the FAO-56 astronomical day length; rain cross-checked against WorldClim 2.1 (Fick and Hijmans 2017; summary statistics only); cities from GeoNames cities15000 (CC BY 4.0); country outlines from Natural Earth (public domain).

Tools: Python (pandas, NumPy, SciPy, matplotlib, Pillow, tifffile).

Interactive: https://tristan-hotham.github.io/sun-and-rain/
Blog post: https://blog.tristanhotham.com/2026/10/28/sun-and-rain/
Paper: https://doi.org/10.5281/zenodo.23732580
