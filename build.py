#!/usr/bin/env python3
"""Build FARA's static site from the dataset.

    python3 build.py

Writes:
  fara.html                     the interactive archive (template + embedded data)
  village/<id>-<slug>/index.html   one page per village (for search engines, link previews, citing)
  township/<slug>/index.html    one index page per township
  township/<slug>/gazetteer/    a print-designed gazetteer of the township (build_extra.py; tools/build_pdfs.py makes the PDFs)
  embed/<id>/index.html         a small card other websites can show in an iframe (build_extra.py)
  stories/<slug>/index.html     guided scrolling accounts written in content/stories/*.json (build_extra.py)
  villages/index.html           A-Z index of every village
  methods/, changelog/          how the data was gathered and corrected, and what changed in each edition (build_edition.py)
  CITATION.cff                  how to cite the edition named in edition.json (build_edition.py)
  sitemap.xml, robots.txt, llms.txt
  sw.js                         offline support (cache name changes whenever the site changes)

Everything is plain static files; no server code is needed.
"""
import hashlib, html, json, math, os, re, shutil, unicodedata
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = 'https://map.rohingya.ro'
COLLECTED = '2 July 2026'
TOWN_COLORS = {'Maungdaw': '#00E5FF', 'Buthidaung': '#2BF08D', 'Rathedaung': '#FFB020', 'Sittwe': '#FF4D8C'}
ANALYTICS = '<script defer src="/_vercel/insights/script.js"></script>'

import build_edition
ED = build_edition.load(ROOT)          # the edition being published: version, date, DOI, authors (edition.json)

def p(*a): return os.path.join(ROOT, *a)
def esc(s): return html.escape(str(s if s is not None else ''), quote=True)
def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f: f.write(text)

def slugify(s):
    s = unicodedata.normalize('NFKD', s or '')
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')

V = json.load(open(p('arakan_villages.json'), encoding='utf-8'))
for v in V:
    v['slug'] = '%d-%s' % (v['id'], slugify(v.get('rohingya_name') or v.get('name') or 'village') or 'village')
BY_ID = {v['id']: v for v in V}
N = len(V)

def unverified(v):
    try: la, ln = float(v['lat']), float(v['lng'])
    except Exception: return True
    return v.get('coord_status') == 'unverified' or not (18 < la < 23.5 and 91 < ln < 95)
def ro(v): return v.get('rohingya_name') or v.get('name') or 'Unnamed village'
def en(v): return v.get('name') or ''
def rid(v): return 'FARA-%04d' % v['id']
def vurl(v): return '/village/%s/' % v['slug']
def turl(t): return '/township/%s/' % slugify(t)
def coord(v):
    la, ln = float(v['lat']), float(v['lng'])
    return '%.4f° %s, %.4f° %s' % (abs(la), 'N' if la >= 0 else 'S', abs(ln), 'E' if ln >= 0 else 'W')
def dist_km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (float(a['lat']), float(a['lng']), float(b['lat']), float(b['lng'])))
    h = math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 12742 * math.asin(math.sqrt(h))
def fmt_dist(d): return '%d m' % round(d*1000) if d < 1 else '%.1f km' % d

PLOT = [v for v in V if not unverified(v)]

# official place codes (MIMU P-codes), written into the data by tools/add_pcodes.py
PCODE_SOURCE = 'MIMU Place Codes, Release 9.7 (January 2026)'
PCODE_URL = 'https://themimu.info/place-codes'
VILLAGE_INACTIVE = {'inactive_removed_from_list': 'MIMU no longer lists this as a village (marked inactive).',
                    'inactive_reclassified_to_ward': 'MIMU now counts this village as part of a town ward (marked inactive).'}
TRACT_INACTIVE = {'inactive_reclassified_to_ward': 'former village tract, now town wards', 'inactive_reclassified_to_town': 'former village tract, now a town',
                  'inactive': 'former village tract'}
def pcode_rows(v):
    """Rows for the 'Official place codes' table of a village page, plus notes. Empty when the data has no codes."""
    if not v.get('pcode_township'): return [], []
    code = lambda c: '<span class="mono">%s</span>' % esc(c)
    named = lambda name, c: '%s%s' % (esc(name) + ' · ' if name else '', code(c))
    rows, notes = [], []
    if v.get('pcode_village'):
        rows.append(('Village', named(v.get('mimu_village_name'), v['pcode_village'])))
        if v.get('mimu_village_status') in VILLAGE_INACTIVE: notes.append(VILLAGE_INACTIVE[v['mimu_village_status']] + ' The code remains its official reference.')
    elif v.get('pcode_match') == 'unconfirmed':
        rows.append(('Village', '<em>not confirmed yet</em>'))
        notes.append('A likely official code has been found for this village but is still being checked, so it is not shown.')
    else:
        rows.append(('Village', '<em>no official place code</em>'))
        notes.append('This village is not in the official MIMU village list, so it has no place code of its own.')
    if v.get('pcode_village_tract'):
        t = named(v.get('mimu_village_tract_name'), v['pcode_village_tract'])
        if v.get('mimu_village_tract_status') in TRACT_INACTIVE: t += ' <em>(%s)</em>' % TRACT_INACTIVE[v['mimu_village_tract_status']]
        rows.append(('Village tract', t))
        if v.get('village_tract') and v.get('mimu_village_tract_name') and slugify(v['village_tract']) != slugify(v['mimu_village_tract_name']):
            notes.append('MIMU spells or assigns the village tract differently from the source of this archive (%s).' % esc(v['village_tract']))
    rows.append(('Township', named(v.get('township'), v['pcode_township'])))
    rows.append(('District', named(v.get('district'), v['pcode_district'])))
    return rows, notes

# ------------------------------------------------------------------ the interactive archive
KEYS = ['id', 'name', 'lat', 'lng', 'township', 'district', 'village_tract', 'rohingya_name', 'village_name_mmr', 'coord_status', 'slug']

# what UNOSAT's 2017 satellite analysis marked at or near each village (tools/match_unosat.py)
ST17 = {}
if os.path.exists(p('status_unosat_2017.json')):
    ST17 = json.load(open(p('status_unosat_2017.json'), encoding='utf-8'))['villages']
