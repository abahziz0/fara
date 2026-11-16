"""The parts of the FARA build that sit beside the village pages (called from build.py):

  embed/<id>/index.html                 a small card other websites can show in an <iframe>
  township/<slug>/gazetteer/index.html  a print-designed gazetteer of one township (tools/build_pdfs.py turns it into a PDF)
  stories/<slug>/index.html             guided, scrolling accounts written in content/stories/*.json
  stories/index.html

Everything here is generated from the same data as the rest of the site, so the numbers cannot drift apart.
"""
import json, math, os, re, unicodedata
from collections import Counter, defaultdict
from datetime import date

PRINT_COLORS = {'Maungdaw': '#008CA3', 'Buthidaung': '#16895A', 'Rathedaung': '#B06A00', 'Sittwe': '#BE2460'}
ST_LABEL_SHORT = {'destroyed': 'Destroyed in 2017', 'nearby': 'Destruction nearby in 2017'}
ST_COLOR = {'destroyed': '#FF3B5C', 'nearby': '#FFB020'}
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Share+Tech+Mono&family=Noto+Sans+Myanmar:wght@400;600&display=swap" rel="stylesheet">')
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']


def long_date(d): return '%d %s %d' % (d.day, MONTHS[d.month - 1], d.year)


def nv(n): return '%d %s' % (n, 'village' if n == 1 else 'villages')


def plain(s):
    """Lower case, accents removed, punctuation ignored: for putting names in alphabetical order."""
    s = unicodedata.normalize('NFKD', s or '')
    return re.sub(r'[^a-z0-9]+', ' ', ''.join(ch for ch in s if not unicodedata.combining(ch)).lower()).strip()


def run(g):
    """g is build.py's namespace: the data and its small helpers."""
    ctx = Ctx(g)
    n_embed = build_embeds(ctx)
    n_gaz = build_gazetteers(ctx)
    n_story = build_stories(ctx)
    return n_embed, n_gaz, n_story


class Ctx:
    def __init__(self, g):
        self.g = g
        for k in ('V', 'N', 'SITE', 'ROOT', 'TOWN_COLORS', 'ST17', 'COLLECTED', 'ANALYTICS', 'LOGO', 'PCODE_SOURCE', 'ST17_URL'):
            setattr(self, k, g[k])
        for k in ('p', 'esc', 'write', 'slugify', 'unverified', 'ro', 'en', 'rid', 'vurl', 'turl', 'page', 'crumbs', 'crumbs_ld'):
            setattr(self, k, g[k])
        self.towns = [t for t in self.TOWN_COLORS if any(v.get('township') == t for v in self.V)]
        self.today = date.today()
        b = self.p('boundaries.json')
        self.bounds = json.load(open(b, encoding='utf-8')) if os.path.exists(b) else None
        self.tract_by_code = {t['p']: t for t in self.bounds['tracts']} if self.bounds else {}
        self.town_by_name = {t['n']: t for t in self.bounds['towns']} if self.bounds else {}

    def status(self, v):
        r = self.ST17.get(str(v['id']))
        if not r or r.get('reason') == 'no verified location': return None
        return r['status']


# =====================================================================================================  embed cards
EMBED_CSS = '''*{box-sizing:border-box;margin:0;padding:0}html,body{height:100%}
body{background:#050B14;color:#E8F2FF;font-family:'Space Grotesk',system-ui,sans-serif;-webkit-font-smoothing:antialiased}
a.card{display:flex;flex-direction:column;height:100%;min-height:300px;color:inherit;text-decoration:none;border:1px solid rgba(0,229,255,.28);background:#071120;position:relative;overflow:hidden}
a.card::before{content:"";position:absolute;z-index:2;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,#00E5FF,transparent 65%)}
.img{position:relative;flex:1 1 0;min-height:110px;background:#03070d center/cover no-repeat}
.img::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(2,5,10,.35),transparent 30%,transparent 62%,rgba(7,17,32,.92))}
.ring{position:absolute;left:50%;top:50%;width:30px;height:30px;margin:-15px 0 0 -15px;border:2px solid #00E5FF;border-radius:50%;box-shadow:0 0 0 1px rgba(2,5,10,.6),0 0 14px rgba(0,229,255,.7);z-index:1}
.tag,.town,.cred{position:absolute;z-index:1;font:400 10px 'Share Tech Mono',monospace;letter-spacing:.14em;text-transform:uppercase}
.tag{left:12px;top:12px;padding:4px 8px;background:rgba(2,5,10,.78);border:1px solid rgba(0,229,255,.3);color:#8FA8C7}
.town{right:12px;top:12px;padding:4px 8px;background:rgba(2,5,10,.78);border:1px solid currentColor}
.town i{display:inline-block;width:6px;height:6px;border-radius:50%;background:currentColor;margin-right:6px;vertical-align:1px}
.cred{right:8px;bottom:6px;font-size:8px;letter-spacing:.06em;text-transform:none;color:rgba(232,242,255,.6)}
.noimg{display:grid;place-items:center;color:#54708F;font:400 11px 'Share Tech Mono',monospace;text-align:center;padding:16px;line-height:1.6}
.txt{flex:none;padding:14px 16px 13px}
.k{font:400 9px 'Share Tech Mono',monospace;letter-spacing:.24em;text-transform:uppercase;color:#54708F}
h1{margin-top:5px;font-size:25px;line-height:1.12;font-weight:700;letter-spacing:-.01em}
.alt{margin-top:4px;font-size:13.5px;color:#8FA8C7}
.alt .mmr{font-family:'Noto Sans Myanmar','Space Grotesk',sans-serif}
dl{display:flex;gap:18px;flex-wrap:wrap;margin-top:11px;padding-top:10px;border-top:1px solid rgba(110,160,210,.16)}
dt{font:400 8.5px 'Share Tech Mono',monospace;letter-spacing:.2em;text-transform:uppercase;color:#54708F}
dd{margin-top:3px;font-size:12.5px;font-weight:500}
dd.mono{font:400 12px 'Share Tech Mono',monospace;color:#00E5FF}
.st{display:flex;align-items:center;gap:8px;margin-top:10px;font:400 10.5px 'Share Tech Mono',monospace;color:#C9D8EA;line-height:1.4}
.st i{flex:none;width:8px;height:8px;border-radius:50%}
.foot{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:12px;padding-top:10px;border-top:1px solid rgba(110,160,210,.16);font:400 10px 'Share Tech Mono',monospace;letter-spacing:.1em;text-transform:uppercase}
.foot .b{display:flex;align-items:center;gap:8px;color:#8FA8C7;min-width:0}
.foot .b img{flex:none;height:16px;width:16px}
.foot .b span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.foot .go{flex:none;color:#00E5FF}
a.card:hover .go,a.card:focus-visible .go{text-decoration:underline}
@media (max-width:330px){h1{font-size:21px}.foot .b span{display:none}}'''


def esri_export(lat, lng, w, h, half_m=420):
    R = 6378137
    mx, my = math.radians(lng) * R, math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * R
    hw = half_m / math.cos(math.radians(lat)); hh = hw * h / w
    return ('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?bbox=%.1f,%.1f,%.1f,%.1f'
            '&bboxSR=3857&imageSR=3857&size=%d,%d&format=jpg&f=image' % (mx - hw, my - hh, mx + hw, my + hh, w, h))


def embed_code(c, v):
    return ('<iframe src="%s/embed/%d/" title="%s — FARA, the Arakan Village Name Archive" width="100%%" height="430" '
            'style="border:0;max-width:480px" loading="lazy"></iframe>' % (c.SITE, v['id'], c.esc(c.ro(v))))


def build_embeds(c):
    esc = c.esc
    for v in c.V:
        name, off, mm = c.ro(v), c.en(v), v.get('village_name_mmr') or ''
        town, tract = v.get('township') or '', v.get('village_tract') or ''
        unv = c.unverified(v)
        col = c.TOWN_COLORS.get(town, '#8FA8C7')
        if unv:
            img = '<div class="img noimg">Location not verified yet.<br>The name is on record.</div>'
        else:
            img = ('<div class="img" style="background-image:url(\'%s\')" role="img" aria-label="Satellite image of %s"><span class="ring"></span>'
                   '<span class="tag">%s</span><span class="town" style="color:%s"><i></i>%s</span><span class="cred">Imagery: Esri</span></div>'
                   % (esc(esri_export(float(v['lat']), float(v['lng']), 800, 450)), esc(name), c.rid(v), col, esc(town)))
        alt = ' · '.join(x for x in [esc(off) if off and off != name else '', '<span class="mmr">%s</span>' % esc(mm) if mm else ''] if x)
        facts = ''
        if tract: facts += '<div><dt>Village tract</dt><dd>%s</dd></div>' % esc(tract)
        if town and unv: facts += '<div><dt>Township</dt><dd>%s</dd></div>' % esc(town)
        if not unv: facts += '<div><dt>Coordinates</dt><dd class="mono">%.5f, %.5f</dd></div>' % (float(v['lat']), float(v['lng']))
        st = c.status(v)
        st_html = ('<p class="st"><i style="background:%s"></i>%s · UNOSAT satellite analysis</p>' % (ST_COLOR[st], ST_LABEL_SHORT[st])) if st in ST_LABEL_SHORT else ''
        html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, follow">
<title>%(name)s — FARA, the Arakan Village Name Archive</title>
<link rel="canonical" href="%(site)s%(vurl)s">
%(fonts)s
<link rel="stylesheet" href="/embed/card.css">
</head>
<body>
<a class="card" href="%(site)s%(vurl)s" target="_blank" rel="noopener" aria-label="%(name)s, a Rohingya village in %(town)s township. Open its record in FARA.">
  %(img)s
  <div class="txt">
    <div class="k">Rohingya village · Arakan</div>
    <h1>%(name)s</h1>
    %(alt)s
    %(facts)s
    %(st)s
    <div class="foot"><span class="b"><img src="/logo.svg" alt="" width="16" height="16"><span>FARA · Arakan Village Name Archive</span></span><span class="go">Open record →</span></div>
  </div>
