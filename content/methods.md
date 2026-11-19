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

The old-map layer is made of sixteen Survey of India sheets in two periods: five one-inch sheets surveyed between 1890 and 1906, and seven one-inch sheets of 1925 to 1936 with four half-inch sheets of 1926 to 1942 where no one-inch sheet is available. The scans were made and placed on modern coordinates by the Old Survey of India Maps community and Horst Held, who share them under CC BY 4.0. A one-inch sheet of 1890 for the hills north of Buthidaung was left out because it is almost blank. A third period, the map of 1954 and 1955, is four sheets of the United States Army; it was placed in a different way and has its own part below.

How the sheets are placed, and how the placement was checked:

- Each sheet is placed by its four corners. Two known corrections are part of that. Sheets printed before 1905 carry longitudes 2 minutes 27 seconds too far east, because of the value then used for the Madras Observatory. And all the sheets use the Everest figure of the Earth, which at this place differs from today's coordinates (WGS 84) by about 280 metres east to west and 100 metres north to south.
- Paper stretches unevenly, so inside a sheet a place can drift from where the corners put it. Ten of the sixteen sheets print their latitude and longitude grid every five minutes. On those, FARA found each grid line along its length and warped the picture so that every line falls where its latitude or longitude says. Before this, grid lines were up to 156 metres out on the 1891 sheet, up to 32 metres on the one-inch sheets of 1925 to 1936, and up to 57 metres on the half-inch sheets. Afterwards they are within 5 metres on every sheet.
- Six sheets print no such grid: four sheets of 1904 and 1905, and two wartime reprints of 1942. They are placed by their corners only.
- Every sheet was then checked a second time, sheet by sheet. For each sheet, close-up pictures were made at four spots in different parts of it, with today's rivers, creeks, coast and main roads from OpenStreetMap drawn over the sheet as it is placed, and the same spots were looked at against satellite pictures. The table gives the result. "Distance" is how far today's lines lie from the drawn ones.

| Sheet | Year | Placed by | Distance | What was checked |
|---|---|---|---|---|
| 84 C/3-7 | 1905 | corners | 30 to 90 m | Two creeks on the Bangladesh side: 30 to 60 m. The Kha Maung Seik river and the Yokhat chaung against the satellite picture: 45 to 90 m. Most of the Burmese hills are blank on this sheet, so there is little to compare. The least certain sheet. |
| 84 C/4-8 | 1905 | corners | 15 to 70 m | A creek at Nhila on the Bangladesh side: 15 to 30 m. Three creeks near Kyein Chaung (Don, Leikya, Lamudeing) are drawn 50 to 70 m south-east of where they run today, by satellite picture and by today's map. Where this sheet meets 84 D/1-5 the lines join. The difference is local to those creeks, so the sheet was not moved. |
| 84 D/1-5 | 1904 | corners | 10 to 30 m | Main road in Maungdaw town: 10 m. Road south of Maungdaw: 13 m. A stream crossing near Teknaf: 30 m. Creeks north of Maungdaw: 10 to 20 m. |
| 84 D/2-6 | 1904 | corners | 15 to 30 m on the mainland | Road at Ah Lel Than Kyaw: 15 to 30 m. Road at Thayekonbaung: 15 m. A creek near Ton Chaung against the satellite picture: 10 to 20 m. St Martin's Island is drawn 60 to 150 m east of today's outline; the mainland on the same sheet fits, so this is the old survey of the island. |
| 84 D/11-15 | 1891 | grid | 15 to 45 m | Grid lines were up to 156 m out before the correction and are within 3 m after it. Mayu river bank: 30 to 45 m. Coast: 15 m. A track at Pyungauk: 15 to 30 m. Tidal creeks have moved 50 to 100 m in places, each in its own direction. |
| 84 D/9 | 1935 | grid | 10 to 30 m | Creek south of Buthidaung: 15 to 30 m. River bend at Megyaungzi: 30 m. Buthidaung town, river and roads: 10 to 20 m. |
| 84 D/10 | 1936 | grid | 30 to 90 m | River banks at four spots: 30 to 90 m. Today's map draws these rivers coarsely here, which limits the check. |
| 84 D/11 | 1925 | grid | 15 to 60 m | Roads at Gwedaukchaung and Shinkhali: 15 to 30 m. Coast: 30 to 60 m (the width of the beach). One road has been moved 60 to 90 m since. |
| 84 D/13 | 1936 | grid | 15 to 30 m | Kyauktaw river front: 15 to 30 m. Yo chaung: 15 to 30 m. Kaladan banks: 30 m, one bank has shifted about 100 m. |
| 84 D/14 | 1935, printed 1942 | corners | 15 to 30 m | River bends at four spots (Sabahta, Sinthe, Apaukwa and the loop to the east): 15 to 30 m. |
| 84 D/15 | 1925 | grid | 15 to 30 m | River banks at Pyunkhaung, Mraunggri and Zadipyin: 15 to 30 m. |
| 84 D/16 | 1925 | grid | 15 to 30 m | The streets of Akyab (Sittwe): within 15 m of today's streets. Creeks and the Kaladan bank: 15 to 30 m. |
| half-inch 84 C/SW | 1941 | grid | 50 to 100 m | Rivers and creeks at four spots: 50 to 100 m. One loop of the Matamuhari is drawn up to 500 m from today's course (the river has moved or the loop was drawn loosely). |
| half-inch 84 C/SE | 1938 | grid | 50 to 100 m | Rivers at Kyilewa and Ngame, and a hill stream: 50 to 100 m. |
| half-inch 84 D/NW | 1942 | corners | 25 to 100 m | The Maungdaw to Buthidaung road and a road crossing south of Maungdaw: 25 to 50 m. Creeks: 50 to 100 m. |
| half-inch 84 D/SE | 1926 | grid | 25 to 100 m | A road on the Sittwe peninsula: 25 to 50 m. River banks: 50 to 100 m. |
| US Army NF 46-14 Akyab | compiled 1954, printed 1960 | yard grid | 40 to 90 m | Main road at Maungdaw: 40 m. Maungdaw to Buthidaung road: 40 m east of the river, about 85 m in the hills, where the sheet smooths out the bends. Road on the Sittwe peninsula: 40 to 80 m, drawn west of today's. Mayu river banks at Buthidaung and Rathedaung: 40 to 75 m. |
| US Army NF 46-10 Cox's Bazar | compiled 1954, printed 1960 | yard grid | 20 to 100 m | Road at Kyunbouk and Karani Bazar, north of Maungdaw: 25 to 40 m along 6 km. Roads between Ukhia and Cox's Bazar on the Bangladesh side: 20 to 45 m. Banks of the Naf and the Kalapanzin: 60 to 100 m. |
| US Army NF 46-15 Myohaung | compiled 1954, printed 1960 | yard grid | 20 to 100 m | Road from Kyauktaw to Myohaung (Mrauk U): 20 to 30 m. Roads in Myohaung town: 50 m. Road at Minbya: up to 100 m, drawn about 80 m west of today's; the least certain part of this sheet. River banks at Myebon and on the Lemro: 60 to 100 m. |
| US Army NE 46-3 Kyaukpyu | compiled 1955, printed 1959 | yard grid | 30 to 100 m | Main road in Kyaukpyu town: 30 m. Shore of the Kyaukpyu peninsula: 30 to 50 m. Shores of East Boronga island: 60 to 100 m. At An and Ramree today's roads pass through the villages drawn, but little there can be measured. A thinner check than on the other two sheets. |

