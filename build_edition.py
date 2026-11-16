"""Editions, citing, the methods page and the change log (called from build.py).

  edition.json           the edition being published: version, date, DOI, authors, licence. Edit this to publish a new edition.
  CHANGELOG.md           what changed in each edition                       -> /changelog/
  content/methods.md     how the data was gathered and corrected            -> /methods/
  corrections.csv        every change made to a value taken from the source
  CITATION.cff           written here, so GitHub and reference managers can read how to cite the archive

{{tokens}} in the two texts are filled with numbers counted from the data at build time, so the pages cannot drift from the archive.
The citation wording here has a twin in fara_template.html (citeFormats); change both together.
"""
import csv, hashlib, html, json, os, re

MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
REPO = 'https://github.com/abahziz0/fara'


def esc(s): return html.escape(str(s if s is not None else ''), quote=True)
def clean(s): return ' '.join(str(s or '').split())
def long_day(iso):
    y, m, d = iso.split('-')
    return '%d %s %s' % (int(d), MONTHS[int(m) - 1], y)


# ------------------------------------------------------------------ the edition
def load(root):
    ed = json.load(open(os.path.join(root, 'edition.json'), encoding='utf-8'))
    if not re.fullmatch(r'\d+\.\d+(\.\d+)?', ed['version']): raise SystemExit('edition.json: version must look like 1.0')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', ed['date']): raise SystemExit('edition.json: date must be YYYY-MM-DD')
    for k in ('doi', 'concept_doi'):
        ed[k] = re.sub(r'^https?://(dx\.)?doi\.org/', '', clean(ed.get(k)))
    ed['date_long'] = long_day(ed['date'])
    ed['year'] = ed['date'][:4]
    ed['label'] = 'Edition %s · %s' % (ed['version'], ed['date_long'])
    log = open(os.path.join(root, 'CHANGELOG.md'), encoding='utf-8').read()
    newest = re.search(r'^## +(\S+)', log, re.M)
    if not newest or newest.group(1) != ed['version']:
        raise SystemExit('CHANGELOG.md: the newest entry must be for edition %s (write what changed before publishing it)' % ed['version'])
    js = open(os.path.join(root, 'cite.js'), 'rb').read()
    ed['script'] = '<script src="/cite.js?v=%s" defer></script>' % hashlib.sha256(js).hexdigest()[:8]     # a changed script is never served from an old copy
    return ed


def for_app(ed):
    """The little the interactive archive needs to write a citation (see citeFormats in fara_template.html)."""
    return {'v': ed['version'], 'd': ed['date'], 'doi': ed['doi'], 'pub': ed['publisher'] if ed['doi'] else '', 'title': ed['title'],
            'authors': [{'family': a['family'], 'given': a['given']} for a in ed['authors']]}


# ------------------------------------------------------------------ citations
def _names(ed, style):
    out = []
    for a in ed['authors']:
        if style == 'apa': out.append('%s, %s' % (a['family'], ' '.join(w[0] + '.' for w in a['given'].split())))
        else: out.append('%s, %s' % (a['family'], a['given']))
    if len(out) < 2: return out[0]
    return ', '.join(out[:-1]) + (', & ' if style == 'apa' else ', and ') + out[-1]


def record_title(v):
    """'Hadira Para (Kar Di), Buthidaung township': the Rohingya name first, the official name beside it."""
    name, off = clean(v.get('rohingya_name')), clean(v.get('name'))
    t = name or off or 'Unnamed village'
    if name and off and off != name: t += ' (%s)' % off
    if v.get('township'): t += ', %s township' % clean(v['township'])
    return t


