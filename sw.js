/* Deep-Risk-OPP Service Worker — 数据与页面网络优先，静态资源缓存优先 */
const CACHE = 'dr-v5';
const DATA_FILES = ['gor_latest.json', 'capital_flows_latest.json', 'feed.xml'];

self.addEventListener('install', (e) => { self.skipWaiting(); });
self.addEventListener('activate', (e) => { e.waitUntil(self.clients.claim()); });

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  const isData = DATA_FILES.some((s) => url.pathname.endsWith(s));
  const isHTML = e.request.mode === 'navigate' ||
                 url.pathname.endsWith('.html') ||
                 url.pathname.endsWith('/');
  if (isData || isHTML) {
    // 网络优先：保证页面与数据新鲜；离线时回退缓存
    e.respondWith(
      fetch(e.request)
        .then((r) => {
          const clone = r.clone();
          caches.open(CACHE).then((c) => c.put(e.request, clone));
          return r;
        })
        .catch(() => caches.match(e.request))
    );
    return;
  }
  // 静态资源：缓存优先
  e.respondWith(
    caches.match(e.request).then((hit) => hit || fetch(e.request).then((r) => {
      const clone = r.clone();
      caches.open(CACHE).then((c) => c.put(e.request, clone));
      return r;
    }))
  );
});
