#!/usr/bin/env python3
"""Old maps, step 3: cut the sheets into map tiles.

    python3 tools/oldmaps_tile.py WORKDIR oldmaps [layer ...]

Cut georeferenced lat-lon map sheets into web-map tiles (XYZ, 256 px, WebP). No GDAL needed.
Each sheet is a plain rectangle in latitude and longitude; inside one tile at zoom 14 the difference between that
and the web map's projection is far below a pixel, so each tile is a straight crop-and-resize of the sheet.
With layer letters after the folder, only those layers are cut again and the others are left as they are."""
import os, sys, math, glob, json, shutil
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
WORK = os.path.abspath(sys.argv[1]); DL = os.path.join(WORK, 'dl'); FIX = os.path.join(WORK, 'fix'); OUT = sys.argv[2]; ONLY = sys.argv[3:]; ZMIN = 9
# the sheets of 1954 and 1955 are at 1:250,000, four times smaller than the one-inch sheets: one pixel of the scan is 36 m, which is zoom 12.
# They are cut to zoom 13 so that nothing of the scan is lost; beyond that the map only enlarges them.
ZMAXES = {'a': 14, 'b': 14, 'c': 13}; QUALITY = {'a': 62, 'b': 62, 'c': 74}
YEARS = {'a': '1890–1906', 'b': '1925–1944', 'c': '1954–1955'}
NOTE = ('Old map sheets cut into map tiles. a, b: Survey of India sheets. Scans and first placement: Old Survey of India Maps community and Horst Held '
        '(Zenodo 18975982, 11367062, 13346102), CC BY 4.0. pinned_to_printed_grid: the sheet prints its 5-minute latitude/longitude grid and was warped so '
        'every grid line falls on its true position (tools/oldmaps_refine.py). c: United States Army Map Service, Burma 1:250,000, series U542, compiled 1954 and 1955, '
        'printed 1959 and 1960 (public domain); scans from the University of Texas Libraries. These came with no coordinates and were placed by FARA on their printed '
        '10,000-yard grid (tools/oldmaps_ams.py).')
LAYERS = {
 # the 1890 sheet 84 C/12-16 is left out: it is almost blank (the hills were not yet surveyed) and showed as an empty white patch
 'a': [('early', '84C03-84C07*'), ('early', '84C04-84C08*'), ('early', '84D01-84D05*'), ('early', '84D02-84D06*'), ('early', '84D11-84D15*')],
 'b': [('half', '84-C-SW*'), ('half', '84-C-SE_1938*'), ('half', '84-D-NW*'), ('half', '84-D-SE*'),
       ('later', '84D9_OILatLon*'), ('later', '84D10_OILatLon*'), ('later', '84D11_OILatLon*'), ('later', '84D13_OILatLon*'),
       ('later', '84D14_OI_*'), ('later', '84D15_OILatLon*'), ('later', '84D16_OILatLon*')],
 'c': [('ams', 'NF46-14*'), ('ams', 'NF46-10*'), ('ams', 'NF46-15*'), ('ams', 'NE46-03*')],
}
def find(d, pat):
    """the sheet's world file, its picture, and whether it was corrected to its own printed grid"""
    for base in (FIX, DL):
        for wext, pext in (('.jgw', '.jpg'), ('.pgw', '.png')):
            j = glob.glob(os.path.join(base, d, pat + wext))
            if j: assert len(j) == 1, (pat, j); return j[0], j[0][:-4] + pext, base == FIX
    raise SystemExit('sheet not found: %s/%s' % (d, pat))
def lon2x(lon, z): return (lon + 180) / 360 * 2 ** z
def lat2y(lat, z): return (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * 2 ** z
def y2lat(y, z): return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / 2 ** z))))
def x2lon(x, z): return x / 2 ** z * 360 - 180
meta = {}
if ONLY and os.path.exists(os.path.join(OUT, 'sheets.json')):               # keep what is known about the layers that are not cut again
    meta = {k: v for k, v in json.load(open(os.path.join(OUT, 'sheets.json'), encoding='utf-8')).items() if k in LAYERS and k not in ONLY}
