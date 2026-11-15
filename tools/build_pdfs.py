#!/usr/bin/env python3
"""Print each township gazetteer (township/<slug>/gazetteer/) to a PDF in downloads/, using Chrome.

    python3 build.py && python3 tools/build_pdfs.py            # all four
    python3 tools/build_pdfs.py sittwe                         # just one

Needs Google Chrome (or Chromium) and an internet connection the first time, for the three web fonts.
The page is designed for A4 in gazetteer.css: page numbers and running titles come from CSS, not from Chrome.
"""
import functools, http.server, os, re, shutil, socketserver, subprocess, sys, tempfile, threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = next((c for c in ('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', shutil.which('google-chrome') or '',
                           shutil.which('chromium') or '', shutil.which('chromium-browser') or '') if c and os.path.exists(c)), None)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


def main():
    if not CHROME: sys.exit('Google Chrome was not found')
    want = [a.lower() for a in sys.argv[1:]]
    slugs = sorted(d for d in os.listdir(os.path.join(ROOT, 'township'))
                   if os.path.exists(os.path.join(ROOT, 'township', d, 'gazetteer', 'index.html')) and (not want or d in want))
    os.makedirs(os.path.join(ROOT, 'downloads'), exist_ok=True)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=ROOT)) as srv:
        port = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        for slug in slugs:
            out = os.path.join(ROOT, 'downloads', 'fara-gazetteer-%s.pdf' % slug)
            with tempfile.TemporaryDirectory() as prof:
                r = subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--no-first-run', '--user-data-dir=' + prof,
                                    '--no-pdf-header-footer', '--virtual-time-budget=25000', '--run-all-compositor-stages-before-draw',
                                    '--print-to-pdf=' + out, 'http://127.0.0.1:%d/township/%s/gazetteer/' % (port, slug)],
                                   capture_output=True, text=True, timeout=240)
            if not os.path.exists(out): sys.exit('no PDF for %s: %s' % (slug, r.stderr[-400:]))
            data = open(out, 'rb').read()
            pages = len(re.findall(rb'/Type\s*/Page[^s]', data))
            print('downloads/%s · %d pages · %.1f MB' % (os.path.basename(out), pages, len(data) / 1e6))
        srv.shutdown()


if __name__ == '__main__':
    main()