def cite(ed, site, v=None, url=None):
    """The citation of the whole archive, or of one village record, in four forms."""
    doi = ed['doi']
    doi_url = 'https://doi.org/' + doi if doi else ''
    pub = ed['publisher'] if doi else ''
    title, ver, year = ed['title'], ed['version'], ed['year']
    bib = lambda s: re.sub(r'([&%#_{}])', r'\\\1', s)
    if v is None:
        where = pub + '. ' + doi_url if doi else site + '/'
        plain = '%s. %s. Edition %s, %s. %s.' % (_names(ed, 'plain'), title, ver, ed['date_long'], where)
        apa = '%s (%s). %s (Version %s) [Data set]. %s' % (_names(ed, 'apa'), year, title, ver, where)
        key, btitle, burl = 'fara_v' + ver.replace('.', '_'), title, doi_url or site + '/'
        fields = [('author', ' and '.join('%s, %s' % (a['family'], a['given']) for a in ed['authors'])), ('title', btitle)]
        ris = [('TY', 'DATA')] + [('AU', '%s, %s' % (a['family'], a['given'])) for a in ed['authors']] + [('TI', title)]
    else:
        rid, rt = 'FARA-%04d' % v['id'], record_title(v)
        plain = '%s. “%s.” Record %s in %s, edition %s (%s). %s.' % (_names(ed, 'plain'), rt, rid, title, ver, ed['date_long'], url)
        if doi: plain += ' Edition DOI: %s.' % doi_url
        apa = '%s (%s). %s (Record %s). In %s (Version %s) [Data set]. %s%s' % (
            _names(ed, 'apa'), year, rt, rid, title, ver, pub + '. ' + doi_url + '. ' if doi else '', url)
        key, btitle, burl = 'fara_%04d' % v['id'], '%s. Record %s' % (rt, rid), url
        fields = [('author', ' and '.join('%s, %s' % (a['family'], a['given']) for a in ed['authors'])), ('title', btitle), ('howpublished', title)]
        ris = [('TY', 'DATA')] + [('AU', '%s, %s' % (a['family'], a['given'])) for a in ed['authors']] + [('TI', btitle), ('T2', title)]
    fields += [('version', ver), ('year', year), ('month', str(int(ed['date'][5:7])))]
    if doi: fields += [('publisher', pub), ('doi', doi)]
    fields += [('url', burl)]
    bibtex = '@misc{%s,\n%s\n}' % (key, ',\n'.join('  %-12s = {%s}' % (k, bib(val)) for k, val in fields))
    ris += [('ET', ver), ('PY', year), ('DA', ed['date'].replace('-', '/'))]
    if doi: ris += [('PB', pub), ('DO', doi)]
    ris += [('UR', burl), ('ER', '')]
    return {'plain': plain, 'apa': apa, 'bibtex': bibtex, 'ris': '\n'.join('%s  - %s' % kv for kv in ris)}


CITE_LABELS = [('plain', 'Citation'), ('apa', 'APA'), ('bibtex', 'BibTeX'), ('ris', 'RIS')]


def edition_line(ed):
    """'Edition 1.0 · 16 November 2026 · DOI 10.5281/zenodo.1' as HTML."""
    s = esc(ed['label'])
    if ed['doi']: s += ' · DOI <a href="https://doi.org/%s" rel="noopener">%s</a>' % (esc(ed['doi']), esc(ed['doi']))
    return s


def cite_box(ed, site, v=None, url=None):
    """The citation in four forms, readable without scripts; cite.js adds the copy buttons."""
    c = cite(ed, site, v, url)
    block = lambda k, label: '<div class="citefmt%s"><h3>%s</h3><pre>%s</pre></div>' % (' code' if k in ('bibtex', 'ris') else '', label, esc(c[k]))
    return ('<div class="citebox">%s<details><summary>APA, BibTeX and RIS</summary>%s</details>'
            '<p class="citeed">%s · <a href="/methods/">How this archive was made</a> · <a href="/changelog/">Change log</a></p></div>'
            % (block(*CITE_LABELS[0]), ''.join(block(k, label) for k, label in CITE_LABELS[1:]), edition_line(ed)))


def village_cite(ed, site, v, url):
    return ('<h2 id="cite">Cite this record</h2><p class="note">Cite the edition you used, so that your reference still leads to the same data after the archive is corrected.</p>'
            + cite_box(ed, site, v, url) + ed['script'])


# ------------------------------------------------------------------ a small Markdown reader
def _inline(s):
    s = esc(s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'(?<![*\w])\*([^*]+)\*(?![*\w])', r'<i>\1</i>', s)
    def link(m):
        href = m.group(2)
        return '<a href="%s"%s>%s</a>' % (href, ' rel="noopener"' if href.startswith('http') else '', m.group(1))
    return re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', link, s)


def slug(s): return re.sub(r'[^a-z0-9]+', '-', re.sub(r'<[^>]+>', '', s).lower()).strip('-')


