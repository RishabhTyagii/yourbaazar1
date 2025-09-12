self.addEventListener('install', function (e) {
  console.log('Service Worker: Installed');
  e.waitUntil(
    caches.open('yourbaazar-cache-v1').then(function (cache) {
      return cache.addAll([
        '/',
        '/static/css/base.css',
        '/static/css/footer.css',
        '/static/icon/website_logo.png',
      ]);
    })
  );
});

self.addEventListener('fetch', function (e) {
  e.respondWith(
    caches.match(e.request).then(function (response) {
      return response || fetch(e.request);
    })
  );
});
