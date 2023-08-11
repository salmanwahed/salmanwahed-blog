importScripts('https://storage.googleapis.com/workbox-cdn/releases/6.1.5/workbox-sw.js');

const CACHE_NAME = 'salmanwahed-pwa-cache-v1';
const STATIC_ASSETS = [
  '/',
  '/static/logo.png',
];

workbox.precaching.precacheAndRoute(STATIC_ASSETS);

workbox.routing.registerRoute(
  ({ request }) => STATIC_ASSETS.includes(request.url),
  new workbox.strategies.CacheFirst()
);

// You can add additional caching strategies or routes here if needed.