ST17_URL = 'https://data.humdata.org/dataset/destroyed-areas-in-buthidaung-maungdaw-and-rathedaung-townships-of-rakhine-state-in-myanmar-2727'
# fires NASA's satellites detected within 1 km of each village in the autumns of 2017 and 2016 (tools/match_fires.py)
FIRES, FIRES_META = {}, {}
if os.path.exists(p('fires.json')):
    _f = json.load(open(p('fires.json'), encoding='utf-8')); FIRES, FIRES_META = _f['villages'], _f['meta']
FIRMS_URL = 'https://firms.modaps.eosdis.nasa.gov/'
MONTHS_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
def day_list(days, long=True):
    """'28 August, 29 August and 5 September 2017' from ISO days of one year."""
    names = MONTHS_LONG if long else MONTHS_SHORT
    parts = ['%d %s' % (int(d[8:]), names[int(d[5:7]) - 1]) for d in days]
    return (', '.join(parts[:-1]) + ' and ' + parts[-1] if len(parts) > 1 else parts[0]) + ' ' + days[0][:4]
def fire_sentence(v, name):
    """What NASA's fire-detecting satellites recorded near a village, or None when the location is unverified."""
    if unverified(v): return None
    f = FIRES.get(str(v['id'])) or {}
    out = []
    for key in ('2017', '2016'):
        if key in f:
            o = f[key]
            out.append("NASA's fire-detecting satellites recorded a fire within one kilometre of %s on %s%s; the nearest detection was %d metres from the village's recorded position."
                       % (name, day_list(o['days']), ' (%d days)' % len(o['days']) if len(o['days']) > 2 else '', o['nearest_m']))
    if '2017' not in f:
        out.append("NASA's fire-detecting satellites recorded no fire within one kilometre of %s between 25 August and 30 November 2017. Fires under cloud are not detected, so this does not show there was none." % name)
    else:
        out.append('A detection is heat seen from orbit: it does not say what burned.')
    return ' '.join(out)

ST17_LABEL = {'destroyed': 'Destroyed in 2017', 'nearby': 'Destruction nearby in 2017',
              'none_detected': 'No destruction detected in 2017', 'not_assessed': 'Not assessed in 2017'}
MONTHS_LONG = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
def long_day(iso):
    y, m, d = iso.split('-')
    return '%d %s %s' % (int(d), MONTHS_LONG[int(m) - 1], y)
def st17_sentence(v, name):
    """(status, one careful sentence on what UNOSAT marked), or (None, None) when there is no verified location."""
    r = ST17.get(str(v['id']))
    if not r or r.get('reason') == 'no verified location': return None, None
    s = r['status']
    if s == 'destroyed':
        ha = r.get('destroyed_ha_within_300m') or 0
        extent = ": about %g hectares within 300 metres of the village's recorded location" % ha if ha >= 0.1 else ''
        t = ("UNOSAT's analysis of satellite imagery from 31 August to 11 October 2017 marked destroyed buildings at %s%s, first seen in imagery of %s. "
             "UNOSAT has not validated this on the ground." % (name, extent, long_day(r['first_seen'])))
    elif s == 'nearby':
        t = ("UNOSAT marked a zone of destroyed buildings %d metres from the recorded location of %s, in satellite imagery of %s. "
             "It may belong to a neighbouring settlement; this record has not been reviewed individually." % (r['nearest_zone_m'], name, long_day(r['first_seen'])))
    elif s == 'none_detected':
        t = ("UNOSAT's analysis of satellite imagery from 31 August to 11 October 2017 found no destroyed zone within 500 metres of %s. "
             "That does not show the village is standing: the imagery ends on 11 October 2017, some areas were under cloud, and destruction continued afterwards." % name)
    else:
        t = "%s lies outside the area UNOSAT analysed in 2017, so FARA holds no assessment for it." % name
    return s, t
def embed(r):
    # official MIMU place codes, kept short because they are repeated for every village:
    # pv village code, pt tract code, mn / mt MIMU's spelling where it differs from the archive's,
    # ms / ts why MIMU lists the village / tract as inactive, pm 'u' when the village code is not confirmed yet
    d = {k: r[k] for k in KEYS if r.get(k) is not None}
    if r.get('pcode_village'): d['pv'] = r['pcode_village']
    if r.get('pcode_village_tract'): d['pt'] = r['pcode_village_tract']
    if r.get('mimu_village_name') and r['mimu_village_name'] != r.get('name'): d['mn'] = r['mimu_village_name']
    if r.get('mimu_village_tract_name') and r['mimu_village_tract_name'] != r.get('village_tract'): d['mt'] = r['mimu_village_tract_name']
    ms, ts = r.get('mimu_village_status') or '', r.get('mimu_village_tract_status') or ''
    if ms.startswith('inactive'): d['ms'] = 'w' if ms.endswith('ward') else 'r'
    if ts.startswith('inactive'): d['ts'] = 'w' if ts.endswith('ward') else 't'
    if r.get('pcode_match') == 'unconfirmed': d['pm'] = 'u'
    # u: UNOSAT 2017 — s status (d destroyed, n nearby, z none detected; absent = not assessed),
    # h hectares marked destroyed within 300 m, m metres to the nearest zone, f first imagery date, c 'u' uncertain, cl cloud note
    u = ST17.get(str(r['id']))
    if u and u['status'] != 'not_assessed':
        o = {'s': {'destroyed': 'd', 'nearby': 'n', 'none_detected': 'z'}[u['status']]}
        if u.get('first_seen'):
            o.update(h=u.get('destroyed_ha_within_300m'), m=u.get('nearest_zone_m'), f=u['first_seen'])
            if u.get('confidence') == 'uncertain': o['c'] = 'u'
            if u.get('cloud_note'): o['cl'] = 1
        d['u'] = o
    for key, short in (('2017', 'f7'), ('2016', 'f6')):
        o = (FIRES.get(str(r['id'])) or {}).get(key)
        if o: d[short] = [o['nearest_m'], [x[5:7] + x[8:] for x in o['days']]]
    return d
