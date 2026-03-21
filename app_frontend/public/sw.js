// Forewise Service Worker v1.1.0
const CACHE_NAME = 'forewise-v2.0.0';
const APP_VERSION = 'forewise-v2.0.0';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/logo-forewise-transparent.png',
  '/icons/forewise-icon-192.png',
];

// Install: cache static shell + notify clients about update
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch(() => {});
    })
  );
  self.skipWaiting();
});

// Activate: clean old caches + notify all clients
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      const oldKeys = keys.filter((key) => key !== CACHE_NAME);
      if (oldKeys.length > 0) {
        self.clients.matchAll().then((clients) => {
          clients.forEach((client) => {
            client.postMessage({
              type: 'APP_UPDATED',
              version: APP_VERSION,
            });
          });
        });
      }
      return Promise.all(oldKeys.map((key) => caches.delete(key)));
    })
  );
  self.clients.claim();
});

// Listen for skip-waiting message from frontend
self.addEventListener('message', (event) => {
  if (event.data === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Fetch: network-first for API, cache-first for assets
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET') return;
  if (url.pathname.startsWith('/api/')) return;

  if (url.pathname.startsWith('/supplier-portal/')) {
    event.respondWith(
      fetch(event.request).catch(() => caches.match('/index.html'))
    );
    return;
  }

  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then((res) => {
          const clone = res.clone();
          caches.open(CACHE_NAME).then((c) => c.put(event.request, clone));
          return res;
        })
        .catch(() => caches.match('/index.html'))
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then(
      (cached) =>
        cached ||
        fetch(event.request).then((res) => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(CACHE_NAME).then((c) => c.put(event.request, clone));
          }
          return res;
        })
    )
  );
});
