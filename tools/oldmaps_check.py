#!/usr/bin/env python3
"""Old maps, step 4: check every sheet against today's ground, by eye.

For each sheet this makes one picture of four close-ups, taken from four different parts of the sheet where today's map has the
most rivers, creeks, coast or main roads to compare with. Today's water lines are drawn in blue and today's main roads in magenta,
over the sheet as it is placed. A red bar shows 100 metres. If the sheet is placed right, the blue and magenta lines run along
the old drawn rivers and roads; where a river has moved in a century they part company, each in its own direction.

    python3 tools/oldmaps_check.py WORK OUTDIR [sheet-tag]

WORK holds dl/ and fix/ (the sheets, from oldmaps_fetch.py and oldmaps_refine.py) and osm/ (today's lines: Overpass API "out geom"
JSON files for way[waterway], way[natural=coastline], way[natural=water] and main roads over the area; © OpenStreetMap contributors).
"""
import glob, json, math, os, sys, warnings
from PIL import Image, ImageDraw
warnings.simplefilter('ignore'); Image.MAX_IMAGE_PIXELS = None
WORK = os.path.abspath(sys.argv[1]); OUT = os.path.abspath(sys.argv[2]); ONLY = sys.argv[3] if len(sys.argv) > 3 else None
os.makedirs(OUT, exist_ok=True)
_cache = {}
def osm():
    if 'w' in _cache: return _cache['w']
    ways = {}
    for f in glob.glob(os.path.join(WORK, 'osm', '*.json')) + glob.glob(os.path.join(WORK, 'osm', 'grid', '*.json')):
        try: els = json.load(open(f))['elements']
        except Exception: continue
        for el in els:
            t = el.get('tags', {}); g = el.get('geometry')
            if not g or el['id'] in ways: continue
            pts = [(p['lon'], p['lat']) for p in g]                          # the third value: a main line, the only kind a small-scale sheet draws
            if t.get('highway'): ways[el['id']] = ('road', pts, t['highway'] in ('trunk', 'primary', 'secondary', 'tertiary'))
            elif t.get('waterway') or t.get('natural') == 'coastline': ways[el['id']] = ('water', pts, t.get('waterway') == 'river' or t.get('natural') == 'coastline')
            elif t.get('natural') == 'water' and t.get('water') not in ('pond', 'reservoir', 'basin'):
                lo = [p[0] for p in pts]; la = [p[1] for p in pts]; size = math.hypot((max(la) - min(la)) * 110574, (max(lo) - min(lo)) * 104000)
                if size > 400: ways[el['id']] = ('water', pts, size > 1500)
    _cache['w'] = list(ways.values()); return _cache['w']
def sheet(d, pat):
    if (d, pat) in _cache: return _cache[(d, pat)]
    for base in ('fix', 'dl'):
        j = glob.glob(os.path.join(WORK, base, d, pat + '.jgw')) or glob.glob(os.path.join(WORK, base, d, pat + '.pgw'))
        if j: break
    j = j[0]; a = [float(x) for x in open(j).read().split()]
    if j.endswith('.pgw'):                                                  # a sheet cut at its frame: white where there is no sheet
        im = Image.open(j[:-4] + '.png').convert('RGBA'); bg = Image.new('RGB', im.size, (255, 255, 255)); bg.paste(im, (0, 0), im); im = bg
    else: im = Image.open(j[:-4] + '.jpg').convert('RGB')
    _cache[(d, pat)] = (im, a[4] - a[0] / 2, a[5] - a[3] / 2, a[0], -a[3]); return _cache[(d, pat)]
def spot(d, pat, lat, lon, out, half_m=900, size=640, roads=True, main_only=False):
    im, W, N, dx, dy = sheet(d, pat)
    hx = half_m / (111320 * math.cos(math.radians(lat))) ; hy = half_m / 110574
    x0, y0 = (lon - hx - W) / dx, (N - (lat + hy)) / dy; x1, y1 = (lon + hx - W) / dx, (N - (lat - hy)) / dy
    crop = im.crop((int(x0), int(y0), int(x1), int(y1))).resize((size, size), Image.BICUBIC)
    k = size / (x1 - x0); dr = ImageDraw.Draw(crop)
    for kind, pts, main in osm():
        if not any(lon - 2 * hx <= lo <= lon + 2 * hx and lat - 2 * hy <= la <= lat + 2 * hy for lo, la in pts): continue
        if kind == 'road' and not roads: continue
        if main_only and not main: continue
        q = [(((lo - W) / dx - int(x0)) * k, ((N - la) / dy - int(y0)) * k) for lo, la in pts]
        dr.line(q, fill=(0, 80, 255) if kind == 'water' else (230, 0, 200), width=2)
    mpp = 2 * half_m / size; barm = 500 if main_only else 100; bar = barm / mpp
    dr.rectangle((12, size - 22, 12 + bar, size - 14), fill=(255, 0, 0)); dr.text((16 + bar, size - 26), '%d m' % barm, fill=(255, 0, 0))
    crop.save(out, quality=88); return mpp