data = json.dumps([embed(r) for r in V], ensure_ascii=False, separators=(',', ':'))
def cite_meta(title, url):
    """Tags reference managers read (Zotero, Mendeley, Google Scholar): who, what, when, which edition, which DOI."""
    t = esc(re.sub(r'\s*\|\s*FARA\s*$', '', title))
    a = ED['authors'][0]; who = esc('%s, %s' % (a['family'], a['given']))
    doi = ED.get('doi') or ''
    tags = [('citation_title', t), ('citation_author', who), ('citation_publication_date', ED['date'].replace('-', '/')),
            ('citation_publisher', 'FARA — The Arakan Village Name Archive'), ('citation_public_url', url), ('citation_language', 'en'),
            ('DC.title', t), ('DC.creator', who), ('DC.date', ED['date']), ('DC.publisher', 'FARA — The Arakan Village Name Archive'),
            ('DC.type', 'Dataset'), ('DC.language', 'en'), ('DC.rights', (ED.get('licence') or {}).get('url', '')),
            ('DC.source', 'FARA — The Arakan Village Name Archive, edition %s' % ED['version'])]
    if doi: tags += [('citation_doi', doi), ('DC.identifier', 'https://doi.org/' + doi)]
    return ''.join('<meta name="%s" content="%s">\n' % (k, v) for k, v in tags if v)

app = open(p('fara_template.html'), encoding='utf-8').read().replace('__VILLAGE_DATA__', data)
app = build_edition.stamp_app(ED, app, SITE)
app = app.replace('<title>', cite_meta(ED['title'], SITE + '/') + '<title>', 1)
write(p('fara.html'), app)

# ------------------------------------------------------------------ shared page chrome
LOGO = ('<svg viewBox="0 0 64 64" fill="none" aria-hidden="true"><rect x="4" y="4" width="56" height="56" stroke="#00E5FF" stroke-opacity=".35" stroke-width="2"/>'
        '<rect x="4" y="4" width="16" height="4" fill="#00E5FF"/><rect x="4" y="4" width="4" height="16" fill="#00E5FF"/>'
        '<rect x="44" y="56" width="16" height="4" fill="#00E5FF"/><rect x="56" y="44" width="4" height="16" fill="#00E5FF"/>'
        '<circle cx="32" cy="32" r="13" stroke="#00E5FF" stroke-width="2.4" stroke-dasharray="18 8"/><circle cx="32" cy="32" r="4.5" fill="#00E5FF"/></svg>')

_m = re.search(r'<div id="brand">\s*(<svg class="logo".*?</svg>)', app, re.S)
if _m: LOGO = _m.group(1).replace(' class="logo"', '')

CSS_V = hashlib.sha256(open(p('pages.css'), 'rb').read()).hexdigest()[:8]      # so a changed stylesheet is never served from an old copy

def page(path, title, desc, body, jsonld=None, og_title=None, og_image=None, og_alt=None):
    url = SITE + path
    ld = ''.join('<script type="application/ld+json">%s</script>\n' % json.dumps(j, ensure_ascii=False, separators=(',', ':')) for j in (jsonld or []))
    return '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#02050A">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<link rel="canonical" href="%(url)s">
%(cite)s<meta property="og:type" content="article">
<meta property="og:site_name" content="FARA — The Arakan Village Name Archive">
<meta property="og:title" content="%(ogt)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(url)s">
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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Share+Tech+Mono&family=Noto+Sans+Myanmar:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/pages.css?v=%(cssv)s">
%(ld)s</head>
<body>
<header class="top">
  <a class="brand" href="/" aria-label="FARA home">%(logo)s<span><b>FARA</b><i>Arakan Village Name Archive</i></span></a>
  <nav><a href="/">Map</a><a href="/villages/">All villages</a><a href="/stories/">Stories</a></nav>
</header>
<main>
%(body)s
</main>
<footer class="foot">
  <p><b>FARA — The Arakan Village Name Archive.</b> Every village had a name. FARA exists so those names are never erased.</p>
  <p>%(n)s villages across Maungdaw, Buthidaung, Rathedaung and Sittwe townships. Source data: <a href="https://map.rohingyakhobor.com/map" rel="noopener">Rohingya Khobor — Arakan Maps Project</a>, collected %(collected)s.
  Download the data: <a href="/arakan_villages.csv">CSV</a> · <a href="/arakan_villages.json">JSON</a> · <a href="/arakan_villages.geojson">GeoJSON</a>.</p>
  <p><a href="/">The map</a> · <a href="/villages/">All villages, A–Z</a> · <a href="/stories/">Stories</a> · Townships: <a href="/township/maungdaw/">Maungdaw</a>, <a href="/township/buthidaung/">Buthidaung</a>, <a href="/township/rathedaung/">Rathedaung</a>, <a href="/township/sittwe/">Sittwe</a></p>
  <p class="ed">%(edition)s · <a href="/methods/">How this archive was made</a> · <a href="/changelog/">Change log</a> · <a href="/press/">For journalists</a></p>
  <p>A project by AB Aziz · <a href="mailto:ab@rohingya.ro">ab@rohingya.ro</a></p>