</a>
</body>
</html>
''' % dict(name=esc(name), site=c.SITE, vurl=c.vurl(v), fonts=FONTS, town=esc(town or 'Arakan'), img=img,
           alt='<p class="alt">%s</p>' % alt if alt else '', facts='<dl>%s</dl>' % facts if facts else '', st=st_html)
        c.write(c.p('embed', str(v['id']), 'index.html'), html)
    c.write(c.p('embed', 'card.css'), '/* FARA embed card (see build_extra.py) */\n' + EMBED_CSS + '\n')
    return len(c.V)


# =====================================================================================================  gazetteers
class Proj:
    """Equirectangular projection of a lat/lng box onto an SVG canvas of a given width."""
    def __init__(self, lat0, lat1, lng0, lng1, width, aspect=None):
        k = math.cos(math.radians((lat0 + lat1) / 2))
        w, h = (lng1 - lng0) * k, (lat1 - lat0)
        if aspect:                                               # grow the box to the wanted width:height
            if w / h < aspect: grow = (h * aspect - w) / k; lng0 -= grow / 2; lng1 += grow / 2; w = h * aspect
            else: grow = w / aspect - h; lat0 -= grow / 2; lat1 += grow / 2; h = w / aspect
        self.lat0, self.lat1, self.lng0, self.lng1, self.k = lat0, lat1, lng0, lng1, k
        self.s = width / w
        self.W, self.H = width, h * self.s

    def xy(self, lat, lng): return (lng - self.lng0) * self.k * self.s, (self.lat1 - lat) * self.s

    def path(self, pts, close=False):
        out = []
        for i, q in enumerate(pts):
            x, y = self.xy(q[0], q[1]); out.append('%s%.1f %.1f' % ('M' if i == 0 else 'L', x, y))
        return ''.join(out) + ('Z' if close else '')

    def hits(self, pts, pad=0):
        la = [q[0] for q in pts]; ln = [q[1] for q in pts]
        return not (max(la) < self.lat0 - pad or min(la) > self.lat1 + pad or max(ln) < self.lng0 - pad or min(ln) > self.lng1 + pad)


def poly_path(pr, polys):
    return ''.join(pr.path(ring, True) for poly in polys for ring in poly)


def lines_path(pr, arcs, clip=False):
    """Borders as one SVG path. With clip, only the stretches inside the map (plus one point either side) are kept,
    so a small map does not carry a whole township outline."""
    if not clip: return ''.join(pr.path(a) for a in arcs if pr.hits(a))
    pad = (pr.lat1 - pr.lat0) * 0.15
    inside = lambda q: pr.lat0 - pad <= q[0] <= pr.lat1 + pad and pr.lng0 - pad <= q[1] <= pr.lng1 + pad
    out = []
    for a in arcs:
        if not pr.hits(a, pad): continue
        keep = [inside(q) for q in a]
        run = []
        for i, q in enumerate(a):
            near = keep[i] or (i > 0 and keep[i - 1]) or (i + 1 < len(a) and keep[i + 1])
            if near: run.append(q)
            elif run:
                if len(run) > 1: out.append(pr.path(run))
                run = []
        if len(run) > 1: out.append(pr.path(run))
    return ''.join(out)


def bbox_of(points):
    la = [q[0] for q in points]; ln = [q[1] for q in points]
    return min(la), max(la), min(ln), max(ln)


def place_labels(dots, w, h, fs):
    """Put a number beside each dot without covering other dots or numbers where that can be avoided."""
    placed, out = [], []
    cw = fs * 0.56
    for x, y, text in dots:
        tw, th = cw * len(text), fs
        best = None
        for dx, dy, anchor in ((1.9, 0.36, 'start'), (-1.9, 0.36, 'end'), (0, -1.5, 'middle'), (0, 2.6, 'middle'),
                               (1.5, -1.1, 'start'), (-1.5, -1.1, 'end'), (1.5, 2.0, 'start'), (-1.5, 2.0, 'end')):
            lx, ly = x + dx * fs * 0.62, y + dy * fs * 0.62
            x0 = lx if anchor == 'start' else lx - tw if anchor == 'end' else lx - tw / 2
            box = (x0, ly - th * 0.8, x0 + tw, ly + th * 0.2)
            if box[0] < 0.5 or box[2] > w - 0.5 or box[1] < 0.5 or box[3] > h - 0.5: continue
            clash = sum(1 for b in placed if not (box[2] < b[0] or box[0] > b[2] or box[3] < b[1] or box[1] > b[3]))
            clash += sum(1 for ox, oy, _ in dots if (ox, oy) != (x, y) and box[0] - 1 < ox < box[2] + 1 and box[1] - 1 < oy < box[3] + 1)
            if best is None or clash < best[0]: best = (clash, lx, ly, anchor, box)
            if clash == 0: break
        if best is None: best = (0, x + fs, y, 'start', (x, y, x, y))
        placed.append(best[4]); out.append((best[1], best[2], best[3], text))
    return out


def mini_map(c, acc, tract, villages, numbers):
    """A small map of one tract: its outline, the borders around it, and its villages by entry number."""
    pts = [(float(v['lat']), float(v['lng'])) for v in villages if not c.unverified(v)]
    shape = [q for poly in tract['g'] for ring in poly for q in ring] if tract else []
    if not shape and not pts: return '<div class="mini none">not on<br>the boundary map</div>'
    la0, la1, ln0, ln1 = bbox_of(shape + pts)
    pad = max(la1 - la0, (ln1 - ln0), 0.004) * 0.09
    pr = Proj(la0 - pad, la1 + pad, ln0 - pad, ln1 + pad, 104, aspect=52 / 31.0)
    s = '<svg viewBox="0 0 %.1f %.1f" role="img" aria-label="Map of the tract">' % (pr.W, pr.H)
    if c.bounds:
        s += '<path d="%s" fill="none" stroke="#B9C2CD" stroke-width=".45"/>' % lines_path(pr, c.bounds['lines']['tract'], True)
        s += '<path d="%s" fill="none" stroke="#6C7A8A" stroke-width=".8"/>' % lines_path(pr, c.bounds['lines']['town'], True)
    if tract:
        s += '<path d="%s" fill="%s" fill-opacity=".12" stroke="%s" stroke-width="1.1" stroke-linejoin="round" fill-rule="evenodd"/>' % (poly_path(pr, tract['g']), acc, acc)
    dots = []
    for v in villages:
        if c.unverified(v): continue
        x, y = pr.xy(float(v['lat']), float(v['lng'])); dots.append((x, y, str(numbers[v['id']])))
    for x, y, _ in dots:
        s += '<circle cx="%.1f" cy="%.1f" r="1.25" fill="#0B1420" stroke="#fff" stroke-width=".45"/>' % (x, y)
    for lx, ly, anchor, text in place_labels(dots, pr.W, pr.H, 3.5):
        s += ('<text x="%.1f" y="%.1f" text-anchor="%s" font-family="Share Tech Mono,monospace" font-size="3.5" fill="#0B1420" '
              'stroke="#fff" stroke-width="1.1" paint-order="stroke" stroke-linejoin="round">%s</text>' % (lx, ly, anchor, text))
    return '<div class="mini">' + s + '</svg></div>'


def township_map(c, town, acc, vs, width, numbers=None, dot=0.9, labels=True):
    """The township: its outline, tract borders, the archive's villages, and (optionally) the tract section numbers."""
    tw = c.town_by_name.get(town)
    pts = [(float(v['lat']), float(v['lng'])) for v in vs if not c.unverified(v)]
    shape = [q for poly in tw['g'] for ring in poly for q in ring] if tw else pts
    la0, la1, ln0, ln1 = bbox_of(shape + pts)
    pad = max(la1 - la0, ln1 - ln0) * 0.03
    pr = Proj(la0 - pad, la1 + pad, ln0 - pad, ln1 + pad, width)
    s = '<svg viewBox="0 0 %.1f %.1f" preserveAspectRatio="xMaxYMid meet" role="img" aria-label="Map of %s township">' % (pr.W, pr.H, c.esc(town))
    if c.bounds:
        if tw: s += '<path d="%s" fill="%s" fill-opacity=".07" fill-rule="evenodd"/>' % (poly_path(pr, tw['g']), acc)
        s += '<path d="%s" fill="none" stroke="#AEB8C4" stroke-width=".28"/>' % lines_path(pr, c.bounds['lines']['tract'])
        s += '<path d="%s" fill="none" stroke="#7B8794" stroke-width=".4" stroke-linejoin="round"/>' % lines_path(pr, c.bounds['lines']['town'])
        if tw: s += '<path d="%s" fill="none" stroke="#0B1420" stroke-width=".75" stroke-linejoin="round"/>' % poly_path(pr, tw['g'])
    for la, ln in pts:
        x, y = pr.xy(la, ln)
        s += '<circle cx="%.1f" cy="%.1f" r="%.2f" fill="%s"/>' % (x, y, dot, acc)
    if numbers and labels:
        for num, tract in numbers:
            x, y = pr.xy(tract['c'][0], tract['c'][1])
            s += ('<text x="%.1f" y="%.1f" text-anchor="middle" font-family="Share Tech Mono,monospace" font-size="2.7" fill="#0B1420" '
                  'stroke="#fff" stroke-width="1.05" paint-order="stroke" stroke-linejoin="round">%d</text>' % (x, y + 0.95, num))
    return s + '</svg>', pr


ST_SYMBOL = {'destroyed': '<span class="s s-d" title="Destroyed in 2017"></span>', 'nearby': '<span class="s s-n" title="Destruction nearby in 2017"></span>',
             'none_detected': '<span class="s s-z" title="None detected in 2017"></span>',
             'not_assessed': '<span class="s-x" title="Not assessed">–</span>', None: '<span class="s-x" title="Not assessed">–</span>'}


def build_gazetteers(c):
    esc = c.esc
    made = 0
    for town in c.towns:
        acc = PRINT_COLORS.get(town, '#0B1420')
        vs = [v for v in c.V if v.get('township') == town]
        slug = c.slugify(town)
        groups = defaultdict(list)
        for v in vs: groups[v.get('village_tract') or 'Tract not recorded'].append(v)
        names = sorted(groups, key=lambda s: (s == 'Tract not recorded', plain(s)))
        numbers, sections, n = {}, [], 0
        for i, tn in enumerate(names, 1):
            members = sorted(groups[tn], key=lambda v: plain(c.ro(v)))
            for v in members: n += 1; numbers[v['id']] = n
            code = Counter(v.get('pcode_village_tract') for v in members if v.get('pcode_village_tract')).most_common(1)
            code = code[0][0] if code else None
            sections.append({'i': i, 'name': tn, 'members': members, 'code': code, 'tract': c.tract_by_code.get(code)})
        tw = c.town_by_name.get(town)
        n_tracts = sum(1 for s in sections if s['name'] != 'Tract not recorded')
        counts = Counter(c.status(v) for v in vs)
        with_ro = sum(1 for v in vs if v.get('rohingya_name')); with_mm = sum(1 for v in vs if v.get('village_name_mmr'))
        with_pc = sum(1 for v in vs if v.get('pcode_village'))
        ed = c.g.get('ED')                                  # the numbered edition (edition.json); the day of printing when there is none
        edition = '%s, %s' % (ed['version'], ed['date_long']) if ed else 'of ' + long_date(c.today)
        path = '%sgazetteer/' % c.turl(town)
        pdf = '/downloads/fara-gazetteer-%s.pdf' % slug

        cover_map, _ = township_map(c, town, acc, vs, 88, dot=0.62)
        key_map, _ = township_map(c, town, acc, vs, 118, numbers=[(s['i'], s['tract']) for s in sections if s['tract']], dot=0.5)

        h = []
        h.append('<div class="gz-bar"><a href="%s">← %s township</a><span class="sp"></span><span>Printable gazetteer</span>'
                 '<a class="primary" href="%s" download>Download PDF</a><button type="button" onclick="window.print()">Print</button></div>' % (c.turl(town), esc(town), pdf))
        # ---- cover
        h.append('''<section class="cover">
  <div class="mark">%(logo)s<div><b>FARA</b><i>The Arakan Village Name Archive</i></div></div>
  <p class="kick">Gazetteer of Rohingya villages</p>
  <h1>%(town)s<span>Township</span></h1>
  %(my)s
  <p class="where">Arakan (Rakhine State), Myanmar</p>
  <div class="cmap">%(map)s</div>
  <div class="stats"><div><b>%(n)d</b><span>Villages</span></div><div><b>%(t)d</b><span>Village tracts</span></div><div><b>3</b><span>Languages</span></div></div>
  <div class="cfoot"><div class="motto">Every village had a name.</div><div class="ed">Edition %(ed)s<br>map.rohingya.ro</div></div>