SHEETS = [('early', '84C03-84C07*', 'a_84C03-07_1905'), ('early', '84C04-84C08*', 'a_84C04-08_1905'), ('early', '84D01-84D05*', 'a_84D01-05_1904'),
          ('early', '84D02-84D06*', 'a_84D02-06_1904'), ('early', '84D11-84D15*', 'a_84D11-15_1891'),
          ('later', '84D9_OILatLon*', 'b_84D09_1935'), ('later', '84D10_OILatLon*', 'b_84D10_1936'), ('later', '84D11_OILatLon*', 'b_84D11_1925'),
          ('later', '84D13_OILatLon*', 'b_84D13_1936'), ('later', '84D14_OI_*', 'b_84D14_1942'), ('later', '84D15_OILatLon*', 'b_84D15_1925'),
          ('later', '84D16_OILatLon*', 'b_84D16_1925'), ('half', '84-C-SW*', 'b_half_84CSW_1941'), ('half', '84-C-SE_1938*', 'b_half_84CSE_1938'),
          ('half', '84-D-NW*', 'b_half_84DNW_1942'), ('half', '84-D-SE*', 'b_half_84DSE_1926'),
          ('ams', 'NF46-14*', 'c_NF46-14_1954'), ('ams', 'NF46-10*', 'c_NF46-10_1954'), ('ams', 'NF46-15*', 'c_NF46-15_1954'), ('ams', 'NE46-03*', 'c_NE46-03_1955')]
only = ONLY
# Spots chosen by hand where the automatic choice lands on ground the old sheet leaves blank (unsurveyed hills, open sea),
# or where a difference found during the check should stay on show.
MANUAL = {
 'a_84C03-07_1905': [(21.2926, 92.0857), (21.4537, 92.0816), (21.2680, 92.2740), (21.3300, 92.2900)],
 'a_84C04-08_1905': [(21.0448, 92.2475), (21.1061, 92.2463), (21.1255, 92.2340), (21.0828, 92.2666)],
 'a_84D02-06_1904': [(20.7166, 92.4133), (20.6125, 92.3258), (20.7350, 92.4350), (20.6900, 92.4400)],
 # the 1954 sheets are at 1:250,000: spots with a main road or a town, which is what such a sheet draws and what does not move
 'c_NF46-14_1954': [(20.8200, 92.3700), (20.8700, 92.5400), (20.4800, 92.7600), (20.1450, 92.8950)],
 'c_NF46-10_1954': [(21.1200, 92.3000), (21.0350, 92.2500), (21.3300, 92.3300), (21.0450, 92.5900)],
 'c_NF46-15_1954': [(20.5900, 93.1900), (20.3620, 93.2720), (20.0800, 93.3700), (20.8000, 93.2000)],     # Myohaung (Mrauk U), Minbya, Myebon, the Lemro
 'c_NE46-03_1955': [(19.4260, 93.5460), (19.8600, 93.1000), (19.7800, 94.0300), (19.0900, 93.8600)],     # Kyaukpyu town, East Boronga, An, Ramree
}
ways = osm(); report = {}
for d, pat, tag in SHEETS:
    if only and only not in tag: continue
    im, W, N, dx, dy = sheet(d, pat); w, h = im.size
    E, S = W + dx * w, N - dy * h; nx, ny = (6, 3) if w > h * 1.5 else (4, 4)
    cells = {}
    for kind, pts, _main in ways:
        for (lo, la), (lo2, la2) in zip(pts, pts[1:]):
            if not (W < lo < E and S < la < N): continue
            c = (min(nx - 1, int((lo - W) / (E - W) * nx)), min(ny - 1, int((N - la) / (N - S) * ny)))
            L = math.hypot((lo2 - lo) * 104000, (la2 - la) * 110574)
            L *= 0.6 if kind == 'road' else 1.0
            e = cells.setdefault(c, [0.0, 0.0, 0.0]); e[0] += L; e[1] += lo * L; e[2] += la * L
    picks = []
    for c, e in sorted(cells.items(), key=lambda kv: -kv[1][0]):               # the richest cells first, but not two next to each other
        if all(abs(c[0] - p[0][0]) + abs(c[1] - p[0][1]) >= 2 for p in picks): picks.append((c, e))
        if len(picks) == 4: break
    half = 4000 if d == 'ams' else 1000 if d != 'half' else 1700
    sheet_img = Image.new('RGB', (1290, 1290), (255, 255, 255)); spots = []
    chosen = [(lo, la) for la, lo in MANUAL[tag]] if tag in MANUAL else [(e[1] / e[0], e[2] / e[0]) for c, e in picks]
    for k, (lon, lat) in enumerate(chosen):
        lon = min(max(lon, W + dx * 220), E - dx * 220); lat = min(max(lat, S + dy * 220), N - dy * 220)
        f = os.path.join(OUT, '_tmp.jpg'); mpp = spot(d, pat, lat, lon, f, half_m=half, size=640, main_only=d == 'ams')
        t = Image.open(f); ImageDraw.Draw(t).text((8, 6), '%s  %.4f, %.4f  (%.1f m per pixel)' % (tag, lat, lon, mpp), fill=(200, 0, 0))
        sheet_img.paste(t, ((k % 2) * 650, (k // 2) * 650)); spots.append([round(lat, 4), round(lon, 4)])
    sheet_img.save(os.path.join(OUT, '%s.jpg' % tag), quality=82); report[tag] = spots
    print(tag, len(chosen), 'spots', spots, flush=True)
if os.path.exists(os.path.join(OUT, '_tmp.jpg')): os.remove(os.path.join(OUT, '_tmp.jpg'))
old = {}
if ONLY and os.path.exists(os.path.join(OUT, 'spots.json')): old = json.load(open(os.path.join(OUT, 'spots.json')))
old.update(report); json.dump(old, open(os.path.join(OUT, 'spots.json'), 'w'), indent=1)
