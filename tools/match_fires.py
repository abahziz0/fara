#!/usr/bin/env python3
"""Match NASA's satellite fire detections to the villages of the archive.

NASA FIRMS publishes every "active fire" its satellites detect: a place, a day and a time. This script takes the
detections for Myanmar, keeps the ones in northern Arakan, and lists for each village the days on which a fire
was detected within one kilometre of its recorded position, in the autumn of 2017 (and of 2016, when villages in
the north of Maungdaw also burned).

    python3 tools/match_fires.py --from /folder/of/FIRMS/country/files     # first time: cut the extract
    python3 tools/match_fires.py                                            # afterwards: rebuild from the extract

Source files (no account needed): https://firms.modaps.eosdis.nasa.gov/country/
    viirs-snpp_<year>_Myanmar.csv   VIIRS on the Suomi NPP satellite, 375 m pixels, from 2012
    modis_<year>_Myanmar.csv        MODIS on Terra and Aqua, 1 km pixels

Writes
    sources/nasa_firms/extract_aug_dec.csv   the detections in the area, August to December of each year
    fires.json                               per village: the days, the nearest detection, every detection
    fires.csv                                the same as a table, one row per village
    fires_points.json                        every detection of the two autumns, for drawing on a map

The rule, kept deliberately simple so it can be checked by hand:
    a detection counts for a village when it lies within 1,000 m of the village's recorded position;
    low-confidence detections are left out (VIIRS "l", MODIS below 30);
    only detections NASA types as presumed vegetation or land fires (type 0) are used.
What it cannot say: what burned, or who lit it. And a fire under cloud is not detected at all, which in the
monsoon is often. So a village with no detection has not been shown to be untouched.
"""
import argparse, csv, json, math, os, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'sources', 'nasa_firms')
EXTRACT = os.path.join(SRC, 'extract_aug_dec.csv')
BOX = (19.9, 21.6, 92.0, 93.3)                           # south, north, west, east
RADIUS_M = 1000
WINDOWS = {'2017': ('2017-08-25', '2017-11-30'), '2016': ('2016-10-09', '2016-11-30')}
FIELDS = ['sensor', 'acq_date', 'acq_time', 'latitude', 'longitude', 'confidence', 'frp', 'daynight', 'type', 'scan', 'track', 'satellite']
SOURCE = 'NASA FIRMS: VIIRS (Suomi NPP) 375 m and MODIS (Terra, Aqua) 1 km active fire detections, country yearly archive'
URL = 'https://firms.modaps.eosdis.nasa.gov/country/'


def cut_extract(folder):
    os.makedirs(SRC, exist_ok=True)
    n, files = 0, []
    with open(EXTRACT, 'w', newline='', encoding='utf-8') as out:
        w = csv.writer(out); w.writerow(FIELDS)
        for fn in sorted(os.listdir(folder)):
            if not fn.endswith('.csv') or not (fn.startswith('viirs') or fn.startswith('modis')): continue
            sensor = 'V' if fn.startswith('viirs') else 'M'
            files.append('%s (%.1f MB)' % (fn, os.path.getsize(os.path.join(folder, fn)) / 1e6))
            with open(os.path.join(folder, fn), newline='', encoding='utf-8') as f:
                for r in csv.DictReader(f):
                    la, ln = float(r['latitude']), float(r['longitude'])
                    if not (BOX[0] <= la <= BOX[1] and BOX[2] <= ln <= BOX[3]) or r['acq_date'][5:7] < '08': continue
                    w.writerow([sensor, r['acq_date'], r['acq_time'], '%.5f' % la, '%.5f' % ln, r['confidence'], r['frp'], r['daynight'],
                                r.get('type', '0') or '0', r['scan'], r['track'], r['satellite']]); n += 1
    print('extract: %d detections, August to December, from\n  %s' % (n, '\n  '.join(files)))


def local(date, hhmm):
    """NASA gives the day and time in UTC. A village counts its days in Myanmar time, six and a half hours ahead:
    a night pass at 19:44 UTC on the 4th was 02:14 on the 5th for the people under it."""
    t = datetime.strptime(date + hhmm.zfill(4), '%Y-%m-%d%H%M') + timedelta(hours=6, minutes=30)
    return t.strftime('%Y-%m-%d'), t.strftime('%H%M')


