#!/usr/bin/env python3
"""Builds everything FARA needs to look right when a link is shared:

  favicon.svg, favicon.ico, icon-192.png, icon-512.png, apple-touch-icon.png, logo.svg, logo.png
  og.png                         the picture shown when map.rohingya.ro itself is shared
  share/img/v/<id>.png           the picture for each village page (village/<id>-<slug>/, written by build.py)
  art/<id>/index.html            one page per village poster  ->  /art/<id>  (sends people on to Map Art)
  share/img/art/<id>.png         the picture for each poster page

Social networks never run JavaScript and never see the part of a link after "#", so a link only
gets its own preview if it is a real page carrying its own title, description and picture.

Needs Google Chrome (to draw the pictures) and Pillow. Run from the repo root:

  python3 tools/build_share.py              everything
  python3 tools/build_share.py --ids 1 128  only these villages (for a quick look)
  python3 tools/build_share.py --no-cards   icons, og.png and pages only
"""
import argparse, html, json, math, os, re, subprocess, sys, tempfile
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://map.rohingya.ro'
CHROME = os.environ.get('CHROME', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
W, H = 1200, 630
PER_SHEET = 20
CYAN, BG = '#00E5FF', '#02050A'
FONTS = ('<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Share+Tech+Mono'
         '&family=Noto+Sans+Myanmar:wght@400;600&family=Playfair+Display:wght@500;600;700&display=swap" rel="stylesheet">')

esc = lambda s: html.escape(str(s), quote=True)
LOGO = json.load(open(os.path.join(ROOT, 'tools', 'logo.json'), encoding='utf-8'))
TPL = open(os.path.join(ROOT, 'fara_template.html'), encoding='utf-8').read()
TOWN_COLORS = dict(re.findall(r"'([A-Za-z]+)':'(#[0-9A-Fa-f]{6})'", re.search(r'const TOWN_COLORS = \{(.*?)\}', TPL, re.S).group(1)))

# ---------------------------------------------------------------- data
def load():
    V = json.load(open(os.path.join(ROOT, 'arakan_villages.json'), encoding='utf-8'))
    for v in V:
        v['en'] = (v.get('name') or '').strip() or '—'
        v['ro'] = (v.get('rohingya_name') or '').strip() or v['en']
        v['my'] = (v.get('village_name_mmr') or '').strip()
        v['tract'] = (v.get('village_tract') or '').strip()
        v['town'] = v.get('township') or 'Unknown'
        v['la'], v['ln'] = float(v['lat']), float(v['lng'])
        v['ok'] = v.get('coord_status') != 'unverified' and 18 < v['la'] < 23.5 and 91 < v['ln'] < 95
        v['color'] = TOWN_COLORS.get(v['town'], '#8FA8C7')
        v['rec'] = 'FARA-%04d' % v['id']
    return V

# ---------------------------------------------------------------- logo pieces
GLOW = ('<radialGradient id="glow"><stop offset="0" stop-color="#00E5FF" stop-opacity=".75"/><stop offset=".45" stop-color="#00E5FF" '
        'stop-opacity=".28"/><stop offset="1" stop-color="#00E5FF" stop-opacity="0"/></radialGradient>')

def mark(kind, x, y, w, color=CYAN, dot='#fff', glow=True):
    """The Hanifi word ('word') or the single letter Fa ('fa') as SVG, w px wide, top-left at x,y. Its dot is the village point."""
    g = LOGO[kind]; s = w / g['w']; d = g['dot']
    out = f'<g transform="translate({x:.2f},{y:.2f}) scale({s:.5f})"><path d="{g["body"]}" fill="{color}"/>'
    if glow: out += f'<circle cx="{d["cx"]}" cy="{d["cy"]}" r="{d["r"]*2.6:.0f}" fill="url(#glow)"/>'
    return out + f'<path d="{g["dotpath"]}" fill="{dot}"/></g>'

def mark_h(kind, w): return LOGO[kind]['h'] * w / LOGO[kind]['w']

def frame(pad=0):
    """Dark tile with the site's corner brackets, on a 64-unit grid. pad adds a margin for icons that get cropped to a circle."""
    return (f'<rect x="{-pad}" y="{-pad}" width="{64+2*pad}" height="{64+2*pad}" fill="#03101E"/>'
            '<rect x="6" y="6" width="52" height="52" fill="none" stroke="#00E5FF" stroke-opacity=".28" stroke-width="1.5"/>'
            '<path d="M6 6h16v3.5H9.5V22H6zM58 58H42v-3.5h12.5V42H58z" fill="#00E5FF"/>')

def icon_word(pad=0):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-pad} {-pad} {64+2*pad} {64+2*pad}"><defs>{GLOW}</defs>{frame(pad)}'
            f'{mark("word", 10, 32 - mark_h("word", 44)/2, 44)}</svg>')

