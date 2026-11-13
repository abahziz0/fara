#!/usr/bin/env python3
"""Match UNOSAT's 2017 destroyed-settlement zones to FARA's villages.

    python3 tools/match_unosat.py

Source (kept in sources/unosat_2017/, CC BY-SA, credit UNOSAT):
  "Destroyed areas in Buthidaung, Maungdaw, and Rathedaung Townships of Rakhine State in Myanmar"
  https://data.humdata.org/dataset/destroyed-areas-in-buthidaung-maungdaw-and-rathedaung-townships-of-rakhine-state-in-myanmar-2727
  Damage_Analysis_Rakhine_20171011_shp.zip — 1,862 zones of destroyed buildings seen in satellite imagery
  of 31 Aug – 11 Oct 2017, plus the outline of the area UNOSAT analysed. Not field validated.

A FARA village is a single point; UNOSAT's zones are outlines of destroyed building clusters. So the match is
by distance, and the result says what UNOSAT marked AT or NEAR the point, nothing more:

  destroyed       the point lies inside a zone, or at least 1 hectare within 300 m of it is marked destroyed
  nearby          a destroyed zone lies within 500 m, but less than the above
  none_detected   inside the analysed area, with no destroyed zone within 500 m
  not_assessed    outside the area UNOSAT analysed (all of Sittwe township, and a few villages elsewhere)

"none_detected" is NOT "standing": the imagery stops on 11 October 2017, some areas were under cloud,
and destruction continued afterwards.

Writes:
  status_unosat_2017.json   per-village result, keyed by village id
  status_unosat_2017.csv    the same as a review table
  unosat_2017_zones.geojson the zones themselves, for drawing on the map
Because the source is share-alike, these three files are also CC BY-SA 4.0, credit UNOSAT.
"""
import collections, csv, io, json, math, os, struct, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'sources', 'unosat_2017', 'Damage_Analysis_Rakhine_20171011_shp.zip')
PREFIX = 'Damage_Analysis_Rakhine_20171011_shp/'
R_NEAR, R_FAR, GRID, MIN_HA = 300, 500, 15, 1.0

# ---------------------------------------------------------------- minimal shapefile / dBASE readers
def read_dbf(buf, encoding='utf-8'):
    f = io.BytesIO(buf)
    n, hlen, rlen = struct.unpack('<xxxxIHH', f.read(32)[:12])
    fields = []
    while True:
        d = f.read(32)
        if not d or d[0] == 0x0D: break
        fields.append((d[:11].split(b'\x00')[0].decode('ascii', 'replace'), chr(d[11]), d[16]))
    f.seek(hlen)
    rows = []
    for _ in range(n):
        rec = f.read(rlen)
        if len(rec) < rlen: break
        pos, row = 1, {}
        for name, typ, size in fields:
            row[name] = rec[pos:pos+size].decode(encoding, 'replace').strip(); pos += size
        rows.append(row)
    return rows

def read_polygons(buf):
    f = io.BytesIO(buf); f.read(100)
    out = []
    while True:
        h = f.read(8)
        if len(h) < 8: break
        rec = f.read(struct.unpack('>II', h)[1] * 2)
        if struct.unpack('<i', rec[:4])[0] not in (5, 15, 25): out.append([]); continue
        nparts, npts = struct.unpack('<2i', rec[36:44])
        parts = list(struct.unpack('<%di' % nparts, rec[44:44+4*nparts]))
        o = 44 + 4*nparts
        pts = [struct.unpack('<2d', rec[o+16*i:o+16*i+16]) for i in range(npts)]
        out.append([pts[a:b] for a, b in zip(parts, parts[1:] + [npts])])
    return out

# ---------------------------------------------------------------- geometry, in metres on a local flat grid
LAT0 = 20.9
KX, KY = 111320 * math.cos(math.radians(LAT0)), 110540
def xy(lon, lat): return (lon * KX, lat * KY)
def in_ring(x, y, ring):
    ins = False
    for i in range(len(ring) - 1):
        (x1, y1), (x2, y2) = ring[i], ring[i+1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: ins = not ins
    return ins
def in_poly(x, y, rings):
    c = False
    for r in rings:
        if in_ring(x, y, r): c = not c
    return c
def d_seg(px, py, a, b):
    (x1, y1), (x2, y2) = a, b; dx, dy = x2 - x1, y2 - y1
    t = 0 if dx == dy == 0 else max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))
def d_poly(x, y, rings):
    if in_poly(x, y, rings): return 0.0
    return min(d_seg(x, y, rg[i], rg[i+1]) for rg in rings for i in range(len(rg) - 1))
def iso(d): return '%s-%s-%s' % (d[:4], d[4:6], d[6:8]) if d and len(d) == 8 else None

def unverified(v):
    try: la, ln = float(v['lat']), float(v['lng'])
    except Exception: return True
    return v.get('coord_status') == 'unverified' or not (18 < la < 23.5 and 91 < ln < 95)