def markdown(text, raw=None):
    """Headings, paragraphs, lists, tables, bold, italic, code and links: what the methods page and the change log use.
    raw: {marker: html} for whole lines that stand for a ready-made block."""
    out, lines, i = [], text.replace('\r', '').split('\n'), 0
    raw = raw or {}
    while i < len(lines):
        ln = lines[i]
        if not ln.strip(): i += 1; continue
        if ln.strip() in raw:
            out.append(raw[ln.strip()]); i += 1; continue
        m = re.match(r'(#{1,3}) +(.*)', ln)
        if m:
            n, t = len(m.group(1)), _inline(m.group(2).strip())
            out.append('<h%d%s>%s</h%d>' % (n, '' if n == 1 else ' id="%s"' % slug(t), t, n)); i += 1; continue
        if ln.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
            body = [r for r in rows[1:] if not all(re.fullmatch(r':?-+:?', c) for c in r)]
            out.append('<div class="tbl"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (
                ''.join('<th>%s</th>' % _inline(c) for c in rows[0]),
                ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % _inline(c) for c in r) for r in body)))
            continue
        if ln.startswith('- '):
            items = []
            while i < len(lines) and lines[i].startswith('- '):
                items.append(lines[i][2:]); i += 1
            out.append('<ul class="mdl">%s</ul>' % ''.join('<li>%s</li>' % _inline(x) for x in items)); continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r'(#{1,3} |\||- )', lines[i]) and lines[i].strip() not in raw:
            para.append(lines[i].strip()); i += 1
        out.append('<p>%s</p>' % _inline(' '.join(para)))
    return '\n'.join(out)


def fill(text, tokens):
    def sub(m):
        if m.group(1) not in tokens: raise SystemExit('unknown {{%s}} in a text of build_edition.py' % m.group(1))
        return str(tokens[m.group(1)])
    return re.sub(r'\{\{(\w+)\}\}', sub, text)


# ------------------------------------------------------------------ numbers, counted from the data
def tokens(c, ed):
    V, n = c.V, '{:,}'.format
    ids = lambda vs: ', '.join('FARA-%04d' % v['id'] for v in vs)
    st = [c.ST17.get(str(v['id']), {}).get('status') for v in V]
    pc = json.load(open(c.p('pcodes.json'), encoding='utf-8'))
    corr = list(csv.DictReader(open(c.p('corrections.csv'), encoding='utf-8')))
    zones = json.load(open(c.p('unosat_2017_zones.geojson'), encoding='utf-8'))['features']
    unconf = [v for v in V if v.get('pcode_match') == 'unconfirmed']
    none = [v for v in V if v.get('pcode_match') == 'none']
    fm = json.load(open(c.p('fires.json'), encoding='utf-8'))['meta']
    other = fm['same_weeks_other_years_viirs']
    span = lambda w: '%s to %s' % (long_day(w[0])[:-5], long_day(w[1]))          # '25 August to 30 November 2017'
    release = pc['meta']['source']['release']                      # 'MIMU Place Codes (P-codes) Release 9.7, January 2026 (Rakhine workbook)'
    return {
        'n': n(len(V)), 'version': ed['version'], 'date': ed['date_long'], 'collected': c.COLLECTED,
        'town_counts': ', '.join('%s %d' % (t, sum(1 for v in V if v.get('township') == t)) for t in c.towns),
        'n_ro': n(sum(1 for v in V if v.get('rohingya_name'))), 'n_no_ro': n(sum(1 for v in V if not v.get('rohingya_name'))),
        'n_mm': n(sum(1 for v in V if v.get('village_name_mmr'))), 'n_no_mm': n(sum(1 for v in V if not v.get('village_name_mmr'))),
        'n_identical': n(sum(1 for r in pc['records'] if r.get('distance_m') is not None and r['distance_m'] <= 0.1)),
        'n_corr': len(corr), 'n_corr_records': len({r['id'] for r in corr}),
        'n_slur': sum(1 for r in corr if 'Ku Lar' in r['change']),
        'pc_release': release, 'pc_release_short': c.PCODE_SOURCE,
        'pc_exact': n(sum(1 for v in V if v.get('pcode_match') == 'exact')), 'pc_strong': n(sum(1 for v in V if v.get('pcode_match') == 'strong')),
        'pc_unconfirmed': len(unconf), 'pc_unconfirmed_ids': ids(unconf), 'pc_none': len(none), 'pc_none_ids': ids(none),
        'pc_inactive': sum(1 for v in V if (v.get('mimu_village_status') or '').startswith('inactive')),
        'n_pcode': n(sum(1 for v in V if v.get('pcode_village'))),
        'st_url': c.ST17_URL, 'n_zones': n(len(zones)),
        'fire_url': 'https://firms.modaps.eosdis.nasa.gov/', 'fire_window_2017': span(fm['windows']['2017']), 'fire_window_2016': span(fm['windows']['2016']),
        'fire_2017': fm['villages_with_fire']['2017'], 'fire_2016': fm['villages_with_fire']['2016'], 'fire_2017_viirs': other['2017']['villages'],
        'fire_other_max': max(o['villages'] for y, o in other.items() if y != '2017'),
        'fire_points': n(len(json.load(open(c.p('fires_points.json'), encoding='utf-8'))['p'])),
        'st_destroyed': st.count('destroyed'), 'st_nearby': st.count('nearby'), 'st_none': st.count('none_detected'), 'st_na': st.count('not_assessed'),
    }


