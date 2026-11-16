#!/usr/bin/env python3
"""Pack the edition named in edition.json for deposit at Zenodo.

    python3 build.py && python3 tools/build_dataset.py

Writes:
  downloads/fara-dataset-v<version>.zip    the whole edition in one file (also offered on the site)
  dist/fara-v<version>/                    the same files loose, to drag into a Zenodo upload (not kept in git)
  dist/fara-v<version>/zenodo.json         what to type into Zenodo's form: title, description, authors, keywords, licences

The package holds the data files listed in edition.json, plus README.md, METHODS.md, CHANGELOG.md, CITATION.cff,
LICENSE.md and SHA256SUMS.txt. Its texts are filled from the same data as the site, so they cannot disagree with it.
The zip is byte-for-byte the same on every run for the same edition (fixed dates inside it), so git only sees real changes.
"""
import hashlib, json, os, re, shutil, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import build_edition as be          # noqa: E402
import build_extra                  # noqa: E402


def p(*a): return os.path.join(ROOT, *a)


def context():
    """The few things build_edition.tokens needs, without running the whole site build."""
    class C: pass
    c = C()
    c.p = p
    c.V = json.load(open(p('arakan_villages.json'), encoding='utf-8'))
    c.ST17 = json.load(open(p('status_unosat_2017.json'), encoding='utf-8'))['villages']
    src = open(p('build.py'), encoding='utf-8').read()
    const = lambda name: re.search(r"^%s = '([^']*)'" % name, src, re.M).group(1)
    c.SITE, c.COLLECTED, c.PCODE_SOURCE, c.ST17_URL = const('SITE'), const('COLLECTED'), const('PCODE_SOURCE'), const('ST17_URL')
    c.towns = [t for t in build_extra.PRINT_COLORS if any(v.get('township') == t for v in c.V)]
    return c


def links(text, site):
    """Site-relative links in the texts become full addresses, so they work outside the site."""
    return re.sub(r'\]\((/[^)]*)\)', lambda m: '](%s%s)' % (site, m.group(1)), text)


def licence_md(ed, tk):
    lic = ed.get('licence')
    own = ('FARA\'s own part of this package (the compilation, the corrections in `corrections.csv`, the matching in `pcodes.csv` and `status_unosat_2017`, '
           'and the texts) is published under the %s licence (%s): %s\n\n%s' % (lic['name'], lic['short'], lic['url'], lic.get('means', ''))
           if lic else 'The licence for FARA\'s own part of this package has not been set yet. Until it is, please credit FARA and its sources.')
    return '''# Terms of use

%s

Parts of this package come from other publishers and stay under their terms. Please keep these credits with the data.

## Village names and positions as collected

Source: Rohingya Khobor Arakan Maps Project, https://map.rohingyakhobor.com/map, collected %s. Credit the project as the source.

## Official names, positions and place codes

The `pcode_` and `mimu_` fields of `arakan_villages`, and the files `pcodes.csv` and `pcodes_review.csv`.

Source: Myanmar Information Management Unit (MIMU), %s, https://themimu.info/place-codes. © MIMU. MIMU products may be used free of charge with attribution. They are not for sale and not for commercial use.

## Fire detections

The files `fires.csv`, `fires.json` and `fires_points.json`.

Derived from NASA FIRMS active fire data: VIIRS (Suomi NPP) 375 m and MODIS (Terra, Aqua) Collection 6.1, %s. NASA's data are free and open. NASA asks to be credited: "We acknowledge the use of data from NASA's Fire Information for Resource Management System (FIRMS), part of NASA's Earth Science Data and Information System (ESDIS)."

## 2017 satellite analysis

The files `status_unosat_2017.csv`, `status_unosat_2017.json` and `unosat_2017_zones.geojson`.

Derived from UNOSAT, "Destroyed areas in Buthidaung, Maungdaw, and Rathedaung Townships of Rakhine State in Myanmar", %s. Licence: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0), https://creativecommons.org/licenses/by-sa/4.0/. Credit UNOSAT, and share anything made from these files under the same licence.
''' % (own, tk['collected'], tk['pc_release'], tk['fire_url'], tk['st_url'])


