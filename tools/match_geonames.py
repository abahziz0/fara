#!/usr/bin/env python3
"""Other spellings of village names, from GeoNames.

GeoNames (geonames.org, CC BY 4.0) keeps, for each place, the spellings other gazetteers have used for it: among them the
older romanisations of the U.S. Board on Geographic Names, which are the spellings on twentieth-century maps
("Zigyomaw" for Zee Cho Maw). This script attaches those spellings to the villages of the archive.

    python3 tools/match_geonames.py /path/to/MM.txt      # MM.txt from https://download.geonames.org/export/dump/MM.zip

The rule, kept strict so a spelling is never hung on the wrong village:
    the GeoNames place must be a populated place within 700 m of the village's recorded position, AND
    one of its names must be the same as the archive's official name (or MIMU's spelling) once case, spaces,
    hyphens and bracketed parts are ignored.
Only Latin-script spellings that differ from the names the archive already holds are kept.
Writes sources/geonames/alt_names.json: village id -> {geonameid, metres, names}.
"""
import json, math, os, re, sys, unicodedata
from collections import defaultdict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RADIUS_M = 700
def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()
    s = re.sub(r'\([^)]*\)', ' ', s)
    return re.sub(r'[^a-z0-9]', '', s.lower())
def latin(s): return bool(re.match(r"^[A-Za-z][A-Za-z .'()\-]+$", s))
def main():
    src = sys.argv[1]
    V = [v for v in json.load(open(os.path.join(ROOT, 'arakan_villages.json'), encoding='utf-8'))
         if v.get('lat') and v.get('lng') and v.get('coord_status') != 'unverified' and 19 < float(v['lat']) < 22]
    grid = defaultdict(list)
    for line in open(src, encoding='utf-8'):
        f = line.rstrip('\n').split('\t')
        if f[6] != 'P': continue
        la, ln = float(f[4]), float(f[5])
        if not (19.9 < la < 21.6 and 92.0 < ln < 93.3): continue
        names = [f[1]] + [x for x in f[3].split(',') if x]
        grid[(int(la / .02), int(ln / .02))].append((la, ln, f[0], names))
    out = {}
    for v in V:
        la, ln = float(v['lat']), float(v['lng']); k = math.cos(math.radians(la))
        own = {norm(v.get('name')), norm(v.get('mimu_village_name')), norm(re.sub(r'[()]', ' ', v.get('name') or ''))} - {''}
        known = own | {norm(v.get('rohingya_name'))}
        best = None
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for gla, gln, gid, names in grid.get((int(la / .02) + dy, int(ln / .02) + dx), ()):
                    d = math.hypot((gla - la) * 110574, (gln - ln) * 111320 * k)
                    if d > RADIUS_M or not (own & {norm(n) for n in names}): continue
                    if best is None or d < best[0]: best = (d, gid, names)
        if not best: continue
        seen, alts = set(known), []
        for n in best[2]:
            if latin(n) and norm(n) not in seen and len(norm(n)) > 2: seen.add(norm(n)); alts.append(n)
        if alts: out[str(v['id'])] = {'geonameid': int(best[1]), 'metres': round(best[0]), 'names': alts}
    d = os.path.join(ROOT, 'sources', 'geonames'); os.makedirs(d, exist_ok=True)
    json.dump({'meta': {'source': 'GeoNames, https://www.geonames.org/ (CC BY 4.0), country file MM', 'rule': 'populated place within %d m whose name matches the official name; other Latin-script spellings kept' % RADIUS_M},
               'villages': out}, open(os.path.join(d, 'alt_names.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('%d of %d villages gained other spellings (%d spellings)' % (len(out), len(V), sum(len(o['names']) for o in out.values())))
    for i in list(out)[:12]:
        v = next(x for x in V if str(x['id']) == i); print('  ', v['name'], '->', ', '.join(out[i]['names']), '(%d m)' % out[i]['metres'])
if __name__ == '__main__': main()
