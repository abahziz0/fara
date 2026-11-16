#!/usr/bin/env python3
"""Old maps, step 2: pin each sheet to its own printed latitude/longitude grid.

The sheets were placed by their four corners. Inside a sheet the paper has stretched unevenly, so a printed grid line can sit
tens of metres (on one sheet, over a hundred) from where a straight-line placement puts it. Every sheet that prints the 5-minute
grid is corrected here: each grid line is found along its length, and the picture is warped so the line falls exactly where its
latitude or longitude says. Sheets with no printed grid are left as they were placed.

    python3 tools/oldmaps_refine.py WORKDIR      # writes WORKDIR/fix/<set>/<sheet>.jpg (+ .jgw) and prints the error before and after, in metres
"""
import os, glob, shutil, statistics, sys, warnings
from PIL import Image
warnings.simplefilter('ignore')
Image.MAX_IMAGE_PIXELS = None
WORK = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath('oldmaps_work')
DL = os.path.join(WORK, 'dl'); FIX = os.path.join(WORK, 'fix')
# set, file pattern, 5-minute cells across, cells down (None: count from the east edge with the cell size taken from the height)
SHEETS = [('early', '84D11-84D15*', 6, 3),
          ('later', '84D9_OILatLon*', 3, 3), ('later', '84D10_OILatLon*', 3, 3), ('later', '84D11_OILatLon*', 3, 3), ('later', '84D13_OILatLon*', 3, 3),
          ('later', '84D15_OILatLon*', 3, 3), ('later', '84D16_OILatLon*', 3, 3),
          ('half', '84-C-SE_1938*', 6, 6), ('half', '84-D-SE*', 6, 6), ('half', '84-C-SW*', None, 6)]
S = 14            # each line is measured in this many stretches along its length
WIN = 70          # how far from the expected place a line is looked for, in pixels

def measure(dark, e, lo, hi, vertical):
    """where the line near e actually is, in the stretch lo..hi: (offset in px, strength)"""
    w, h = dark.size
    a, b = max(0, int(round(e)) - WIN), min((w if vertical else h), int(round(e)) + WIN)
    box = (a, lo, b, hi) if vertical else (lo, a, hi, b)
    strip = dark.crop(box).resize(((b - a), 1) if vertical else (1, (b - a)), Image.BOX)
    p = list(strip.getdata()); n = len(p)
    base = statistics.median(p)
    best, bi = 0, None
    for i in range(3, n - 3):
        v = p[i] - max(base, (p[i - 3] + p[i + 3]) / 2)
        if v > best and p[i] >= p[i - 1] and p[i] >= p[i + 1]: best, bi = v, i
    if bi is None: return None, 0
    wts = [max(0, p[k] - base) for k in (bi - 1, bi, bi + 1)]
    sub = (wts[2] - wts[0]) / (sum(wts) or 1)                              # centroid of the three brightest columns
    spread = statistics.pstdev(p) or 1
    return a + bi + sub - e, best / spread

def fit(ts, os_, deg=2):
    """smooth curve through the measured offsets, dropping stray readings (a river or a word that looked like a line)"""
    pts = [(t, o) for t, o in zip(ts, os_) if o is not None]
    for _ in range(6):
        if len(pts) < 4: break
        c = polyfit([t for t, _ in pts], [o for _, o in pts], min(deg, len(pts) - 2))
        res = [abs(o - poly(c, t)) for t, o in pts]
        worst = max(range(len(pts)), key=lambda i: res[i])
        if res[worst] <= 3.5: return c
        pts.pop(worst)
    if len(pts) >= 3: return [statistics.median(o for _, o in pts)]
    return None

def polyfit(x, y, deg):
    n = deg + 1; A = [[sum(xi ** (i + j) for xi in x) for j in range(n)] for i in range(n)]; B = [sum(yi * xi ** i for xi, yi in zip(x, y)) for i in range(n)]
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(A[r][i])); A[i], A[p] = A[p], A[i]; B[i], B[p] = B[p], B[i]
        for r in range(i + 1, n):
            f = A[r][i] / A[i][i]
            for c in range(i, n): A[r][c] -= f * A[i][c]
            B[r] -= f * B[i]
    c = [0] * n
    for i in range(n - 1, -1, -1): c[i] = (B[i] - sum(A[i][j] * c[j] for j in range(i + 1, n))) / A[i][i]
    return c
