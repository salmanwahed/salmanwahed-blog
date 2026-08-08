// Self-unregistering service worker.
//
// The previous version imported Workbox from a Google CDN and precached "/"
// with a CacheFirst strategy, which meant returning visitors were served the
// homepage HTML from cache -- they would never see the redesign. The page no
// longer registers a worker, but installs already sitting in visitors'
// browsers keep running until they fetch this file again, so it has to stay
// here and tear itself down.
//
// Safe to delete once traffic has cycled through (a few months).

self.addEventListener('install', function () {
  self.skipWaiting();
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys()
      .then(function (keys) {
        return Promise.all(keys.map(function (k) { return caches.delete(k); }));
      })
      .then(function () { return self.registration.unregister(); })
      .then(function () { return self.clients.matchAll({ type: 'window' }); })
      .then(function (clients) {
        clients.forEach(function (client) { client.navigate(client.url); });
      })
  );
});