def licence_paragraph(ed):
    lic = ed.get('licence')
    if not lic:
        return ('The licence for FARA\'s own part of the data (the compilation, the corrections and the matching) will be stated here with the first edition deposited at Zenodo. '
                'Until then, please credit FARA and its sources when you use the data.')
    return ('FARA\'s own part of the data (the compilation, the corrections and the matching) is published under the [%s](%s) licence (%s). %s'
            % (lic['name'], lic['url'], lic['short'], lic.get('means', '')))


def doi_sentence(ed):
    if not ed['doi']: return '. Each edition is kept permanently at Zenodo, where it receives a DOI, a permanent address that never changes.'
    s = ', kept permanently at Zenodo under its own DOI: [%s](https://doi.org/%s).' % (ed['doi'], ed['doi'])
    if ed['concept_doi']: s += ' The DOI [%s](https://doi.org/%s) always leads to the newest edition.' % (ed['concept_doi'], ed['concept_doi'])
    return s


# ------------------------------------------------------------------ the pages
def build_pages(c, ed):
    """/methods/, /changelog/ and CITATION.cff. Returns the paths for the sitemap."""
    tk = tokens(c, ed)
    tk.update(licence_paragraph=licence_paragraph(ed), doi_sentence=doi_sentence(ed), cite_dataset='@@CITE@@')
    box = cite_box(ed, c.SITE)
    zip_path = '/downloads/fara-dataset-v%s.zip' % ed['version']           # written by tools/build_dataset.py
    nav = ('<p class="cta"><a class="btn primary" href="/">Open the interactive map</a><a class="btn" href="%s">%s</a><a class="btn" href="/corrections.csv">Corrections (CSV)</a>'
           + ('<a class="btn" href="%s">Download edition %s (ZIP)</a>' % (zip_path, esc(ed['version'])) if os.path.exists(c.p(*zip_path.split('/')[1:])) else '') + '</p>')

    # ---- methods
    text = fill(open(c.p('content', 'methods.md'), encoding='utf-8').read(), tk)
    body = markdown(text, {'@@CITE@@': box})
    h1 = re.search(r'<h1>(.*?)</h1>', body).group(1)
    body = body.replace('<h1>%s</h1>' % h1, '<h1>%s</h1><p class="rid"><span class="mono">%s</span></p>' % (h1, edition_line(ed)), 1)
    toc = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body)
    body = body.replace('<h2 ', '<p class="jump">%s</p>\n<h2 ' % ''.join('<a href="#%s">%s</a>' % t for t in toc), 1)
    desc = ('Where the data of FARA, the Arakan Village Name Archive, came from, how the names, positions, place codes and 2017 satellite results '
            'were checked and corrected, what the archive cannot tell you, and how to cite it.')
    ld = {'@context': 'https://schema.org', '@type': 'TechArticle', 'headline': 'How this archive was made', 'description': desc,
          'url': c.SITE + '/methods/', 'dateModified': ed['date'], 'version': ed['version'],
          'author': [_person(a) for a in ed['authors']], 'about': {'@type': 'Dataset', 'name': ed['title'], 'url': c.SITE + '/'}}
    c.write(c.p('methods', 'index.html'), c.page('/methods/', 'How this archive was made: sources, methods and corrections | FARA', desc,
            '<article class="doc">' + c.crumbs([('FARA', '/'), ('Methods', None)]) + body + nav % ('/changelog/', 'Change log') + '</article>' + ed['script'],
            [ld, c.crumbs_ld([('FARA', '/'), ('Methods', '/methods/')])]))

    # ---- change log
    log = open(c.p('CHANGELOG.md'), encoding='utf-8').read()
    body = markdown(log)
    body = body.replace('</h1>', '</h1><p class="rid"><span class="mono">Current: %s</span></p>' % edition_line(ed), 1)
    desc = 'Every change to the data of FARA, the Arakan Village Name Archive, edition by edition: names corrected, fields and records added, and why.'
    c.write(c.p('changelog', 'index.html'), c.page('/changelog/', 'Change log: what changed in each edition | FARA', desc,
            '<article class="doc log">' + c.crumbs([('FARA', '/'), ('Change log', None)]) + body + nav % ('/methods/', 'How this archive was made') + '</article>',
            [c.crumbs_ld([('FARA', '/'), ('Change log', '/changelog/')])]))

    # ---- CITATION.cff
    q = lambda s: '"%s"' % str(s).replace('\\', '\\\\').replace('"', '\\"')
    cff = ['cff-version: 1.2.0', 'message: "If you use this archive, please cite the edition you used."', 'type: dataset',
           'title: ' + q(ed['title']), 'version: ' + q(ed['version']), 'date-released: ' + q(ed['date']), 'authors:']
    for a in ed['authors']:
        cff += ['  - family-names: ' + q(a['family']), '    given-names: ' + q(a['given'])]
        if a.get('orcid'): cff.append('    orcid: ' + q('https://orcid.org/' + a['orcid']))
    if ed['doi']: cff.append('doi: ' + q(ed['doi']))
    cff += ['url: ' + q(c.SITE + '/'), 'repository-code: ' + q(REPO)]
    if ed.get('licence'): cff.append('license: ' + q(ed['licence']['id']))
    cff += ['abstract: ' + q('Names and locations of %s Rohingya villages in Maungdaw, Buthidaung, Rathedaung and Sittwe townships of Arakan (Rakhine State, Myanmar), '
                             'in Rohingya, English and Burmese, with official place codes and the results of the 2017 UNOSAT satellite analysis.' % tk['n']),
            'keywords:'] + ['  - ' + q(k) for k in KEYWORDS]
    c.write(c.p('CITATION.cff'), '\n'.join(cff) + '\n')
    return ['/methods/', '/changelog/']


