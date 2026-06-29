const CACHE_NAME = 'urbis-v2'

self.addEventListener('install', (event) => {
  event.waitUntil(self.skipWaiting())
})

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim())
})

self.addEventListener('fetch', (event) => {
  const { pathname } = new URL(event.request.url)
  // Never intercept API/auth traffic — avoids stale SW responses breaking mobile login.
  if (pathname.startsWith('/api/') || pathname.startsWith('/uploads/')) {
    return
  }

  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request)),
  )
})
