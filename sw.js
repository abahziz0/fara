/* FARA offline support. build.py stamps 3e46b63c312e so every release gets fresh caches.
   - pages: network first, saved copy when offline
   - app files, fonts, libraries: saved on first use
   - map tiles: saved as they are viewed (capped), so areas already looked at stay visible offline */
const VERSION = '3e46b63c312e';
const SHELL = 'fara-shell-' + VERSION, LIBS = 'fara-libs-v1', TILES = 'fara-tiles-v1';
const PRECACHE = ['/', '/fara.html', '/wards.js', '/pages.css', '/manifest.webmanifest', '/icon-192.png', '/icon-512.png', '/apple-touch-icon.png',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css', 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'];
const TILE_HOSTS = /^(server\.arcgisonline\.com|services\.arcgisonline\.com|wayback\.maptiles\.arcgis\.com|tiles\.openfreemap\.org)$/;
const LIB_HOSTS = /^(fonts\.googleapis\.com|fonts\.gstatic\.com|unpkg\.com|cdn\.jsdelivr\.net)$/;
const TILE_LIMIT = 1600;
let puts = 0;

self.addEventListener('install', e => {
  e.waitUntil(caches.open(SHELL).then(c => Promise.allSettled(PRECACHE.map(u => c.add(u)))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('fara-shell-') && k !== SHELL).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

async function trim(cache){
  const keys = await cache.keys();
  if (keys.length > TILE_LIMIT) await Promise.all(keys.slice(0, keys.length - TILE_LIMIT + 200).map(k => cache.delete(k)));
}
/* Saved copy first. Scripts, styles and fonts are normally requested without CORS, which would give an
   unreadable ("opaque") response that cannot be stored safely, so they are re-requested with CORS;
   every host used here allows that. */
async function cacheFirst(req, name, cap){
  const hit = await caches.match(req.url, { ignoreVary:true });
  if (hit) return hit;
  const cache = await caches.open(name);
  let res;
  try { res = await fetch(new Request(req.url, { mode:'cors', credentials:'omit' })); }
  catch (err) { return fetch(req); }
  if (res.ok){
    cache.put(req.url, res.clone());
    if (cap && ++puts % 60 === 0) trim(cache);
  }
  return res;
}
async function networkFirst(req){
  const cache = await caches.open(SHELL);
  try {
    const res = await fetch(req);
    if (res.ok) cache.put(req, res.clone());
    return res;
  } catch (err) {
    return (await cache.match(req, { ignoreSearch:true })) || (await cache.match('/')) || (await cache.match('/fara.html')) || Response.error();
  }
}
async function staleWhileRevalidate(req){
  const cache = await caches.open(SHELL), hit = await cache.match(req);
  const fresh = fetch(req).then(res => { if (res.ok) cache.put(req, res.clone()); return res; }).catch(() => hit);
  return hit || fresh;
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET' || req.headers.has('range')) return;
  const url = new URL(req.url);
  if (url.origin === self.location.origin){
    if (url.pathname.startsWith('/_vercel/') || url.pathname === '/sw.js') return;
    if (req.mode === 'navigate' || (req.headers.get('accept') || '').includes('text/html')){ e.respondWith(networkFirst(req)); return; }
    e.respondWith(staleWhileRevalidate(req)); return;
  }
  if (LIB_HOSTS.test(url.hostname)){ e.respondWith(cacheFirst(req, LIBS)); return; }
  if (TILE_HOSTS.test(url.hostname) && /\/tile\/|\.pbf$|\/planet$/.test(url.pathname)){ e.respondWith(cacheFirst(req, TILES, true)); return; }
});
