# Change log

Every change to the archive's data is written down here, newest first. A change to a value taken from the source is also listed, record by record, in [corrections.csv](/corrections.csv).

An edition is the archive as it stood on one day. Each edition has a number, and from edition 1.0 each is kept permanently at Zenodo under its own DOI, so a citation of an edition always leads to exactly the data that was cited.

- The second number goes up (1.0 to 1.1) when records, names or fields are added or corrected.
- The first number goes up (1.x to 2.0) when the shape of the data changes in a way that could break work built on it, for example a field renamed or removed.
- Record numbers (FARA-0001 and so on) never change and are never used again for another village.

### Since edition 1.1

Added to the website on 16 November 2026. No village record changed, so the edition number stays at 1.1. The three new files will join the dataset with the next edition.

- **Old maps.** Survey of India sheets of 1890 to 1942 can be laid over the map in two periods, shown beside the newest picture in a village's picture viewer, and they open a village's video. Each sheet's placement was checked twice: ten sheets were corrected to their own printed grid, and all sixteen were compared with today's rivers, coast and roads at several spots each. The [methods page](/methods/) gives the result sheet by sheet. New file: `old_maps.csv`.
- **Lines from United Nations reports** on the villages those reports name: the land report of the Independent Investigative Mechanism for Myanmar (2025) and the detailed findings of the Fact-Finding Mission (2018). New file: `un_reports.csv`.
- **Other spellings** of village names, from GeoNames. New file: `other_spellings.csv`.
- A page of [further sources](/sources-list/): old maps, United Nations reports, satellite studies and name lists.

## 1.1 — 16 November 2026

### Added

- **Fires detected by satellite.** Three new files, `fires.csv`, `fires.json` and `fires_points.json`: for each village, the days on which NASA's fire-detecting satellites (VIIRS and MODIS, from NASA FIRMS) recorded a fire within one kilometre of its recorded position, from 25 August to 30 November 2017 and from 9 October to 30 November 2016. 164 villages had a detection in autumn 2017 and 10 in autumn 2016. Days are in Myanmar time.
- A section on the fire detections in the [methods page](/methods/): the source, the rule, and what a detection cannot tell you.

### Unchanged

- No village record changed. The village files, the corrections, the place codes and the UNOSAT results are the same as in edition 1.0.

## 1.0 — 16 November 2026

The first numbered edition, and the first to be given a DOI. It holds everything listed under the earlier dates below.

### Added

- A version number and a date for the archive, shown on every page.
- A "Cite this" button on every village record and village page, with the citation ready to copy as plain text, APA, BibTeX or RIS.
- A [methods page](/methods/): where the data came from, how it was checked and corrected, and what it cannot tell you.
- This change log, and [corrections.csv](/corrections.csv), which lists every change made to a source value.

### Data in this edition

- 1,023 villages in four townships: Maungdaw 378, Buthidaung 338, Rathedaung 214, Sittwe 93.
- 725 with a Rohingya name, 645 with a Burmese-script name, 1,017 with an official village place code.
- What UNOSAT's 2017 satellite analysis marked at or near each village: 243 destroyed, 81 destruction nearby, 596 none detected, 103 not assessed.

## Before the editions were numbered

These states of the archive were public on the dates shown but carried no version number. They are listed so that nothing is hidden.

### 16 November 2026

- **Names corrected in 37 records.** The official list adds the word "Ku Lar" in brackets to the names of some Rohingya villages. The word is used as a slur against Rohingya, so it was left out of `name`, `village_name_mmr` and `mimu_village_name`. Nothing else in those names was changed, and the official place code still points to the official entry. Record FARA-0094, a mixed village, now reads "(Rakhine + Rohingya)". The two villages called Ku Lar Chaung (FARA-0113, FARA-0866) keep their name, because there the word is the place name itself.
- The old web addresses of the renamed village pages lead to the new ones.
- Added township and village-tract boundaries, the dates of every earlier satellite picture of each village, printable gazetteers, embeddable cards and stories. None of these changed a village record.

### 13 November 2026

- **Official place codes added to every record.** Nine new fields: `pcode_village`, `pcode_village_tract`, `pcode_township`, `pcode_district`, `mimu_village_name`, `mimu_village_tract_name`, `mimu_village_status`, `mimu_village_tract_status` and `pcode_match`. Source: MIMU Place Codes, Release 9.7 (January 2026).
- **2017 satellite analysis added.** New files `status_unosat_2017.csv`, `status_unosat_2017.json` and `unosat_2017_zones.geojson`, derived from UNOSAT's analysis of imagery from 31 August to 11 October 2017.
- One page for every village, with its own address.

### 3 July 2026

- **First publication.** 1,023 villages, collected on 2 July 2026 from the Rohingya Khobor Arakan Maps Project.
- Two records had no township or district in the source. FARA-1025 (Fawyazi Para) was placed in Maungdaw and FARA-0338 (Four Miles South) in Buthidaung, following the layer each sits in on the source map.
- FARA-0338 has coordinates in the source that fall in Melbourne, Australia. The record is kept and marked `unverified`; it is not drawn on the map.
