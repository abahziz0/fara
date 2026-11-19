#!/usr/bin/env python3
"""Old maps, the sheets of 1954 and 1955: place four United States Army Map Service sheets on today's coordinates.

    python3 tools/oldmaps_ams.py WORKDIR

The sheets are Burma 1:250,000, series U542: NF 46-14 "Akyab" and NF 46-10 "Cox's Bazar", compiled in 1954 from the one-inch
surveys of 1936 to 1944 and from air photographs of 1943 to 1945 and printed in 1960; NF 46-15 "Myohaung", compiled in 1954 from
the half-inch surveys of 1925 to 1936 and printed in 1960; and NE 46-3 "Kyaukpyu", compiled in 1955 from half-inch sheets and
charts and printed in 1959. They are works of the United States government and so in the public
domain. The scans are from the Perry-Castaneda Library Map Collection of the University of Texas Libraries; they are fetched
here from the Internet Archive's copies, because the library's own site answers scripts with a bot check.

Unlike the Survey of India sheets, these scans carry no coordinates at all. What each sheet does print is a blue grid with a line
every 10,000 yards: the India Zone IIIB grid, a Lambert conical orthomorphic grid on the Everest spheroid (origin 19 N 100 E,
scale 823/824, false origin 3,000,000 yards east and 1,000,000 yards north). Every point of that grid has a known latitude and
longitude, so the grid pins the whole picture:

  1. every grid line is found at stations about 1.8 km apart along its length (some 2,000 readings a sheet);
  2. a smooth surface is fitted through the readings, so that the picture's stretch and skew are taken out;
  3. as a check that does not depend on the grid, the sheet's own frame (drawn along its latitude and longitude limits) and the
     small crosses printed every 15 minutes are found, and compared with where the grid puts them;
  4. the old datum (Everest, Indian datum) is converted to today's (WGS 84) with the shifts published for Myanmar, the same
     shift the Survey of India sheets on this site carry;
  5. the sheet is redrawn as a plain rectangle of latitude and longitude, cut at its printed frame.

Writes WORKDIR/fix/ams/<sheet>.png (with a world file, .pgw) for oldmaps_tile.py, and WORKDIR/fix/ams/report.json with every number.
Pure Python and Pillow."""
import json, math, os, statistics, sys, urllib.request
from PIL import Image, ImageChops, ImageDraw
Image.MAX_IMAGE_PIXELS = None

SHEETS = [
    # name, title, source file at the library, Internet Archive snapshot, frame W E S N (Everest), corners NW NE SW SE read by eye in pixels
    # (only a starting point: the grid survey corrects it), part to keep W E S N
    {'name': 'NF46-14_Akyab_1954', 'sheet': 'NF 46-14', 'title': 'Akyab', 'printed': 'July 1960',
     'url': 'https://web.archive.org/web/20240730144507id_/https://maps.lib.utexas.edu/maps/ams/burma/txu-oclc-6924198-nf46-14.jpg',
     'box': (91.5, 93.0, 20.0, 21.0), 'corners': [(332.5, 168), (4647.5, 170), (338.2, 3226.2), (4676.8, 3230.8)], 'keep': (91.9, 93.0, 20.0, 21.0)},
    {'name': 'NF46-10_CoxsBazar_1954', 'sheet': 'NF 46-10', 'title': "Cox's Bazar", 'printed': 'March 1960',
     'url': 'https://web.archive.org/web/20240804185044id_/https://maps.lib.utexas.edu/maps/ams/burma/txu-oclc-6924198-nf46-10.jpg',
     'box': (91.5, 93.0, 21.0, 22.0), 'corners': [(366, 192.5), (4619, 191.5), (372, 3227.5), (4651, 3228.2)], 'keep': (91.9, 93.0, 21.0, 21.55)},
    # on this sheet and the next the grid is printed in a blue so dark that over the green land tint it reads as grey, so the
    # lines are looked for as "anything without red in it" ('ink': 'dark') and not as blue. The frame of Kyaukpyu starts at 92 55' E.
    {'name': 'NF46-15_Myohaung_1954', 'sheet': 'NF 46-15', 'title': 'Myohaung', 'printed': 'March 1960', 'ink': 'dark',
     'url': 'https://web.archive.org/web/20160410105827im_/http://www.lib.utexas.edu/maps/ams/burma/txu-oclc-6924198-nf46-15.jpg',
     'box': (93.0, 94.5, 20.0, 21.0), 'corners': [(335, 197.5), (4603, 197), (340.8, 3219), (4635.5, 3219.8)], 'keep': (93.0, 94.5, 20.0, 21.0)},
    {'name': 'NE46-03_Kyaukpyu_1955', 'sheet': 'NE 46-3', 'title': 'Kyaukpyu', 'compiled': 1955, 'printed': 'January 1959', 'ink': 'dark',
     'url': 'https://web.archive.org/web/20160304073943id_/http://www.lib.utexas.edu/maps/ams/burma/txu-oclc-6924198-ne46-3.jpg',
     'box': (92 + 55 / 60, 94.5, 19.0, 20.0), 'corners': [(216.5, 208), (4753, 204.2), (226.2, 3231.5), (4790.8, 3229)], 'keep': (92 + 55 / 60, 94.5, 19.0, 20.0)},
]