What the check found. No sheet is misplaced as a whole. Roads and town streets, which do not move, lie 10 to 30 metres from where the sheets draw them. Tidal creeks and river banks have moved since the survey, often by 50 to 100 metres and each in its own direction, so a creek that does not fit does not mean the sheet is wrong. Two differences are worth knowing: three creeks near Kyein Chaung on sheet 84 C/4-8 are drawn 50 to 70 metres south-east of today's, and St Martin's Island on sheet 84 D/2-6 is drawn 60 to 150 metres east of today's outline. Neither sheet was changed for it, because the rest of each sheet fits.

An automatic comparison was also tried, sliding today's water lines over each sheet to find the best fit. It could not tell a river that has moved from a sheet that is misplaced, and it gave wrong answers where the street check showed the sheet to be right, so its numbers are not used.

What to keep in mind: a one-inch map was drawn to about 30 metres at best, and a half-inch map to about 60. The spellings are the surveyors' own. A village missing from an old sheet was not necessarily absent.

**The map of 1954 and 1955.** Added on 19 November 2026: four sheets of the United States Army Map Service, Burma 1:250,000 (series U542). NF 46-14 Akyab and NF 46-10 Cox's Bazar were compiled in 1954 from the one-inch surveys of 1936 to 1944 and from air photographs of 1943 to 1945, and printed in 1960. They cover all four townships. NF 46-15 Myohaung (today's Mrauk U) was compiled in 1954 from the half-inch surveys of 1925 to 1936 and printed in 1960. NE 46-3 Kyaukpyu was compiled in 1955 from half-inch sheets and sea charts and printed in 1959. These two lie east and south-east of the four townships and hold no village of this archive; they are shown so that the map does not stop at the edge of the archive. All four are works of the United States government and in the public domain. The scans are from the Perry-Castañeda Library Map Collection of the University of Texas Libraries.

These sheets are not a new survey. The two of 1954 redraw, at a quarter of the scale, the surveys already shown in the layer of 1925 to 1944. What they add is one continuous map of all four townships from a second publisher, and their names: many villages carry a second name in brackets, such as "Sinchaingbyin (Zullapara)".

How the sheets were placed, and how the placement was checked:

