#!/usr/bin/env python3
"""Old maps, step 1: take only the Arakan sheets (84 C and 84 D) out of the published archives, without downloading the archives whole.

    python3 tools/oldmaps_fetch.py WORKDIR [early later half]

The archives are the georeferenced Survey of India sheets shared by the Old Survey of India Maps community and Horst Held on Zenodo
(records 18975982, 11367062 and 13346102, CC BY 4.0). They are several gigabytes each; a zip can be read from the far end, so only the
sheets that are needed are fetched. The sheets land in WORKDIR/dl/<set>/ as .jpg with a world file (.jgw).
"""
import io, os, re, sys, zipfile, urllib.request
WORK = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath('oldmaps_work')
class HttpFile(io.RawIOBase):
    def __init__(s, url):
        s.url = url; s.pos = 0; s.cache = {}
        r = urllib.request.urlopen(urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'curl/8'}))
        s.size = int(r.headers['Content-Length']); s.url = r.geturl()
    def seekable(s): return True
    def readable(s): return True
    def tell(s): return s.pos
    def seek(s, o, w=0):
        s.pos = o if w == 0 else s.pos + o if w == 1 else s.size + o; return s.pos
    def _get(s, a, b):
        r = urllib.request.urlopen(urllib.request.Request(s.url, headers={'Range': 'bytes=%d-%d' % (a, b - 1), 'User-Agent': 'curl/8'}))
        return r.read()
    def read(s, n=-1):
        if n < 0: n = s.size - s.pos
        n = min(n, s.size - s.pos)
        if n <= 0: return b''
        B = 1 << 22
        out = b''
        if n > B * 2:
            out = s._get(s.pos, s.pos + n)
        else:
            a = s.pos
            while len(out) < n:
                k = (a + len(out)) // B
                if k not in s.cache: s.cache[k] = s._get(k * B, min(s.size, (k + 1) * B))
                off = a + len(out) - k * B
                out += s.cache[k][off:off + n - len(out)]
        s.pos += len(out); return out
    def readinto(s, b):
        d = s.read(len(b)); b[:len(d)] = d; return len(d)
def open_zip(url): return zipfile.ZipFile(io.BufferedReader(HttpFile(url), 1 << 20))
DL = os.path.join(WORK, 'dl')
SETS = {'early': 'https://zenodo.org/records/18975982/files/mmHistoricOItopomaps_OxU.gdb.zip?download=1',
        'later': 'https://zenodo.org/records/11367062/files/mm_OI_JBv2024.zip?download=1',
        'half':  'https://zenodo.org/records/13346102/files/mm_HI_JBv2024_epsg4326.zip?download=1'}
for key in (sys.argv[2:] or list(SETS)):
    z = open_zip(SETS[key]); out = os.path.join(DL, key); os.makedirs(out, exist_ok=True)
    infos = z.infolist(); print(key, len(infos), 'entries; sample', [i.filename for i in infos[:3]])
    for i in infos:
        base = os.path.basename(i.filename)
        if not re.match(r'^84[ -_]?[CD]', base): continue
        if not base.lower().endswith(('.jpg', '.jgw', '.jpgw', '.wld', '.tif', '.tfw', '.kml')):
            continue
        print(' ', i.file_size, i.filename, flush=True)
        if i.file_size > 60e6: print('   skipped: too large'); continue
        dst = os.path.join(out, re.sub(r'[^A-Za-z0-9._-]', '_', base))
        if os.path.exists(dst) and os.path.getsize(dst) == i.file_size: continue
        with z.open(i) as f, open(dst, 'wb') as g: g.write(f.read())
