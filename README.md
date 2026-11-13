# FARA — The Arakan Village Name Archive

Data scraped from **https://map.rohingyakhobor.com/map** (Rohingya Khobor — Arakan Maps project) on **2026-07-02**.

> *Fará — "village" in the Rohingya language. Every village had a name. FARA exists so those names are never erased.*

The dataset contains **1,023 villages** across 4 townships of Arakan (Rakhine State, Myanmar), each with its name in multiple languages/scripts and exact coordinates. Built to support **research, reporting, documentation, and evidence-based understanding** of Rohingya village names and locations.

## The Website — `fara.html`

A self-contained, single-file archive explorer styled as a futuristic intelligence console. Open it in any browser or host it anywhere as a static file (internet needed for map tiles/fonts; the data itself is embedded).

**Features:**
- **Command palette** (`⌘K` / `Ctrl+K`) — every action and village one keystroke away
- **Trilingual instant search** (`/`) — Rohingya, English, Burmese names + tracts
- **Village dossiers** — record ID (`FARA-0043`), Rohingya-first names, coordinates with copy, Google Maps link, shareable deep links (`#v=<id>`), copy-as-text record, 6 nearest villages with distances
- **Satellite imagery in every dossier** — loads automatically when a village is opened. Requires internet; no API key or server.
  - **Clear** — the sharpest free image of the village (Esri World Imagery, ≈30–60 cm), stitched from native zoom-18 tiles and labelled with its real capture date, age, resolution and source.
  - **History** — every earlier capture of the same spot from the Esri Wayback archive (typically 8–10 dates back to 2010), each with its capture date.
  - **Latest** — the newest Copernicus Sentinel-2 pass that is cloud-free *over the village itself* (checked against the scene-classification band, not the scene average), contrast-stretched and lightly sharpened. 10 m per pixel: recent, not sharp. Step to older/newer passes with ◂ ▸.
  - **Full-screen viewer** — click either image to zoom and pan. **Clear** tab has a capture-date timeline; **Latest** tab has a pass timeline with clear/cloudy markers; **Compare** tab is a draggable before/after swipe between any two capture dates. `←` `→` step through dates, `Esc` closes.
  - Older captures are often hazy with a green-blue cast; the viewer applies a gentle display-only colour correction to them (the imagery itself is untouched).
  - Sources: Esri World Imagery + Wayback, Earth Search STAC (Element 84) + public Sentinel-2 cloud-optimised GeoTIFFs read in the browser with geotiff.js.
- **Registry table** (`R`) — full sortable/filterable archive with CSV export of any filtered subset
- **Measure tool** (`M`) — click points on the map to measure distances
- **Watchlist** — bookmark villages (persisted locally)
- **Telemetry** (`T`) — records per township, name-coverage rings, verified-location count
- **Optics** — dark Grid / satellite Orbital basemaps, graticule overlay (`G`), permanent labels at high zoom
- **Live status bar** — cursor coordinates, zoom, villages in view, scrolling name-preservation ticker, Myanmar time (MMT), AB Aziz credit
- **Orbital (satellite) basemap by default**, Grid dark map one click away; loads straight into the map with a scan-line fly-in (no intro or loading screen); custom FARA favicon
- **Mission modal** credits the project: A project by AB Aziz · ab@rohingya.ro
- **Discover** (`D`) — radar-sweep to a random village
- **Map Art Studio** (`P`, "Map Art" in the top bar, or the Map Art tab on phones) — printable poster art for any village at 2400×3600 px (8″×12″ @ 300 DPI).
  - **Two steps:** choose a village, pick a style. The poster draws itself (about a second) and redraws live as options change. Opening it from a village record starts with that village.
  - **What is drawn:** roads, tracks and footpaths, railways, rivers, streams and drains, sea and lakes, woodland, wetland and farmland, **houses and other buildings**, **landmarks** (places of worship, schools, clinics, jetties…) and the **neighbouring villages by their Rohingya names** — wherever OpenStreetMap has them mapped.
  - **More options** (collapsed by default): 5 shapes (Classic, Full, Circle, Heart, "2 Homes" with any city in the world), 4 zoom levels, marker, toggles for names and for houses/landmarks, the words on the poster, exact coordinates. 6 colour styles.
  - **Data:** OpenFreeMap vector tiles (OpenStreetMap data served from a CDN), decoded in the browser with a small built-in reader; falls back to the Overpass API (three servers asked at once) if the tiles cannot be reached. The OpenStreetMap credit is given in the About text.
  - PNG download, print, and share. Every share carries a caption about the village (names, township, tract, location), a line about the archive and the village's link. WhatsApp opens with the caption; Facebook opens with the village link; Instagram and TikTok get the poster through the phone's share sheet, or on a computer the poster is saved and the caption copied. Fixed "by AB Aziz" credit. Requires internet.
