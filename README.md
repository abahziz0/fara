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
- **Orbital (satellite) basemap by default**, Grid dark map one click away; loads straight into the map with a scan-line fly-in (no intro screen); custom FARA favicon
- **Mission modal** credits the project: A project by AB Aziz · ab@rohingya.ro
- **Discover** (`D`) — radar-sweep to a random village
- **Map Art Studio** (`P`, or "Map Art" in the top bar) — generate printable poster art for any village or coordinates: live road/river data from OpenStreetMap rendered on canvas at 2400×3600 px (8″×12″ @ 300 DPI). **5 formats** (Classic framed, Full-bleed, Circle, Heart-clipped, "Two Homes" duo — second place can be any village or **any city in the world** via built-in geocoding), **6 themes**, village **markers** (ring/heart/none), editable trilingual title block + optional message line, fixed **"by AB Aziz" watermark**, typo-tolerant search, PNG download + print + **share** (system share sheet with the poster image; falls back to download + caption copy + opening Facebook/WhatsApp/Instagram/TikTok). Requires internet (Overpass API, 3 fallback endpoints; Nominatim for world search).
- Keyboard shortcuts overlay (`?`), terminal boot sequence, responsive mobile layout, reduced-motion support

`fara_template.html` is the editable source. Regenerate after edits:

```
python3 -c "import json; d=json.dumps([{k:r[k] for k in ['id','name','lat','lng','township','district','village_tract','rohingya_name','village_name_mmr','coord_status'] if r.get(k) is not None} for r in json.load(open('arakan_villages.json'))],ensure_ascii=False,separators=(',',':')); open('fara.html','w').write(open('fara_template.html').read().replace('__VILLAGE_DATA__',d))"
```

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

## Files

| File | Description |
|------|-------------|
| `fara.html` | **The archive website** — single self-contained file |
| `fara_template.html` | Editable source template (data placeholder inside) |
| `arakan_villages.json` | All 1,023 villages, pretty JSON (sorted district → township → tract → name) |
| `arakan_villages.csv` | Spreadsheet-friendly CSV |
| `arakan_villages.geojson` | Point FeatureCollection (verified coordinates only) — QGIS/Leaflet/Mapbox ready |
| `summary.json` | Counts, coverage, corrections log |
| `by_township/` | Per-township `.json` + `.csv` splits |
