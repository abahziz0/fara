#!/usr/bin/env python3
"""Write the official MIMU place codes (P-codes) from pcodes.json into the village data files.

    python3 tools/add_pcodes.py

Reads   pcodes.json                       the match results (one entry per FARA id)
Updates arakan_villages.json / .csv / .geojson, by_township/*.json / *.csv, summary.json

Safe to run again: it only sets the fields listed in FIELDS and leaves everything else as it is.
A village code is written only for matches graded "exact" or "strong". The few "probable" matches
are marked pcode_match = "unconfirmed" and get no village code until a person has confirmed them
(the candidates are listed in pcodes_review.csv).
"""
import csv, io, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def p(*a): return os.path.join(ROOT, *a)

FIELDS = ['pcode_district', 'pcode_township', 'pcode_village_tract', 'pcode_village',
          'mimu_village_name', 'mimu_village_tract_name', 'mimu_village_status', 'mimu_village_tract_status', 'pcode_match']
VILLAGE_STATUS = {None: 'active', 'Name Change': 'active', 'Delete': 'inactive_removed_from_list', 'VillagetoWard': 'inactive_reclassified_to_ward'}
TRACT_STATUS = {'VTtoWard': 'inactive_reclassified_to_ward', 'VTtoTown': 'inactive_reclassified_to_town'}

P = json.load(open(p('pcodes.json'), encoding='utf-8'))
RELEASE = P['meta']['source']['release']

def fields_for(r):
    confirmed = r['village_tier'] in ('exact', 'strong', 'shared')
    out = dict.fromkeys(FIELDS)
    out['pcode_district'], out['pcode_township'] = r['district_pcode'], r['township_pcode']
    out['pcode_match'] = r['village_tier'] if confirmed else ('unconfirmed' if r['village_tier'] in ('probable', 'ambiguous') else 'none')
    if confirmed:
        # the tract MIMU itself places this village in (differs from the archive's tract label for 3 records)
        out['pcode_village'] = r['village_pcode']
        out['mimu_village_name'] = r['village_name_mimu']
        out['mimu_village_status'] = VILLAGE_STATUS[r['mimu_change_type']] if r['mimu_village_status'] != 'Active' else 'active'
        out['pcode_village_tract'], out['mimu_village_tract_name'] = r['vt_pcode_of_mimu_village'], r['vt_name_of_mimu_village']
        inactive, change = r['vt_status_of_mimu_village'] != 'Active', r['vt_change_of_mimu_village']
    else:
        out['pcode_village_tract'], out['mimu_village_tract_name'] = r['vt_pcode'], r['vt_name_mimu']
        inactive, change = bool(r['vt_pcode']) and r['vt_mimu_status'] != 'Active', r.get('vt_mimu_change_type')
    if out['pcode_village_tract']:
        out['mimu_village_tract_status'] = TRACT_STATUS.get(change, 'inactive') if inactive else 'active'
    return out

BY_ID = {r['id']: fields_for(r) for r in P['records']}

def update_json(path):
    rows = json.load(open(path, encoding='utf-8'))
    for v in rows: v.update(BY_ID[v['id']])
    with open(path, 'w', encoding='utf-8') as f: f.write(json.dumps(rows, ensure_ascii=False, indent=2))
    return rows

def update_csv(path):
    rows = list(csv.reader(io.StringIO(open(path, encoding='utf-8', newline='').read(), newline='')))
    head = [h for h in rows[0] if h not in FIELDS]
    keep = [i for i, h in enumerate(rows[0]) if h not in FIELDS]
    out = io.StringIO(newline='')
    w = csv.writer(out, lineterminator='\r\n')
    w.writerow(head + FIELDS)
    for r in rows[1:]:
        f = BY_ID[int(r[0])]
        w.writerow([r[i] for i in keep] + [f[k] or '' for k in FIELDS])
    with open(path, 'w', encoding='utf-8', newline='') as fh: fh.write(out.getvalue())

V = update_json(p('arakan_villages.json'))
update_csv(p('arakan_villages.csv'))
g = json.load(open(p('arakan_villages.geojson'), encoding='utf-8'))
for ft in g['features']: ft['properties'].update(BY_ID[ft['properties']['id']])
with open(p('arakan_villages.geojson'), 'w', encoding='utf-8') as f: f.write(json.dumps(g, ensure_ascii=False))
for name in sorted(os.listdir(p('by_township'))):
    if name.endswith('.json'): update_json(p('by_township', name))
    elif name.endswith('.csv'): update_csv(p('by_township', name))

s = json.load(open(p('summary.json'), encoding='utf-8'))
s['place_codes'] = {
    'source': RELEASE,
    'villages_with_code': sum(1 for v in V if v['pcode_village']),
    'villages_unconfirmed': [v['id'] for v in V if v['pcode_match'] == 'unconfirmed'],
    'villages_without_code': [v['id'] for v in V if v['pcode_match'] == 'none'],
    'villages_inactive_in_mimu': sum(1 for v in V if (v['mimu_village_status'] or '').startswith('inactive')),
    'village_tracts_with_code': len({v['pcode_village_tract'] for v in V if v['pcode_village_tract']}),
}
with open(p('summary.json'), 'w', encoding='utf-8') as f: f.write(json.dumps(s, ensure_ascii=False, indent=2))
print('place codes written: %d villages with a code, %d unconfirmed, %d without; source: %s'
      % (s['place_codes']['villages_with_code'], len(s['place_codes']['villages_unconfirmed']), len(s['place_codes']['villages_without_code']), RELEASE))