# ---- Everest 1830 spheroid and the India Zone IIIB grid (Lambert conical orthomorphic), in Indian yards ----
INV_F = 300.8017; F_ = 1 / INV_F; E2 = 2 * F_ - F_ * F_; EC = math.sqrt(E2)
A_YD = 20922931.80 / 3                      # semi-major axis: 20,922,931.80 Indian feet
PHI0 = math.radians(19.0); LAM0 = math.radians(100.0); K0 = 823 / 824; FE = 3000000.0; FN = 1000000.0
def _t(phi):
    s = math.sin(phi); return math.tan(math.pi / 4 - phi / 2) / (((1 - EC * s) / (1 + EC * s)) ** (EC / 2))
_n = math.sin(PHI0); _m0 = math.cos(PHI0) / math.sqrt(1 - E2 * math.sin(PHI0) ** 2); _t0 = _t(PHI0)
_F = _m0 / (_n * _t0 ** _n); _R0 = A_YD * _F * K0 * _t0 ** _n
def ll2grid(lon, lat):
    r = A_YD * _F * K0 * _t(math.radians(lat)) ** _n; th = _n * (math.radians(lon) - LAM0)
    return FE + r * math.sin(th), FN + _R0 - r * math.cos(th)
def grid2ll(E, N):
    dx = E - FE; dy = _R0 - (N - FN); r = math.hypot(dx, dy); th = math.atan2(dx, dy)
    t = (r / (A_YD * _F * K0)) ** (1 / _n); phi = math.pi / 2 - 2 * math.atan(t)
    for _ in range(8):
        s = math.sin(phi); phi = math.pi / 2 - 2 * math.atan(t * ((1 - EC * s) / (1 + EC * s)) ** (EC / 2))
    return math.degrees(LAM0 + th / _n), math.degrees(phi)

# ---- old datum to today's: Everest 1830 (Indian datum) to WGS 84, the three shifts published for Myanmar (EPSG transformation 1304) ----
A_EV = 6377276.345; A_WGS = 6378137.0; F_WGS = 1 / 298.257223563; SHIFT = (246.632, 784.833, 276.923)
def _geo2xyz(lon, lat, a, f):
    e2 = 2 * f - f * f; la, lo = math.radians(lat), math.radians(lon); n = a / math.sqrt(1 - e2 * math.sin(la) ** 2)
    return n * math.cos(la) * math.cos(lo), n * math.cos(la) * math.sin(lo), n * (1 - e2) * math.sin(la)
def _xyz2geo(x, y, z, a, f):
    e2 = 2 * f - f * f; lo = math.atan2(y, x); p = math.hypot(x, y); la = math.atan2(z, p * (1 - e2))
    for _ in range(6):
        n = a / math.sqrt(1 - e2 * math.sin(la) ** 2); la = math.atan2(z + e2 * n * math.sin(la), p)
    return math.degrees(lo), math.degrees(la)
