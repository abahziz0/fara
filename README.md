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

### Finding, reading the past, and taking it with you

- **Browse without typing** (`B`, or the Browse button in the search bar): township → village tract → village. For people who know where a village is but not how its name is spelt in Latin letters. On a computer the map moves to the tract as you choose it.
- **Borders** (`O`, under Optics → Overlays): township and village-tract boundaries, with tract names once zoomed in. Tapping a tract name lists its villages; the tract of the open village is outlined. Each border is drawn once (not once per side). Source: UN OCHA's *Myanmar Subnational Administrative Boundaries* (COD-AB, source MIMU), **CC BY-IGO**, about 1:250,000, so approximate. MIMU's own download of the same boundaries may not be used on an online platform without written agreement, which is why the openly licensed COD-AB edition is used. Built by `tools/build_boundaries.py` into `boundaries.json`.
- **Imagery by year** (`Y`, the "Imagery" bar at the bottom of the map; the clock button on phones): shows the whole map in the last edition of Esri's World Imagery published in each year from 2014. An edition holds the newest pictures Esri had at the time, so a picture can be older than its edition; the capture date at the centre of the map is looked up and shown when zoomed in.
- **Instant capture dates**: the dates of every earlier satellite capture of every village are looked up ahead of time by `tools/build_captures.py` (about 34,000 requests to Esri's Wayback archive, 45 minutes) and saved in `captures.json`, so the timeline in a village record appears at once. The site then only asks Esri whether anything newer has been published. Run the script again every few months (`--refresh`); it only asks for what is new.
- **Download an image** (in the imagery viewer): what is on screen as one picture, with the village's names, the capture date, a scale bar, the sources and a link. In Compare it holds both dates of the same ground.
- **Annotate** (in the imagery viewer): arrows, circles, boxes, freehand lines and short notes. Marks are stored by latitude and longitude, so they stay on the same building when the date changes, and they are part of the downloaded image (which says the marks were added by its maker). Nothing is uploaded.
- **Embed**: every village has a small card at `/embed/<id>/` for use in an `<iframe>` on another site (button in the village record, and the code is on each village page). No cookies, no tracking.
- **Printable gazetteers**: one booklet per township at `/township/<name>/gazetteer/`, designed for A4: cover, how to read it, a key map of the village tracts, every village by tract (Rohingya name, official name, Burmese, coordinates, place code, 2017 status) with a small map of each tract, an A–Z index of both Rohingya and official names, and a page of ruled lines for names it is missing. `python3 tools/build_pdfs.py` prints them to `downloads/fara-gazetteer-<township>.pdf` with Chrome.
- **Stories** at `/stories/`: accounts where the map moves as you scroll. Two kinds, one engine (`stories.js`, `stories.css`):
  - *Written stories*: one file each in `content/stories/` (text plus what the map should show at each step). `{{tokens}}` in the text are filled with numbers from the data at build time, so a story cannot drift from the archive.
  - *Village stories*: one for each of the 324 villages where UNOSAT mapped destruction at or beside the village in 2017, at `/stories/<id>-<name>/`. They are generated: where the village is, the last satellite picture from before August 2017, the first one after with UNOSAT's finding, the newest picture, the township's numbers, and links on. The text states dates and UNOSAT's figures only; it never describes what a picture shows.
  - *The index* at `/stories/` lists every story by township, with a name filter, township and finding switches, and a small map whose dots are links.
  - *Found by search engines*: every story has its own title and description (no two alike), one H1, Article and Breadcrumb structured data, a link preview picture, and is in `sitemap.xml`. Each village page, township page and village record links to its story; each story links to its village, township, four neighbouring stories and the next and previous story.
  - *Fast*: the text is in the page and shows before any script runs; scripts are deferred; what all stories share (village dots, township borders) is one cached file, `stories/data.js`; the destroyed zones around a village travel inside its page; the pictures for the next step are fetched while the reader is still on the current one. A first visit to a village story is about 40 KB compressed, plus the map library and tiles.
- **Fires detected by satellite** (NASA FIRMS): for each village, the days on which NASA's fire-detecting satellites (VIIRS at 375 m, MODIS at 1 km) recorded a fire within 1 km of its recorded position, in autumn 2017 (25 Aug – 30 Nov) and autumn 2016 (9 Oct – 30 Nov). 164 villages had a detection in 2017 (149 by VIIRS alone); in the same weeks of every other year from 2013 to 2019 VIIRS never found more than 10. Days are in Myanmar time. Shown on the village record, the village page, the registry (and its CSV export), the imagery viewer ("2017 record" draws the detections with their days beside UNOSAT's zones), downloaded images, the stories and the video. A detection is heat seen from orbit: it does not say what burned, and fires under cloud are not detected. `python3 tools/match_fires.py` rebuilds `fires.json`, `fires.csv` and `fires_points.json` from the extract in `sources/nasa_firms/` (cut from NASA's country files with `--from <folder>`).
- **Play, and video**: "Play the years" on the village record (and ▶ Play, pinned at the start of the viewer's timeline) steps from the oldest picture to the newest, each fading into the next. "Make a video" on the village record (and the Video button in the viewer, beside Picture) makes a short film of the same thing (square, wide or tall): a title card, each picture with its date on a timeline, what UNOSAT and NASA recorded in autumn 2017 where they did, and a closing card with the sources. It is drawn frame by frame and written as an MP4 in the browser (WebCodecs with the small `mp4-muxer` library from jsDelivr; where that is missing, the canvas is recorded as it plays). Nothing is uploaded.
- **Caching**: `vercel.json` tells browsers to keep share pictures, icons and PDFs for a week, and data files and stylesheets for an hour (then refresh in the background). Pages themselves are always checked for a newer copy.

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
- **A word left out of 37 names:** MIMU's list adds "Ku Lar" (ကုလား) to the names of some Rohingya villages, for example "X (Ku Lar)". The word is used as a slur against Rohingya, so FARA leaves it out of `name`, `village_name_mmr` and `mimu_village_name` for those 37 records, here and in the `pcodes` files; record 94, a mixed village, reads "(Rakhine + Rohingya)" instead. The place code still points to MIMU's own entry. The two villages called Ku Lar Chaung (ids 113, 866) keep their name, because there the word is the place name itself.
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
| `build.py`, `build_extra.py` | Build the whole static site from the template and the dataset (the second: embed cards, gazetteers, stories) |
| `tools/build_captures.py`, `captures.json`, `sources/esri_wayback/` | Satellite capture dates for every village, looked up ahead of time (the folder keeps the raw answers so later runs only ask for what is new) |
| `tools/build_boundaries.py`, `boundaries.json`, `sources/cod_ab_mmr/` | Township and village-tract boundaries (UN OCHA COD-AB, CC BY-IGO) |
| `tools/build_pdfs.py`, `downloads/`, `gazetteer.css` | The printable township gazetteers as PDFs, and their print design |
| `content/stories/`, `stories/`, `stories.js`, `stories.css` | Story texts, the generated story pages, and the scrolling-map engine |
| `embed/` | Generated embed cards, one per village |
| `tools/match_fires.py`, `fires.json`, `fires.csv`, `fires_points.json`, `sources/nasa_firms/` | NASA FIRMS fire detections matched to villages, and the extract they are built from |
| `village/`, `township/`, `villages/` | Generated record and index pages |
| `pages.css` | Styles for the generated pages |
| `sitemap.xml`, `robots.txt`, `llms.txt`, `og.png` | Search engine, AI assistant and link-preview files |
| `sw.template.js`, `sw.js` | Offline support (the second is generated) |
| `tools/build_share.py`, `tools/logo.json` | Builds the logo, icons and share pictures |
| `favicon.svg`, `favicon.ico`, `logo.svg`, `logo.png` | Site icon and logo |
| `share/img/`, `art/` | Generated share pictures and poster pages |
| `manifest.webmanifest`, `icon-192.png`, `icon-512.png`, `apple-touch-icon.png` | Home-screen install support for phones |
| `by_township/` | Per-township `.json` + `.csv` splits |