def poly(c, t): return sum(ci * t ** i for i, ci in enumerate(c))

def lines_of(im, nx, ny):
    w, h = im.size
    if nx is None:
        cell = h / ny; xs = []; k = 1
        while w - k * cell > cell * .25: xs.append(w - k * cell); k += 1
        xs = sorted(xs)
    else: xs = [w * i / nx for i in range(1, nx)]
    ys = [h * j / ny for j in range(1, ny)]
    return xs, ys

def survey(im, nx, ny):
    """returns (vertical lines [(x, curve)], horizontal lines [(y, curve)], list of all good readings in px)"""
    w, h = im.size; dark = im.convert('L').point(lambda v: 255 - v)
    xs, ys = lines_of(im, nx, ny); V, Hh, read = [], [], []
    for e in xs:
        ts, os_ = [], []
        for s in range(S):
            lo, hi = h * s // S, h * (s + 1) // S; o, st = measure(dark, e, lo, hi, True)
            ts.append((lo + hi) / 2 / h); os_.append(o if st > 4.2 else None)
        c = fit(ts, os_); V.append((e, c))
        if c: read += [abs(poly(c, t)) for t in ts]
    for e in ys:
        ts, os_ = [], []
        for s in range(S):
            lo, hi = w * s // S, w * (s + 1) // S; o, st = measure(dark, e, lo, hi, False)
            ts.append((lo + hi) / 2 / w); os_.append(o if st > 4.2 else None)
        c = fit(ts, os_); Hh.append((e, c))
        if c: read += [abs(poly(c, t)) for t in ts]
    return V, Hh, read

def field(lines, size):
    """offset anywhere between the lines: zero on the sheet's edges, the measured curve on each line, straight in between"""
    known = [(0.0, [0.0])] + [(e, c) for e, c in lines if c] + [(float(size), [0.0])]
    def f(pos, t):
        for (a, ca), (b, cb) in zip(known, known[1:]):
            if a <= pos <= b:
                k = (pos - a) / (b - a) if b > a else 0
                return poly(ca, t) * (1 - k) + poly(cb, t) * k
        return 0.0
    return f

def main():
    for d, pat, nx, ny in SHEETS:
        j = glob.glob(os.path.join(DL, d, pat + '.jgw')); assert len(j) == 1, pat; j = j[0]
        a = [float(x) for x in open(j).read().split()]; mpp = a[0] * 111320 * 0.936
        im = Image.open(j[:-4] + '.jpg').convert('RGB'); w, h = im.size
        V, Hh, before = survey(im, nx, ny)
        fx, fy = field(V, w), field(Hh, h)
        step = 160; mesh = []
        gx = list(range(0, w, step)) + [w]; gy = list(range(0, h, step)) + [h]
        src = lambda x, y: (x + fx(x, y / h), y + fy(y, x / w))
        for x0, x1 in zip(gx, gx[1:]):
            for y0, y1 in zip(gy, gy[1:]):
                q = src(x0, y0) + src(x0, y1) + src(x1, y1) + src(x1, y0)
                mesh.append(((x0, y0, x1, y1), q))
        out = im.transform((w, h), Image.MESH, mesh, Image.BICUBIC)
        V2, H2, after = survey(out, nx, ny)
        os.makedirs(os.path.join(FIX, d), exist_ok=True)
        dst = os.path.join(FIX, d, os.path.basename(j)[:-4])
        out.save(dst + '.jpg', quality=93); shutil.copy(j, dst + '.jgw')
        found = sum(1 for _, c in V + Hh if c); total = len(V) + len(Hh)
        st = lambda r: ('worst %3.0f m, typical %3.0f m' % (max(r) * mpp, statistics.median(r) * mpp)) if r else 'no line found'
        print('%-44s grid lines found %2d of %2d · before: %s · after: %s' % (os.path.basename(j)[:44], found, total, st(before), st(after)), flush=True)
if __name__ == '__main__': main()