- **Built for phones** (screens up to 760 px wide) — not a shrunk desktop:
  - floating search bar that opens a full-screen search with recently opened villages
  - bottom tab bar: Map · Records · Discover · Map Art · Menu
  - the village record is a draggable sheet with three stops (peek / half / full); the map re-centres the village in the space above it, and tapping the map tucks the sheet away
  - Menu (townships, optics, tools) is a pull-down-to-dismiss sheet; dialogs become full pages; the records table shows three readable columns
  - imagery viewer goes full screen with its tabs and date timeline at thumb height
  - larger tap targets, forgiving marker taps, safe-area insets for notches, and "Add to Home Screen" support (`manifest.webmanifest` + icons)
- Keyboard shortcuts overlay (`?`), reduced-motion support

`fara_template.html` is the editable source. After any edit, rebuild everything with:

```
python3 build.py
```

This writes `fara.html`, one page per village, the township and A–Z index pages, `sitemap.xml`, `robots.txt`, `llms.txt` and `sw.js`.

### Pages for search engines, AI assistants and link previews

- **One page per village** at `/village/<id>-<name>/` (1,023 pages): names in three languages, location, a satellite image, nearby villages, a short question-and-answer section, how to cite, and a button into the interactive map. Each has its own title, description, link preview and structured data (`Place`, `BreadcrumbList`, `FAQPage`).
- **Township pages** at `/township/<name>/` and an **A–Z index** at `/villages/`.
- `sitemap.xml` (1,029 URLs), `robots.txt` (search engines and AI crawlers welcome), `llms.txt` (a plain summary of the archive and its data for AI assistants), and `Dataset` + `WebSite` structured data on the home page.
- The record panel's **Share Link** and Map Art captions point to the village's own page, so shared links show that village's name.

### Logo, site icon and share pictures

The logo is the word *fara* in Hanifi Rohingya (𐴉𐴝𐴌𐴝); the dot of its first letter is drawn as a village point. It is stored as outlines in `tools/logo.json` (from Noto Sans Hanifi Rohingya Bold, SIL Open Font License), so it looks the same everywhere without needing the font.

```
python3 tools/build_share.py
```

writes the site icons (`favicon.svg`, `favicon.ico`, `icon-192.png`, `icon-512.png`, `apple-touch-icon.png`), `logo.svg` / `logo.png`, the site's share picture `og.png`, one share picture per village (`share/img/v/<id>.png`: names, township, tract, coordinates and a locator map), and one page and picture per village poster (`art/<id>/`, `share/img/art/<id>.png`). A poster shared from Map Art links to `/art/<id>`, which previews as a poster and opens Map Art on that village. Needs Google Chrome and Pillow; takes about five minutes. Run it again when village data changes.

### 2017 destruction (UNOSAT)

Every village carries what UNOSAT's satellite analysis of 31 August – 11 October 2017 marked at or near it.

