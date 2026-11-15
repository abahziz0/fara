#!/usr/bin/env python3
"""Township and village-tract boundaries for the four townships of the archive.

Source: "Myanmar - Subnational Administrative Boundaries" (COD-AB), published by UN OCHA on the Humanitarian
Data Exchange under CC BY-IGO, sourced from MIMU: https://data.humdata.org/dataset/cod-ab-mmr
(MIMU's own download of the same boundaries may not be used on an online platform without written
agreement, which is why this archive uses the openly licensed COD-AB edition.)

    python3 tools/build_boundaries.py --from /path/to/unzipped/cod-ab   # first time: cut the extract out of the national files
    python3 tools/build_boundaries.py                                   # afterwards: rebuild from the extract

Writes
    sources/cod_ab_mmr/extract.geojson   the admin 3 and admin 4 features of the four townships, untouched apart from rounding
    boundaries.json                      what the site loads when "Borders" is switched on, and what build.py uses for the gazetteers:
        { src, lic, url,
          towns:  [{ p, n, my, a, c:[lat,lng], g:[polygon[ring[[lat,lng]…]]] }],
          tracts: [{ p, t, n, my, a, c:[lat,lng], town:0|1, g:[…] }],
          lines:  { tract:[[[lat,lng]…]…], town:[…] } }      each border drawn once, not once per side
"""
import argparse, json, os, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, 'sources', 'cod_ab_mmr')
EXTRACT = os.path.join(SRC_DIR, 'extract.geojson')
OUT = os.path.join(ROOT, 'boundaries.json')
TOWNSHIPS = {'MMR012009': 'Maungdaw', 'MMR012010': 'Buthidaung', 'MMR012008': 'Rathedaung', 'MMR012001': 'Sittwe'}
KEEP = ('adm3_name', 'adm3_name1', 'adm3_pcode', 'adm4_name', 'adm4_name1', 'adm4_pcode', 'area_sqkm', 'center_lat',
        'center_lon', 'valid_on', 'version')


def polys(geom):
    return geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]


def cut_extract(folder):
    feats = []
    for level in (3, 4):
        with open(os.path.join(folder, f'mmr_admin{level}.geojson'), encoding='utf-8') as f:
            for ft in json.load(f)['features']:
                p = ft['properties']
                if p.get('adm3_pcode') not in TOWNSHIPS: continue
                geom = {'type': 'MultiPolygon', 'coordinates': [[[[round(x, 6), round(y, 6)] for x, y, *_ in ring] for ring in poly]
                                                                 for poly in polys(ft['geometry'])]}
                feats.append({'type': 'Feature', 'properties': {'level': level, **{k: p.get(k) for k in KEEP if k in p}}, 'geometry': geom})
    os.makedirs(SRC_DIR, exist_ok=True)
    with open(EXTRACT, 'w', encoding='utf-8') as f:
        json.dump({'type': 'FeatureCollection', 'name': 'COD-AB Myanmar v01, admin 3 and 4, four townships of the FARA archive',
                   'license': 'CC BY-IGO', 'source': 'https://data.humdata.org/dataset/cod-ab-mmr', 'features': feats},
                  f, ensure_ascii=False, separators=(',', ':'))
    print(f'extract: {len(feats)} features · {os.path.getsize(EXTRACT)/1024:.0f} KB')


def ring_area_centroid(ring):
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
        k = x0 * y1 - x1 * y0
        a += k; cx += (x0 + x1) * k; cy += (y0 + y1) * k
    if abs(a) < 1e-14: return 0.0, ring[0][0], ring[0][1]
    return a / 2, cx / (3 * a), cy / (3 * a)


def inside(x, y, poly):
    """Point in polygon with holes, even-odd."""
    hit = False
    for ring in poly:
        for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
            if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0: hit = not hit
    return hit


def label_point(geom, hint):
    """A point guaranteed to be inside: the published centre if it is inside, else the centroid of the largest part,
    else the middle of the widest horizontal span through that part."""
    ps = polys(geom)
    if hint and any(inside(hint[0], hint[1], p) for p in ps): return hint
    big = max(ps, key=lambda p: abs(ring_area_centroid(p[0])[0]))
    _, cx, cy = ring_area_centroid(big[0])
    if inside(cx, cy, big): return (cx, cy)
    xs = sorted(x for ring in big for (x0, y0), (x1, y1) in zip(ring, ring[1:]) if (y0 > cy) != (y1 > cy)
                for x in [(x1 - x0) * (cy - y0) / (y1 - y0) + x0])
    spans = [(xs[i + 1] - xs[i], (xs[i] + xs[i + 1]) / 2) for i in range(0, len(xs) - 1, 2)]
    return (max(spans)[1], cy) if spans else (cx, cy)