def icon_fa(glow=True):
    w = 30
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">{"<defs>"+GLOW+"</defs>" if glow else ""}{frame()}'
            f'{mark("fa", 32 - w/2, 32 - mark_h("fa", w)/2, w, glow=glow)}</svg>')

def lockup(wd=760, ht=200, bg=None):
    y = ht/2
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {wd} {ht}" width="{wd}" height="{ht}"><defs>{GLOW}</defs>'
            + (f'<rect width="{wd}" height="{ht}" fill="{bg}"/>' if bg else '')
            + mark('word', 40, y - mark_h('word', 250)/2, 250)
            + f'<rect x="322" y="{y-44}" width="1.5" height="88" fill="#00E5FF" opacity=".35"/>'
              f'<text x="354" y="{y+8}" font-family="Space Grotesk" font-weight="700" font-size="64" letter-spacing="14" fill="#E8F2FF">FARA</text>'
              f'<text x="356" y="{y+42}" font-family="Share Tech Mono" font-size="15.5" letter-spacing="5.2" fill="#7F94B0">ARAKAN VILLAGE NAME ARCHIVE</text></svg>')

# ---------------------------------------------------------------- drawing with Chrome
PROFILE = os.path.join(tempfile.gettempdir(), 'fara-share-chrome')

def shoot(body, w, h, css=''):
    """Render an HTML fragment at exactly w x h and return it as a PIL image."""
    with tempfile.TemporaryDirectory() as d:
        page, png = os.path.join(d, 'p.html'), os.path.join(d, 'p.png')
        open(page, 'w', encoding='utf-8').write(
            f'<!doctype html><meta charset="utf-8">{FONTS}<style>*{{margin:0;padding:0;box-sizing:border-box}}'
            f'html,body{{width:{w}px;height:{h}px;overflow:hidden;background:{BG}}}{css}</style>{body}')
        subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                        f'--user-data-dir={PROFILE}', '--virtual-time-budget=9000', f'--window-size={w},{h}',
                        f'--screenshot={png}', 'file://' + page], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        im = Image.open(png).convert('RGB'); im.load()
    if im.size != (w, h): raise SystemExit(f'Chrome returned {im.size}, wanted {(w, h)}')
    return im