- **Four results:** *destroyed* (the village's point is inside a UNOSAT destroyed zone, or at least 1 hectare within 300 m is marked destroyed), *destruction nearby* (a zone within 500 m, but less than that), *none detected*, and *not assessed* (outside the area UNOSAT analysed: all of Sittwe and a few villages elsewhere). Counts: 243 / 81 / 596 / 103.
- **"None detected" is not "standing":** the imagery ends on 11 October 2017, some areas were under cloud, destruction continued afterwards, and UNOSAT did not validate the zones on the ground. A village is one point and the zones are outlines, so the match is by distance.
- **On the site:** a status block on each village record with a *See before and after* button, which opens the swipe view on the captures either side of the 2017 imagery with UNOSAT's zones outlined in yellow; a *2017 zones* toggle in the imagery viewer; a *2017 Destruction* card on the map to filter villages and colour them by status; a registry column and CSV fields; a section and a question on every village page; a line in the PDF record.
- **Files:** `status_unosat_2017.json` / `.csv` (per village: status, distance to the nearest zone, hectares marked destroyed within 300 m, imagery dates, confidence), `unosat_2017_zones.geojson` (the 1,862 zones), `tools/match_unosat.py` (reproduces the match), `sources/unosat_2017/` (UNOSAT's original file and its provenance).
- **Licence:** UNOSAT's data is CC BY-SA, so these derived files are CC BY-SA 4.0 too. Credit UNOSAT.

### Community, research and offline

- **Suggest a name or correction** on every village record. Suggestions are never published directly; they go to the archive's keeper for review. Each suggestion is posted to FormSubmit (`SUGGEST_ENDPOINT` in the template), which forwards it by email to the keeper's inbox; if the visitor is offline or delivery fails it is kept on the device and sent later. With `SUGGEST_ENDPOINT` empty, the visitor's email app opens with the suggestion written out instead.
- **Area tool** (`A`): outline an area on the map to list the villages inside it, then filter the registry to them and export CSV.
- **PDF Record**: a one-page printable record for any village (names, location, both satellite images with their dates, nearby villages, source and citation).
- **Works offline**: a service worker saves the app, and the map tiles you have looked at, on the device. Pages load from the network when online, so updates arrive normally.
- **Usage statistics**: Vercel Web Analytics (no cookies, no personal data). Enable it once under the project's Analytics tab in Vercel.

## Coverage

| Township   | Villages | District |
|------------|---------:|----------|
| Maungdaw   | 378 | Maungdaw |
| Buthidaung | 338 | Maungdaw |
| Rathedaung | 214 | Sittwe |
| Sittwe     | 93  | Sittwe |

- **290** distinct village tracts (township + tract pairs).
- 298 villages missing a Rohingya name; 378 missing a Burmese-script name (blank in the source).
- **1 record with unverified coordinates** (see Corrections).

## Corrections applied to the source data

| ID | Village | Correction |
|----|---------|-----------|
| 1025 | Fawyazi Para | Township/district were null → assigned **Maungdaw** (source layer: "Maungdaw Village") |
| 338 | Four Miles South | Township/district were null → assigned **Buthidaung** (source layer: "Buthidaung Village"). Source coordinates plot in Melbourne, Australia — clearly erroneous, so flagged `coord_status: unverified`. The record is preserved and searchable but not plotted on the map. |

Records with data issues are **flagged, never silently altered**.

## Fields

| Field | Description |
|-------|-------------|
| `id` | Internal ID from the source map (shown as `FARA-<id>` in the app) |
| `name` | Romanized / official (MIMU-style) English name |
| `rohingya_name` | Name in Rohingya (Rohingyalish) |
| `village_name_mmr` | Name in Burmese script (Myanmar) |
| `lat` / `lng` | Coordinates, decimal degrees WGS84 |
| `village_tract` | Village tract |
| `township` / `district` | Administrative divisions |
| `layer` / `layer_color` | Source map layer info |
| `coord_status` | `unverified` when source coordinates are known-bad (only id 338) |
| `pcode_village` | Official MIMU village place code (6 digits, e.g. `197894`). Empty when there is none or it is not confirmed yet |
| `pcode_village_tract` | MIMU village tract code (e.g. `MMR012009034`), the tract MIMU itself places the village in |
| `pcode_township` / `pcode_district` | MIMU township and district codes (e.g. `MMR012009`, `MMR012D002`) |
| `mimu_village_name` / `mimu_village_tract_name` | MIMU's official spelling of the village and its tract |
| `mimu_village_status` / `mimu_village_tract_status` | `active`, or `inactive_…` when MIMU has removed the place from its list or reclassified it to a ward or town |
| `pcode_match` | How sure the village code is: `exact`, `strong`, `unconfirmed` (a likely code awaits a human check, so none is given) or `none` (no official code exists) |

## Official place codes (MIMU P-codes)

Every record carries the place codes the United Nations and aid agencies use for Myanmar, so it can be linked to their datasets.

- **Source:** MIMU Place Codes, Release 9.7 (22 January 2026), Rakhine workbook, from https://themimu.info/place-codes. © Myanmar Information Management Unit; free to use with attribution, not for sale or commercial use.
- **Result:** 1,017 of 1,023 villages have a village code (995 exact, 22 strong). 4 are unconfirmed (ids 716, 796, 800, 802) and 2 have no official code (ids 338, 1025). All 290 named village tracts have a code.
- **How they were matched:** 1,016 records sit on exactly the same coordinates as a MIMU village point, one village each; name and tract were then compared. The Rohingya name was not used for matching. A code is only given when the match is exact or strong; nothing is guessed.
- **Inactive in MIMU:** 72 matched villages and 5 tracts are marked inactive by MIMU (removed from the official list, or reclassified to a town ward or town). Their codes are kept and the status is shown.
- **Files:** `pcodes.json` and `pcodes.csv` hold the full match for every record (tier, method, distance, MIMU names); `pcodes_review.csv` lists the records a person should look at.
- **To update:** edit or regenerate `pcodes.json`, then run `python3 tools/add_pcodes.py` (writes the codes into the data files) and `python3 build.py`.

## Files

| File | Description |
|------|-------------|
| `fara.html` | **The archive website** — single self-contained file |
| `fara_template.html` | Editable source template (data placeholder inside) |
| `arakan_villages.json` | All 1,023 villages, pretty JSON (sorted district → township → tract → name) |
| `arakan_villages.csv` | Spreadsheet-friendly CSV |
| `arakan_villages.geojson` | Point FeatureCollection (verified coordinates only) — QGIS/Leaflet/Mapbox ready |
| `summary.json` | Counts, coverage, corrections log |
| `pcodes.json`, `pcodes.csv`, `pcodes_review.csv` | Official MIMU place codes matched to every record, and the records needing review |
| `tools/add_pcodes.py` | Writes the place codes from `pcodes.json` into the data files |
| `build.py` | Builds the whole static site from the template and the dataset |
| `village/`, `township/`, `villages/` | Generated record and index pages |
| `pages.css` | Styles for the generated pages |
| `sitemap.xml`, `robots.txt`, `llms.txt`, `og.png` | Search engine, AI assistant and link-preview files |
| `sw.template.js`, `sw.js` | Offline support (the second is generated) |
| `tools/build_share.py`, `tools/logo.json` | Builds the logo, icons and share pictures |
| `favicon.svg`, `favicon.ico`, `logo.svg`, `logo.png` | Site icon and logo |
| `share/img/`, `art/` | Generated share pictures and poster pages |
| `manifest.webmanifest`, `icon-192.png`, `icon-512.png`, `apple-touch-icon.png` | Home-screen install support for phones |
| `by_township/` | Per-township `.json` + `.csv` splits |