KEYWORDS = ['Rohingya', 'Arakan', 'Rakhine State', 'Myanmar', 'village names', 'place names', 'toponymy', 'gazetteer',
            'Maungdaw', 'Buthidaung', 'Rathedaung', 'Sittwe']


def _person(a):
    d = {'@type': 'Person', 'name': '%s %s' % (a['given'], a['family']), 'givenName': a['given'], 'familyName': a['family']}
    if a.get('also_known_as'): d['alternateName'] = a['also_known_as']
    if a.get('orcid'): d['sameAs'] = 'https://orcid.org/' + a['orcid']
    return d


# ------------------------------------------------------------------ the interactive archive
def stamp_app(ed, app, site):
    """Give fara.html its edition: the data for citeFormats, the line in the About box, and the dataset's version, DOI and licence for search engines."""
    for token in ('__EDITION__', '__EDITION_LINE__'):
        if token not in app: raise SystemExit('fara_template.html: %s is missing' % token)
    app = app.replace('__EDITION__', json.dumps(for_app(ed), ensure_ascii=False, separators=(',', ':')))
    app = app.replace('__EDITION_LINE__', edition_line(ed))
    def dataset(m):
        d = json.loads(m.group(1))
        if d.get('@type') != 'Dataset': return m.group(0)
        d.update(version=ed['version'], dateModified=ed['date'], creator=[_person(a) for a in ed['authors']],
                 citation=cite(ed, site)['plain'])
        if ed['doi']: d['identifier'] = 'https://doi.org/' + ed['doi']; d['sameAs'] = 'https://doi.org/' + ed['doi']
        if ed.get('licence'): d['license'] = ed['licence']['url']
        d['subjectOf'] = [{'@type': 'TechArticle', 'name': 'How this archive was made', 'url': site + '/methods/'},
                          {'@type': 'WebPage', 'name': 'Change log', 'url': site + '/changelog/'}]
        return '<script type="application/ld+json">%s</script>' % json.dumps(d, ensure_ascii=False, separators=(',', ':'))
    return re.sub(r'<script type="application/ld\+json">(\{.*?\})</script>', dataset, app)