def ev2wgs(lon, lat):
    x, y, z = _geo2xyz(lon, lat, A_EV, F_); return _xyz2geo(x + SHIFT[0], y + SHIFT[1], z + SHIFT[2], A_WGS, F_WGS)
def wgs2ev(lon, lat):
    x, y, z = _geo2xyz(lon, lat, A_WGS, F_WGS); return _xyz2geo(x - SHIFT[0], y - SHIFT[1], z - SHIFT[2], A_EV, F_)

# ---- small least squares ----
def terms(u, v): return (1.0, u, v, u * u, u * v, v * v, u * u * u, u * u * v, u * v * v, v * v * v)
def solve(A, B):
    n = len(B); A = [r[:] for r in A]; B = B[:]
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(A[r][i])); A[i], A[p] = A[p], A[i]; B[i], B[p] = B[p], B[i]
        for r in range(i + 1, n):
            f = A[r][i] / A[i][i]
            for c in range(i, n): A[r][c] -= f * A[i][c]
            B[r] -= f * B[i]
    c = [0.0] * n
    for i in range(n - 1, -1, -1): c[i] = (B[i] - sum(A[i][j] * c[j] for j in range(i + 1, n))) / A[i][i]
    return c
def surf(c, u, v): return sum(a * b for a, b in zip(c, terms(u, v)))
def surf_fit(pts, tol):
    """pts: (u, v, value, tag). A surface of the third degree through the readings, dropping stray ones (a river, a word or a
    number that looked like the line) until every reading kept lies within tol. Returns (coefficients, kept points)."""
    pts = list(pts)
    while True:
        n = 10; A = [[0.0] * n for _ in range(n)]; B = [0.0] * n
        for u, v, o, _ in pts:
            t = terms(u, v)
            for i in range(n):
                B[i] += t[i] * o
                for j in range(n): A[i][j] += t[i] * t[j]
        c = solve(A, B)
        res = [abs(o - surf(c, u, v)) for u, v, o, _ in pts]
        bad = [i for i, r in enumerate(res) if r > tol]
        if not bad: return c, pts
        cut = max(tol, sorted(res)[-max(1, len(bad) // 3)])           # drop the worst third of the strays each round
        pts = [p for p, r in zip(pts, res) if r < cut]
def line_fit(pts, deg=2, tol=1.5):
    """curve of the second degree through (t, value) readings along one edge of the frame, dropping stray ones"""
    pts = list(pts)
    while len(pts) > deg + 3:
        n = deg + 1; A = [[sum(t ** (i + j) for t, _ in pts) for j in range(n)] for i in range(n)]; B = [sum(o * t ** i for t, o in pts) for i in range(n)]
        c = solve(A, B); res = [abs(o - sum(ci * t ** i for i, ci in enumerate(c))) for t, o in pts]; w = max(range(len(pts)), key=lambda i: res[i])
        if res[w] <= tol: return c
        pts.pop(w)
    return [statistics.median(o for _, o in pts)] if pts else [0.0]

class Sheet:
    def __init__(s, path, box, corners, ink='blue'):
        s.im = Image.open(path).convert('RGB'); s.w, s.h = s.im.size; s.box = box; s.c = corners
        r, g, b = s.im.split()
        s.blue = ImageChops.subtract(b, r)                                   # the grid is printed in blue
        if ink == 'dark': s.blue = ImageChops.invert(r)                      # ... or in a blue so dark that it reads as grey: anything without red in it
        s.dark = ImageChops.invert(ImageChops.lighter(ImageChops.lighter(r, g), b))   # black line work
        W, E, S, N = box
        ce = [ll2grid(lo, la) for lo, la in ((W, N), (E, N), (W, S), (E, S))]
        s.Emin = min(c[0] for c in ce); s.Emax = max(c[0] for c in ce); s.Nmin = min(c[1] for c in ce); s.Nmax = max(c[1] for c in ce)
        s.Elines = [e for e in range(int(s.Emin // 10000 + 1) * 10000, int(s.Emax) + 1, 10000)]
        s.Nlines = [n for n in range(int(s.Nmin // 10000 + 1) * 10000, int(s.Nmax) + 1, 10000)]
        s.cx = [0.0] * 10; s.cy = [0.0] * 10          # correction surfaces, in pixels, over (te, tn)
    def tn(s, N): return (N - s.Nmin) / (s.Nmax - s.Nmin)
    def te(s, E): return (E - s.Emin) / (s.Emax - s.Emin)
    def base(s, lon, lat):
        """first guess: straight between the four corners"""
        W, E, S, N = s.box; u = (lon - W) / (E - W); v = (N - lat) / (N - S); (ax, ay), (bx, by), (cx, cy), (dx, dy) = s.c
        return ((1 - u) * (1 - v) * ax + u * (1 - v) * bx + (1 - u) * v * cx + u * v * dx,
                (1 - u) * (1 - v) * ay + u * (1 - v) * by + (1 - u) * v * cy + u * v * dy)
    def grid2px(s, E, N):
        lon, lat = grid2ll(E, N); x, y = s.base(lon, lat); u, v = s.te(E), s.tn(N)
        return x + surf(s.cx, u, v), y + surf(s.cy, u, v)
    def ll2px(s, lon, lat):
        """a place (longitude and latitude on the Everest spheroid) to its pixel in the scan"""
        return s.grid2px(*ll2grid(lon, lat))
    def inside(s, lon, lat, m=0.004):
        W, E, S, N = s.box; return W + m < lon < E - m and S + m < lat < N - m
    def _profile(s, chan, P, a, across, L, WIN):
        """mean of the channel along direction a (length L) for each step across, 2*WIN steps"""
        (px, py), (ax, ay), (cx, cy) = P, a, across; h = L / 2
        q = (px - ax * h - cx * WIN, py - ay * h - cy * WIN, px + ax * h - cx * WIN, py + ay * h - cy * WIN,
             px + ax * h + cx * WIN, py + ay * h + cy * WIN, px - ax * h + cx * WIN, py - ay * h + cy * WIN)
        strip = chan.transform((2 * WIN, int(L)), Image.QUAD, q, Image.BILINEAR).resize((2 * WIN, 1), Image.BOX)
        return list(strip.get_flattened_data() if hasattr(strip, 'get_flattened_data') else strip.getdata())
    @staticmethod
    def _peak(p, WIN, minstrength=3.0):
        n = len(p); base = statistics.median(p); spread = statistics.pstdev(p) or 1.0
        best, bi = 0, None
        for i in range(2, n - 2):
            v = p[i] - base
            if v > best and p[i] >= p[i - 1] and p[i] >= p[i + 1]: best, bi = v, i
        if bi is None or best / spread < minstrength or best < 12: return None
        w = [max(0.0, p[k] - base) for k in (bi - 2, bi - 1, bi, bi + 1, bi + 2)]
        return bi + (-2 * w[0] - w[1] + w[3] + 2 * w[4]) / (sum(w) or 1) + 0.5 - WIN
    def readings(s, WIN=24, L=56, step=2000.0):
        """look for every blue grid line at stations along its length, from the model as it stands.
        Returns (x readings on easting lines, y readings on northing lines), each (te, tn, offset in px or None, line value)."""
        rx, ry = [], []
        for E in s.Elines:
            N = s.Nmin - 20000
            while N < s.Nmax + 20000:
                N += step
                if not s.inside(*grid2ll(E, N)): continue
                P = s.grid2px(E, N); P2 = s.grid2px(E, N - 2000); d = math.hypot(P2[0] - P[0], P2[1] - P[1]); a = ((P2[0] - P[0]) / d, (P2[1] - P[1]) / d)
                if not (WIN + 2 < P[0] < s.w - WIN - 2 and L < P[1] < s.h - L): continue
                rx.append((s.te(E), s.tn(N), s._peak(s._profile(s.blue, P, a, (1, 0), L, WIN), WIN), E))
        for N in s.Nlines:
            E = s.Emin - 20000
            while E < s.Emax + 20000:
                E += step
                if not s.inside(*grid2ll(E, N)): continue
                P = s.grid2px(E, N); P2 = s.grid2px(E + 2000, N); d = math.hypot(P2[0] - P[0], P2[1] - P[1]); a = ((P2[0] - P[0]) / d, (P2[1] - P[1]) / d)
                if not (L < P[0] < s.w - L and WIN + 2 < P[1] < s.h - WIN - 2): continue
                ry.append((s.te(E), s.tn(N), s._peak(s._profile(s.blue, P, a, (0, 1), L, WIN), WIN), N))
        return rx, ry
    def pin(s, tols=(2.5, 1.5, 1.2)):
        """pin the model to the printed grid: read the lines, fit the correction surfaces, three times over. Returns one report per pass."""
        out = []
        for tol in tols:
            rx, ry = s.readings()
            gx = [r for r in rx if r[2] is not None]; gy = [r for r in ry if r[2] is not None]
            cx, kx = surf_fit(gx, tol); cy, ky = surf_fit(gy, tol)
            before = [abs(r[2]) for r in kx + ky]
            s.cx = [a + b for a, b in zip(s.cx, cx)]; s.cy = [a + b for a, b in zip(s.cy, cy)]
            left = [abs(o - surf(cx, u, v)) for u, v, o, _ in kx] + [abs(o - surf(cy, u, v)) for u, v, o, _ in ky]
            lines = {}
            for kind, allr, kept in (('E', rx, kx), ('N', ry, ky)):
                keptset = {(r[0], r[1]) for r in kept}
                for r in allr:
                    e = lines.setdefault((kind, r[3]), [0, 0]); e[1] += 1
                    if (r[0], r[1]) in keptset: e[0] += 1
            out.append({'stations': len(rx) + len(ry), 'read': len(gx) + len(gy), 'kept': len(kx) + len(ky),
                        'before_typical_px': round(statistics.median(before), 2), 'before_worst_px': round(max(before), 2),
                        'after_typical_px': round(statistics.median(left), 2), 'after_worst_px': round(max(left), 2),
                        'lines_found': sum(1 for g, t in lines.values() if t >= 6 and g >= 0.5 * t), 'lines': sum(1 for g, t in lines.values() if t >= 6)})
        return out
    def frame(s, WIN=14, L=50):
        """the sheet's own frame and its 15-minute crosses, against where the grid-based model puts them (printed minus model, px).
        Returns {'N': [(lon, dy)], 'S': [(lon, dy)], 'W': [(lat, dx)], 'E': [(lat, dx)], 'cross': [(lon, lat, dx, dy)]}"""
        W_, E_, S_, N_ = s.box; out = {'N': [], 'S': [], 'W': [], 'E': [], 'cross': []}
        def one(lon, lat, along, across):
            P = s.ll2px(lon, lat)
            if not (WIN + L < P[0] < s.w - WIN - L and WIN + L < P[1] < s.h - WIN - L): return None
            return s._peak(s._profile(s.dark, P, along, across, L, WIN), WIN)
        k = 0.03; lon = W_ + k
        while lon < E_ - k / 2:
            for edge, lat in (('N', N_), ('S', S_)):
                P = s.ll2px(lon, lat); P2 = s.ll2px(lon + 0.01, lat); d = math.hypot(P2[0] - P[0], P2[1] - P[1])
                o = one(lon, lat, ((P2[0] - P[0]) / d, (P2[1] - P[1]) / d), (0, 1))
                if o is not None: out[edge].append((lon, o))
            lon += k
        lat = S_ + k
        while lat < N_ - k / 2:
            for edge, lon in (('W', W_), ('E', E_)):
                P = s.ll2px(lon, lat); P2 = s.ll2px(lon, lat - 0.01); d = math.hypot(P2[0] - P[0], P2[1] - P[1])
                o = one(lon, lat, ((P2[0] - P[0]) / d, (P2[1] - P[1]) / d), (1, 0))
                if o is not None: out[edge].append((lat, o))
            lat += k
        q = 0.25; lat = math.floor(S_ / q + 1e-9) * q + q                   # the crosses sit on whole quarter degrees, wherever the frame starts
        while lat < N_ - q / 2:
            lon = math.floor(W_ / q + 1e-9) * q + q
            while lon < E_ - q / 2:
                P = s.ll2px(lon, lat)
                out['cross'].append((round(lon, 2), round(lat, 2), s._peak(s._profile(s.dark, P, (0, 1), (1, 0), 22, 12), 12), s._peak(s._profile(s.dark, P, (1, 0), (0, 1), 22, 12), 12)))
                lon += q
            lat += q
        return out
    def cut(s, keep, fr, inset=2.0):
        """the part of the scan to keep, as a mask: inside the printed frame (a little inside, so the frame line itself is left out),
        or inside the keep box where that is smaller than the frame"""
        W_, E_, S_, N_ = s.box; kw, ke, ks, kn = keep
        fit = {e: line_fit(fr[e]) for e in 'NSWE'}; off = lambda e, t: sum(c * t ** i for i, c in enumerate(fit[e]))
        pts = []; n = 200
        for i in range(n + 1):                                   # along the top, west to east
            lon = kw + (ke - kw) * i / n; x, y = s.ll2px(lon, kn); pts.append((x, y + (off('N', lon) + inset if kn == N_ else 0)))
        for i in range(n + 1):                                   # down the east side
            lat = kn - (kn - ks) * i / n; x, y = s.ll2px(ke, lat); pts.append((x + (off('E', lat) - inset if ke == E_ else 0), y))
        for i in range(n + 1):                                   # back along the bottom
            lon = ke - (ke - kw) * i / n; x, y = s.ll2px(lon, ks); pts.append((x, y + (off('S', lon) - inset if ks == S_ else 0)))
        for i in range(n + 1):                                   # up the west side
            lat = ks + (kn - ks) * i / n; x, y = s.ll2px(kw, lat); pts.append((x + (off('W', lat) + inset if kw == W_ else 0), y))
        m = Image.new('L', s.im.size, 0); ImageDraw.Draw(m).polygon(pts, fill=255); return m
    def warp(s, keep, mask, step_deg=0.00027, cell=48):
        """the kept part as a plain rectangle of latitude and longitude on WGS 84. Returns (picture with transparency, west, north, degrees per pixel)."""
        kw, ke, ks, kn = keep; w0, n0 = ev2wgs(kw, kn); e0, s0 = ev2wgs(ke, ks)
        w0 -= 6 * step_deg; n0 += 6 * step_deg; cols = int((e0 - w0) / step_deg) + 6; rows = int((n0 - s0) / step_deg) + 6
        xs = list(range(0, cols, cell)) + [cols]; ys = list(range(0, rows, cell)) + [rows]
        src = {(X, Y): s.ll2px(*wgs2ev(w0 + X * step_deg, n0 - Y * step_deg)) for X in xs for Y in ys}
        mesh = [((x0, y0, x1, y1), src[(x0, y0)] + src[(x0, y1)] + src[(x1, y1)] + src[(x1, y0)]) for x0, x1 in zip(xs, xs[1:]) for y0, y1 in zip(ys, ys[1:])]
        rgba = s.im.copy(); rgba.putalpha(mask)
        return rgba.convert('RGBa').transform((cols, rows), Image.MESH, mesh, Image.BICUBIC).convert('RGBA'), w0, n0, step_deg

def main():
    WORK = os.path.abspath(sys.argv[1]); DL = os.path.join(WORK, 'dl', 'ams'); FIX = os.path.join(WORK, 'fix', 'ams')
    os.makedirs(DL, exist_ok=True); os.makedirs(FIX, exist_ok=True); report = {}
    for sh in SHEETS:
        src = os.path.join(DL, sh['name'] + '.jpg')
        if not os.path.exists(src):
            print('fetching', sh['url'], flush=True)
            with urllib.request.urlopen(urllib.request.Request(sh['url'], headers={'User-Agent': 'curl/8'})) as r, open(src, 'wb') as g: g.write(r.read())
        s = Sheet(src, sh['box'], sh['corners'], sh.get('ink', 'blue')); passes = s.pin(); fr = s.frame()
        W_, E_, S_, N_ = sh['box']; a = s.ll2px((W_ + E_) / 2, S_ + .45); b = s.ll2px((W_ + E_) / 2, S_ + .55)
        mpp = 0.1 * 110700 / math.hypot(b[0] - a[0], b[1] - a[1])
        med = lambda v: round(statistics.median(v) * mpp) if v else None
        xs = [c[2] for c in fr['cross'] if c[2] is not None]; ys = [c[3] for c in fr['cross'] if c[3] is not None]
        east = [c for c in fr['cross'] if c[0] >= 92.2]                       # the part of the sheet that holds the villages of this archive
        rep = {'sheet': sh['sheet'], 'title': sh['title'], 'compiled': sh.get('compiled', 1954), 'printed': sh['printed'], 'scan_pixels': [s.w, s.h], 'metres_per_pixel': round(mpp, 1),
               'grid_lines': passes[-1]['lines'], 'grid_lines_found': passes[-1]['lines_found'], 'stations_read': passes[-1]['read'], 'stations_kept': passes[-1]['kept'],
               'grid_off_before_m': {'typical': round(passes[0]['before_typical_px'] * mpp), 'worst': round(passes[0]['before_worst_px'] * mpp)},
               'grid_off_after_m': {'typical': round(passes[-1]['after_typical_px'] * mpp), 'worst': round(passes[-1]['after_worst_px'] * mpp)},
               'frame_against_grid_m': {'north_edge': med([o for _, o in fr['N']]), 'south_edge': med([o for _, o in fr['S']]), 'west_edge': med([o for _, o in fr['W']]), 'east_edge': med([o for _, o in fr['E']]),
                                        'note': 'printed frame minus where the grid puts it; plus is south (north and south edges) or east (west and east edges)'},
               'crosses_against_grid_m': {'read': len(xs), 'of': len(fr['cross']), 'east_west_mean': round(statistics.mean(xs) * mpp), 'east_west_worst': round(max(map(abs, xs)) * mpp),
                                          'north_south_mean': round(statistics.mean(ys) * mpp), 'north_south_worst': round(max(map(abs, ys)) * mpp),
                                          'east_of_92.2E_worst': round(max([abs(c[2]) for c in east if c[2] is not None] + [abs(c[3]) for c in east if c[3] is not None]) * mpp)},
               'crosses_px': [[c[0], c[1], None if c[2] is None else round(c[2], 2), None if c[3] is None else round(c[3], 2)] for c in fr['cross']]}
        im, w0, n0, d = s.warp(sh['keep'], s.cut(sh['keep'], fr))
        im.save(os.path.join(FIX, sh['name'] + '.png'), compress_level=3)
        open(os.path.join(FIX, sh['name'] + '.pgw'), 'w').write('%.10f\n0\n0\n%.10f\n%.10f\n%.10f\n' % (d, -d, w0 + d / 2, n0 - d / 2))
        report[sh['name']] = rep
        print('%s: %d of %d grid lines found, %d readings kept · grid lines off before %d m typical, %d m worst · after %d m typical, %d m worst' % (
            sh['name'], rep['grid_lines_found'], rep['grid_lines'], rep['stations_kept'], rep['grid_off_before_m']['typical'], rep['grid_off_before_m']['worst'],
            rep['grid_off_after_m']['typical'], rep['grid_off_after_m']['worst']), flush=True)
        print('   printed frame against the grid, metres: north %s, south %s, west %s, east %s · crosses: east-west mean %+d (worst %d), north-south mean %+d (worst %d), east of 92.2 E worst %d' % (
            rep['frame_against_grid_m']['north_edge'], rep['frame_against_grid_m']['south_edge'], rep['frame_against_grid_m']['west_edge'], rep['frame_against_grid_m']['east_edge'],
            rep['crosses_against_grid_m']['east_west_mean'], rep['crosses_against_grid_m']['east_west_worst'], rep['crosses_against_grid_m']['north_south_mean'],
            rep['crosses_against_grid_m']['north_south_worst'], rep['crosses_against_grid_m']['east_of_92.2E_worst']), flush=True)
    json.dump(report, open(os.path.join(FIX, 'report.json'), 'w'), indent=1)
if __name__ == '__main__': main()
