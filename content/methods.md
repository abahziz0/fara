# How this archive was made

FARA records the names and positions of {{n}} Rohingya villages in four townships of Arakan (Rakhine State, Myanmar). This page says where every part of the data came from, what was done to it, and what it cannot tell you. It describes edition {{version}} of {{date}}.

## In short

- The villages, their names and their positions were collected on {{collected}} from the public map of the Rohingya Khobor Arakan Maps Project.
- FARA changes a source value only for a stated reason, and writes every such change down. There are {{n_corr}} so far, in {{n_corr_records}} records. All are listed in [corrections.csv](/corrections.csv).
- A missing name is shown as missing. Nothing is guessed.
- Official place codes, the 2017 satellite analysis, the fire detections and the boundaries come from other publishers. Each is credited and described below, with its own terms of use.

## Where the villages come from

The records were collected on {{collected}} from the map published by the [Rohingya Khobor Arakan Maps Project](https://map.rohingyakhobor.com/map). For each village the source gives a number, a name in Latin letters, a Rohingya name, a name in Burmese script, a latitude and longitude, a village tract, a township and a district, and the map layer it is drawn in.

FARA keeps the source's number as the record number: record 43 on the source map is FARA-0043 here. A record number never changes and is never given to another village.

The archive covers the four townships the source covers: {{town_counts}}. It is not a list of every Rohingya village in Arakan, and a village's absence from it says nothing about that village.

## Names

Each record can hold three names.

- **Rohingya name** (`rohingya_name`): the name as Rohingya people say it, written in Latin letters, as the source gives it. {{n_ro}} records have one and {{n_no_ro}} do not.
- **Official name** (`name`): the romanised name used on government and United Nations maps.
- **Burmese name** (`village_name_mmr`): the name in Burmese script. {{n_mm}} records have one and {{n_no_mm}} do not.

FARA did not collect the Rohingya names itself and has not checked each one with people from the village. They are the names the Arakan Maps Project recorded. A spelling can vary, because Rohingya written in Latin letters has more than one spelling in use.

Names are corrected through suggestions: every village record has a "Suggest a name or correction" button. A suggestion is never published as it arrives. The archive's keeper reads it, checks it where that is possible, and only then changes the record. The change appears in the [change log](/changelog/) and in the next edition.

## Positions

Latitude and longitude are in decimal degrees on the WGS84 datum, as the source gives them. A village is recorded as one point, not as an outline, so the point marks a village and does not show how far it extends.

When the official place codes were added (see below), {{n_identical}} of the {{n}} positions turned out to be the same, to within a tenth of a metre, as the village points in the official MIMU list. For those villages the position is therefore the official one, not a new survey.

One record, FARA-0338, has a position in the source that falls in Melbourne, Australia. It is kept and can be searched, is marked `coord_status: unverified`, and is not drawn on the map.

## Corrections

Records with a problem are flagged, never quietly altered. When a source value is changed, the change is written to [corrections.csv](/corrections.csv) with the record, the date, the fields and the reason.

| What | Records | When |
|---|---|---|
| Township and district were empty in the source. They were filled in from the map layer the record belongs to. | FARA-0338, FARA-1025 | 3 July 2026 |
| The word "Ku Lar" in brackets was left out of the name. | {{n_slur}} records | 16 November 2026 |

On the second: the official list adds "Ku Lar" in brackets to the names of some Rohingya villages. The word is used as a slur against Rohingya. It is not part of the place name, so FARA leaves it out of `name`, `village_name_mmr` and `mimu_village_name`. Nothing else in those names is changed, and the official place code still leads to the official entry. Record FARA-0094, a mixed village, reads "(Rakhine + Rohingya)" instead. Two villages called Ku Lar Chaung (FARA-0113, FARA-0866) keep their name, because there the word is the place name itself.

## Official place codes

Every record carries the place codes the United Nations and aid agencies use for Myanmar, so that it can be joined to their data.

- **Source:** {{pc_release}}, from the [Myanmar Information Management Unit](https://themimu.info/place-codes).
- **How they were matched:** each FARA position was compared with MIMU's village points, and then the name and village tract were compared. The Rohingya name was not used. A code is given only when the match is *exact* (same position, same name, same tract: {{pc_exact}} records) or *strong* (same position or within 250 metres, and the name differs only in spelling or the tract is labelled differently: {{pc_strong}} records).
- **Not given:** {{pc_unconfirmed}} records have a likely code that a person has not yet confirmed, so none is shown ({{pc_unconfirmed_ids}}). {{pc_none}} records have no official code at all ({{pc_none_ids}}).
- **Inactive:** {{pc_inactive}} matched villages are marked inactive by MIMU, meaning removed from the official list or counted as part of a town. Their codes are kept and the status is shown.

The full match for every record, with method and distance, is in [pcodes.csv](/pcodes.csv). The records that still need a person's eye are in [pcodes_review.csv](/pcodes_review.csv).

## What satellites recorded in 2017

Each village carries what [UNOSAT's analysis]({{st_url}}) of satellite imagery from 31 August to 11 October 2017 marked at or near it. UNOSAT published {{n_zones}} outlines of destroyed buildings. FARA compared each village's point with those outlines.

| Result | Rule | Villages |
|---|---|---|
| Destroyed | The village's point is inside a zone, or at least one hectare within 300 metres is marked destroyed. | {{st_destroyed}} |
| Destruction nearby | A zone lies within 500 metres, but less than the rule above. | {{st_nearby}} |
| None detected | No zone within 500 metres. | {{st_none}} |
| Not assessed | The village is outside the area UNOSAT analysed, or has no verified position. | {{st_na}} |

Read these results with care.

- **"None detected" does not mean the village is standing.** The imagery ends on 11 October 2017, some areas were under cloud, and destruction continued afterwards.
- UNOSAT did not validate its zones on the ground.
- A village is one point and a zone is an outline, so the match is by distance. A zone near a village may belong to a neighbouring settlement.

The script that makes the match, `tools/match_unosat.py`, and UNOSAT's original file are in the [project's source](https://github.com/abahziz0/fara).

## Fires detected by satellite

Each village also carries the days on which NASA's fire-detecting satellites recorded a fire near it, in two autumns: {{fire_window_2017}} and {{fire_window_2016}}, when fires were also detected near villages in the north of Maungdaw.

- **Source:** [NASA FIRMS]({{fire_url}}), the yearly country files for Myanmar. Two instruments are used: VIIRS on the Suomi NPP satellite, which sees fires in pixels 375 metres across, and MODIS on the Terra and Aqua satellites, in pixels 1 kilometre across.
- **The rule:** a detection counts for a village when it lies within 1,000 metres of the village's recorded position. Low-confidence detections are left out (VIIRS marked "l", MODIS below 30), and only detections NASA types as presumed vegetation or land fires are used. The rule is simple on purpose, so that it can be checked by hand.
- **Days are in Myanmar time.** NASA gives each detection in UTC. Myanmar is six and a half hours ahead, so a night pass late on the 4th in UTC is counted on the 5th, the day it was for the people under it. The UTC date and time are kept beside it.
- **Result:** {{fire_2017}} villages had a detection within one kilometre in autumn 2017, and {{fire_2016}} in autumn 2016.
- **For comparison:** counting VIIRS alone, {{fire_2017_viirs}} villages had a detection between 25 August and 30 November 2017. In the same weeks of every other year from 2013 to 2019 the number was never above {{fire_other_max}}.

Read these results with care too.

- **A detection is heat seen from orbit.** It does not say what burned, or who lit it.
- **A fire under cloud is not detected at all**, and in the monsoon months cloud is common. A village with no detection has not been shown to be untouched.
- A pixel is 375 metres or 1 kilometre across, and a village is one point. A detection near a village may be a fire in a neighbouring settlement or in fields.
- The fire results and the UNOSAT results come from different satellites and different methods. Neither was used to make the other.

`fires.csv` has one row per village and autumn. `fires.json` adds every single detection with its time, distance, confidence and strength. `fires_points.json` holds all {{fire_points}} detections of the two autumns in the area, whether or not a village is near. The script is `tools/match_fires.py`.

## Old maps, United Nations reports and other spellings

These are shown on the website and offered as separate files. They are not part of the village records, and they do not change any record.

### Old maps

The old-map layer is made of sixteen Survey of India sheets in two periods: five one-inch sheets surveyed between 1890 and 1906, and seven one-inch sheets of 1925 to 1936 with four half-inch sheets of 1926 to 1942 where no one-inch sheet is available. The scans were made and placed on modern coordinates by the Old Survey of India Maps community and Horst Held, who share them under CC BY 4.0. A one-inch sheet of 1890 for the hills north of Buthidaung was left out because it is almost blank.

How the sheets are placed, and how the placement was checked:

- Each sheet is placed by its four corners. Two known corrections are part of that. Sheets printed before 1905 carry longitudes 2 minutes 27 seconds too far east, because of the value then used for the Madras Observatory. And all the sheets use the Everest figure of the Earth, which at this place differs from today's coordinates (WGS 84) by about 280 metres east to west and 100 metres north to south.
- Paper stretches unevenly, so inside a sheet a place can drift from where the corners put it. Ten of the sixteen sheets print their latitude and longitude grid every five minutes. On those, FARA found each grid line along its length and warped the picture so that every line falls where its latitude or longitude says. Before this, grid lines were up to 156 metres out on the 1891 sheet, up to 32 metres on the one-inch sheets of 1925 to 1936, and up to 57 metres on the half-inch sheets. Afterwards they are within 5 metres on every sheet.
- Six sheets print no such grid: four sheets of 1904 and 1905, and two wartime reprints of 1942. They are placed by their corners only.
- Every sheet was then compared with today's roads, rivers and coast from OpenStreetMap and with satellite pictures. The streets of Akyab (Sittwe) on the 1925 sheet lie within about 15 metres of today's streets. Creeks and river banks on the other sheets, including the six without a grid, lie within about 10 to 40 metres where they were checked.

What to keep in mind: a one-inch map was drawn to about 30 metres at best, and a half-inch map to about 60. Rivers and coasts have moved in a century. St Martin's Island on the 1904 sheet lies about 60 to 150 metres from today's outline. The spellings are the surveyors' own. A village missing from an old sheet was not necessarily absent.

The scripts are `tools/oldmaps_fetch.py` (takes only the needed sheets from the published archives), `tools/oldmaps_refine.py` (the grid correction, with the error before and after for each sheet) and `tools/oldmaps_tile.py` (cuts the map tiles). `oldmaps/sheets.json` lists every sheet used and whether it was corrected to its grid. `old_maps.csv` says, for each village, which period covers its position.

### United Nations reports

Where a United Nations report names a village or village tract of this archive, the village record carries a short line saying what the report found, with a link and the paragraph numbers. The lines were written from the text of the reports: the public summary of the land report of the Independent Investigative Mechanism for Myanmar (29 September 2025), and chapter V of the detailed findings of the Fact-Finding Mission (A/HRC/39/CRP.2, 17 September 2018). Each paragraph number was checked against the report. The lines keep to places, dates and counts. They do not retell what witnesses said; for that, read the report. The same lines are in `un_reports.csv`, and the hand-written source file is `sources/un_reports/records.json`.

### Other spellings

Some village records list other spellings of the name. They come from GeoNames, which keeps the spellings used by older gazetteers and maps. A spelling is attached only when the GeoNames place is a populated place within 700 metres of the village's recorded position and one of its names is the same as the archive's official name. The spellings are in `other_spellings.csv`; the script is `tools/match_geonames.py`.

These three files will join the dataset with the next numbered edition.

## Boundaries and satellite pictures on the site

These are shown on the website but are not part of the village records.

- **Township and village-tract boundaries** come from UN OCHA's *Myanmar Subnational Administrative Boundaries* (COD-AB, source MIMU). They are drawn at about 1:250,000, so they are approximate, and showing them does not endorse any boundary.
- **Satellite pictures** come from Esri World Imagery and its Wayback archive, and from the Copernicus Sentinel-2 satellites. The site shows each picture with its capture date. FARA does not store or alter the pictures.

## What this archive cannot tell you

- Whether a village exists today, or who lives there.
- How many people lived in a village at any time.
- Where a village begins and ends.
- What happened in a village. The 2017 results state what UNOSAT's analysts marked from orbit, and the fire results what NASA's satellites detected, and nothing more.

## Safety and care

FARA is a record of places, not of people.

- **No personal data.** The archive holds no names of people, no household lists, no photographs of people and no testimony. A suggestion sent through the site is read by the archive's keeper and is not published; an email address given with it is used only to reply.
- **Only what is already public.** Village positions come from a public map and match those in the official MIMU place-code list. The satellite pictures, the UNOSAT analysis and the NASA fire detections are public data.
- **Careful words.** FARA reports what a source recorded and says what that source cannot show. It does not say who destroyed a building or lit a fire, and it does not describe what a satellite picture shows.
- **No tracking.** The site sets no cookies and counts visits without identifying anyone.
- **Asking for a change or a removal.** If something here is wrong, or you believe publishing it puts someone at risk, write to [ab@rohingya.ro](mailto:ab@rohingya.ro). Requests are answered, and what is changed is recorded in the [change log](/changelog/).

## Editions and how to cite

The archive changes as names are added and corrected. So that a citation stays true, it is published in numbered editions. Each edition is the data exactly as it stood on its date{{doi_sentence}}

Cite the edition you used:

{{cite_dataset}}

To cite one village, use the "Cite this" button on its record or its page. The citation there names the record and the edition together. Everything that changed between editions is in the [change log](/changelog/).

## Sources and terms of use

{{licence_paragraph}}

Parts of the data come from other publishers and stay under their terms:

| Part | Publisher | Terms |
|---|---|---|
| Village names and positions as collected | [Rohingya Khobor Arakan Maps Project](https://map.rohingyakhobor.com/map) | Credit the project as the source. |
| Official names, positions and place codes (the `pcode_` and `mimu_` fields, `pcodes.csv`) | [Myanmar Information Management Unit](https://themimu.info/place-codes), {{pc_release_short}} | © MIMU. Free to use with attribution. Not for sale or commercial use. |
| 2017 analysis (`status_unosat_2017` files, `unosat_2017_zones.geojson`) | [UNOSAT]({{st_url}}) | CC BY-SA 4.0. Credit UNOSAT; share changes under the same licence. |
| Fire detections (`fires` files) | [NASA FIRMS]({{fire_url}}), VIIRS and MODIS active fire data | Free and open. NASA asks to be credited as the source. |
| Township and village-tract boundaries (website only) | UN OCHA, COD-AB (source MIMU) | CC BY-IGO. |
| Old maps (website only, and `old_maps.csv`) | Survey of India sheets, scanned and placed by the [Old Survey of India Maps](https://zenodo.org/communities/old-survey-of-india-maps/) community and Horst Held | CC BY 4.0. Credit the community. |
| Lines from United Nations reports (`un_reports.csv`) | [IIMM](https://iimm.un.org/) and the [Fact-Finding Mission on Myanmar](https://digitallibrary.un.org/record/1643079) | © United Nations. Summarised briefly with the source named; read the reports for the full text. |
| Other spellings (`other_spellings.csv`) | [GeoNames](https://www.geonames.org/) | CC BY 4.0. |

## Questions and corrections

Write to [ab@rohingya.ro](mailto:ab@rohingya.ro), or use the "Suggest a name or correction" button on any village record.