</section>''' % dict(logo=c.LOGO.replace('#00E5FF', acc), town=esc(town), map=cover_map, n=len(vs), t=n_tracts, ed=edition,
                     my='<p class="my mmr">%sမြို့နယ်</p>' % esc(tw['my']) if tw and tw.get('my') else ''))

        # ---- how to read
        sample = max(vs, key=lambda v: (bool(v.get('rohingya_name')) and c.en(v) != v.get('rohingya_name'), bool(v.get('village_name_mmr')), bool(v.get('pcode_village')), not c.unverified(v), -numbers[v['id']]))
        h.append('''<section class="sheet">
<h2><small>About this gazetteer</small>The villages of %(town)s, by name</h2>
<p class="lead">This booklet lists the %(n)d Rohingya villages of %(town)s township that FARA has on record: each one's name in Rohingya, its official name, its name in Burmese script, where it is, and its official place code. It is made to be printed, kept and carried.</p>
<div class="two">
<div>
<h3>Why it exists</h3>
<p>Rohingya village names are being renamed, left off official maps and forgotten as villages empty. FARA (“fará” is the Rohingya word for village) keeps them on record. A gazetteer on paper does not depend on a website staying online.</p>
<h3>How it is arranged</h3>
<p>Villages are grouped by village tract, and the tracts run in alphabetical order, each with a number. Within a tract the villages run A to Z by Rohingya name. Every village has an entry number, used on the small map of its tract and in the index at the back, which lists both Rohingya and official names.</p>
<h3>Reading an entry</h3>
<div class="sample">
  <div class="row"><span class="lbl">No.</span><span class="val mono">%(s_no)d</span></div>
  <div class="row"><span class="lbl">Rohingya</span><span class="val"><b>%(s_ro)s</b> — the name its people use</span></div>
  <div class="row"><span class="lbl">Official</span><span class="val">%(s_en)s — the romanised name on government and UN maps</span></div>
  <div class="row"><span class="lbl">Burmese</span><span class="val mmr">%(s_mm)s</span></div>
  <div class="row"><span class="lbl">Position</span><span class="val mono">%(s_co)s</span></div>
  <div class="row"><span class="lbl">Code</span><span class="val mono">%(s_pc)s</span></div>
</div>
<p>Positions are latitude and longitude in decimal degrees (WGS84). The code is the MIMU place code (“P-code”) that the United Nations and aid agencies use for the village; a dash means it has none.</p>
<p>Where a name has not been recorded yet, the gazetteer says so rather than guessing. In this township %(with_ro)d of %(n)d villages have a recorded Rohingya name, %(with_mm)d a Burmese-script name and %(with_pc)d an official place code.</p>
</div>
<div>
<h3>The 2017 column</h3>
<p>The last column shows what UNOSAT, the United Nations satellite centre, marked at or near each village in satellite imagery taken between 31 August and 11 October 2017.</p>
<ul class="key">
  <li><span class="s s-d"></span><span><b>Destroyed.</b> Destroyed buildings were mapped at the village. %(c_d)s in this township.</span></li>
  <li><span class="s s-n"></span><span><b>Destruction nearby.</b> A destroyed zone lies within 500 metres; it may belong to a neighbouring settlement. %(c_n)s.</span></li>
  <li><span class="s s-z"></span><span><b>None detected.</b> No destroyed zone within 500 metres. %(c_z)s.</span></li>
  <li><span class="s-x">–</span><span><b>Not assessed.</b> Outside the area UNOSAT analysed, or the location is unverified. %(c_x)s.</span></li>
</ul>%(uncovered)s
<p><b>“None detected” does not mean a village is standing.</b> The imagery ends on 11 October 2017, parts of the area were under cloud, destruction continued after that date, and UNOSAT did not validate its analysis on the ground.</p>
<h3>Sources</h3>
<p>Village names and positions: Rohingya Khobor, Arakan Maps Project, collected %(collected)s. Place codes: %(pcsrc)s, © Myanmar Information Management Unit. Boundaries on the maps: UN OCHA, Myanmar Subnational Administrative Boundaries (COD-AB, source: MIMU), CC BY-IGO; approximate, and not an endorsement of any boundary. 2017 analysis: UNOSAT, CC BY-SA.</p>
<h3>Corrections</h3>
<p>If a name is missing, misspelt or in the wrong place, please say so: <b>ab@rohingya.ro</b>, or the “Suggest a name or correction” button on any village at <b>map.rohingya.ro</b>. Records with known problems are flagged, never silently changed.</p>
</div>
</div>
</section>''' % dict(town=esc(town), n=len(vs), s_no=numbers[sample['id']], s_ro=esc(c.ro(sample)), s_en=esc(c.en(sample) or '—'),
                     s_mm=esc(sample.get('village_name_mmr') or '—'),
                     s_co='%.5f, %.5f' % (float(sample['lat']), float(sample['lng'])) if not c.unverified(sample) else 'unverified',
                     s_pc=esc(sample.get('pcode_village') or '—'), with_ro=with_ro, with_mm=with_mm, with_pc=with_pc,
                     c_d=nv(counts.get('destroyed', 0)), c_n=nv(counts.get('nearby', 0)), c_z=nv(counts.get('none_detected', 0)),
                     c_x=nv(counts.get('not_assessed', 0) + counts.get(None, 0)), collected=c.COLLECTED, pcsrc=esc(c.PCODE_SOURCE),
                     uncovered='' if counts.get('destroyed') or counts.get('nearby') or counts.get('none_detected') else
                     '\n<p><b>UNOSAT\'s 2017 analysis covered Maungdaw, Buthidaung and Rathedaung, not %s township,</b> so every village in this gazetteer is marked “not assessed”.</p>' % esc(town)))

        # ---- key map
        if c.bounds:
            li = ''.join('<li><b>%d</b><span>%s%s</span></li>' % (s['i'], esc(s['name']), '' if s['tract'] else ' <i>†</i>') for s in sections)
            missing = any(not s['tract'] for s in sections)
            h.append('''<section class="sheet brk">
