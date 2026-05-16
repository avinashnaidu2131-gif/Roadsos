const CACHE = "roadsos-v3";
const STATIC = ["/", "/static/css/style.css", "/static/css/style3d.css",
  "/static/js/map.js", "/static/js/chat.js", "/static/js/features.js",
  "/static/js/realtime.js", "/static/js/impact.js",
  "/static/manifest.json", "/static/icon-192.png", "/static/icon-512.png"];

self.addEventListener("install", e => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(STATIC).catch(() => {})));
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);

  if (url.pathname.startsWith("/api/")) {
    e.respondWith(
      fetch(e.request).then(res => {
        caches.open(CACHE).then(c => c.put(e.request, res.clone()));
        return res;
      }).catch(() => caches.match(e.request).then(r => r ||
        new Response(JSON.stringify({error:"Offline",offline:true}),
          {headers:{"Content-Type":"application/json"}})))
    );
    return;
  }

  e.respondWith(
    caches.match(e.request).then(r => r ||
      fetch(e.request).then(res => {
        if (res.ok) caches.open(CACHE).then(c => c.put(e.request, res.clone()));
        return res;
      })
    )
  );
});

self.addEventListener("push", e => {
  const d = e.data ? e.data.json() : {title:"RoadSoS Alert", body:"Emergency nearby"};
  e.waitUntil(self.registration.showNotification(d.title || "RoadSoS", {
    body: d.body, icon: "/static/icon-192.png", badge: "/static/icon-192.png",
    vibrate: [200,100,200,100,600], requireInteraction: true,
    actions: [{action:"sos",title:"SOS"},{action:"dismiss",title:"Dismiss"}]
  }));
});

self.addEventListener("notificationclick", e => {
  e.notification.close();
  e.waitUntil(clients.openWindow(e.action === "sos" ? "/?action=sos" : "/"));
});

self.addEventListener("sync", e => {
  if (e.tag === "sos-sync") e.waitUntil(syncPending());
});

async function syncPending() {
  try {
    const db = await new Promise((res, rej) => {
      const r = indexedDB.open("roadsos-db", 1);
      r.onupgradeneeded = e => e.target.result.createObjectStore("pending", {keyPath:"id",autoIncrement:true});
      r.onsuccess = e => res(e.target.result);
      r.onerror = rej;
    });
    const items = await new Promise((res, rej) => {
      const tx = db.transaction("pending","readonly");
      const req = tx.objectStore("pending").getAll();
      req.onsuccess = () => res(req.result); req.onerror = rej;
    });
    for (const item of items) {
      try {
        await fetch("/api/sos-report", {method:"POST",body:JSON.stringify(item),headers:{"Content-Type":"application/json"}});
        await new Promise((res,rej)=>{const tx=db.transaction("pending","readwrite");tx.objectStore("pending").delete(item.id);tx.oncomplete=res;tx.onerror=rej;});
      } catch(_) {}
    }
  } catch(_) {}
}
