#!/usr/bin/env python3
"""Build FARA's static site from the dataset.

    python3 build.py

Writes:
  fara.html                     the interactive archive (template + embedded data)
  village/<id>-<slug>/index.html   one page per village (for search engines, link previews, citing)
  township/<slug>/index.html    one index page per township
  villages/index.html           A-Z index of every village
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
    return d
data = json.dumps([embed(r) for r in V], ensure_ascii=False, separators=(',', ':'))
app = open(p('fara_template.html'), encoding='utf-8').read().replace('__VILLAGE_DATA__', data)
write(p('fara.html'), app)

# ------------------------------------------------------------------ shared page chrome
LOGO = ('<svg viewBox="0 0 64 64" fill="none" aria-hidden="true"><rect x="4" y="4" width="56" height="56" stroke="#00E5FF" stroke-opacity=".35" stroke-width="2"/>'
        '<rect x="4" y="4" width="16" height="4" fill="#00E5FF"/><rect x="4" y="4" width="4" height="16" fill="#00E5FF"/>'
        '<rect x="44" y="56" width="16" height="4" fill="#00E5FF"/><rect x="56" y="44" width="4" height="16" fill="#00E5FF"/>'
        '<circle cx="32" cy="32" r="13" stroke="#00E5FF" stroke-width="2.4" stroke-dasharray="18 8"/><circle cx="32" cy="32" r="4.5" fill="#00E5FF"/></svg>')

_m = re.search(r'<div id="brand">\s*(<svg class="logo".*?</svg>)', app, re.S)
if _m: LOGO = _m.group(1).replace(' class="logo"', '')

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
<meta property="og:type" content="article">
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
<link rel="stylesheet" href="/pages.css">
%(ld)s</head>
<body>
<header class="top">
  <a class="brand" href="/" aria-label="FARA home">%(logo)s<span><b>FARA</b><i>Arakan Village Name Archive</i></span></a>
  <nav><a href="/">Map</a><a href="/villages/">All villages</a></nav>
</header>
<main>
%(body)s
</main>
<footer class="foot">
  <p><b>FARA — The Arakan Village Name Archive.</b> Every village had a name. FARA exists so those names are never erased.</p>
  <p>%(n)s villages across Maungdaw, Buthidaung, Rathedaung and Sittwe townships. Source data: <a href="https://map.rohingyakhobor.com/map" rel="noopener">Rohingya Khobor — Arakan Maps Project</a>, collected %(collected)s.
  Download the data: <a href="/arakan_villages.csv">CSV</a> · <a href="/arakan_villages.json">JSON</a> · <a href="/arakan_villages.geojson">GeoJSON</a>.</p>
  <p>A project by AB Aziz · <a href="mailto:ab@rohingya.ro">ab@rohingya.ro</a></p>
</footer>
%(analytics)s
<script>if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(function(){});</script>
</body>
</html>
''' % dict(title=esc(title), desc=esc(desc), url=url, ogt=esc(og_title or title), site=SITE, ld=ld, logo=LOGO, body=body,
           ogi=og_image or (SITE + '/og.png'), oga=esc(og_alt or 'FARA — The Arakan Village Name Archive'),
           n='{:,}'.format(N), collected=COLLECTED, analytics=ANALYTICS)

def crumbs(items):
    out = []
    for i, (name, href) in enumerate(items):
        out.append('<a href="%s">%s</a>' % (href, esc(name)) if href and i < len(items)-1 else '<span>%s</span>' % esc(name))
    return '<nav class="crumbs" aria-label="Breadcrumb">' + '<i>/</i>'.join(out) + '</nav>'
def crumbs_ld(items):
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i+1, 'name': n, 'item': SITE + h} for i, (n, h) in enumerate(items)]}

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
    if near: qa.append(('Which villages are near %s?' % name, 'The nearest villages in the archive are ' + ', '.join('%s (%s)' % (ro(x), fmt_dist(d)) for d, x in near[:5]) + '.'))
    qa.append(('What is FARA?', 'FARA, the Arakan Village Name Archive, preserves the names and locations of %s Rohingya villages across Arakan in Rohingya, English and Burmese, so that those names are never erased.' % '{:,}'.format(N)))

    body = crumbs([('FARA', '/'), (town + ' township' if town else 'Villages', turl(town) if town else '/villages/'), (name, None)])
    body += '<p class="rid"><span class="mono">%s</span><span class="tag" style="color:%s"><i></i>%s</span></p>' % (rid(v), TOWN_COLORS.get(town, '#8FA8C7'), esc(town or 'Arakan'))
    body += '<h1>%s</h1>' % esc(name)
    alt = ' · '.join(x for x in [esc(off) if both else '', '<span class="mmr">%s</span>' % esc(mm) if mm else ''] if x)
    if alt: body += '<p class="alt">%s</p>' % alt
    body += '<p class="lede">%s</p>' % esc(lede)
    body += '<p class="cta"><a class="btn primary" href="/#v=%d">Open on the interactive map</a>' % v['id']
    if not unv: body += '<a class="btn" href="https://www.google.com/maps?q=%.6f,%.6f" rel="noopener">Google Maps</a>' % (float(v['lat']), float(v['lng']))
    body += '<a class="btn" href="/#v=%d&amp;suggest">Suggest a name or correction</a></p>' % v['id']
    body += img
    body += '<h2>Names</h2>' + tbl(rows_names) + '<h2>Location</h2>' + tbl(rows_loc)
    pc_rows, pc_notes = pcode_rows(v)
    if pc_rows:
        body += '<h2>Official place codes</h2>' + tbl(pc_rows)
        body += ('<p class="note">%sPlace codes (P-codes) are the reference numbers the United Nations and aid agencies use for places in Myanmar. '
                 'They link this record to other datasets. Source: <a href="%s" rel="noopener">%s</a>, © Myanmar Information Management Unit. '
                 'The names beside the codes are MIMU\'s official spellings.</p>' % (''.join(n + ' ' for n in pc_notes), PCODE_URL, PCODE_SOURCE))
    if near:
        body += '<h2>Nearby villages</h2><ul class="near">' + ''.join(
            '<li><a href="%s"><b>%s</b><span>%s</span></a><em>%s</em></li>' % (vurl(x), esc(ro(x)), esc(en(x)) if en(x) != ro(x) else '', fmt_dist(d)) for d, x in near) + '</ul>'
    body += '<h2>Questions and answers</h2><div class="qa">' + ''.join('<h3>%s</h3><p>%s</p>' % (esc(q), esc(a)) for q, a in qa) + '</div>'
    body += ('<h2>About this record</h2><p class="note">This record comes from the <a href="https://map.rohingyakhobor.com/map" rel="noopener">Rohingya Khobor — Arakan Maps Project</a>, collected on %s. '
             'Records with known problems are flagged, never silently altered. To cite it: <span class="cite">FARA — The Arakan Village Name Archive, record %s, “%s”, %s%s.</span></p>'
             % (COLLECTED, rid(v), esc(name), SITE, vurl(v)))

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
    body += '<p class="cta"><a class="btn primary" href="/">Open the interactive map</a><a class="btn" href="/by_township/%s.csv">Download this township (CSV)</a></p>' % t
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

# ------------------------------------------------------------------ sitemap, robots, llms.txt
today = date.today().isoformat()
urls = [('/', '1.0'), ('/villages/', '0.8')] + [(turl(t), '0.8') for t in towns] + [(vurl(v), '0.6') for v in V]
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
- %(with_pc)s villages carry their official MIMU place code (P-code), with village tract, township and district codes, from %(pc_source)s. Villages MIMU has dropped from its list are marked inactive; villages with no official code are stated as having none.

## How the site is organised
- [Interactive map](%(site)s/): search in Rohingya, English or Burmese; satellite imagery with capture dates, earlier captures and the latest Sentinel-2 pass for every village.
- [All villages, A–Z](%(site)s/villages/)
%(town_links)s
- One page per village at %(site)s/village/<id>-<name>/ with names, location, nearby villages and a short question-and-answer section.

## Data
- [CSV](%(site)s/arakan_villages.csv)
- [JSON](%(site)s/arakan_villages.json)
- [GeoJSON](%(site)s/arakan_villages.geojson) (verified coordinates only)
- Fields: id, name (official romanised), rohingya_name, village_name_mmr (Burmese script), lat, lng, village_tract, township, district, coord_status, pcode_village, pcode_village_tract, pcode_township, pcode_district, mimu_village_name, mimu_village_tract_name, mimu_village_status, mimu_village_tract_status, pcode_match.
- [Place-code matching, record by record](%(site)s/pcodes.csv): how each code was matched, and the few records still to be confirmed.

## Citing
Cite a record as: FARA — The Arakan Village Name Archive, record FARA-<id>, "<village name>", followed by the page URL.
''' % dict(n='{:,}'.format(N), collected=COLLECTED, site=SITE,
           towns=', '.join('%s (%d)' % (t, sum(1 for v in V if v.get('township') == t)) for t in towns),
           with_pc='{:,}'.format(sum(1 for v in V if v.get('pcode_village'))), pc_source=PCODE_SOURCE,
           with_ro=sum(1 for v in V if v.get('rohingya_name')), with_mm=sum(1 for v in V if v.get('village_name_mmr')),
           town_links='\n'.join('- [%s township](%s%s)' % (t, SITE, turl(t)) for t in towns)))

# ------------------------------------------------------------------ service worker (offline)
sw_src = p('sw.template.js')
if os.path.exists(sw_src):
    h = hashlib.sha256()
    for f in ('fara.html', 'wards.js', 'pages.css', 'sw.template.js'):
        if os.path.exists(p(f)): h.update(open(p(f), 'rb').read())
    write(p('sw.js'), open(sw_src, encoding='utf-8').read().replace('__VERSION__', h.hexdigest()[:12]))

print('built: fara.html, %d village pages, %d township pages, sitemap (%d urls), robots.txt, llms.txt%s'
      % (N, len(towns), len(urls), ', sw.js' if os.path.exists(sw_src) else ''))