<h2><small>Key map</small>%(town)s township and its village tracts</h2>
<div class="keymap"><div>%(map)s</div><ol>%(li)s</ol></div>
<p class="maplegend">Each number is a village tract, in the order of the pages that follow. Dots are the villages in this gazetteer. Thin lines are village-tract boundaries, the heavy line is the township boundary.%(dag)s Boundaries: UN OCHA COD-AB (source: MIMU), CC BY-IGO, at about 1:250,000; they are approximate.</p>
</section>''' % dict(town=esc(town), map=key_map, li=li,
                     dag=' † No boundary is drawn for this tract, so it has no number on the map: MIMU has since made it a town or town wards, or the archive records no tract for the village. Its villages are listed and mapped all the same.' if missing else ''))

        # ---- tracts
        h.append('<section class="sheet brk"><h2><small>The villages</small>%d village tracts, %d villages</h2>' % (n_tracts, len(vs)))
        for s in sections:
            m = s['members']
            tmy = s['tract'].get('my') if s['tract'] else ''
            mimu = Counter(v.get('mimu_village_tract_name') for v in m if v.get('mimu_village_tract_name')).most_common(1)
            mimu = mimu[0][0] if mimu else ''
            meta = ['<b>%d</b> %s' % (len(m), 'village' if len(m) == 1 else 'villages'),
                    'entries <b>%d%s</b>' % (numbers[m[0]['id']], '–%d' % numbers[m[-1]['id']] if len(m) > 1 else '')]
            if s['code']: meta.append('tract code <b>%s</b>' % esc(s['code']))
            if mimu and c.slugify(mimu) != c.slugify(s['name']): meta.append('MIMU spelling <b>%s</b>' % esc(mimu))
            # why a tract has no outline: MIMU has since reclassified it (its villages keep their codes)
            gone = Counter(v.get('mimu_village_tract_status') for v in m if (v.get('mimu_village_tract_status') or '').startswith('inactive')).most_common(1)
            if gone and gone[0][1] * 2 > len(m) and gone[0][0] in c.g['TRACT_INACTIVE']:
                meta.append('in MIMU\'s list: <b>%s</b>' % c.g['TRACT_INACTIVE'][gone[0][0]])
            rows = []
            for v in m:
                rows.append('<tr><td class="n">%d</td><td class="ro">%s</td><td class="en">%s</td><td class="mm mmr">%s</td><td class="co">%s</td><td class="pc">%s</td><td class="st">%s</td></tr>' % (
                    numbers[v['id']], esc(v['rohingya_name'].strip()) if v.get('rohingya_name') else '<em>not yet recorded</em>',
                    esc(c.en(v)) or '<em>—</em>', esc(v.get('village_name_mmr') or '') or '<em>—</em>',
                    '%.5f, %.5f' % (float(v['lat']), float(v['lng'])) if not c.unverified(v) else '<em>unverified</em>',
                    esc(v.get('pcode_village') or '') or '<em>—</em>', ST_SYMBOL[c.status(v)]))
            h.append('''<div class="tract">
<div class="thead"><div><div class="tn"><span class="num">%(i)d</span><h3>%(name)s</h3>%(my)s</div><p class="meta">%(meta)s</p></div>%(mini)s</div>
<div class="tblwrap"><table class="gz"><thead><tr><th class="n">No.</th><th class="ro">Rohingya name</th><th class="en">Official name</th><th class="mm">Burmese</th><th class="co">Lat., long.</th><th class="pc">Code</th><th class="st">2017</th></tr></thead>
<tbody>%(rows)s</tbody></table></div>
</div>''' % dict(i=s['i'], name=esc(s['name']), my='<span class="tmy mmr">%s</span>' % esc(tmy) if tmy else '', meta=' · '.join(meta),
                 mini=mini_map(c, acc, s['tract'], m, numbers), rows=''.join(rows)))
        h.append('</section>')

        # ---- index
        entries = []
        for v in vs:
            if v.get('rohingya_name'): entries.append((v['rohingya_name'].strip(), numbers[v['id']], False))
            if c.en(v) and plain(c.en(v)) != plain(v.get('rohingya_name')): entries.append((c.en(v).strip(), numbers[v['id']], True))
        entries.sort(key=lambda e: (plain(e[0]), e[1]))
        idx, letter = [], ''
        for name, num, off in entries:
            first = (plain(name)[:1] or '#').upper()
            if first != letter: letter = first; idx.append('<div class="let">%s</div>' % esc(letter))
            idx.append('<p%s><span>%s</span><i></i><b>%d</b></p>' % (' class="off"' if off else '', esc(name), num))
        h.append('''<section class="sheet brk">
<h2><small>Index</small>Every name, A to Z</h2>
<p class="lead">Rohingya names are in upright type and official names in <i>italics</i>. The number is the entry number in the pages before.</p>
<div class="idx">%s</div>
</section>''' % ''.join(idx))

        # ---- colophon
        h.append('''<section class="sheet brk"><div class="col">
<h2><small>About</small>FARA, the Arakan Village Name Archive</h2>
<p class="lead">FARA preserves the names and locations of %(N)s Rohingya villages across Maungdaw, Buthidaung, Rathedaung and Sittwe townships of Arakan, in Rohingya, English and Burmese. Every village had a name. FARA exists so those names are never erased.</p>
<h3>Online</h3>
<p>The full archive, with satellite imagery of every village, is at <b>map.rohingya.ro</b>. This township is at <b>map.rohingya.ro%(turl)s</b>, and the newest edition of this gazetteer at <b>map.rohingya.ro%(pdf)s</b>.</p>
<h3>Using this gazetteer</h3>
<p>You are free to print, copy and share it. The village names and positions come from the Rohingya Khobor Arakan Maps Project. Place codes are © Myanmar Information Management Unit. The boundaries are from UN OCHA's COD-AB dataset (source: MIMU; CC BY-IGO) and the 2017 analysis from UNOSAT (CC BY-SA); please keep those credits with the maps and the 2017 column.</p>
<h3>How to cite</h3>
<span class="cite">FARA — The Arakan Village Name Archive. <i>Gazetteer of Rohingya Villages: %(town)s Township.</i> Edition %(ed)s. map.rohingya.ro%(path)s</span>
<h3>Contact</h3>
<p>A project by AB Aziz · ab@rohingya.ro</p>
</div>
<div class="notes">
<h3>Names this gazetteer is missing, or has wrong</h3>
<p>Write them here: the village, its tract, and the name as its people say it. Then send a photograph of this page to ab@rohingya.ro.</p>
%(lines)s
</div></section>''' % dict(N='{:,}'.format(c.N), turl=c.turl(town), pdf=pdf, town=esc(town), ed=edition, path=path, lines='<i></i>' * 8))

        title = 'Gazetteer of Rohingya Villages: %s Township | FARA' % town
        desc = 'A printable gazetteer of the %d Rohingya villages of %s township, Arakan (Rakhine State, Myanmar): names in Rohingya, English and Burmese, coordinates, place codes and maps of every village tract.' % (len(vs), town)
        html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#050B14">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<link rel="canonical" href="%(site)s%(path)s">
%(cite)s<meta property="og:type" content="book">
<meta property="og:site_name" content="FARA — The Arakan Village Name Archive">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(site)s%(path)s">
<meta property="og:image" content="%(site)s/og.png">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="alternate" type="application/pdf" href="%(pdf)s" title="PDF edition">
%(fonts)s
<link rel="stylesheet" href="/gazetteer.css">
<style>body{--acc:%(acc)s}@page{@top-right{content:"%(town)s Township";font:500 7.4pt 'Space Grotesk',sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#5B6B7C;vertical-align:bottom;padding-bottom:4mm}}@page cover{@top-right{content:none}}</style>
<script type="application/ld+json">%(ld)s</script>
</head>
<body>
%(body)s
%(analytics)s
</body>
</html>
''' % dict(cite=c.g['cite_meta'](title, c.SITE + path), title=esc(title), desc=esc(desc), site=c.SITE, path=path, pdf=pdf, fonts=FONTS, acc=acc, town=esc(town), body='\n'.join(h), analytics=c.ANALYTICS,
           ld=json.dumps({'@context': 'https://schema.org', '@type': 'Book', 'name': 'Gazetteer of Rohingya Villages: %s Township' % town,
                          'url': c.SITE + path, 'inLanguage': ['en', 'rhg', 'my'], 'datePublished': c.today.isoformat(),
                          'publisher': {'@type': 'Organization', 'name': 'FARA — The Arakan Village Name Archive', 'url': c.SITE + '/'},
                          'about': {'@type': 'AdministrativeArea', 'name': town + ' Township, Rakhine State (Arakan), Myanmar'},
                          'encoding': {'@type': 'MediaObject', 'encodingFormat': 'application/pdf', 'contentUrl': c.SITE + pdf}}, ensure_ascii=False, separators=(',', ':')))
        c.write(c.p('township', slug, 'gazetteer', 'index.html'), html)
        made += 1
    return made


# =====================================================================================================  stories
# Two kinds, one engine (stories.js + stories.css):
#   written stories        content/stories/*.json, text by hand, numbers filled in from the data
#   village stories        one for every village where UNOSAT mapped destruction at or near it in 2017,
#                          made from that village's names, its dated satellite pictures and UNOSAT's finding
STORY_DATE = '2026-11-16'                       # first published; dateModified follows each build
STORY_STATUSES = ('destroyed', 'nearby')
LD = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':'))


def zone_polys(c):
    """Every UNOSAT destroyed zone as (south, north, west, east, polygon in lng/lat)."""
    f = c.p('unosat_2017_zones.geojson')
    if not os.path.exists(f): return []
    out = []
    for ft in json.load(open(f, encoding='utf-8'))['features']:
        g = ft['geometry']
        for poly in (g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]):
            xs = [q[0] for q in poly[0]]; ys = [q[1] for q in poly[0]]
            out.append((min(ys), max(ys), min(xs), max(xs), poly))
    return out