def build_lines(tracts):
    """Every border once. An edge between two tracts of one township is a tract line; an edge between two
    townships, or with nothing mapped on the other side, is a township line."""
    owners = defaultdict(set)
    for i, t in enumerate(tracts):
        for poly in polys(t['geometry']):
            for ring in poly:
                for a, b in zip(ring, ring[1:]):
                    a, b = tuple(a), tuple(b)
                    if a != b: owners[(a, b) if a < b else (b, a)].add(i)
    kinds = {}
    for e, own in owners.items():
        towns = {tracts[i]['properties']['adm3_pcode'] for i in own}
        kinds[e] = 'town' if len(own) == 1 or len(towns) > 1 else 'tract'
    out = {}
    for kind in ('tract', 'town'):
        adj = defaultdict(list)
        for (a, b), k in kinds.items():
            if k == kind: adj[a].append(b); adj[b].append(a)
        used, arcs = set(), []

        def walk(start, nxt):
            arc, prev, cur = [start, nxt], start, nxt
            used.add((start, nxt) if start < nxt else (nxt, start))
            while len(adj[cur]) == 2 and cur != start:
                n = adj[cur][0] if adj[cur][1] == prev else adj[cur][1]
                e = (cur, n) if cur < n else (n, cur)
                if e in used: break
                used.add(e); arc.append(n); prev, cur = cur, n
            return arc
        for node in [n for n in adj if len(adj[n]) != 2]:        # start at junctions and loose ends
            for n in adj[node]:
                if ((node, n) if node < n else (n, node)) not in used: arcs.append(walk(node, n))
        for node in adj:                                          # what is left are closed loops (islands)
            for n in adj[node]:
                if ((node, n) if node < n else (n, node)) not in used: arcs.append(walk(node, n))
        out[kind] = [[[round(y, 5), round(x, 5)] for x, y in arc] for arc in arcs]
    shared = sum(1 for own in owners.values() if len(own) > 1)
    return out, len(owners), shared


def latlng(geom):
    return [[[[round(y, 5), round(x, 5)] for x, y in ring] for ring in poly] for poly in polys(geom)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--from', dest='folder', help='folder holding mmr_admin3.geojson and mmr_admin4.geojson')
    a = ap.parse_args()
    if a.folder: cut_extract(a.folder)
    if not os.path.exists(EXTRACT): sys.exit('no extract yet: run once with --from <folder of the unzipped COD-AB GeoJSON>')
    feats = json.load(open(EXTRACT, encoding='utf-8'))['features']
    towns = [f for f in feats if f['properties']['level'] == 3]
    tracts = [f for f in feats if f['properties']['level'] == 4 and f['properties'].get('adm4_pcode')]

    lines, n_edges, n_shared = build_lines(tracts)
    doc = {'src': 'UN OCHA COD-AB Myanmar v01 (source: MIMU)', 'lic': 'CC BY-IGO', 'url': 'https://data.humdata.org/dataset/cod-ab-mmr',
           'towns': [], 'tracts': [], 'lines': lines}
    for f in sorted(towns, key=lambda f: f['properties']['adm3_pcode']):
        p = f['properties']
        x, y = label_point(f['geometry'], (p['center_lon'], p['center_lat']))
        doc['towns'].append({'p': p['adm3_pcode'], 'n': p['adm3_name'], 'my': p.get('adm3_name1'), 'a': round(p['area_sqkm'], 1),
                             'c': [round(y, 5), round(x, 5)], 'g': latlng(f['geometry'])})
    for f in sorted(tracts, key=lambda f: f['properties']['adm4_pcode']):
        p = f['properties']
        x, y = label_point(f['geometry'], (p['center_lon'], p['center_lat']))
        doc['tracts'].append({'p': p['adm4_pcode'], 't': p['adm3_pcode'], 'n': p['adm4_name'], 'my': p.get('adm4_name1'),
                              'a': round(p['area_sqkm'], 2), 'c': [round(y, 5), round(x, 5)],
                              'town': 1 if p['adm4_pcode'][9:10] == '7' else 0, 'g': latlng(f['geometry'])})
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, separators=(',', ':'))
    pts = lambda arcs: sum(len(a) for a in arcs)
    print(f'boundaries.json: {len(doc["towns"])} townships · {len(doc["tracts"])} tracts · {n_edges} edges, {n_shared} shared · '
          f'{len(lines["tract"])} tract lines ({pts(lines["tract"])} points) · {len(lines["town"])} township lines ({pts(lines["town"])} points) · '
          f'{os.path.getsize(OUT)/1024:.0f} KB')

    # how the archive's own tract codes line up with the boundaries
    V = json.load(open(os.path.join(ROOT, 'arakan_villages.json'), encoding='utf-8'))
    codes = {t['p'] for t in doc['tracts']}
    have = {v.get('pcode_village_tract') for v in V if v.get('pcode_village_tract')}
    by = {t['p']: t for t in doc['tracts']}
    ok = out_ = 0
    for v in V:
        t = by.get(v.get('pcode_village_tract'))
        if not t or not v.get('lat'): continue
        if any(inside(float(v['lat']), float(v['lng']), [[(q[0], q[1]) for q in ring] for ring in poly]) for poly in t['g']): ok += 1
        else: out_ += 1
    print(f'archive tract codes: {len(have)} · found among the boundaries: {len(have & codes)} · missing: {sorted(have - codes)[:8]}')
    print(f'villages whose point falls inside their own tract: {ok} · outside: {out_}')


if __name__ == '__main__':
    main()
