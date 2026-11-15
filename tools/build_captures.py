#!/usr/bin/env python3
"""Look up, once and for all villages, which earlier satellite captures Esri's World Imagery Wayback
archive holds of each village and the day each one was taken. The site then shows capture dates
instantly instead of asking Esri's (slow) metadata server while a visitor waits.

    python3 tools/build_captures.py            # resume / fill in whatever is missing
    python3 tools/build_captures.py --refresh  # also re-check villages already done for newer releases
    python3 tools/build_captures.py --only 199,204

Writes
    sources/esri_wayback/captures_raw.jsonl   one line per village, kept so a later run only asks for what is new
    captures.json                             compact file the site loads on demand

Method (the same one the site uses live, see loadHistory in fara_template.html):
  1. Ask the Wayback tile map for the village's zoom-17 tile in the newest release. The answer names the
     release that tile really comes from; everything in between is the same picture. Step to the release
     before that and repeat until the archive runs out.
  2. For each distinct picture, ask that release's metadata layer for the capture date, resolution and
     satellite at the village's point.
  3. Ask whether that release also has a zoom-18 tile there (decides how far the viewer can zoom).
Every request has a time limit and is retried; a date that cannot be found is stored as null and the site
then labels the picture "by <release date>".
"""
import argparse, json, math, os, sys, threading, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WB = 'https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery'
WB_CFG = 'https://s3-us-west-2.amazonaws.com/config.maptiles.arcgis.com/waybackconfig.json'
RAW = os.path.join(ROOT, 'sources', 'esri_wayback', 'captures_raw.jsonl')
OUT = os.path.join(ROOT, 'captures.json')
UA = {'User-Agent': 'fara-archive-build/1.0 (village name archive; one-off capture date lookup)'}

stats = {'req': 0, 'retry': 0, 'fail': 0}
lock = threading.Lock()


def get_json(url, timeout=20, tries=4):
    last = None
    for n in range(tries):
        with lock:
            stats['req'] += 1
            if n: stats['retry'] += 1
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                j = json.loads(r.read().decode('utf-8'))
            if isinstance(j, dict) and j.get('error'):
                raise RuntimeError(str(j['error'])[:120])
            return j
        except Exception as e:                                    # noqa: BLE001 - any network trouble is retried
            last = e
            time.sleep(0.6 * (n + 1) ** 2)
    with lock: stats['fail'] += 1
    raise RuntimeError(f'{url[:110]} … {last}')


def tile_xy(lat, lng, z):
    n = 2 ** z
    x = int((lng + 180) / 360 * n)
    y = int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)
    return x, y


def load_releases():
    cfg = get_json(WB_CFG)
    rels = []
    for k, v in cfg.items():
        day = v['itemTitle'][-11:-1]
        if len(day) == 10 and day[4] == '-':
            rels.append({'rel': int(k), 'released': day, 'meta': v['metadataLayerUrl']})
    rels.sort(key=lambda r: r['released'], reverse=True)          # newest first
    return rels


def capture(rel, lat, lng):
    """Capture date of one release at this point: the zoom-17 metadata layer, then its neighbours."""
    geom = json.dumps({'x': lng, 'y': lat, 'spatialReference': {'wkid': 4326}}, separators=(',', ':'))
    q = ('f=json&where=1%3D1&outFields=SRC_DATE2,NICE_DESC,SAMP_RES,SRC_ACC&returnGeometry=false'
         '&geometryType=esriGeometryPoint&spatialRel=esriSpatialRelIntersects&geometry=' + urllib.parse.quote(geom))
    failed = False
    for layer in (6, 7, 5):
        try:
            j = get_json(f"{rel['meta']}/{layer}/query?{q}", timeout=25)
        except RuntimeError:
            failed = True
            continue
        feats = [f['attributes'] for f in j.get('features') or [] if (f.get('attributes') or {}).get('SRC_DATE2')]
        if feats:
            a = max(feats, key=lambda f: f['SRC_DATE2'])
            day = time.strftime('%Y-%m-%d', time.gmtime(a['SRC_DATE2'] / 1000))
            return day, a.get('SAMP_RES'), (a.get('NICE_DESC') or '').strip() or None, False
    return None, None, None, failed


def village(v, rels, index):
    lat, lng = float(v['lat']), float(v['lng'])
    x17, y17 = tile_xy(lat, lng, 17)
    x18, y18 = tile_xy(lat, lng, 18)
    versions, i = [], 0
    while i < len(rels):
        j = get_json(f"{WB}/MapServer/tilemap/{rels[i]['rel']}/17/{y17}/{x17}")
        if not j.get('data') or j['data'][0] != 1:
            break                                                 # no imagery this far back
        k = index.get(j['select'][0], i) if j.get('select') else i
        if k < i: k = i
        versions.append(k)
        i = k + 1
    out, incomplete = [], False
    for k in versions:
        rel = rels[k]
        day, res, src, failed = capture(rel, lat, lng)
        incomplete = incomplete or failed
        try:
            tm = get_json(f"{WB}/MapServer/tilemap/{rel['rel']}/18/{y18}/{x18}")
            z18 = bool(tm.get('data') and tm['data'][0] == 1)
        except RuntimeError:
            z18, incomplete = False, True
        out.append({'rel': rel['rel'], 'released': rel['released'], 'date': day, 'res': res, 'src': src, 'z18': z18})
    return {'id': v['id'], 'lat': lat, 'lng': lng, 'newest': rels[0]['rel'], 'incomplete': incomplete, 'caps': out}