def zone_stats(zones):
    """How many destroyed zones UNOSAT mapped, and their total area in hectares."""
    total = 0.0
    for _, _, _, _, poly in zones:
        for i, ring in enumerate(poly):
            k = math.cos(math.radians(ring[0][1])); a = 0.0
            for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
                a += (x0 * k * 111320) * (y1 * 110574) - (x1 * k * 111320) * (y0 * 110574)
            total += abs(a) / 2 * (1 if i == 0 else -1)
    return len(zones), total / 10000


def zones_near(zones, lat, lng, km=1.8):
    """The zones around one village, as [lat,lng] rings: enough for the story's close-up, so the page needs no big download."""
    dlat = km / 110.574; dlng = km / (111.320 * math.cos(math.radians(lat)))
    out = []
    for la0, la1, ln0, ln1, poly in zones:
        if la1 < lat - dlat or la0 > lat + dlat or ln1 < lng - dlng or ln0 > lng + dlng: continue
        rings = []
        for ring in poly:
            pts = []
            for q in thin([(q[1], q[0]) for q in ring], 0.00003):     # corners closer than about 3 m to a straight line are dropped
                p2 = [round(q[0], 5), round(q[1], 5)]
                if not pts or pts[-1] != p2: pts.append(p2)
            if len(pts) > 3: rings.append(pts)
        if rings: out.append(rings)
    return out


def thin(pts, tol):
    """Douglas-Peucker: drop points that lie within tol of the line between their neighbours."""
    if len(pts) < 5: return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (y0, x0), (y1, x1) = pts[a], pts[b]
        dx, dy = x1 - x0, y1 - y0; n2 = dx * dx + dy * dy
        worst, at = 0.0, -1
        for i in range(a + 1, b):
            y, x = pts[i]
            if n2 == 0: d = math.hypot(x - x0, y - y0)
            else:
                t = max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / n2))
                d = math.hypot(x - (x0 + t * dx), y - (y0 + t * dy))
            if d > worst: worst, at = d, i
        if worst > tol and at > 0:
            keep[at] = True; stack.append((a, at)); stack.append((at, b))
    return [q for q, k in zip(pts, keep) if k]


def km_between(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (float(a['lat']), float(a['lng']), float(b['lat']), float(b['lng'])))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def clip(text, n):
    """Cut at a word, for titles and descriptions."""
    if len(text) <= n: return text
    return text[:n - 1].rsplit(' ', 1)[0].rstrip(' ,;:') + '…'


def story_shell(c, path, title, desc, body, data, ld, og_image=None, og_alt=None, ver=''):
    """The page around a story: head (SEO, previews, fast loading), the story itself, the scripts."""
    esc = c.esc
    return '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#02050A">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<link rel="canonical" href="%(site)s%(path)s">
%(cite)s<meta name="robots" content="index, follow, max-image-preview:large">
<meta property="og:type" content="article">
<meta property="og:site_name" content="FARA — The Arakan Village Name Archive">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(site)s%(path)s">
<meta property="og:image" content="%(ogi)s">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="%(oga)s">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="%(ogi)s">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="preconnect" href="https://unpkg.com" crossorigin>
<link rel="preconnect" href="https://services.arcgisonline.com" crossorigin>
<link rel="preconnect" href="https://wayback.maptiles.arcgis.com" crossorigin>
%(fonts)s
<link rel="stylesheet" href="/stories.css?v=%(ver)s">
<link id="lfcss" rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" media="print" onload="this.media='all'">
<noscript><link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"></noscript>
%(ld)s</head>
<body>
%(body)s
<script>window.FARA_STORY=%(data)s;</script>
<script defer src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script defer src="/stories/data.js?v=%(ver)s"></script>
<script defer src="/stories.js?v=%(ver)s"></script>
%(analytics)s
<script>if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(function(){});</script>
</body>
</html>
''' % dict(cite=c.g['cite_meta'](title, c.SITE + path), title=esc(title), desc=esc(desc), site=c.SITE, path=path, fonts=FONTS, body=body, analytics=c.ANALYTICS, ver=ver,
           data=LD(data), ld=''.join('<script type="application/ld+json">%s</script>\n' % LD(j) for j in ld),
           ogi=og_image or (c.SITE + '/og.png'), oga=esc(og_alt or title))


def article_ld(c, path, headline, desc, image=None, about=None):
    d = {'@context': 'https://schema.org', '@type': 'Article', 'headline': clip(headline, 110), 'description': desc, 'url': c.SITE + path,
         'mainEntityOfPage': c.SITE + path, 'datePublished': STORY_DATE, 'dateModified': c.today.isoformat(), 'inLanguage': 'en',
         'image': [image or c.SITE + '/og.png'],
         'author': {'@type': 'Person', 'name': 'AB Aziz', 'url': c.SITE + '/'},
         'publisher': {'@type': 'Organization', 'name': 'FARA — The Arakan Village Name Archive', 'url': c.SITE + '/',
                       'logo': {'@type': 'ImageObject', 'url': c.SITE + '/logo.png'}},
         'isPartOf': {'@type': 'CreativeWorkSeries', 'name': 'FARA Stories', 'url': c.SITE + '/stories/'}}
    if about: d['about'] = about
    return d


def fire_points(c):
    """Every fire detection of the two autumns as (lat, lng, yyyymmdd)."""
    f = c.p('fires_points.json')
    return [(q[0], q[1], q[2]) for q in json.load(open(f, encoding='utf-8'))['p']] if os.path.exists(f) else []


def fires_near(points, lat, lng, km=2.2):
    """Detections around one village, each with its day written out, to travel inside the story page."""
    dlat = km / 110.574; dlng = km / (111.320 * math.cos(math.radians(lat)))
    return [[la, ln, '%d %s %d' % (d % 100, MONTHS[d // 100 % 100 - 1][:3], d // 10000)] for la, ln, d in points
            if abs(la - lat) <= dlat and abs(ln - lng) <= dlng]


def days_text(days):
    """'28 August, 29 August and 5 September 2017'."""
    parts = ['%d %s' % (int(d[8:]), MONTHS[int(d[5:7]) - 1]) for d in days]
    return (', '.join(parts[:-1]) + ' and ' + parts[-1] if len(parts) > 1 else parts[0]) + ' ' + days[0][:4]


SOURCES_VILLAGE = [
    ('UNOSAT: Destroyed areas in Buthidaung, Maungdaw, and Rathedaung Townships of Rakhine State in Myanmar',
     'https://data.humdata.org/dataset/destroyed-areas-in-buthidaung-maungdaw-and-rathedaung-townships-of-rakhine-state-in-myanmar-2727',
     'the destroyed zones and their dates. CC BY-SA. Analysis from satellite imagery, not validated on the ground.'),
    ('NASA FIRMS: active fire detections (VIIRS 375 m and MODIS 1 km)', 'https://firms.modaps.eosdis.nasa.gov/',
     'the fires and their days, in Myanmar time. A detection is heat seen from orbit; fires under cloud are not detected.'),
    ('Esri World Imagery Wayback', 'https://livingatlas.arcgis.com/wayback/', 'the satellite pictures and their capture dates.'),
    ('Rohingya Khobor: Arakan Maps Project', 'https://map.rohingyakhobor.com/map', 'the village name and position.'),
    ('UN OCHA: Myanmar Subnational Administrative Boundaries (COD-AB, source: MIMU)', 'https://data.humdata.org/dataset/cod-ab-mmr', 'township boundaries. CC BY-IGO.'),
]
METHOD = ('How villages were matched: a village is counted as destroyed when a UNOSAT zone covers its recorded position or at least one hectare is marked destroyed '
          'within 300 metres of it, and as “nearby” when any zone lies within 500 metres. Matching is by position only and has not been reviewed village by village. '
          'The pictures are shown as Esri published them; FARA does not describe what they show. The per-village results are in '
          '<a href="/status_unosat_2017.csv">status_unosat_2017.csv</a>.')


def story_body(c, kicker, h1, dek, crumbs, steps_html, sources, method, links, published, extra=''):
    esc = c.esc
    srcs = ''.join('<li><a href="%s" rel="noopener">%s</a>%s</li>' % (esc(u), esc(n), ' — ' + esc(note) if note else '') for n, u, note in sources)
    return '''<div class="story" id="story">
  <div class="smap" id="smap" aria-hidden="true"></div>
  <div class="scap" id="scap" aria-live="polite"></div>
  <div class="slegend" id="slegend"></div>
  <header class="shero">
    <a class="sbrand" href="/" aria-label="FARA home">%(logo)s<span><b>FARA</b><i>Stories</i></span></a>
    <nav class="scrumbs" aria-label="Breadcrumb">%(crumbs)s</nav>
    <p class="skick">%(kicker)s</p>
    <h1>%(h1)s</h1>
    <p class="sdek">%(dek)s</p>
    <p class="sscroll">Scroll to begin <span aria-hidden="true">↓</span></p>
  </header>
  <main class="steps">%(steps)s</main>
  <footer class="send">
    <div class="scard wide">
      %(extra)s
      <h2>Sources and method</h2>
      <ul class="ssrc">%(srcs)s</ul>
      <p class="snote">%(method)s</p>
      <p class="sbtns">%(links)s</p>
      <p class="snote">Published %(date)s · FARA — The Arakan Village Name Archive · a project by AB Aziz · <a href="mailto:ab@rohingya.ro">ab@rohingya.ro</a></p>
    </div>
  </footer>