def good(r):
    if (r['type'] or '0') != '0': return False
    return r['confidence'] != 'l' if r['sensor'] == 'V' else float(r['confidence']) >= 30


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--from', dest='folder', help='folder holding the FIRMS country files for Myanmar')
    a = ap.parse_args()
    if a.folder: cut_extract(a.folder)
    if not os.path.exists(EXTRACT): sys.exit('no extract yet: run once with --from <folder of the FIRMS country files>')
    rows = [r for r in csv.DictReader(open(EXTRACT, newline='', encoding='utf-8')) if good(r)]
    V = [v for v in json.load(open(os.path.join(ROOT, 'arakan_villages.json'), encoding='utf-8'))
         if v.get('lat') and v.get('lng') and v.get('coord_status') != 'unverified']
    grid = defaultdict(list)                                         # villages by 0.02 degree cell, so each detection is compared with few
    for v in V: grid[(int(float(v['lat']) / .02), int(float(v['lng']) / .02))].append(v)

    def near(la, ln):
        out, k = [], math.cos(math.radians(la))
        gy, gx = int(la / .02), int(ln / .02)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for v in grid.get((gy + dy, gx + dx), ()):
                    d = math.hypot((float(v['lat']) - la) * 110574, (float(v['lng']) - ln) * 111320 * k)
                    if d <= RADIUS_M: out.append((round(d), v['id']))
        return out

    per = defaultdict(lambda: defaultdict(list))                     # village id -> window -> detections
    points = []
    base = defaultdict(lambda: {'villages': set(), 'detections': 0})  # the same weeks of every year, VIIRS only, for comparison
    lo, hi = WINDOWS['2017'][0][5:], WINDOWS['2017'][1][5:]
    for r in rows:
        la, ln, date = float(r['latitude']), float(r['longitude']), r['acq_date']
        hits = None
        for key, (d0, d1) in WINDOWS.items():
            if d0 <= date <= d1:
                hits = near(la, ln)
                day, clock = local(date, r['acq_time'])
                points.append([round(la, 5), round(ln, 5), int(day.replace('-', '')), r['sensor'], 1 if hits else 0])
                for d, vid in hits:
                    per[vid][key].append([day, clock, r['sensor'], d, r['confidence'], float(r['frp'] or 0), r['daynight'], date, r['acq_time']])
        if r['sensor'] == 'V' and lo <= date[5:] <= hi:
            hits = near(la, ln) if hits is None else hits
            if hits:
                base[date[:4]]['detections'] += 1
                base[date[:4]]['villages'].update(vid for _, vid in hits)

    out = {}
    for vid, wins in per.items():
        out[str(vid)] = {}
        for key, det in wins.items():
            det.sort()
            days = sorted({d[0] for d in det})
            out[str(vid)][key] = {'days': days, 'detections': len(det), 'nearest_m': min(d[3] for d in det), 'first': days[0], 'last': days[-1], 'det': det}
    years = sorted(base)
    meta = {'source': SOURCE, 'url': URL, 'citation': 'NASA FIRMS, https://firms.modaps.eosdis.nasa.gov/ (MODIS Collection 6.1 and VIIRS S-NPP 375 m standard-quality archive)',
            'windows': WINDOWS, 'radius_m': RADIUS_M,
            'rule': 'a detection within 1,000 m of the recorded position; low confidence left out; presumed vegetation or land fires only',
            'time': 'days are in Myanmar time (UTC+6:30); each detection lists [local day, local time, sensor V or M, metres from the village, confidence, fire radiative power MW, D day or N night pass, UTC date, UTC time]',
            'caution': 'A detection is heat seen from orbit: it does not say what burned or who lit it. Fires under cloud are not detected, so no detection does not mean no fire.',
            'villages_with_fire': {k: sum(1 for w in out.values() if k in w) for k in WINDOWS},
            'same_weeks_other_years_viirs': {y: {'villages': len(base[y]['villages']), 'detections': base[y]['detections']} for y in years}}
    json.dump({'meta': meta, 'villages': out}, open(os.path.join(ROOT, 'fires.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    json.dump({'source': SOURCE, 'windows': WINDOWS, 'p': sorted(points, key=lambda p: p[2])},
              open(os.path.join(ROOT, 'fires_points.json'), 'w', encoding='utf-8'), separators=(',', ':'))
    by_id = {v['id']: v for v in V}
    with open(os.path.join(ROOT, 'fires.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['id', 'rohingya_name', 'name', 'township', 'village_tract', 'autumn', 'fire_days', 'first_day', 'last_day', 'detections', 'nearest_m', 'days'])
        for vid in sorted(per):
            v = by_id[vid]
            for key in sorted(out[str(vid)]):
                o = out[str(vid)][key]
                w.writerow([vid, v.get('rohingya_name') or '', v.get('name') or '', v.get('township') or '', v.get('village_tract') or '', key,
                            len(o['days']), o['first'], o['last'], o['detections'], o['nearest_m'], ' '.join(o['days'])])
    print('fires.json: %s' % ', '.join('%s villages with a fire within 1 km in autumn %s' % (n, k) for k, n in sorted(meta['villages_with_fire'].items())))
    print('same weeks (25 Aug to 30 Nov), VIIRS only, villages with a detection: ' + ', '.join('%s: %d' % (y, len(base[y]['villages'])) for y in years))
    print('fires_points.json: %d detections of the two autumns in the area · %d KB' % (len(points), os.path.getsize(os.path.join(ROOT, 'fires_points.json')) / 1024))
    # how this lines up with what UNOSAT mapped
    st = json.load(open(os.path.join(ROOT, 'status_unosat_2017.json'), encoding='utf-8'))['villages']
    c = Counter((st[str(v['id'])]['status'], str(v['id']) in out and '2017' in out[str(v['id'])]) for v in V)
    for s in ('destroyed', 'nearby', 'none_detected', 'not_assessed'):
        print('  UNOSAT %-14s fire detected: %3d   none: %3d' % (s, c[(s, True)], c[(s, False)]))


if __name__ == '__main__':
    main()
