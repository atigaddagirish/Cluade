// Service worker — offline cache for the HAT IS 801 calculator.
// Bump CACHE version whenever index.html or assets change to force an update.
const CACHE = 'hat-is801-v30';
const ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icon.svg',
  './weather.html',
  './weather.webmanifest',
  './weather-icon.svg'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('message', e => {
  if(e.data && e.data.type==='SKIP_WAITING') self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Network-first for navigations (so updates land), cache fallback offline.
// IMPORTANT: only manage SAME-ORIGIN app-shell requests. Cross-origin data/API
// calls (Open-Meteo forecast, IMD relay on raw.githubusercontent, IMD radar/
// satellite images) must go straight to the network — never intercept them, or
// a failed fetch would serve the HTML shell in place of their JSON/image.
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  if (new URL(req.url).origin !== self.location.origin) return;   // let cross-origin pass through
  e.respondWith(
    fetch(req)
      .then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
        return res;
      })
      .catch(() => caches.match(req).then(r => r || caches.match('./index.html')))
  );
});