def main():
    ed = be.load(ROOT)
    c = context()
    tk = be.tokens(c, ed)
    cite = be.cite(ed, c.SITE)
    name = 'fara-v' + ed['version']
    files = ed['dataset_files']
    missing = [f for f, _ in files if not os.path.exists(p(f))]
    if missing: sys.exit('edition.json lists files that do not exist: ' + ', '.join(missing))
    if not os.path.exists(p('CITATION.cff')): sys.exit('run python3 build.py first (CITATION.cff is missing)')

    docs = [('README.md', 'What this package is, its files and fields, and how to cite it.'),
            ('METHODS.md', 'Where every part of the data came from and how it was checked and corrected.'),
            ('CHANGELOG.md', 'What changed in each edition.'),
            ('LICENSE.md', 'Terms of use, for FARA\'s part and for each source.'),
            ('CITATION.cff', 'The citation in a form GitHub and reference managers read.'),
            ('SHA256SUMS.txt', 'A checksum of every file, to confirm a copy is complete and unaltered.')]
    table = '| File | What it holds |\n|---|---|\n' + ''.join('| `%s` | %s |\n' % (f, d) for f, d in files + docs)
    lic_para = be.licence_paragraph(ed)
    tk.update(licence_paragraph=lic_para, cite_dataset='> ' + cite['plain'], file_table=table.rstrip(),
              doi_sentence=be.doi_sentence(dict(ed, concept_doi='')),      # a deposited edition cannot name the all-versions DOI: Zenodo shows it only after publishing
              doi_line=' · DOI https://doi.org/' + ed['doi'] if ed['doi'] else '')
    out = {}
    out['README.md'] = links(be.fill(open(p('content', 'dataset_readme.md'), encoding='utf-8').read(), tk), c.SITE)
    out['METHODS.md'] = links(be.fill(open(p('content', 'methods.md'), encoding='utf-8').read(), tk), c.SITE)
    out['CHANGELOG.md'] = links(open(p('CHANGELOG.md'), encoding='utf-8').read(), c.SITE)
    out['LICENSE.md'] = licence_md(ed, tk)
    out['CITATION.cff'] = open(p('CITATION.cff'), encoding='utf-8').read()
    blobs = {f: open(p(f), 'rb').read() for f, _ in files}
    blobs.update({k: v.encode('utf-8') for k, v in out.items()})
    blobs['SHA256SUMS.txt'] = ''.join('%s  %s\n' % (hashlib.sha256(blobs[k]).hexdigest(), k) for k in sorted(blobs)).encode()

    # ---- loose files, for dragging into Zenodo
    d = p('dist', name)
    if os.path.isdir(d): shutil.rmtree(d)
    os.makedirs(d)
    for k, b in blobs.items():
        with open(os.path.join(d, k), 'wb') as f: f.write(b)

    # ---- one zip, the same bytes on every run
    y, m, day = (int(x) for x in ed['date'].split('-'))
    zpath = p('downloads', 'fara-dataset-v%s.zip' % ed['version'])
    os.makedirs(os.path.dirname(zpath), exist_ok=True)
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for k in sorted(blobs):
            info = zipfile.ZipInfo('%s/%s' % (name, k), date_time=(y, m, day, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, blobs[k])

    # ---- what goes into Zenodo's form
    lic = ed.get('licence')
    desc = ('<p>FARA ("fará" means "village" in the Rohingya language) records the names and positions of %(n)s Rohingya villages in four townships of Arakan '
            '(Rakhine State, Myanmar): %(town_counts)s. Each record gives the village\'s Rohingya name, its official romanised name, its name in Burmese script where known, '
            'its village tract, township and district, its coordinates (WGS84) and its official MIMU place codes. A second table gives what UNOSAT\'s analysis of satellite imagery '
            'from 31 August to 11 October 2017 marked at or near each village, and a third the days on which NASA\'s satellites detected a fire within one kilometre of it '
            'in the autumns of 2016 and 2017.</p>'
            '<p>Rohingya village names are being renamed and removed from official maps. FARA keeps them on record for research, reporting, human-rights documentation '
            'and the Rohingya community. The living archive, with a map and satellite imagery of every village, is at <a href="%(site)s/">%(site)s</a>.</p>'
            '<p>This is edition %(version)s of %(date)s. The archive is published in numbered editions so that a citation always leads to the same data. '
            '<code>METHODS.md</code> says where every part of the data came from and how it was checked and corrected; <code>CHANGELOG.md</code> lists what changed; '
            '<code>corrections.csv</code> lists every change made to a source value.</p>'
            '<p><b>Sources and terms.</b> Village names and positions as collected: Rohingya Khobor Arakan Maps Project. Official names, positions and place codes: '
            '© Myanmar Information Management Unit (MIMU), free to use with attribution, not for sale or commercial use. 2017 analysis: derived from UNOSAT data, CC BY-SA 4.0. '
            'Fire detections: derived from NASA FIRMS data, free and open. '
            'See <code>LICENSE.md</code>.</p>') % dict(tk, site=c.SITE)
    meta = {
        'resource_type': 'Dataset', 'title': ed['title'], 'publication_date': ed['date'], 'version': ed['version'],
        'creators': [{'family_name': a['family'], 'given_name': a['given'], 'orcid': a.get('orcid', '')} for a in ed['authors']],
        'description_html': desc,
        'licences': ([lic['name']] if lic else ['NOT DECIDED YET']) + ['Creative Commons Attribution Share Alike 4.0 International (the three UNOSAT-derived files)'],
        'copyright': 'Official names, positions and place codes © Myanmar Information Management Unit (MIMU). 2017 analysis derived from UNOSAT data (CC BY-SA 4.0).',
        'keywords': be.KEYWORDS + ['Rohingya language', 'P-codes', 'UNOSAT', 'NASA FIRMS', 'human rights documentation'],
        'languages': ['English', 'Rohingya', 'Burmese'],
        'publisher': 'Zenodo',
        'related_works': [
            {'relation': 'Is supplement to', 'identifier': c.SITE + '/', 'scheme': 'URL', 'resource_type': 'Other', 'note': 'the living archive'},
            {'relation': 'Is derived from', 'identifier': 'https://map.rohingyakhobor.com/map', 'scheme': 'URL', 'resource_type': 'Dataset', 'note': 'source of the villages'},
            {'relation': 'Is derived from', 'identifier': tk['st_url'], 'scheme': 'URL', 'resource_type': 'Dataset', 'note': 'UNOSAT 2017 analysis'},
            {'relation': 'References', 'identifier': 'https://themimu.info/place-codes', 'scheme': 'URL', 'resource_type': 'Dataset', 'note': 'MIMU place codes'},
            {'relation': 'Is documented by', 'identifier': c.SITE + '/methods/', 'scheme': 'URL', 'resource_type': 'Other', 'note': 'methods'},
            {'relation': 'Is supplemented by', 'identifier': be.REPO, 'scheme': 'URL', 'resource_type': 'Software', 'note': 'scripts that build the archive'}],
        'files': sorted(blobs),
    }
    with open(os.path.join(d, 'zenodo.json'), 'w', encoding='utf-8') as f: json.dump(meta, f, ensure_ascii=False, indent=2)

    size = sum(len(b) for b in blobs.values())
    print('edition %s: %d files, %.1f MB loose in dist/%s/ ; downloads/%s is %.1f MB%s'
          % (ed['version'], len(blobs), size / 1e6, name, os.path.basename(zpath), os.path.getsize(zpath) / 1e6,
             '' if ed['doi'] else ' ; no DOI yet (reserve one at Zenodo, put it in edition.json, then run both builds again)'))


if __name__ == '__main__':
    main()
