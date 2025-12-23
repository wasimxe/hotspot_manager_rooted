// Hotspot Manager Service Worker
const CACHE_NAME = 'hotspot-manager-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json'
];

// Install event - cache resources
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Service Worker: Caching files');
        return cache.addAll(urlsToCache);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Service Worker: Clearing old cache');
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', event => {
  const { request } = event;

  // Skip API requests - always fetch from network
  if (request.url.includes('/api/')) {
    event.respondWith(
      fetch(request).catch(err => {
        return new Response(
          JSON.stringify({
            error: 'Network unavailable',
            message: 'Please check your connection'
          }),
          {
            headers: { 'Content-Type': 'application/json' },
            status: 503
          }
        );
      })
    );
    return;
  }

  // For static files - cache first, fallback to network
  event.respondWith(
    caches.match(request)
      .then(response => {
        if (response) {
          return response;
        }

        return fetch(request).then(response => {
          // Check if valid response
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          // Clone the response
          const responseToCache = response.clone();

          caches.open(CACHE_NAME)
            .then(cache => {
              cache.put(request, responseToCache);
            });

          return response;
        });
      })
      .catch(() => {
        // Offline fallback
        return new Response(
          `<!DOCTYPE html>
          <html>
          <head>
            <title>Offline - Hotspot Manager</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
              body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-align: center;
                padding: 20px;
              }
              h1 { margin-bottom: 10px; }
              p { opacity: 0.9; }
              button {
                margin-top: 20px;
                padding: 12px 24px;
                background: white;
                color: #667eea;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
              }
            </style>
          </head>
          <body>
            <div>
              <h1>📡 You're Offline</h1>
              <p>The Hotspot Manager requires an active connection.</p>
              <button onclick="location.reload()">Try Again</button>
            </div>
          </body>
          </html>`,
          { headers: { 'Content-Type': 'text/html' } }
        );
      })
  );
});

// Handle background sync if supported
self.addEventListener('sync', event => {
  if (event.tag === 'sync-devices') {
    event.waitUntil(syncDevices());
  }
});

async function syncDevices() {
  try {
    const response = await fetch('/api/devices');
    const data = await response.json();

    // Broadcast update to all clients
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
      client.postMessage({
        type: 'DEVICES_UPDATED',
        devices: data.devices
      });
    });
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

// Handle push notifications if supported
self.addEventListener('push', event => {
  const options = {
    body: event.data ? event.data.text() : 'New hotspot activity',
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    vibrate: [200, 100, 200],
    tag: 'hotspot-notification',
    requireInteraction: false
  };

  event.waitUntil(
    self.registration.showNotification('Hotspot Manager', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
  event.notification.close();

  event.waitUntil(
    clients.openWindow('/')
  );
});