def main():
    z = zipfile.ZipFile(SRC)
    rows = read_dbf(z.read(PREFIX + 'Damage_Zones_Rakhine_20171011.dbf'))
    polys = read_polygons(z.read(PREFIX + 'Damage_Zones_Rakhine_20171011.shp'))
    extent = [[xy(*p) for p in ring] for ring in read_polygons(z.read(PREFIX + 'Analysis_extent_Maungdaw_20171011.shp'))[0]]
    zones = []
    for rings_ll, r in zip(polys, rows):
        if not rings_ll: continue
        rings = [[xy(*p) for p in ring] for ring in rings_ll]
        xs = [p[0] for rg in rings for p in rg]; ys = [p[1] for rg in rings for p in rg]
        zones.append(dict(rings=rings, ll=rings_ll, bb=(min(xs), min(ys), max(xs), max(ys)),
                          date=iso(r['SensorDate']), sensor=r['SensorID'], conf=r['Confidence'], note=r['Notes']))

    V = json.load(open(os.path.join(ROOT, 'arakan_villages.json'), encoding='utf-8'))
    result, table = {}, []
    disc = [(gx, gy) for gx in range(-R_NEAR, R_NEAR + 1, GRID) for gy in range(-R_NEAR, R_NEAR + 1, GRID) if gx*gx + gy*gy <= R_NEAR*R_NEAR]
    for v in V:
        rec = dict(source='UNOSAT', imagery='2017-08-31/2017-10-11')
        if unverified(v):
            rec.update(status='not_assessed', reason='no verified location')
        else:
            x, y = xy(float(v['lng']), float(v['lat']))
            if not in_poly(x, y, extent):
                rec.update(status='not_assessed', reason='outside the area UNOSAT analysed')
            else:
                near = [zz for zz in zones if zz['bb'][0] - R_FAR < x < zz['bb'][2] + R_FAR and zz['bb'][1] - R_FAR < y < zz['bb'][3] + R_FAR]
                dist = [(d_poly(x, y, zz['rings']), zz) for zz in near]
                dist = [(d, zz) for d, zz in dist if d <= R_FAR]
                close = [zz for d, zz in dist if d <= R_NEAR]
                hits = sum(1 for gx, gy in disc if any(zz['bb'][0] <= x+gx <= zz['bb'][2] and zz['bb'][1] <= y+gy <= zz['bb'][3]
                                                       and in_poly(x+gx, y+gy, zz['rings']) for zz in close))
                ha = round(hits * GRID * GRID / 1e4, 2)
                dmin = round(min((d for d, _ in dist), default=-1))
                inside = any(d == 0 for d, _ in dist)
                if inside or ha >= MIN_HA: status = 'destroyed'
                elif dist: status = 'nearby'
                else: status = 'none_detected'
                rec['status'] = status
                if dist:
                    use = close or [zz for _, zz in dist]
                    dates = sorted({zz['date'] for zz in use if zz['date']})
                    rec.update(point_inside_zone=inside, nearest_zone_m=dmin, destroyed_ha_within_300m=ha,
                               share_of_300m_circle=round(hits / len(disc), 3), zones=len(use),
                               first_seen=dates[0] if dates else None, last_seen=dates[-1] if dates else None,
                               confidence='uncertain' if all(zz['conf'] == 'Uncertain' for zz in use) else 'medium',
                               cloud_note=any(zz['note'] for zz in use))
        result[str(v['id'])] = rec
        table.append(dict(id=v['id'], rohingya_name=v.get('rohingya_name') or '', name=v.get('name') or '', township=v.get('township') or '',
                          village_tract=v.get('village_tract') or '', lat=v.get('lat'), lng=v.get('lng'),
                          **{k: rec.get(k, '') for k in ('status', 'reason', 'point_inside_zone', 'nearest_zone_m', 'destroyed_ha_within_300m',
                                                          'share_of_300m_circle', 'zones', 'first_seen', 'last_seen', 'confidence', 'cloud_note')}))

    meta = dict(source='UNOSAT — Destroyed areas in Buthidaung, Maungdaw, and Rathedaung Townships of Rakhine State in Myanmar',
                url='https://data.humdata.org/dataset/destroyed-areas-in-buthidaung-maungdaw-and-rathedaung-townships-of-rakhine-state-in-myanmar-2727',
                licence='CC BY-SA 4.0 (source is CC BY-SA; credit UNOSAT)', imagery='31 August – 11 October 2017', field_validated=False,
                method='point-in-zone, or >= %g ha marked destroyed within %d m = destroyed; any zone within %d m = nearby' % (MIN_HA, R_NEAR, R_FAR),
                caution='none_detected does not mean standing: imagery ends 11 October 2017, some areas were under cloud, and destruction continued afterwards.')
    json.dump(dict(meta=meta, villages=result), open(os.path.join(ROOT, 'status_unosat_2017.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, 'status_unosat_2017.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(table[0].keys())); w.writeheader(); w.writerows(table)
    feats = [dict(type='Feature', properties=dict(date=zz['date'], sensor=zz['sensor'], confidence=zz['conf'].lower(), **({'note': zz['note']} if zz['note'] else {})),
                  geometry=dict(type='Polygon', coordinates=[[[round(a, 5), round(b, 5)] for a, b in ring] for ring in zz['ll']])) for zz in zones]
    json.dump(dict(type='FeatureCollection', name='UNOSAT destroyed zones, northern Rakhine, 31 Aug – 11 Oct 2017', licence='CC BY-SA 4.0, UNOSAT', features=feats),
              open(os.path.join(ROOT, 'unosat_2017_zones.geojson'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

    c = collections.Counter(r['status'] for r in result.values())
    print('zones: %d' % len(zones))
    print('villages:', dict(c))
    by = collections.Counter((BY[k]['township'], r['status']) for k, r in result.items() for BY in [{str(v['id']): v for v in V}])
    for t in sorted({t for t, _ in by}):
        print('  %-11s' % t, {s: by[(t, s)] for s in ('destroyed', 'nearby', 'none_detected', 'not_assessed') if by[(t, s)]})

if __name__ == '__main__':
    main()
