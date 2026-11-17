/*! BLOCKTIDE TV — © 2026 Igor Serrano. Todos os direitos reservados. */
// Guarda a aplicação para abrir depressa (e sem rede mostra o ecrã inicial). Os vídeos vêm sempre do YouTube.
const CACHE = 'btv-0.4.0';
const SHELL = ['./', './index.html', './styles.css', './theme.css', './app.js', './catalog.json', './manifest.webmanifest',
  './icons/icon-192.png', './icons/logo-96.png', './fonts/lilita-one-400.woff2', './fonts/nunito-700.woff2', './fonts/nunito-800.woff2', './fonts/nunito-900.woff2'];
self.addEventListener('install', (e) => { e.waitUntil((async () => { const c = await caches.open(CACHE); await c.addAll(SHELL); await self.skipWaiting(); })()); });
self.addEventListener('activate', (e) => { e.waitUntil((async () => {
  for (const k of await caches.keys()) if (k !== CACHE) await caches.delete(k);
  await self.clients.claim();
})()); });
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== self.location.origin) return; // YouTube e miniaturas: rede normal
  e.respondWith((async () => {
    const c = await caches.open(CACHE);
    if (url.pathname.endsWith('/catalog.json')) { // catálogo: sempre o mais recente quando há rede
      try { const r = await fetch(e.request); c.put(e.request, r.clone()); return r; } catch (_) { return (await c.match(e.request)) || Response.error(); }
    }
    const hit = await c.match(e.request, { ignoreSearch: true });
    if (hit) return hit;
    try { const r = await fetch(e.request); if (r.ok) c.put(e.request, r.clone()); return r; } catch (_) { return (await c.match('./index.html')) || Response.error(); }
  })());
});
