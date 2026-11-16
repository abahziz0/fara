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

## Boundaries and satellite pictures on the site

These are shown on the website but are not part of the village records.

- **Township and village-tract boundaries** come from UN OCHA's *Myanmar Subnational Administrative Boundaries* (COD-AB, source MIMU). They are drawn at about 1:250,000, so they are approximate, and showing them does not endorse any boundary.
- **Satellite pictures** come from Esri World Imagery and its Wayback archive, and from the Copernicus Sentinel-2 satellites. The site shows each picture with its capture date. FARA does not store or alter the pictures.

## What this archive cannot tell you

- Whether a village exists today, or who lives there.
- How many people lived in a village at any time.
- Where a village begins and ends.
- What happened in a village. The 2017 results state what UNOSAT's analysts marked from orbit, and the fire results what NASA's satellites detected, and nothing more.

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

## Questions and corrections

Write to [ab@rohingya.ro](mailto:ab@rohingya.ro), or use the "Suggest a name or correction" button on any village record.