</footer>
%(analytics)s
<script>if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(function(){});</script>
</body>
</html>
''' % dict(title=esc(title), desc=esc(desc), url=url, ogt=esc(og_title or title), site=SITE, ld=ld, logo=LOGO, body=body,
           ogi=og_image or (SITE + '/og.png'), oga=esc(og_alt or 'FARA — The Arakan Village Name Archive'),
           n='{:,}'.format(N), collected=COLLECTED, analytics=ANALYTICS, cssv=CSS_V, edition=build_edition.edition_line(ED), cite=cite_meta(title, url))

def crumbs(items):
    out = []
    for i, (name, href) in enumerate(items):
        out.append('<a href="%s">%s</a>' % (href, esc(name)) if href and i < len(items)-1 else '<span>%s</span>' % esc(name))
    return '<nav class="crumbs" aria-label="Breadcrumb">' + '<i>/</i>'.join(out) + '</nav>'
def crumbs_ld(items):
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i+1, 'name': n, 'item': SITE + h} for i, (n, h) in enumerate(items)]}

import build_extra
EXTRA = build_extra.Ctx(globals())
# stories first: the village and township pages link to them
if os.path.isdir(p('stories')): shutil.rmtree(p('stories'))
n_story = build_extra.build_stories(EXTRA)
story_paths = getattr(EXTRA, 'story_paths', [])
STORY = getattr(EXTRA, 'village_stories', {})          # village id -> its story page

# ------------------------------------------------------------------ village pages
if os.path.isdir(p('village')): shutil.rmtree(p('village'))
for v in V:
    name, off, mm = ro(v), en(v), v.get('village_name_mmr') or ''
    town, dist, tract = v.get('township') or '', v.get('district') or '', v.get('village_tract') or ''
    unv = unverified(v)
    has_ro = bool(v.get('rohingya_name'))
    both = has_ro and off and off != name
    where = ', '.join(x for x in [tract + ' village tract' if tract else '', town + ' township' if town else '',
                                  dist + ' district' if dist else ''] if x)
    lede = '%s is a Rohingya village in %s, Arakan (Rakhine State, Myanmar).' % (name, where or 'Arakan')
    if both: lede += ' Its official romanised name is %s.' % off
    if mm: lede += ' In Burmese it is written %s.' % mm
    if not unv: lede += ' It lies at %s.' % coord(v)
    if not has_ro: lede += ' Its Rohingya name has not yet been recorded in the archive.'
    title = '%s%s — Rohingya village in %s, Arakan | FARA' % (name, ' (%s)' % off if both else '', town or 'Arakan')
    desc = ('%s%s is a Rohingya village in %s, Arakan (Rakhine State, Myanmar). Names in Rohingya, English and Burmese, location and satellite imagery.'
            % (name, ' (%s)' % off if both else '', (town + ' township') if town else 'Arakan'))[:300]

    near = []
    if not unv:
        near = sorted(((dist_km(v, x), x) for x in PLOT if x['id'] != v['id']), key=lambda t: t[0])[:8]
    rows_names = [('Rohingya name', esc(v['rohingya_name']) if has_ro else '<em>not yet recorded</em>'),
                  ('Official name (romanised)', esc(off) or '—'),
                  ('Burmese', '<span class="mmr">%s</span>' % esc(mm) if mm else '<em>not recorded</em>')]
    rows_loc = [('Township', '<a href="%s">%s</a>' % (turl(town), esc(town)) if town else '—'), ('District', esc(dist) or '—'),
                ('Village tract', esc(tract) or '—'),
                ('Coordinates (WGS84)', '<span class="mono">%.6f, %.6f</span>' % (float(v['lat']), float(v['lng'])) if not unv
                 else '<em>unverified — the coordinates in the source are invalid</em>'),
                ('Record', '<span class="mono">%s</span>' % rid(v))]
    tbl = lambda rows: '<dl class="facts">' + ''.join('<div><dt>%s</dt><dd>%s</dd></div>' % r for r in rows) + '</dl>'

    img = ''
    if not unv:
        la, ln, R = float(v['lat']), float(v['lng']), 6378137
        mx, my = math.radians(ln)*R, math.log(math.tan(math.pi/4 + math.radians(la)/2))*R
        hw = 450/math.cos(math.radians(la)); hh = hw*10/16
        src = ('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?bbox=%.1f,%.1f,%.1f,%.1f'
               '&bboxSR=3857&imageSR=3857&size=960,600&format=jpg&f=image' % (mx-hw, my-hh, mx+hw, my+hh))
        img = ('<figure class="sat"><a href="/#v=%d"><img loading="lazy" width="960" height="600" src="%s" alt="Satellite image of %s, %s township"></a>'
               '<figcaption>Satellite image, about 900 m across. Imagery: Esri World Imagery. Open the map for capture dates, earlier images and the latest pass.</figcaption></figure>'
               % (v['id'], esc(src), esc(name), esc(town)))

    qa = [('Where is %s?' % name, lede)]
    if both: qa.append(('What is the Rohingya name of %s?' % off, 'The Rohingya name of %s is %s. %s is the official romanised name used on government and UN maps.' % (off, name, off)))
    if mm: qa.append(('How is %s written in Burmese?' % name, '%s is written %s in Burmese script.' % (name, mm)))
    if v.get('pcode_village'): qa.append(('What is the official place code (P-code) of %s?' % name,
        'The MIMU place code of %s is %s%s. Its village tract code is %s and its township code is %s.' % (
            name, v['pcode_village'], ' (listed by MIMU as %s)' % v['mimu_village_name'] if v.get('mimu_village_name') else '', v['pcode_village_tract'], v['pcode_township'])))
    st_code, st_text = st17_sentence(v, name)
    if st_text: qa.append(('Was %s destroyed in 2017?' % name, st_text))
    fire_text = fire_sentence(v, name) if FIRES else None
    if fire_text: qa.append(('Were fires detected at %s in 2017?' % name, fire_text))
    if near: qa.append(('Which villages are near %s?' % name, 'The nearest villages in the archive are ' + ', '.join('%s (%s)' % (ro(x), fmt_dist(d)) for d, x in near[:5]) + '.'))
    qa.append(('What is FARA?', 'FARA, the Arakan Village Name Archive, preserves the names and locations of %s Rohingya villages across Arakan in Rohingya, English and Burmese, so that those names are never erased.' % '{:,}'.format(N)))

    body = crumbs([('FARA', '/'), (town + ' township' if town else 'Villages', turl(town) if town else '/villages/'), (name, None)])
    body += '<p class="rid"><span class="mono">%s</span><span class="tag" style="color:%s"><i></i>%s</span></p>' % (rid(v), TOWN_COLORS.get(town, '#8FA8C7'), esc(town or 'Arakan'))
    body += '<h1>%s</h1>' % esc(name)
    alt = ' · '.join(x for x in [esc(off) if both else '', '<span class="mmr">%s</span>' % esc(mm) if mm else ''] if x)
    if alt: body += '<p class="alt">%s</p>' % alt
    body += '<p class="lede">%s</p>' % esc(lede)
    body += '<p class="cta"><a class="btn primary" href="/#v=%d">Open on the interactive map</a>' % v['id']
    if v['id'] in STORY: body += '<a class="btn" href="%s">Its story in 2017</a>' % STORY[v['id']]
    if not unv: body += '<a class="btn" href="https://www.google.com/maps?q=%.6f,%.6f" rel="noopener">Google Maps</a>' % (float(v['lat']), float(v['lng']))
    body += '<a class="btn" href="/#v=%d&amp;suggest">Suggest a name or correction</a><a class="btn" href="#cite">Cite this</a></p>' % v['id']
    body += img
    body += '<h2>Names</h2>' + tbl(rows_names) + '<h2>Location</h2>' + tbl(rows_loc)
    pc_rows, pc_notes = pcode_rows(v)
    if pc_rows:
        body += '<h2>Official place codes</h2>' + tbl(pc_rows)
        body += ('<p class="note">%sPlace codes (P-codes) are the reference numbers the United Nations and aid agencies use for places in Myanmar. '
                 'They link this record to other datasets. Source: <a href="%s" rel="noopener">%s</a>, © Myanmar Information Management Unit. '
                 'The names beside the codes are MIMU\'s official spellings.</p>' % (''.join(n + ' ' for n in pc_notes), PCODE_URL, PCODE_SOURCE))
    if st_text:
        body += ('<h2>2017 · satellite analysis</h2><p class="lede st17"><b>%s.</b> %s</p>'
                 '<p class="note">Source: <a href="%s" rel="noopener">UNOSAT, “Destroyed areas in Buthidaung, Maungdaw, and Rathedaung Townships”</a> (CC BY-SA), '
                 'matched to this village by location. <a href="/#v=%d">Open the map</a> to compare satellite images from before and after.</p>'
                 % (ST17_LABEL[st_code], esc(st_text), ST17_URL, v['id']))
        if fire_text:
            body += ('<p class="lede st17"><b>Fire detections.</b> %s</p><p class="note">Source: <a href="%s" rel="noopener">NASA FIRMS</a>, VIIRS and MODIS active fire data. '
                     'Days are in Myanmar time. <a href="/fires.csv">All detections by village (CSV)</a>.</p>' % (esc(fire_text), FIRMS_URL))
        if v['id'] in STORY:
            body += ('<p class="note"><a href="%s"><b>Read the story of %s in 2017</b></a>: the last satellite picture from before that autumn, the first one after, '
                     'and what UNOSAT mapped, step by step.</p>' % (STORY[v['id']], esc(name)))
    if near:
        body += '<h2>Nearby villages</h2><ul class="near">' + ''.join(
            '<li><a href="%s"><b>%s</b><span>%s</span></a><em>%s</em></li>' % (vurl(x), esc(ro(x)), esc(en(x)) if en(x) != ro(x) else '', fmt_dist(d)) for d, x in near) + '</ul>'
    body += '<h2>Questions and answers</h2><div class="qa">' + ''.join('<h3>%s</h3><p>%s</p>' % (esc(q), esc(a)) for q, a in qa) + '</div>'
    body += ('<h2>Show this village on your own site</h2><p class="note">Paste this code into a web page to show a small card for %s that links back to this record. It is free to use.</p>'
             '<pre class="embedcode"><code>%s</code></pre>' % (esc(name), esc(build_extra.embed_code(EXTRA, v))))
    body += ('<h2>About this record</h2><p class="note">This record comes from the <a href="https://map.rohingyakhobor.com/map" rel="noopener">Rohingya Khobor — Arakan Maps Project</a>, collected on %s. '
             'Records with known problems are flagged, never silently altered: <a href="/methods/">how this archive was made</a>.</p>' % COLLECTED)
    body += build_edition.village_cite(ED, SITE, v, SITE + vurl(v))

    place = {'@context': 'https://schema.org', '@type': 'Place', '@id': SITE + vurl(v), 'name': name, 'url': SITE + vurl(v),
             'identifier': rid(v), 'description': lede,
             'alternateName': [x for x in [off if both else None, mm or None] if x],
             'containedInPlace': {'@type': 'AdministrativeArea', 'name': (town + ' Township') if town else 'Arakan',
                                  'containedInPlace': {'@type': 'AdministrativeArea', 'name': 'Rakhine State (Arakan)',
                                                       'containedInPlace': {'@type': 'Country', 'name': 'Myanmar'}}},
             'isPartOf': {'@type': 'Dataset', 'name': 'FARA — The Arakan Village Name Archive', 'url': SITE + '/'}}
    if not place['alternateName']: del place['alternateName']
    props = [(k, v.get(f)) for k, f in (('MIMU village place code (P-code)', 'pcode_village'), ('MIMU village tract place code (P-code)', 'pcode_village_tract'),
                                        ('MIMU township place code (P-code)', 'pcode_township'))]
    if any(val for _, val in props):
        place['additionalProperty'] = [{'@type': 'PropertyValue', 'name': k, 'value': val} for k, val in props if val]
    if not unv: place['geo'] = {'@type': 'GeoCoordinates', 'latitude': float(v['lat']), 'longitude': float(v['lng'])}
    faq = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in qa]}
    bc = crumbs_ld([('FARA', '/'), ((town + ' township') if town else 'Villages', turl(town) if town else '/villages/'), (name, vurl(v))])
    card = SITE + '/share/img/v/%d.png' % v['id'] if os.path.exists(p('share', 'img', 'v', '%d.png' % v['id'])) else None
    write(p('village', v['slug'], 'index.html'), page(vurl(v), title, desc, body, [place, bc, faq],
          og_title='%s%s — Rohingya village in %s, Arakan' % (name, ' (%s)' % off if both else '', town or 'Arakan'),
          og_image=card, og_alt='%s — Rohingya village in %s, Arakan: names, location and map' % (name, (town + ' township') if town else 'Arakan')))

# ------------------------------------------------------------------ township + all-villages indexes
def vlist(vs):
    vs = sorted(vs, key=lambda x: ro(x).lower())
    return '<ul class="vlist">' + ''.join('<li><a href="%s"><b>%s</b>%s</a></li>' % (
        vurl(x), esc(ro(x)), '<span>%s</span>' % esc(en(x)) if en(x) and en(x) != ro(x) else '') for x in vs) + '</ul>'

towns = [t for t in TOWN_COLORS if any(v.get('township') == t for v in V)]
if os.path.isdir(p('township')): shutil.rmtree(p('township'))
for t in towns:
    vs = [v for v in V if v.get('township') == t]
    tracts = len({v.get('village_tract') for v in vs if v.get('village_tract')})
    desc = 'All %d Rohingya villages of %s township, Arakan (Rakhine State, Myanmar) in the FARA archive, with their Rohingya, English and Burmese names and locations.' % (len(vs), t)
    body = crumbs([('FARA', '/'), (t + ' township', None)])
    body += '<h1>%s township</h1><p class="lede">FARA records %d Rohingya villages in %s township, across %d village tracts. Each has its name in Rohingya, its official romanised name, its Burmese name where known, and its location.</p>' % (esc(t), len(vs), esc(t), tracts)
    body += '<p class="cta"><a class="btn primary" href="/">Open the interactive map</a><a class="btn" href="/downloads/fara-gazetteer-%s.pdf">Printable gazetteer (PDF)</a><a class="btn" href="%sgazetteer/">Gazetteer (web)</a><a class="btn" href="/by_township/%s.csv">Download this township (CSV)</a></p>' % (slugify(t), turl(t), t)
    told = sorted((v for v in vs if v['id'] in STORY), key=lambda x: ro(x).lower())
    if told:
        body += ('<h2>Stories from %s</h2><p class="note">%d villages of %s township have a story of their own: what satellites recorded there in 2017, with dated pictures from before and after. '
                 '<a href="/stories/#%s">See them all on the stories page</a>, or start with <a href="/stories/what-the-satellites-recorded/">the whole account</a>.</p>'
                 % (esc(t), len(told), esc(t), slugify(t)))
        body += '<ul class="vlist">' + ''.join('<li><a href="%s"><b>%s</b>%s</a></li>' % (
            STORY[x['id']], esc(ro(x)), '<span>%s</span>' % esc(en(x)) if en(x) and en(x) != ro(x) else '') for x in told) + '</ul>'
    body += '<h2>Villages in %s</h2>' % esc(t) + vlist(vs)
    ld = {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': '%s township — Rohingya villages' % t, 'url': SITE + turl(t), 'description': desc}
    write(p('township', slugify(t), 'index.html'), page(turl(t), '%s township — %d Rohingya villages | FARA' % (t, len(vs)), desc, body,
          [ld, crumbs_ld([('FARA', '/'), (t + ' township', turl(t))])]))

desc = 'An A–Z list of all %s Rohingya villages in the FARA archive, across Maungdaw, Buthidaung, Rathedaung and Sittwe townships of Arakan (Rakhine State, Myanmar).' % '{:,}'.format(N)
body = crumbs([('FARA', '/'), ('All villages', None)])
body += '<h1>All villages</h1><p class="lede">%s</p><p class="cta"><a class="btn primary" href="/">Open the interactive map</a></p>' % esc(desc)
body += '<p class="jump">' + ''.join('<a href="#%s">%s (%d)</a>' % (slugify(t), esc(t), sum(1 for v in V if v.get('township') == t)) for t in towns) + '</p>'
for t in towns:
    body += '<h2 id="%s"><a href="%s">%s township</a></h2>' % (slugify(t), turl(t), esc(t)) + vlist([v for v in V if v.get('township') == t])
write(p('villages', 'index.html'), page('/villages/', 'All %s Rohingya villages of Arakan, A–Z | FARA' % '{:,}'.format(N), desc, body,
      [crumbs_ld([('FARA', '/'), ('All villages', '/villages/')])]))

# ------------------------------------------------------------------ embed cards, gazetteers, stories
n_embed = build_extra.build_embeds(EXTRA)
n_gaz = build_extra.build_gazetteers(EXTRA)

# ------------------------------------------------------------------ methods, change log, CITATION.cff
edition_paths = build_edition.build_pages(EXTRA, ED)

# ------------------------------------------------------------------ for journalists
_st = [ (ST17.get(str(v['id'])) or {}).get('status') for v in V ]
_cite = build_edition.cite(ED, SITE)['plain']
_doi = ED.get('doi') or ''
body = crumbs([('FARA', '/'), ('For journalists', None)])
body += '<h1>For journalists</h1><p class="lede">What FARA is, the numbers you can quote, how to credit it, and who to ask. Everything here may be used in reporting.</p>'
body += ('<h2>In one paragraph</h2><p class="note">FARA, the Arakan Village Name Archive, is a public record of the names and locations of %s Rohingya villages in Maungdaw, Buthidaung, Rathedaung and Sittwe townships of Arakan (Rakhine State, Myanmar). '
         'Each village is listed with its Rohingya name, its official name, its name in Burmese where known, its position and its official place code, beside what satellites recorded there in 2017. '
         '“Fará” is the Rohingya word for village. The archive is free, openly licensed and published in numbered editions so that a citation always leads to the same data.</p>' % '{:,}'.format(N))
facts = [('Villages on record', '{:,}'.format(N)), ('With a recorded Rohingya name', '{:,}'.format(sum(1 for v in V if v.get('rohingya_name')))),
         ('Marked destroyed by UNOSAT in 2017', str(_st.count('destroyed'))), ('With a destroyed zone within 500 m', str(_st.count('nearby'))),
         ('With a fire detected by NASA satellites within 1 km, autumn 2017', str((FIRES_META.get('villages_with_fire') or {}).get('2017', '—'))),
         ('Village stories', str(len(STORY))), ('Current edition', 'Edition %s, %s' % (ED['version'], long_day(ED['date'])))]
body += '<h2>Numbers you can quote</h2><dl class="facts">' + ''.join('<div><dt>%s</dt><dd>%s</dd></div>' % (esc(k), esc(x)) for k, x in facts) + '</dl>'
body += ('<p class="note">The 2017 figures are counts of villages in this archive, matched by position to UNOSAT’s satellite analysis of 31 August – 11 October 2017 and to NASA’s fire detections. '
         'They are not counts of all villages destroyed. “None detected” does not mean a village is standing. <a href="/methods/">How each number was made</a>.</p>')
body += ('<h2>How to credit</h2><p class="note">In text: <b>FARA, the Arakan Village Name Archive (map.rohingya.ro)</b>. For a figure from the 2017 analysis, add <b>UNOSAT</b>; for fire detections, <b>NASA FIRMS</b>; '
         'for a satellite picture, <b>Esri World Imagery</b> and the date shown on it.</p><p class="note">Full citation:<span class="cite">%s</span></p>' % esc(_cite))
body += ('<h2>What you may use</h2><p class="note">The data is under the Creative Commons Attribution 4.0 licence: copy it, publish it and adapt it, with credit. '
         'Screenshots of the map, pictures and videos made with the site’s Picture and Video buttons, the story pages and the printable gazetteers may be used in reporting with the credits they carry. '
         'Satellite pictures remain © Esri and its imagery providers; keep the credit line that is printed on them.</p>')
body += ('<h2>Useful links</h2><ul class="vlist"><li><a href="/stories/what-the-satellites-recorded/"><b>What the satellites recorded</b><span>the account of autumn 2017</span></a></li>'
         '<li><a href="/stories/"><b>Village stories</b><span>one for each village where destruction was mapped</span></a></li>'
         '<li><a href="/methods/"><b>Methods</b><span>sources, corrections, limits</span></a></li>'
         '<li><a href="/downloads/fara-dataset-v%s.zip"><b>The dataset</b><span>edition %s, ZIP</span></a></li>'
         '<li><a href="/logo.png"><b>Logo</b><span>PNG</span></a></li><li><a href="/logo.svg"><b>Logo</b><span>SVG</span></a></li></ul>' % (ED['version'], ED['version']))
body += ('<h2>Contact</h2><p class="note">AB Aziz, who keeps the archive: <a href="mailto:ab@rohingya.ro">ab@rohingya.ro</a>. Corrections are welcome and are recorded publicly in the <a href="/changelog/">change log</a>.</p>')
write(p('press', 'index.html'), page('/press/', 'For journalists: facts, credit line and contact | FARA',
      'What FARA, the Arakan Village Name Archive, is; figures you can quote on Rohingya villages and 2017; how to credit it; and who to contact.', body,
      [{'@context': 'https://schema.org', '@type': 'AboutPage', 'name': 'FARA for journalists', 'url': SITE + '/press/',
        'about': {'@type': 'Dataset', 'name': ED['title'], 'url': SITE + '/', 'identifier': ('https://doi.org/' + _doi) if _doi else SITE + '/'}},
       crumbs_ld([('FARA', '/'), ('For journalists', '/press/')])]))
edition_paths = list(edition_paths) + ['/press/']

# ------------------------------------------------------------------ sitemap, robots, llms.txt
today = date.today().isoformat()
urls = ([('/', '1.0'), ('/villages/', '0.8')] + [(ep, '0.7') for ep in edition_paths] + [(turl(t), '0.8') for t in towns] + [(turl(t) + 'gazetteer/', '0.7') for t in towns]
        + ([('/stories/', '0.8')] + [(sp, '0.8') for sp in story_paths] if story_paths else []) + [(vurl(v), '0.6') for v in V])
write(p('sitemap.xml'), '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(
    '  <url><loc>%s%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>\n' % (SITE, u, today, pr) for u, pr in urls) + '</urlset>\n')
write(p('robots.txt'), '''# FARA — The Arakan Village Name Archive
# Everything here is meant to be found, read and cited, by people, search engines and AI assistants.
User-agent: *
Allow: /