- The scans came with no coordinates. Each sheet prints a blue grid with a line every 10,000 yards: the India Zone IIIB grid on the Everest figure of the Earth. Every point of that grid has a known latitude and longitude. FARA found each grid line at stations along its length (1,842 readings kept on the Akyab sheet, 1,546 on the Cox's Bazar sheet, 1,764 on the Myohaung sheet, 1,634 on the Kyaukpyu sheet; 117 of the 121 lines were found) and fitted the picture to them. Placed straight between the four corners, the grid lines were typically 50 to 80 metres out and at worst 390; after the fit they are typically 15 metres and at worst 44 metres from where the grid says.
- The same change to today's coordinates was then made as for the Survey of India sheets.
- First check, against the sheet's own latitude and longitude marks, which the fit did not use. On the Akyab sheet the frame and the fifteen crosses printed every 15 minutes lie within 75 metres of where the grid puts them, about 30 metres on average. On the Cox's Bazar sheet the two do not agree. The foot of the frame is drawn 135 metres north of the grid's line of 21 degrees, and in the south-west corner, which is open sea, the frame is more than 200 metres west of the grid. Over the land east of 92.2° E the crosses are within 160 metres. Today's roads decide between them: with the sheet placed by its grid, they run along the roads the sheet draws. So the grid was kept and the frame was not used. On the Myohaung sheet the frame and the crosses lie within 100 metres of the grid, 60 metres north to south on average; today's roads there fit the grid to within 25 metres north to south, so the grid was kept. East to west that sheet is less certain around Minbya: the road is drawn about 80 metres west of today's, and the crosses there also lie 50 to 90 metres west of the grid, so that part may sit up to about 100 metres too far west. Today's highway partly follows a new line there, and no one-inch map covers the ground east of 93° E to settle it. The Kyaukpyu sheet shows the same disagreement as Cox's Bazar, smaller: its frame is up to 140 metres from the grid, and its crosses 95 metres on average. In Kyaukpyu town, where the crosses are about 130 metres out, today's main road lies 30 metres from the road the sheet draws when it is placed by its grid. The grid was kept there too.
- Second check, against today's ground, as for the other sheets (see the table). For these sheets a count was added: each point of today's main roads was compared with the red road lines the sheets draw. On the Cox's Bazar sheet half the points are within 30 metres and nine in ten within 100. On the Akyab sheet half are within 40 metres at Maungdaw and on the north of the Sittwe peninsula; on the south of the peninsula it is 60 to 80 metres, the sheet drawing the road west of today's; and on the hill road between Maungdaw and Buthidaung it is about 85 metres, because the sheet smooths out the bends. On the Myohaung sheet half of 1,089 points are within 52 metres: 20 to 30 metres on the road from Kyauktaw to Myohaung, and about 100 metres near Minbya, where the sheet draws the road west of today's. On the Kyaukpyu sheet only 65 points of today's roads have a drawn road to compare with: half are within 45 metres, and in Kyaukpyu town within 30.
- Where the Akyab and Cox's Bazar sheets meet, along latitude 21° N, the layer shows a gap about 300 metres wide. The frame of the Cox's Bazar sheet is drawn too far north, so the sheet stops short of that line, and the frame lines themselves are trimmed away. That strip of ground is on neither sheet as shown here.

What to keep in mind for this map: one pixel of the scan is 36 metres on the ground. A village mark is about 100 metres wide and a road line about 130. A village can be drawn 100 to 200 metres from its place so that its name fits beside it. The sheets say themselves that names are left out where the map is crowded, so many villages are marks without a name. The layer is sharp up to zoom 12 and is only enlarged beyond zoom 13. The picture viewer and the videos of villages keep to the one-inch maps, which show a village's ground in detail.

The close-up pictures are at `/oldmaps/check/` (one per sheet, listed on the [further sources](/sources-list/) page), with `results.json` and the spots used. Today's lines in them are © OpenStreetMap contributors.

The scripts are `tools/oldmaps_fetch.py` (takes only the needed sheets from the published archives), `tools/oldmaps_refine.py` (the grid correction, with the error before and after for each sheet), `tools/oldmaps_ams.py` (places the four sheets of 1954 and 1955 on their printed yard grid, with every figure given above), `tools/oldmaps_tile.py` (cuts the map tiles) and `tools/oldmaps_check.py` (makes the close-up pictures). `oldmaps/sheets.json` lists every sheet used and whether it was corrected to its grid. `old_maps.csv` says, for each village, which period covers its position.

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
| The map of 1954 and 1955 (website only) | United States Army Map Service, Burma 1:250,000, series U542, sheets NF 46-14, NF 46-10, NF 46-15 and NE 46-3. Scans: [Perry-Castañeda Library Map Collection](https://maps.lib.utexas.edu/maps/ams/burma/), University of Texas Libraries | Public domain, as a work of the United States government. Credit the library for the scans. |
| Lines from United Nations reports (`un_reports.csv`) | [IIMM](https://iimm.un.org/) and the [Fact-Finding Mission on Myanmar](https://digitallibrary.un.org/record/1643079) | © United Nations. Summarised briefly with the source named; read the reports for the full text. |
| Other spellings (`other_spellings.csv`) | [GeoNames](https://www.geonames.org/) | CC BY 4.0. |

## Questions and corrections

Write to [ab@rohingya.ro](mailto:ab@rohingya.ro), or use the "Suggest a name or correction" button on any village record.
