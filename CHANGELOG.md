# Change log

Every change to the archive's data is written down here, newest first. A change to a value taken from the source is also listed, record by record, in [corrections.csv](/corrections.csv).

An edition is the archive as it stood on one day. Each edition has a number, and from edition 1.0 each is kept permanently at Zenodo under its own DOI, so a citation of an edition always leads to exactly the data that was cited.

- The second number goes up (1.0 to 1.1) when records, names or fields are added or corrected.
- The first number goes up (1.x to 2.0) when the shape of the data changes in a way that could break work built on it, for example a field renamed or removed.
- Record numbers (FARA-0001 and so on) never change and are never used again for another village.

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