User-agent: GPTBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: Applebot-Extended
Allow: /
User-agent: CCBot
Allow: /

Sitemap: %s/sitemap.xml
''' % SITE)
write(p('llms.txt'), '''# FARA — The Arakan Village Name Archive

> FARA ("fará" means "village" in the Rohingya language) is a public archive of the names and locations of %(n)s Rohingya villages in Arakan (Rakhine State, Myanmar). Each record gives the village's Rohingya name, its official romanised name, its Burmese-script name where known, its village tract, township and district, and its coordinates. Every village had a name; FARA exists so those names are never erased.

Rohingya village names are being renamed, depopulated and removed from official maps. FARA keeps them on record for research, reporting, human-rights documentation and the Rohingya community. It is a project by AB Aziz (ab@rohingya.ro).

## Facts
- %(n)s villages in four townships: %(towns)s.
- Source data: Rohingya Khobor — Arakan Maps Project (https://map.rohingyakhobor.com/map), collected %(collected)s.
- %(with_ro)s villages have a recorded Rohingya name; %(with_mm)s have a Burmese-script name. Missing names are stated as missing, not guessed.
- Records with known data problems are flagged, never silently altered. One record has unverified coordinates.
- Coordinates are decimal degrees, WGS84.
- Each village also carries what UNOSAT's satellite analysis of 31 August – 11 October 2017 marked at or near it: destroyed, destruction nearby, none detected, or not assessed. "None detected" does not mean the village is standing; the imagery ends on 11 October 2017 and the analysis was not validated on the ground.
- %(with_pc)s villages carry their official MIMU place code (P-code), with village tract, township and district codes, from %(pc_source)s. Villages MIMU has dropped from its list are marked inactive; villages with no official code are stated as having none.

## How the site is organised
- [Interactive map](%(site)s/): search in Rohingya, English or Burmese; satellite imagery with capture dates, earlier captures and the latest Sentinel-2 pass for every village.
- [All villages, A–Z](%(site)s/villages/)
%(town_links)s
- One page per village at %(site)s/village/<id>-<name>/ with names, location, nearby villages and a short question-and-answer section.
- Printable gazetteers, one per township, with every village's names, coordinates and place code and a map of every village tract:
%(gaz_links)s
%(story_links)s- An embeddable card for every village at %(site)s/embed/<id>/ (for use in an iframe; it links back to the village page).
- On the map: township and village-tract boundaries, the whole map in the imagery of earlier years (2014 onwards), and a browse list (township, village tract, village) for finding a village without typing.

## Data
- [CSV](%(site)s/arakan_villages.csv)
- [JSON](%(site)s/arakan_villages.json)
- [GeoJSON](%(site)s/arakan_villages.geojson) (verified coordinates only)
- [2017 destruction per village, CSV](%(site)s/status_unosat_2017.csv) and [the destroyed zones, GeoJSON](%(site)s/unosat_2017_zones.geojson): derived from UNOSAT data, CC BY-SA 4.0, credit UNOSAT
- Fields: id, name (official romanised), rohingya_name, village_name_mmr (Burmese script), lat, lng, village_tract, township, district, coord_status, pcode_village, pcode_village_tract, pcode_township, pcode_district, mimu_village_name, mimu_village_tract_name, mimu_village_status, mimu_village_tract_status, pcode_match.
- [Fires detected by satellite near each village, CSV](%(site)s/fires.csv), [JSON](%(site)s/fires.json) and [every detection as points](%(site)s/fires_points.json): NASA FIRMS active fire detections (VIIRS 375 m and MODIS 1 km) within 1 km of a village's recorded position, 25 August – 30 November 2017 and 9 October – 30 November 2016, with days in Myanmar time. %(n_fire)s villages had a detection in autumn 2017 (%(n_fire_v)s by VIIRS alone); in the same weeks of 2013–2016 and 2018–2019 VIIRS never found more than %(fire_max)s. A detection does not say what burned, and fires under cloud are not detected.
- [Place-code matching, record by record](%(site)s/pcodes.csv): how each code was matched, and the few records still to be confirmed.
- [Satellite capture dates per village](%(site)s/captures.json): for each village, the dates of the images Esri's World Imagery Wayback archive holds (looked up by tools/build_captures.py).
- [Township and village-tract boundaries](%(site)s/boundaries.json): from UN OCHA's COD-AB dataset for Myanmar (source MIMU), CC BY-IGO; approximate, about 1:250,000.

## Editions, methods and citing
- This is edition %(ed_version)s of %(ed_date)s%(ed_doi)s. The archive is published in numbered editions so that a citation always leads to the same data.
- [How this archive was made](%(site)s/methods/): where every part of the data came from, how it was checked and corrected, and what it cannot tell you.
- [Change log](%(site)s/changelog/): what changed in each edition. [Corrections, record by record (CSV)](%(site)s/corrections.csv). [The edition as data](%(site)s/edition.json).
- Cite the archive as: %(cite_all)s
- Cite one village by naming its record and the edition, for example: %(cite_one)s
- Every village page has a "Cite this" section with the citation in plain text, APA, BibTeX and RIS.
''' % dict(ed_version=ED['version'], ed_date=ED['date_long'], ed_doi=', DOI https://doi.org/' + ED['doi'] if ED['doi'] else '',
           cite_all=build_edition.cite(ED, SITE)['plain'], cite_one=build_edition.cite(ED, SITE, V[0], SITE + vurl(V[0]))['plain'],
           n='{:,}'.format(N), collected=COLLECTED, site=SITE,
           towns=', '.join('%s (%d)' % (t, sum(1 for v in V if v.get('township') == t)) for t in towns),
           with_pc='{:,}'.format(sum(1 for v in V if v.get('pcode_village'))), pc_source=PCODE_SOURCE,
           n_fire=(FIRES_META.get('villages_with_fire') or {}).get('2017', 0),
           n_fire_v=((FIRES_META.get('same_weeks_other_years_viirs') or {}).get('2017') or {}).get('villages', 0),
           fire_max=max([o['villages'] for y, o in (FIRES_META.get('same_weeks_other_years_viirs') or {}).items() if y != '2017'] or [0]),
           with_ro=sum(1 for v in V if v.get('rohingya_name')), with_mm=sum(1 for v in V if v.get('village_name_mmr')),
           town_links='\n'.join('- [%s township](%s%s)' % (t, SITE, turl(t)) for t in towns),
           gaz_links='\n'.join('  - [%s township gazetteer](%s%sgazetteer/) · [PDF](%s/downloads/fara-gazetteer-%s.pdf)' % (t, SITE, turl(t), SITE, slugify(t)) for t in towns),
           story_links=('- [Stories](%s/stories/): guided accounts told with the map and the satellite record. One written account of autumn 2017 '
                        '(%s/stories/what-the-satellites-recorded/) and one story at %s/stories/<id>-<name>/ for each of the %d villages where UNOSAT mapped destruction at or beside the village, '
                        'with the dated satellite pictures from before and after.\n' % (SITE, SITE, SITE, len(STORY))) if story_paths else ''))

# ------------------------------------------------------------------ service worker (offline)
sw_src = p('sw.template.js')
if os.path.exists(sw_src):
    h = hashlib.sha256()
    for f in ('fara.html', 'wards.js', 'pages.css', 'fires_points.json', 'gazetteer.css', 'stories.css', 'stories.js', 'captures.json', 'boundaries.json', 'sw.template.js'):
        if os.path.exists(p(f)): h.update(open(p(f), 'rb').read())
    h.update(open(p('edition.json'), 'rb').read())          # a new edition is a new release too
    write(p('sw.js'), open(sw_src, encoding='utf-8').read().replace('__VERSION__', h.hexdigest()[:12]))

print('built: edition %s, fara.html, %d village pages, %d township pages, %d embed cards, %d gazetteers, %d stories, methods, change log, sitemap (%d urls), robots.txt, llms.txt%s'
      % (ED['version'], N, len(towns), n_embed, n_gaz, n_story, len(urls), ', sw.js' if os.path.exists(sw_src) else ''))