for key, sheets in LAYERS.items():
    if ONLY and key not in ONLY: continue
    ZMAX = ZMAXES[key]
    shutil.rmtree(os.path.join(OUT, key), ignore_errors=True)
    tmp = os.path.join(OUT, '_tmp', key); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    used = []; box = [180, 90, -180, -90]
    for d, pat in sheets:
        j, pic, pinned = find(d, pat)                                      # pinned: corrected to its own printed grid
        a = [float(x) for x in open(j).read().split()]
        cut = pic.endswith('.png')                                         # a picture with transparency: cut at its printed frame
        im = Image.open(pic).convert('RGBa' if cut else 'RGB'); w, h = im.size
        W = a[4] - a[0] / 2; N = a[5] - a[3] / 2; dx = a[0]; dy = -a[3]; E = W + dx * w; S = N - dy * h
        used.append({'file': os.path.basename(j)[:-4] if cut else os.path.basename(j)[:-9], 'set': d, 'w': round(W, 4), 's': round(S, 4), 'e': round(E, 4), 'n': round(N, 4), 'pinned_to_printed_grid': pinned})
        box = [min(box[0], W), min(box[1], S), max(box[2], E), max(box[3], N)]
        z = ZMAX; n = 0
        for tx in range(int(lon2x(W, z)), int(lon2x(E, z)) + 1):
            for ty in range(int(lat2y(N, z)), int(lat2y(S, z)) + 1):
                tw, te, tn, ts = x2lon(tx, z), x2lon(tx + 1, z), y2lat(ty, z), y2lat(ty + 1, z)
                cw, ce, cn, cs = max(tw, W), min(te, E), min(tn, N), max(ts, S)
                if ce <= cw or cn <= cs: continue
                px0 = round((cw - tw) / (te - tw) * 256); px1 = round((ce - tw) / (te - tw) * 256)
                py0 = round((tn - cn) / (tn - ts) * 256); py1 = round((tn - cs) / (tn - ts) * 256)
                if px1 <= px0 or py1 <= py0: continue
                src = ((cw - W) / dx, (N - cn) / dy, (ce - W) / dx, (N - cs) / dy)
                piece = im.resize((px1 - px0, py1 - py0), Image.LANCZOS, box=src)
                f = os.path.join(tmp, '%d_%d.png' % (tx, ty))
                t = Image.open(f).convert('RGBA') if os.path.exists(f) else Image.new('RGBA', (256, 256), (0, 0, 0, 0))
                if cut: t.alpha_composite(piece.convert('RGBA'), (px0, py0))
                else: t.paste(piece, (px0, py0))
                t.save(f, compress_level=1); n += 1
        print(key, os.path.basename(j)[:40], n, 'tiles', flush=True); im.close()
    # pyramid: z14 pngs -> webp, then each lower zoom from its four children
    cur = {}
    for f in glob.glob(os.path.join(tmp, '*.png')):
        x, y = map(int, os.path.basename(f)[:-4].split('_')); cur[(x, y)] = Image.open(f).convert('RGBA')   # empty tiles at a sheet's edge are kept: the map asks for them
    total = 0
    for z in range(ZMAX, ZMIN - 1, -1):
        for (x, y), t in cur.items():
            d = os.path.join(OUT, key, str(z), str(x)); os.makedirs(d, exist_ok=True)
            t.save(os.path.join(d, '%d.webp' % y), 'WEBP', quality=QUALITY[key], method=5); total += os.path.getsize(os.path.join(d, '%d.webp' % y))
        nxt = {}
        for (x, y), t in cur.items():
            p = (x // 2, y // 2)
            if p not in nxt: nxt[p] = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
            nxt[p].paste(t, ((x % 2) * 256, (y % 2) * 256))
        print(key, 'zoom', z, len(cur), 'tiles', flush=True)
        cur = {p: t.resize((256, 256), Image.LANCZOS) for p, t in nxt.items()}
    meta[key] = {'sheets': used, 'bounds': [round(v, 4) for v in box], 'minzoom': ZMIN, 'maxzoom': ZMAX, 'bytes': total, 'years': YEARS[key]}
    shutil.rmtree(tmp)
shutil.rmtree(os.path.join(OUT, '_tmp'), ignore_errors=True)
meta = {k: meta[k] for k in LAYERS if k in meta}; meta['note'] = NOTE
json.dump(meta, open(os.path.join(OUT, 'sheets.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(json.dumps({k: (v['bounds'], v['bytes']) for k, v in meta.items() if k in LAYERS}))