def read_raw():
    done = {}
    if os.path.exists(RAW):
        with open(RAW, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    done[r['id']] = r                             # a later line replaces an earlier one
    return done


def write_site_file(done, rels):
    """captures.json: { made, newest, src:[names], v:{ id:[[release, yyyymmdd|0, cm|0, srcIndex|-1, z18, releasedYyyymmdd], …] } }"""
    srcs, src_ix, out = [], {}, {}
    for vid, r in sorted(done.items()):
        seen, rows, kept = set(), [], []
        for c in r['caps']:                                       # newest release first, as the archive was walked
            key = c['date'] or 'r' + str(c['rel'])
            if key in seen: continue                              # the same capture republished in an earlier release
            seen.add(key); kept.append(c)
        # the picture in the newest release is what the live map shows, so it stays first; the rest run newest capture first
        caps = kept[:1] + sorted(kept[1:], key=lambda c: (c['date'] or c['released'], c['released']), reverse=True)
        for c in caps:
            s = -1
            if c['src']:
                if c['src'] not in src_ix: src_ix[c['src']] = len(srcs); srcs.append(c['src'])
                s = src_ix[c['src']]
            rows.append([c['rel'], int(c['date'].replace('-', '')) if c['date'] else 0,
                         round(c['res'] * 100) if c['res'] else 0, s, 1 if c['z18'] else 0,
                         int(c['released'].replace('-', ''))])
        if rows: out[str(vid)] = rows
    doc = {'made': time.strftime('%Y-%m-%d'), 'newest': rels[0]['rel'], 'newest_released': rels[0]['released'],
           'src': srcs, 'v': out}
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(doc, f, separators=(',', ':'), ensure_ascii=False)
    return doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--refresh', action='store_true', help='re-check finished villages against releases published since')
    ap.add_argument('--only', help='comma-separated village ids')
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--write-only', action='store_true', help='ask nothing; just rewrite captures.json from what has been looked up so far')
    a = ap.parse_args()

    villages = [v for v in json.load(open(os.path.join(ROOT, 'arakan_villages.json'), encoding='utf-8'))
                if v.get('lat') and v.get('lng') and v.get('coord_status') != 'unverified']
    if a.only:
        want = {int(x) for x in a.only.split(',')}
        villages = [v for v in villages if v['id'] in want]
    rels = load_releases()
    index = {r['rel']: i for i, r in enumerate(rels)}
    os.makedirs(os.path.dirname(RAW), exist_ok=True)
    done = read_raw()

    def needed(v):
        r = done.get(v['id'])
        if not r or r.get('incomplete'): return True
        if abs(r['lat'] - float(v['lat'])) > 1e-6 or abs(r['lng'] - float(v['lng'])) > 1e-6: return True   # the point moved
        return a.refresh and r.get('newest') != rels[0]['rel']
    todo = [] if a.write_only else [v for v in villages if needed(v)]
    print(f'{len(rels)} releases ({rels[-1]["released"]} … {rels[0]["released"]}) · {len(villages)} villages · {len(todo)} to look up', flush=True)

    t0, n, errors = time.time(), 0, []
    with open(RAW, 'a', encoding='utf-8') as raw, ThreadPoolExecutor(a.workers) as pool:
        futs = {pool.submit(village, v, rels, index): v for v in todo}
        for fut in as_completed(futs):
            v = futs[fut]; n += 1
            try:
                r = fut.result()
                done[r['id']] = r
                raw.write(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n'); raw.flush()
            except Exception as e:                                # noqa: BLE001
                errors.append((v['id'], str(e)[:160]))
            if n % 25 == 0 or n == len(todo):
                el = time.time() - t0
                print(f'  {n}/{len(todo)} villages · {stats["req"]} requests ({stats["retry"]} retries, {stats["fail"]} gave up) · '
                      f'{el/60:.1f} min · about {el/n*(len(todo)-n)/60:.1f} min left', flush=True)

    doc = write_site_file({v['id']: done[v['id']] for v in json.load(open(os.path.join(ROOT, 'arakan_villages.json'), encoding='utf-8')) if v['id'] in done}, rels)
    caps = [c for rows in doc['v'].values() for c in rows]
    print(f'captures.json: {len(doc["v"])} villages · {len(caps)} captures · {sum(1 for c in caps if not c[1])} without a capture date · '
          f'{os.path.getsize(OUT)/1024:.0f} KB · {stats["req"]} requests in all')
    still = [vid for vid, r in done.items() if r.get('incomplete')]
    if errors or still:
        print(f'{len(errors)} villages failed outright, {len(still)} have gaps: run again to fill them in')
        for e in errors[:10]: print('   ', e)
        sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