</div>''' % dict(logo=c.LOGO, crumbs=crumbs, kicker=esc(kicker), h1=esc(h1), dek=esc(dek), steps='\n'.join(steps_html), srcs=srcs, method=method,
                 links=links, date=published, extra=extra)


def step(i, html):
    return '<section class="step%s" data-i="%d"><div class="scard">%s</div></section>' % (' first' if i == 0 else '', i, html)


def village_story(c, v, caps, zones, by_town, near, prev_next, ver, shared_name, used, fires, fire):
    """One village's story: where it is, the last picture before autumn 2017, the first one after with UNOSAT's finding,
    the newest picture, the township it is part of, and where to go next. Every sentence comes from the data."""
    esc, g = c.esc, c.g
    name, off, mm = c.ro(v).strip(), c.en(v).strip(), (v.get('village_name_mmr') or '').strip()
    town, tract = v.get('township') or '', (v.get('village_tract') or '').strip()
    has_ro = bool(v.get('rohingya_name')); both = has_ro and off and plain(off) != plain(name)
    r = c.ST17[str(v['id'])]; status = r['status']
    lat, lng = float(v['lat']), float(v['lng'])
    ymd = lambda n: g['long_day']('%04d-%02d-%02d' % (n // 10000, n // 100 % 100, n % 100))
    rows = [x for x in caps if x[1]]
    bef = max((x for x in rows if x[1] < 20170825), key=lambda x: x[1]); aft = min((x for x in rows if x[1] > 20171011), key=lambda x: x[1])
    old = min(rows, key=lambda x: x[1]); new = max(rows, key=lambda x: x[1])
    base = lambda x: {'rel': x[0], 'z18': bool(x[4])}
    path = '/stories/%s/' % v['slug']
    N, P = esc(name), [lat, lng]
    td, tn = by_town[town].get('destroyed', 0), by_town[town].get('nearby', 0)

    # ---- the words
    where = '%s is a Rohingya village in %s%s township, in the north of Arakan, the land Myanmar calls Rakhine State.' % (
        N, esc(tract) + ' village tract, ' if tract else '', esc(town))
    if both: names = 'On official maps it is written <b>%s</b>.' % esc(off)
    elif not has_ro: names = 'Its Rohingya name has not been recorded in the archive yet; %s is its official name.' % N
    else: names = 'Its official name is written the same way.'
    if mm: names += ' In Burmese: <span class="mmr">%s</span>.' % esc(mm)
    ha = r.get('destroyed_ha_within_300m') or 0
    first = g['long_day'](r['first_seen'])
    if status == 'destroyed':
        found = ('The yellow line is what UNOSAT, the United Nations satellite centre, mapped as destroyed: %s, first seen in a satellite image of %s.'
                 % ('about <b>%g hectares</b> within 300 metres of the village’s recorded position' % ha if ha >= 0.1 else 'buildings at the village’s recorded position', first))
        part = ('%s is one of <b>%d villages</b> in %s township where UNOSAT mapped destroyed buildings at the recorded position. Another %d had a destroyed zone within 500 metres.'
                % (N, td, esc(town), tn))
        dek = ('%s%s is a Rohingya village in %s township, Arakan. These are the satellite pictures of it from before and after the autumn of 2017, and what the United Nations mapped there.'
               % (name, ' (%s)' % off if both else '', town))
        desc = 'Satellite pictures of %s%s, a Rohingya village in %s township, Arakan, before and after autumn 2017, and what UNOSAT mapped as destroyed there.'
    else:
        found = ('The yellow line is a zone UNOSAT, the United Nations satellite centre, mapped as destroyed, <b>%d metres</b> from the village’s recorded position and first seen in a satellite image of %s. '
                 'It may belong to a neighbouring settlement: this record has not been reviewed on its own.' % (r['nearest_zone_m'], first))
        part = ('In %s township UNOSAT mapped destroyed buildings at the recorded position of <b>%d villages</b>. %s is one of %d more with a destroyed zone within 500 metres.'
                % (esc(town), td, N, tn))
        dek = ('%s%s is a Rohingya village in %s township, Arakan. These are the satellite pictures of it from before and after the autumn of 2017, and the destroyed zone the United Nations mapped beside it.'
               % (name, ' (%s)' % off if both else '', town))
        desc = 'Satellite pictures of %s%s, a Rohingya village in %s township, Arakan, before and after autumn 2017, and the destroyed zone UNOSAT mapped beside it.'
    # several villages share a name (three "Fuk Para"): those say which tract, so no two pages have the same title or description
    tag = ' (%s tract)' % tract if shared_name and tract else ''
    d1 = desc % (name, tag or (' (%s)' % off if both else ''), town)
    if len(d1) > 165: d1 = desc % (name, tag, town)
    desc = clip(d1, 165)
    if desc in used: desc = clip(desc.rstrip('.…') + '. Record %s.' % c.rid(v), 175)
    used.add(desc)
    flags = []
    if r.get('confidence') == 'uncertain': flags.append('UNOSAT rated its reading of this zone as uncertain.')
    if r.get('cloud_note'): flags.append('Parts of the area were under cloud in some of the images.')
    flags.append('UNOSAT worked from satellite images alone and did not check its findings on the ground.')
    f17, f16 = (fire or {}).get('2017'), (fire or {}).get('2016')
    if not f17: flags.append('NASA’s fire-detecting satellites recorded no fire within a kilometre in those weeks; a fire under monsoon cloud goes unseen.')

    S, J = [], []
    def add(m, html): S.append(step(len(S), html)); J.append(m)
    add({'fit': town, 'base': 'dark', 'dots': 'town', 'lines': True, 'pin': P},
        '<p class="k">%s township · Arakan</p><h2>%s</h2><p>%s</p><p>%s</p>' % (esc(town), 'A village called ' + N if has_ro else N, where, names))
    add({'at': P, 'zoom': 16, 'base': base(bef), 'dots': 'none', 'pin': True, 'caption': '<b>Photographed %s</b> · Esri World Imagery, Wayback archive' % ymd(bef[1])},
        '<p class="k">Before</p><h2>%s</h2><p>The most recent picture of %s in Esri’s archive from before August 2017. The ring marks the village’s recorded position.</p>%s'
        % (ymd(bef[1]), N, '<p class="fine">The oldest picture of this ground in the archive is from %s.</p>' % ymd(old[1]) if old[1] != bef[1] else ''))
    if f17:
        n = len(f17['days'])
        add({'at': P, 'zoom': 15, 'base': base(bef), 'dots': 'none', 'pin': True, 'fires': True,
             'caption': '<b>Orange dots:</b> fires detected by NASA satellites, with the day · picture of %s' % ymd(bef[1])},
            '<p class="k">Between the two pictures</p><h2 class="big fire"><b>%d</b><span>%s on which a satellite<br>detected fire here</span></h2>'
            '<p>NASA’s fire-detecting satellites pass over several times a day. They recorded fire within one kilometre of %s on <b>%s</b>. '
            'The nearest detection was %d metres from the village’s recorded position.</p>%s'
            '<p class="fine">A detection is heat seen from orbit. It does not say what burned, and fires under cloud are not seen at all. Days are in Myanmar time.</p>'
            % (n, 'day' if n == 1 else 'days', N, days_text(f17['days']), f17['nearest_m'],
               '<p>Fire was also detected here a year earlier, on %s.</p>' % days_text(f16['days']) if f16 else ''))
    add({'at': P, 'zoom': 16, 'base': base(aft), 'dots': 'none', 'pin': True, 'zones': True, 'fires': bool(f17),
         'caption': '<b>Photographed %s</b> · yellow line: destroyed zone mapped by UNOSAT' % ymd(aft[1])},
        '<p class="k">After</p><h2>%s</h2><p>The same ground, in the earliest picture the archive holds from after that autumn. %s</p><p class="fine">%s</p>'
        % (ymd(aft[1]), found, ' '.join(flags)))
    if new[1] > aft[1]:
        add({'at': P, 'zoom': 16, 'base': base(new), 'dots': 'none', 'pin': True, 'zones': True,
             'caption': '<b>Photographed %s</b> · the newest picture in the archive' % ymd(new[1])},
            '<p class="k">Most recent</p><h2>%s</h2><p>The newest picture of the same ground. The yellow line is the same outline as before.</p>'
            '<p class="sbtns"><a class="sbtn primary" href="/#v=%d">See all %d pictures of %s</a></p>' % (ymd(new[1]), v['id'], len(rows), N))
    add({'fit': town, 'base': 'dark', 'dots': 'st17', 'lines': True, 'pin': P, 'legend': 'st17'},
        '<p class="k">Not one village alone</p><h2 class="big red"><b>%d</b><span>villages in %s<br>with destroyed buildings</span></h2><p>%s</p>'
        '<p>The survey used pictures taken between 31 August and 11 October 2017. It cannot show what happened after that date.</p>'
        '<p class="sbtns"><a class="sbtn" href="/stories/what-the-satellites-recorded/">Read the whole account</a></p>' % (td, esc(town), part))
    nb = ''.join('<li><a href="/stories/%s/">%s</a><span>%s</span></li>' % (x['slug'], esc(c.ro(x).strip()), '%d m' % round(d * 1000) if d < 1 else '%.1f km' % d) for d, x in near)
    add({'at': P, 'zoom': 13, 'base': 'dark', 'dots': 'town', 'lines': True, 'pin': True},
        '<p class="k">The name remains</p><h2>Do you know %s?</h2><p>FARA keeps this village on record: its name, its place, and what the satellites saw. '
        'If you know its name as its people say it, or something here is wrong, tell us.</p>'
        '<p class="sbtns"><a class="sbtn primary" href="%s">The full record of %s</a><a class="sbtn" href="/#v=%d&amp;suggest">Suggest a name or correction</a></p>%s'
        % (N, c.vurl(v), N, v['id'], '<p class="k near">Stories of villages nearby</p><ul class="snear">%s</ul>' % nb if nb else ''))

    # ---- the page
    who = '%s, %s tract,' % (name, tract) if shared_name and tract else name
    t = '%s (%s) in 2017: the satellite record | FARA' % (name, off) if both and not shared_name else '%s in 2017: the satellite record | FARA' % who
    if len(t) > 65: t = '%s in 2017: the satellite record | FARA' % who
    if len(t) > 65: t = '%s in 2017: the satellite record' % who
    if t in used: t = '%s in 2017: the satellite record (%s)' % (who, c.rid(v))
    used.add(t)
    crumbs = '<a href="/">FARA</a><i>/</i><a href="/stories/">Stories</a><i>/</i><a href="%s">%s township</a>' % (c.turl(town), esc(town))
    pv, nx = prev_next
    walk = ''.join('<a class="sbtn" href="/stories/%s/">%s %s</a>' % (x['slug'], lab, esc(c.ro(x).strip())) for x, lab in ((pv, '←'), (nx, '→')) if x)
    links = ('<a class="sbtn primary" href="/stories/">All village stories</a><a class="sbtn" href="%s">%s township</a>'
             '<a class="sbtn" href="%sgazetteer/">Printable gazetteer</a>%s' % (c.turl(town), esc(town), c.turl(town), walk))
    body = story_body(c, '%s township · 2017' % town, name, dek, crumbs, S, SOURCES_VILLAGE, METHOD, links, long_date(date.fromisoformat(STORY_DATE)))
    card = c.SITE + '/share/img/v/%d.png' % v['id'] if os.path.exists(c.p('share', 'img', 'v', '%d.png' % v['id'])) else None
    place = {'@type': 'Place', 'name': name, 'url': c.SITE + c.vurl(v), 'geo': {'@type': 'GeoCoordinates', 'latitude': lat, 'longitude': lng},
             'containedInPlace': {'@type': 'AdministrativeArea', 'name': town + ' Township, Rakhine State (Arakan), Myanmar'}}
    alt = [x for x in [off if both else None, mm or None] if x]
    if alt: place['alternateName'] = alt
    ld = [article_ld(c, path, '%s in 2017: the satellite record' % name, desc, card, place),
          c.crumbs_ld([('FARA', '/'), ('Stories', '/stories/'), (town + ' township', c.turl(town)), (name, path)])]
    data = {'steps': J, 'zones': zones}
    if f17 and fires: data['fires'] = fires
    html = story_shell(c, path, t, desc, body, data, ld, card,
                       '%s — Rohingya village in %s township, Arakan' % (name, town), ver)
    c.write(c.p('stories', v['slug'], 'index.html'), html)
    return {'v': v, 'path': path, 'name': name, 'off': off if both else '', 'town': town, 'tract': tract, 'status': status, 'ha': ha,
            'm': r.get('nearest_zone_m'), 'y0': bef[1] // 10000, 'y1': aft[1] // 10000, 'fire': f17['days'] if f17 else None}


def index_map(c, entries):
    """Every village as a dot; the ones with a story are bright and are links."""
    pts = [(float(v['lat']), float(v['lng'])) for v in c.V if not c.unverified(v)]
    la0, la1, ln0, ln1 = bbox_of(pts)
    pr = Proj(la0 - .03, la1 + .03, ln0 - .03, ln1 + .03, 300)
    s = '<svg class="imap" viewBox="0 0 %.0f %.0f" role="img" aria-label="Map of Arakan showing the villages that have a story">' % (pr.W, pr.H)
    if c.bounds: s += '<path d="%s" fill="none" stroke="rgba(232,242,255,.34)" stroke-width=".7" stroke-linejoin="round"/>' % lines_path(pr, c.bounds['lines']['town'])
    have = {e['v']['id'] for e in entries}
    faint = ''.join('M%.1f %.1fh0' % pr.xy(float(v['lat']), float(v['lng'])) for v in c.V if not c.unverified(v) and v['id'] not in have)
    s += '<path d="%s" stroke="#5F7691" stroke-width="1.5" stroke-linecap="round" opacity=".7"/>' % faint
    for e in sorted(entries, key=lambda e: e['status'] == 'destroyed'):
        x, y = pr.xy(float(e['v']['lat']), float(e['v']['lng']))
        s += '<a href="%s"><circle cx="%.1f" cy="%.1f" r="1.9" fill="%s"><title>%s</title></circle></a>' % (e['path'], x, y, ST_COLOR[e['status']], c.esc(e['name']))
    if c.bounds:
        for t in c.bounds['towns']:
            x, y = pr.xy(t['c'][0], t['c'][1])
            s += '<text x="%.1f" y="%.1f" text-anchor="middle">%s</text>' % (x, y, c.esc(t['n'].upper()))
    return s + '</svg>'


INDEX_JS = '''(function(){var q=document.getElementById('sxq'),items=[].slice.call(document.querySelectorAll('.sxlist li')),t='',s='',n=document.getElementById('sxcount');
function norm(x){return x.toLowerCase().normalize('NFKD').replace(/[\\u0300-\\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim()}
function run(){var k=norm(q.value),c=0;items.forEach(function(li){var ok=(!t||li.dataset.t===t)&&(!s||li.dataset.s===s)&&(!k||li.dataset.n.indexOf(k)>-1);li.hidden=!ok;if(ok)c++});
[].forEach.call(document.querySelectorAll('.sxgroup'),function(g){g.hidden=!g.querySelector('li:not([hidden])')});
n.textContent=c===items.length?'':(c?c+(c===1?' story':' stories')+' shown':'No story matches. Try the official name, or a shorter spelling.')}
q.addEventListener('input',run);
[].forEach.call(document.querySelectorAll('.sxchips'),function(g){g.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;
[].forEach.call(g.querySelectorAll('button'),function(x){x.classList.toggle('on',x===b);x.setAttribute('aria-pressed',String(x===b))});
if('t' in b.dataset)t=b.dataset.t;else s=b.dataset.s;run()})})})();'''


def build_stories(c):
    esc = c.esc
    zones = zone_polys(c)
    n_zones, zone_ha = zone_stats(zones)
    fpts = fire_points(c)
    FIRE = c.g.get('FIRES') or {}
    fmeta = c.g.get('FIRES_META') or {}
    counts = Counter(c.status(v) for v in c.V)
    by_town = {t: Counter(c.status(v) for v in c.V if v.get('township') == t) for t in c.towns}
    caps = json.load(open(c.p('captures.json'), encoding='utf-8')).get('v', {}) if os.path.exists(c.p('captures.json')) else {}

    # what every story page shares, in one cached file: the villages as dots and the township borders
    dots = [[v['id'], round(float(v['lat']), 5), round(float(v['lng']), 5), c.towns.index(v['township']) if v.get('township') in c.towns else -1,
             {'destroyed': 'd', 'nearby': 'n', 'none_detected': 'z'}.get(c.status(v), 'x')] for v in c.V if not c.unverified(v)]
    shared = 'window.FARA_STORY_DATA=' + LD({'towns': c.towns, 'colors': [c.TOWN_COLORS[t] for t in c.towns], 'dots': dots,
                                              'lines': [[[round(q[0], 4), round(q[1], 4)] for q in a] for a in c.bounds['lines']['town']] if c.bounds else None}) + ';\n'
    import hashlib
    h = hashlib.sha256(shared.encode('utf-8'))
    for f in ('stories.js', 'stories.css'):
        if os.path.exists(c.p(f)): h.update(open(c.p(f), 'rb').read())
    ver = h.hexdigest()[:8]
    c.write(c.p('stories', 'data.js'), shared)

    # ---- village stories
    made = []
    pool = [v for v in c.V if c.status(v) in STORY_STATUSES and not c.unverified(v) and
            any(x[1] and x[1] < 20170825 for x in caps.get(str(v['id']), [])) and any(x[1] > 20171011 for x in caps.get(str(v['id']), []))]
    order = sorted(pool, key=lambda v: (c.towns.index(v['township']), plain(c.ro(v)), v['id']))
    shared_names = Counter(plain(c.ro(v)) for v in pool)
    used = set()
    for i, v in enumerate(order):
        near = sorted(((km_between(v, x), x) for x in pool if x['id'] != v['id']), key=lambda t: t[0])[:4]
        same = [x for x in order if x['township'] == v['township']]
        k = same.index(v)
        made.append(village_story(c, v, caps[str(v['id'])], zones_near(zones, float(v['lat']), float(v['lng'])), by_town, near,
                                  (same[k - 1] if k else None, same[k + 1] if k + 1 < len(same) else None), ver,
                                  shared_names[plain(c.ro(v))] > 1, used,
                                  fires_near([q for q in fpts if q[2] > 20170800], float(v['lat']), float(v['lng'])), FIRE.get(str(v['id']))))

    # ---- written stories
    tokens = {'n': '{:,}'.format(c.N), 'n_destroyed': counts.get('destroyed', 0), 'n_nearby': counts.get('nearby', 0),
              'n_none': counts.get('none_detected', 0), 'n_not': counts.get('not_assessed', 0) + counts.get(None, 0),
              'n_zones': '{:,}'.format(n_zones), 'zone_ha': '{:,}'.format(int(round(zone_ha, -1))),
              'n_with_ro': sum(1 for v in c.V if v.get('rohingya_name')), 'n_towns': len(c.towns), 'n_stories': len(made),
              'n_fire': (fmeta.get('villages_with_fire') or {}).get('2017', 0), 'n_fire_2016': (fmeta.get('villages_with_fire') or {}).get('2016', 0),
              'n_fire_viirs': ((fmeta.get('same_weeks_other_years_viirs') or {}).get('2017') or {}).get('villages', 0),
              'fire_max_other': max([o['villages'] for y, o in (fmeta.get('same_weeks_other_years_viirs') or {}).items() if y != '2017'] or [0])}
    for t in c.towns:
        for k, key in (('destroyed', 'd'), ('nearby', 'n'), ('none_detected', 'z')): tokens['%s_%s' % (c.slugify(t), key)] = by_town[t].get(k, 0)
        tokens['%s_all' % c.slugify(t)] = sum(by_town[t].values())

    def fill(text, extra):
        def sub(m):
            k = m.group(1)
            if k in extra: return str(extra[k])
            if k in tokens: return str(tokens[k])
            raise KeyError('story token {{%s}} is not defined' % k)
        return re.sub(r'\{\{(\w+)\}\}', sub, text)

    written = []
    src_dir = c.p('content', 'stories')
    for fn in sorted(os.listdir(src_dir)) if os.path.isdir(src_dir) else []:
        if not fn.endswith('.json'): continue
        st = json.load(open(os.path.join(src_dir, fn), encoding='utf-8'))
        extra, bases = {}, {}
        fv = next((v for v in c.V if v['id'] == st.get('village')), None)
        if fv:
            r = c.ST17.get(str(fv['id'])) or {}
            extra.update(v_name=esc(c.ro(fv)), v_official=esc(c.en(fv)), v_tract=esc(fv.get('village_tract') or ''), v_town=esc(fv.get('township') or ''),
                         v_mmr=esc(fv.get('village_name_mmr') or ''), v_url=c.vurl(fv), v_id=fv['id'], v_rid=c.rid(fv), v_story='/stories/%s/' % fv['slug'],
                         v_ha=('%g' % r.get('destroyed_ha_within_300m')) if r.get('destroyed_ha_within_300m') else '',
                         v_first=c.g['long_day'](r['first_seen']) if r.get('first_seen') else '')
            rows = [x for x in caps.get(str(fv['id']), []) if x[1]]
            bef = max((x for x in rows if x[1] < 20170825), key=lambda x: x[1], default=None)
            aft = min((x for x in rows if x[1] > 20171011), key=lambda x: x[1], default=None)
            ymd = lambda n: c.g['long_day']('%04d-%02d-%02d' % (n // 10000, n // 100 % 100, n % 100))
            if not (bef and aft): raise SystemExit('story %s: no capture dates yet for village %s; run tools/build_captures.py first' % (st['slug'], fv['id']))
            extra.update(cap_before=ymd(bef[1]), cap_after=ymd(aft[1]))
            bases = {'before': {'rel': bef[0], 'z18': bool(bef[4])}, 'after': {'rel': aft[0], 'z18': bool(aft[4])}}
        S, J = [], []
        for s in st['steps']:
            m = dict(s.get('map') or {})
            if fv and m.get('at') == 'village': m['at'] = [float(fv['lat']), float(fv['lng'])]
            if m.get('base') in bases: m['base'] = bases[m['base']]
            if m.get('caption'): m['caption'] = fill(m['caption'], extra)
            S.append(step(len(S), fill(s['html'], extra))); J.append(m)
        path = '/stories/%s/' % st['slug']
        title, summary = fill(st['title'], extra), fill(st['summary'], extra)
        crumbs = '<a href="/">FARA</a><i>/</i><a href="/stories/">Stories</a>'
        links = '<a class="sbtn primary" href="/stories/#villages">The stories of %d villages</a><a class="sbtn" href="/">Open the archive</a><a class="sbtn" href="/villages/">All villages, A–Z</a>' % len(made)
        body = story_body(c, st.get('kicker', ''), title, summary, crumbs, S, [(x['name'], x['url'], x.get('note')) for x in st.get('sources', [])],
                          fill(st.get('method', ''), extra), links, long_date(date.fromisoformat(st['date'])))
        ld = [article_ld(c, path, title, summary), c.crumbs_ld([('FARA', '/'), ('Stories', '/stories/'), (title, path)])]
        page_data = {'steps': J}
        if fv:
            page_data['zones'] = zones_near(zones, float(fv['lat']), float(fv['lng']))
            page_data['fires'] = fires_near([q for q in fpts if q[2] > 20170800], float(fv['lat']), float(fv['lng']))
        c.write(c.p('stories', st['slug'], 'index.html'), story_shell(c, path, title + ' | FARA', clip(st.get('description') or summary, 160), body, page_data, ld, ver=ver))
        written.append({'path': path, 'title': title, 'summary': summary, 'kicker': st.get('kicker', ''), 'date': st['date'], 'steps': len(S)})

    # ---- the index: featured stories, then every village story, findable by township, by what was found, or by name
    nd = sum(1 for e in made if e['status'] == 'destroyed'); nn = len(made) - nd
    body = c.crumbs([('FARA', '/'), ('Stories', None)])
    body += ('<div class="sxhero"><div><h1>Stories</h1><p class="lede">Guided accounts told with the archive itself: the map, the satellite record and the names. '
             'Each one moves as you scroll, and every figure in it comes from data you can open and check.</p>'
             '<dl class="sxstats"><div><dt>%d</dt><dd>stories</dd></div><div><dt>%d</dt><dd>villages destroyed</dd></div><div><dt>%d</dt><dd>destruction nearby</dd></div><div><dt>%d</dt><dd>townships</dd></div></dl></div>'
             '<figure class="sxmap">%s<figcaption><i class="d"></i>destroyed<i class="n"></i>destruction nearby<i class="o"></i>other villages · tap a dot</figcaption></figure></div>'
             % (len(made) + len(written), nd, nn, len({e['town'] for e in made}), index_map(c, made)))
    if written:
        body += '<h2 id="featured">The whole account</h2><ul class="storylist">' + ''.join(
            '<li><a href="%s"><span class="k">%s</span><b>%s</b><span class="d">%s</span><span class="go">Read the story · %d parts →</span></a></li>'
            % (w['path'], esc(w['kicker']), esc(w['title']), esc(w['summary']), w['steps']) for w in written) + '</ul>'
    body += ('<h2 id="villages">Village stories</h2><p class="lede">One story for each of the %d villages where UNOSAT mapped destruction at or beside the village in 2017. '
             'Each shows the village in the last satellite picture from before that autumn and the first one after, with their dates.</p>' % len(made))
    tcount = Counter(e['town'] for e in made)
    body += ('<div class="sxbar"><input id="sxq" type="search" placeholder="Find a village by name" aria-label="Find a village story by name" autocomplete="off">'
             '<div class="sxchips" role="group" aria-label="Township"><button type="button" data-t="" class="on" aria-pressed="true">All <b>%d</b></button>%s</div>'
             '<div class="sxchips" role="group" aria-label="What UNOSAT found"><button type="button" data-s="" class="on" aria-pressed="true">All</button>'
             '<button type="button" data-s="d" aria-pressed="false"><i class="d"></i>Destroyed <b>%d</b></button><button type="button" data-s="n" aria-pressed="false"><i class="n"></i>Nearby <b>%d</b></button></div></div>'
             '<p class="sxcount" id="sxcount" aria-live="polite"></p>'
             % (len(made), ''.join('<button type="button" data-t="%s" aria-pressed="false">%s <b>%d</b></button>' % (esc(t), esc(t), tcount[t]) for t in c.towns if tcount[t]), nd, nn))
    for t in c.towns:
        es = [e for e in made if e['town'] == t]
        if not es: continue
        body += '<section class="sxgroup"><h3 id="%s"><a href="%s">%s township</a><span>%d stories</span></h3><ul class="sxlist">' % (c.slugify(t), c.turl(t), esc(t), len(es))
        for e in es:
            what = ('%g ha destroyed' % e['ha'] if e['ha'] >= 0.1 else 'destroyed') if e['status'] == 'destroyed' else 'zone %d m away' % e['m']
            if e['fire']: what += ' · fire %d %s' % (int(e['fire'][0][8:]), MONTHS[int(e['fire'][0][5:7]) - 1][:3])
            body += ('<li data-t="%s" data-s="%s" data-n="%s"><a href="%s"><i class="%s"></i><b>%s</b>%s<em>%s · %d → %d</em></a></li>'
                     % (esc(t), e['status'][0], esc(plain(e['name'] + ' ' + e['off'] + ' ' + e['tract'])), e['path'], e['status'][0], esc(e['name']),
                        '<span>%s</span>' % esc(e['off']) if e['off'] else '', what, e['y0'], e['y1']))
        body += '</ul></section>'
    body += '<script>%s</script>' % INDEX_JS
    items = [{'@type': 'ListItem', 'position': i + 1, 'url': c.SITE + x['path'], 'name': x.get('title') or x['name']} for i, x in enumerate(written + made)]
    c.write(c.p('stories', 'index.html'), c.page('/stories/', 'Stories: %d Rohingya villages in the satellite record of 2017 | FARA' % len(made),
            'Scrolling stories told with the FARA map and satellite pictures: one for each of %d Rohingya villages in Arakan where the UN mapped destruction in 2017, with dated before-and-after images.' % len(made),
            body, [{'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': 'FARA Stories', 'url': c.SITE + '/stories/',
                    'description': 'Guided accounts told with the FARA map, satellite imagery and the names of Rohingya villages in Arakan.',
                    'mainEntity': {'@type': 'ItemList', 'numberOfItems': len(items), 'itemListElement': items}},
                   c.crumbs_ld([('FARA', '/'), ('Stories', '/stories/')])]))
    c.story_paths = [w['path'] for w in written] + [e['path'] for e in made]
    c.village_stories = {e['v']['id']: e['path'] for e in made}
    return len(written) + len(made)
