# FARA — The Arakan Village Name Archive

Edition {{version}} · {{date}}{{doi_line}}

FARA ("fará" means "village" in the Rohingya language) records the names and positions of {{n}} Rohingya villages in four townships of Arakan (Rakhine State, Myanmar): {{town_counts}}. Each record gives the village's Rohingya name, its official romanised name, its name in Burmese script where known, its village tract, township and district, its coordinates, and its official place codes.

Rohingya village names are being renamed and removed from official maps. FARA keeps them on record for research, reporting, human-rights documentation and the Rohingya community.

The living archive, with a map and satellite imagery of every village, is at https://map.rohingya.ro/. This package is that archive's data as it stood on {{date}}.

## Files

{{file_table}}

`METHODS.md` says where every part of the data came from and how it was checked and corrected. `CHANGELOG.md` lists what changed in each edition. Read both before relying on the data.

## Fields of `arakan_villages`

| Field | Meaning |
|---|---|
| `id` | Record number, from the source map. Cited as `FARA-0043`. Never changes, never reused. |
| `name` | Official romanised name, as used on government and United Nations maps. |
| `rohingya_name` | The name in Rohingya, in Latin letters. Empty when not yet recorded. |
| `village_name_mmr` | The name in Burmese script. Empty when not recorded. |
| `lat`, `lng` | Position in decimal degrees, WGS84. One point per village. |
| `village_tract`, `township`, `district` | Administrative units the village is in. |
| `layer`, `layer_color` | The layer the record is drawn in on the source map. |
| `coord_status` | `unverified` when the source position is known to be wrong (one record, FARA-0338). |
| `pcode_village` | Official MIMU village place code. Empty when there is none or it is not confirmed. |
| `pcode_village_tract`, `pcode_township`, `pcode_district` | MIMU codes of the tract, township and district. |
| `mimu_village_name`, `mimu_village_tract_name` | MIMU's spelling of the village and its tract. |
| `mimu_village_status`, `mimu_village_tract_status` | `active`, or `inactive_…` when MIMU has removed or reclassified the place. |
| `pcode_match` | How sure the village code is: `exact`, `strong`, `unconfirmed` or `none`. |

## Fields of `status_unosat_2017`

| Field | Meaning |
|---|---|
| `status` | `destroyed`, `nearby`, `none_detected` or `not_assessed`. |
| `point_inside_zone` | Whether the village's point is inside a zone UNOSAT marked destroyed. |
| `nearest_zone_m` | Metres from the village's point to the nearest zone. |
| `destroyed_ha_within_300m` | Hectares marked destroyed within 300 metres of the point. |
| `first_seen`, `last_seen` | Dates of the imagery in which UNOSAT saw the destruction. |
| `confidence`, `cloud_note` | UNOSAT's own notes on certainty and cloud. |

"None detected" does not mean a village is standing. The imagery ends on 11 October 2017, some areas were under cloud, destruction continued afterwards, and UNOSAT did not validate its zones on the ground.

## Missing values

A missing name or code is an empty value. Nothing is guessed. {{n_no_ro}} records have no Rohingya name and {{n_no_mm}} have no Burmese-script name.

## How to cite

{{cite_dataset}}

To cite one village, give its record number and name with the edition, for example: record FARA-0043.

## Terms of use

{{licence_paragraph}}

Parts of the data come from other publishers and stay under their terms:

- **Village names and positions as collected:** Rohingya Khobor Arakan Maps Project, https://map.rohingyakhobor.com/map. Credit the project as the source.
- **Official names, positions and place codes** (the `pcode_` and `mimu_` fields, `pcodes.csv`, `pcodes_review.csv`): © Myanmar Information Management Unit (MIMU), {{pc_release_short}}, https://themimu.info/place-codes. Free to use with attribution. Not for sale or commercial use.
- **2017 analysis** (`status_unosat_2017.csv`, `status_unosat_2017.json`, `unosat_2017_zones.geojson`): derived from UNOSAT, "Destroyed areas in Buthidaung, Maungdaw, and Rathedaung Townships of Rakhine State in Myanmar", {{st_url}}. CC BY-SA 4.0. Credit UNOSAT.

## Contact

Abdul Aziz (AB Aziz) · ab@rohingya.ro · https://orcid.org/0009-0003-8386-3740

Corrections are welcome: every village record on https://map.rohingya.ro/ has a "Suggest a name or correction" button.