def save_card(im, path):
    """Flat dark artwork: 160 colours are indistinguishable from full colour here and a third of the size."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.quantize(colors=160, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(path, optimize=True)

# ---------------------------------------------------------------- shared card parts
CARD_CSS = '''
.card{position:relative;width:1200px;height:630px;overflow:hidden;background:#02050A;color:#E8F2FF;font-family:'Space Grotesk',sans-serif}
.card::before{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(0,229,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(0,229,255,.035) 1px,transparent 1px);background-size:42px 42px}
.card::after{content:"";position:absolute;left:0;right:0;top:0;height:4px;background:linear-gradient(90deg,#00E5FF,rgba(0,229,255,0) 72%)}
.mono{font-family:'Share Tech Mono',monospace}
.my{font-family:'Noto Sans Myanmar',sans-serif}
.brand{position:absolute;left:60px;top:50px;display:flex;align-items:center;gap:18px}
.brand b{font-size:30px;font-weight:700;letter-spacing:.34em;color:#00E5FF}
.brand i{font-style:normal;font-family:'Share Tech Mono',monospace;font-size:12.5px;letter-spacing:.22em;color:#7F94B0;border-left:1px solid rgba(0,229,255,.3);padding:5px 0 5px 18px}
.url{position:absolute;font-family:'Share Tech Mono',monospace;font-size:15px;letter-spacing:.16em;color:#00E5FF}
.chip{display:inline-flex;align-items:center;gap:8px;font-family:'Share Tech Mono',monospace;font-size:14px;letter-spacing:.18em;text-transform:uppercase;padding:4px 12px;border:1px solid currentColor}
.chip::before{content:"";width:8px;height:8px;border-radius:50%;background:currentColor}
.k{font-family:'Share Tech Mono',monospace;font-size:11.5px;letter-spacing:.24em;color:#56708F;text-transform:uppercase;margin-bottom:7px}
.notch{position:absolute;width:26px;height:26px;border:solid #00E5FF;border-width:0}
'''
BRAND = lambda: (f'<div class="brand"><svg width="96" height="{mark_h("word", 96):.1f}" viewBox="0 0 96 {mark_h("word", 96):.1f}">'
                 f'{mark("word", 0, 0, 96, glow=False)}</svg><b>FARA</b><i>THE ARAKAN VILLAGE NAME ARCHIVE</i></div>')

def name_size(s, sizes):
    """Pick a font size for a name by its length: sizes = [(max_chars, px), ...]."""
    for n, px in sizes:
        if len(s) <= n: return px
    return sizes[-1][1]

class Locator:
    """Dot map of every village; one of them can be lit up."""
    def __init__(self, V, w, h, pad=22):
        P = [v for v in V if v['ok']]
        self.la0, self.la1 = min(v['la'] for v in P), max(v['la'] for v in P)
        self.ln0, self.ln1 = min(v['ln'] for v in P), max(v['ln'] for v in P)
        self.k = math.cos(math.radians((self.la0 + self.la1) / 2))
        self.s = min((w - 2*pad) / ((self.ln1 - self.ln0) * self.k), (h - 2*pad) / (self.la1 - self.la0))
        self.ox = (w - (self.ln1 - self.ln0) * self.k * self.s) / 2
        self.oy = (h - (self.la1 - self.la0) * self.s) / 2
        self.w, self.h = w, h
        self.dots = ''.join(f'<circle cx="{self.x(v):.1f}" cy="{self.y(v):.1f}" r="2.1" fill="{v["color"]}"/>' for v in P)
    def x(self, v): return self.ox + (v['ln'] - self.ln0) * self.k * self.s
    def y(self, v): return self.oy + (self.la1 - v['la']) * self.s
    def symbol(self, sid='dots'): return f'<svg width="0" height="0" style="position:absolute"><defs>{GLOW}<g id="{sid}">{self.dots}</g></defs></svg>'
    def svg(self, v=None, opacity=.5, sid='dots'):
        s = f'<svg width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}"><use href="#{sid}" opacity="{opacity}"/>'
        if v is not None and v['ok']:
            x, y = self.x(v), self.y(v)
            s += (f'<path d="M0 {y:.1f}H{self.w}M{x:.1f} 0V{self.h}" stroke="#00E5FF" stroke-opacity=".22" stroke-width="1"/>'
                  f'<circle cx="{x:.1f}" cy="{y:.1f}" r="46" fill="url(#glow)"/>'
                  f'<circle cx="{x:.1f}" cy="{y:.1f}" r="30" fill="none" stroke="#00E5FF" stroke-opacity=".35" stroke-width="1.5"/>'
                  f'<circle cx="{x:.1f}" cy="{y:.1f}" r="16" fill="none" stroke="#00E5FF" stroke-width="2"/>'
                  f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="#fff"/>')
        return s + '</svg>'

# ---------------------------------------------------------------- village card
VILLAGE_CSS = CARD_CSS + '''
.v .rec{position:absolute;left:60px;top:150px;display:flex;align-items:center;gap:16px;font-family:'Share Tech Mono',monospace;font-size:16px;letter-spacing:.2em;color:#7F94B0}
.v .names{position:absolute;left:60px;top:196px;width:670px}
.v .ro{font-weight:700;line-height:1.04;letter-spacing:-.01em;color:#fff;overflow-wrap:break-word}
.v .en{font-family:'Share Tech Mono',monospace;font-size:25px;color:#9FB4D0;margin-top:14px;letter-spacing:.02em}
.v .mm{font-size:27px;line-height:1.6;color:#C9D8EC;margin-top:4px}
.v .meta{position:absolute;left:60px;bottom:52px;width:670px;display:flex;gap:0;border-top:1px solid rgba(110,160,210,.2);padding-top:16px}
.v .meta>div{flex:1;min-width:0;padding-right:18px}
.v .meta .val{font-size:18.5px;font-weight:500;line-height:1.25;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.v .meta .val.mono{font-family:'Share Tech Mono',monospace;color:#00E5FF;font-size:17.5px}
.v .loc{position:absolute;right:56px;top:50px;width:340px;height:530px;border:1px solid rgba(0,229,255,.24);background:rgba(5,12,22,.72)}
.v .loc .t{position:absolute;left:16px;top:13px;font-family:'Share Tech Mono',monospace;font-size:11px;letter-spacing:.24em;color:#56708F}
.v .loc .b{position:absolute;left:16px;bottom:12px;right:16px;display:flex;justify-content:space-between;font-family:'Share Tech Mono',monospace;font-size:11px;letter-spacing:.16em;color:#56708F}
.v .loc svg{position:absolute;left:0;top:0}
.v .loc .n1{left:-1px;top:-1px;border-left-width:3px;border-top-width:3px}
.v .loc .n2{right:-1px;bottom:-1px;border-right-width:3px;border-bottom-width:3px}
'''
def village_card(v, loc, total):
    px = name_size(v['ro'], [(11, 92), (15, 78), (20, 64), (27, 52), (36, 44), (99, 38)])
    en = f'<div class="en">{esc(v["en"])}</div>' if v['en'] != v['ro'] else ''
    mm = f'<div class="mm my">{esc(v["my"])}</div>' if v['my'] else ''
    coords = f'{v["la"]:.5f}, {v["ln"]:.5f}' if v['ok'] else 'UNVERIFIED'
    return f'''<section class="card v">{BRAND()}
<div class="rec"><span>{v["rec"]}</span><span class="chip" style="color:{v["color"]}">{esc(v["town"])}</span></div>
<div class="names"><div class="ro" style="font-size:{px}px">{esc(v["ro"])}</div>{en}{mm}</div>
<div class="meta"><div><div class="k">Township</div><div class="val">{esc(v["town"])}</div></div>
<div style="flex:1.35"><div class="k">Village tract</div><div class="val">{esc(v["tract"] or "—")}</div></div>
<div><div class="k">Coordinates</div><div class="val mono">{coords}</div></div></div>
<div class="loc"><div class="t">// LOCATION · ARAKAN</div>{loc.svg(v)}<div class="b"><span>{total:,} VILLAGES</span><span>MAP.ROHINGYA.RO</span></div>
<i class="notch n1"></i><i class="notch n2"></i></div></section>'''

# ---------------------------------------------------------------- poster card
ART_CSS = CARD_CSS + '''
.a .poster{position:absolute;left:78px;top:38px;width:370px;height:554px;background:#FAFAF7;color:#141414;transform:rotate(-2.2deg);box-shadow:0 30px 70px rgba(0,0,0,.75),0 0 0 1px rgba(255,255,255,.06)}
.a .poster .in{position:absolute;inset:14px;border:1.5px solid #141414}
.a .poster svg{position:absolute;left:15.5px;top:15.5px}
.a .poster .tb{position:absolute;left:24px;right:24px;bottom:26px;text-align:center}
.a .poster .pn{font-family:'Playfair Display',serif;font-weight:600;line-height:1.08;letter-spacing:.01em}
.a .poster .rule{width:44px;height:1.5px;background:#141414;margin:11px auto 10px}
.a .poster .pa{font-size:10px;letter-spacing:.42em;font-weight:600;padding-left:.42em}
.a .poster .pc{font-size:9px;letter-spacing:.14em;color:#5A5A5A;margin-top:6px}
.a .poster .pf{font-size:5.6px;letter-spacing:.22em;color:#5A5A5A;margin-top:9px}
.a .txt{position:absolute;left:530px;top:160px;width:612px}
.a .lab{font-family:'Share Tech Mono',monospace;font-size:16px;letter-spacing:.3em;color:#00E5FF}
.a .pre{font-size:30px;font-weight:500;color:#9FB4D0;margin-top:22px}
.a .ro{font-weight:700;line-height:1.05;letter-spacing:-.01em;color:#fff;margin-top:4px;overflow-wrap:break-word}
.a .sub{font-size:21px;line-height:1.45;color:#9FB4D0;margin-top:20px}
.a .sub .my{color:#C9D8EC}
.a .cta{position:absolute;left:530px;bottom:54px;display:flex;align-items:center;gap:22px}
.a .cta span{font-family:'Share Tech Mono',monospace;font-size:15px;letter-spacing:.16em;color:#02050A;background:#00E5FF;padding:9px 16px}
.a .cta em{font-style:normal;font-family:'Share Tech Mono',monospace;font-size:14px;letter-spacing:.16em;color:#7F94B0}
.a .brand{left:530px}
'''
def km(a, b):
    dla, dln = math.radians(b['la'] - a['la']), math.radians(b['ln'] - a['ln'])
    s = math.sin(dla/2)**2 + math.cos(math.radians(a['la'])) * math.cos(math.radians(b['la'])) * math.sin(dln/2)**2
    return 12742 * math.asin(math.sqrt(s))

def poster_map(v, P, w=339, h=372, reach=11.0):
    """The village among its neighbours, drawn the way the Noir poster is: ink on paper, the village ringed in red."""
    cx, cy, s = w/2, h/2 + 4, (w/2) / reach
    k = math.cos(math.radians(v['la']))
    pt = lambda o: (cx + (o['ln'] - v['ln']) * 111.32 * k * s, cy - (o['la'] - v['la']) * 110.574 * s)
    near = sorted(((km(v, o), o) for o in P if o['id'] != v['id']), key=lambda t: t[0])
    out = f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}" fill="#FAFAF7"/>'
    for r in (3, 6, 9, 12, 15):
        out += f'<circle cx="{cx}" cy="{cy}" r="{r*s:.1f}" fill="none" stroke="#141414" stroke-opacity=".16" stroke-width="1" stroke-dasharray="2 5"/>'
    for d, o in near[:7]:
        x, y = pt(o); out += f'<path d="M{cx} {cy}L{x:.1f} {y:.1f}" stroke="#141414" stroke-opacity=".5" stroke-width="1"/>'
    for d, o in near:
        if d > reach * 1.7: break
        x, y = pt(o)
        if -6 < x < w + 6 and -6 < y < h + 6: out += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{3.1 if d < 4 else 2.4}" fill="#141414"/>'
    out += (f'<defs><linearGradient id="pfade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FAFAF7" stop-opacity="0"/><stop offset="1" stop-color="#FAFAF7"/></linearGradient></defs>'
            f'<rect y="{h-80}" width="{w}" height="80" fill="url(#pfade)"/>')
    out += (f'<circle cx="{cx}" cy="{cy}" r="13" fill="#FAFAF7" stroke="#C43D3D" stroke-width="3"/><circle cx="{cx}" cy="{cy}" r="4.5" fill="#C43D3D"/>')
    return out + '</svg>'

def art_card(v, P):
    px = name_size(v['ro'], [(11, 84), (15, 72), (20, 60), (27, 50), (36, 42), (99, 36)])
    ppx = name_size(v['ro'], [(10, 34), (14, 29), (19, 24), (26, 20), (99, 16)])
    sub = ' · '.join(x for x in [esc(v['en']) if v['en'] != v['ro'] else '', f'<span class="my">{esc(v["my"])}</span>' if v['my'] else ''] if x)
    place = f'{esc(v["town"])} Township, Arakan'
    ns, ew = ('N' if v['la'] >= 0 else 'S'), ('E' if v['ln'] >= 0 else 'W')
    return f'''<section class="card a">
<div class="poster"><div class="in"></div>{poster_map(v, P)}
<div class="tb"><div class="pn" style="font-size:{ppx}px">{esc(v["ro"])}</div><div class="rule"></div><div class="pa">ARAKAN</div>
<div class="pc">{abs(v["la"]):.4f}° {ns}  /  {abs(v["ln"]):.4f}° {ew}</div><div class="pf">FARA · THE ARAKAN VILLAGE NAME ARCHIVE</div></div></div>
{BRAND()}
<div class="txt"><div class="lab">// MAP ART · VILLAGE POSTER</div><div class="pre">A map poster of</div>
<div class="ro" style="font-size:{px}px">{esc(v["ro"])}</div><div class="sub">{sub + "<br>" if sub else ""}{place}</div></div>
<div class="cta"><span>MAKE YOUR OWN</span><em>MAP.ROHINGYA.RO</em></div></section>'''

# ---------------------------------------------------------------- site card (og.png)
OG_CSS = CARD_CSS + '''
.o .lg{position:absolute;left:64px;top:92px}
.o h1{position:absolute;left:64px;top:262px;font-size:104px;font-weight:700;letter-spacing:.3em;color:#00E5FF;line-height:1}
.o .tag{position:absolute;left:68px;top:380px;font-family:'Share Tech Mono',monospace;font-size:19px;letter-spacing:.3em;color:#7F94B0}
.o .line{position:absolute;left:66px;top:440px;font-size:38px;font-weight:600;color:#fff}
.o .sub{position:absolute;left:66px;top:498px;width:640px;font-size:22px;line-height:1.4;color:#9FB4D0}
.o .loc{position:absolute;right:50px;top:36px;width:380px;height:558px}
.o .leg{position:absolute;right:392px;bottom:52px;display:flex;flex-direction:column;gap:9px;font-family:'Share Tech Mono',monospace;font-size:13px;letter-spacing:.14em;color:#9FB4D0;text-transform:uppercase}
.o .leg span{display:flex;align-items:center;gap:9px}
.o .leg i{width:9px;height:9px;border-radius:50%}
'''
def og_card(V):
    loc = Locator(V, 380, 558, pad=14)
    n = len(V); towns = sorted({v['town'] for v in V if v['town'] in TOWN_COLORS}, key=lambda t: list(TOWN_COLORS).index(t))
    leg = ''.join(f'<span><i style="background:{TOWN_COLORS[t]}"></i>{esc(t)}</span>' for t in towns)
    return loc.symbol() + f'''<section class="card o">
<svg class="lg" width="330" height="{mark_h("word", 330)+40:.0f}" viewBox="0 -30 330 {mark_h("word", 330)+40:.0f}"><defs>{GLOW}</defs>{mark("word", 0, 0, 330)}</svg>
<h1>FARA</h1><div class="tag">THE ARAKAN VILLAGE NAME ARCHIVE</div>
<div class="line">Every village had a name.</div>
<div class="sub">{n:,} Rohingya villages across Arakan, preserved in Rohingya, English and Burmese.</div>
<div class="loc">{loc.svg(None, opacity=.95)}</div><div class="leg">{leg}</div></section>'''

# ---------------------------------------------------------------- share pages
PAGE = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article"><meta property="og:site_name" content="FARA — The Arakan Village Name Archive">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{img}"><meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{alt}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}"><meta name="twitter:image" content="{img}">
<link rel="icon" href="/favicon.ico" sizes="32x32"><link rel="icon" type="image/svg+xml" href="/favicon.svg">
<meta http-equiv="refresh" content="0;url={go}">
<script>location.replace({go_js});</script>
<style>body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#02050A;color:#E8F2FF;font:16px/1.6 system-ui,sans-serif;text-align:center;padding:24px}}a{{color:#00E5FF}}h1{{font-size:28px;margin:0 0 6px}}p{{margin:4px 0;color:#9FB4D0}}</style>
</head><body><main><h1>{h1}</h1>{body}<p><a href="{go}">{cta}</a></p></main></body></html>
'''
def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(text)

def names_line(v):
    return ' · '.join(x for x in [v['ro'], v['en'] if v['en'] != v['ro'] else '', v['my']] if x)

def art_page(v):
    both = f'{v["ro"]} ({v["en"]})' if v['en'] != v['ro'] else v['ro']
    desc = (f'A printable map poster of {both}, a Rohingya village in {v["town"]} Township, Arakan. '
            'Make your own in FARA Map Art: choose a style, download it, print it, share it.')
    go = f'/#art={v["id"]}'
    return PAGE.format(title=esc(f'Map poster of {v["ro"]} — FARA Map Art'), desc=esc(desc), url=f'{SITE}/art/{v["id"]}', img=f'{SITE}/share/img/art/{v["id"]}.png',
                       alt=esc(f'Map poster of {both}'), go=go, go_js=json.dumps(go), h1=esc('Map poster of ' + v['ro']),
                       body=f'<p>{esc(names_line(v))}</p><p>{esc(v["town"])} Township, Arakan</p>', cta='Make this poster in FARA Map Art')

# ---------------------------------------------------------------- build steps
def build_icons():
    out = lambda n: os.path.join(ROOT, n)
    open(out('favicon.svg'), 'w').write(icon_fa(glow=False))
    open(out('logo.svg'), 'w').write(icon_word())
    sq = lambda svg, n=1024: shoot(svg.replace('<svg ', f'<svg width="{n}" height="{n}" style="display:block" ', 1), n, n)
    fa = sq(icon_fa())
    fa.resize((48, 48), Image.LANCZOS).save(out('favicon.ico'), sizes=[(16, 16), (32, 32), (48, 48)])
    app = sq(icon_word(pad=7))                      # margin keeps the brackets inside Android's round mask and iOS's corners
    for n, f in ((512, 'icon-512.png'), (192, 'icon-192.png'), (180, 'apple-touch-icon.png')):
        app.resize((n, n), Image.LANCZOS).save(out(f), optimize=True)
    shoot(lockup(bg=BG).replace('<svg ', '<svg style="display:block;width:1520px;height:400px" ', 1), 1520, 400).save(out('logo.png'), optimize=True)
    print('icons: favicon.svg favicon.ico icon-192.png icon-512.png apple-touch-icon.png logo.svg logo.png')

def build_og(V):
    shoot(og_card(V), W, H, OG_CSS).save(os.path.join(ROOT, 'og.png'), optimize=True)
    print('og.png')

def build_cards(V, which, kind):
    loc = Locator(V, 340, 530, pad=26); P = [v for v in V if v['ok']]; total = len(V)
    css = VILLAGE_CSS if kind == 'v' else ART_CSS
    for i in range(0, len(which), PER_SHEET):
        chunk = which[i:i + PER_SHEET]
        body = loc.symbol() + ''.join(village_card(v, loc, total) if kind == 'v' else art_card(v, P) for v in chunk)
        sheet = shoot(body, W, H * len(chunk), css)
        for j, v in enumerate(chunk):
            save_card(sheet.crop((0, j * H, W, (j + 1) * H)), os.path.join(ROOT, 'share', 'img', kind, f'{v["id"]}.png'))
        print(f'  {kind} cards {min(i + PER_SHEET, len(which))}/{len(which)}', flush=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ids', type=int, nargs='*'); ap.add_argument('--no-cards', action='store_true'); ap.add_argument('--no-icons', action='store_true')
    a = ap.parse_args()
    V = load()
    which = [v for v in V if not a.ids or v['id'] in a.ids]
    if not a.no_icons: build_icons(); build_og(V)
    for v in which:
        if v['ok']: write(os.path.join(ROOT, 'art', str(v['id']), 'index.html'), art_page(v))
    print(f'poster pages: {sum(v["ok"] for v in which)}')
    if not a.no_cards:
        build_cards(V, which, 'v')
        build_cards(V, [v for v in which if v['ok']], 'art')

if __name__ == '__main__':
    main()
