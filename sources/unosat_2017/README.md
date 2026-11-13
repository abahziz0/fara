# UNOSAT — destroyed areas in northern Rakhine, 2017

`Damage_Analysis_Rakhine_20171011_shp.zip` is an unmodified copy of the shapefile published by UNOSAT on the
Humanitarian Data Exchange:

- Title: Destroyed areas in Buthidaung, Maungdaw, and Rathedaung Townships of Rakhine State in Myanmar
- Page: https://data.humdata.org/dataset/destroyed-areas-in-buthidaung-maungdaw-and-rathedaung-townships-of-rakhine-state-in-myanmar-2727
- File: https://unosat-maps.web.cern.ch/unosat-maps/MM/CE20130326MMR/Damage_Analysis_Rakhine_20171011_shp.zip
- Downloaded: 13 November 2026 · SHA-256 `654e7213b4face4f6933d3c3a342a605a21029ececd0f9694e3aacefded3a497`
- Licence: Creative Commons Attribution Share-Alike (CC BY-SA). Credit: UNOSAT.

It holds 1,862 zones of destroyed buildings seen in satellite imagery collected between 31 August and
11 October 2017, the outline of the 4,820 km² area analysed, and satellite fire detections. UNOSAT marks every
zone "not yet field validated".

`tools/match_unosat.py` matches these zones to FARA's villages. Its outputs (`status_unosat_2017.json`,
`status_unosat_2017.csv`, `unosat_2017_zones.geojson`) are derived from this data and carry the same licence.
