let cacheData = "appv1";
this.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(cacheData).then((cache) => {
      cache.addAll([
        "/@vite/client",
        "/src/main.jsx?t=1655800211982",
        "/@react-refresh",
        "/src/App.jsx",
        "/src/serviceWorker.js?t=1655800211982",
        "/node_modules/.vite/deps/react_jsx-dev-runtime.js?v=00f57254",
        "/node_modules/vite/dist/client/env.mjs",
        "/node_modules/.vite/deps/chunk-QM6KTHUM.js?v=af32fe9f",
        "/node_modules/.vite/deps/chunk-6MDKZZLV.js?v=af32fe9f",
        "/src/components/Home.jsx",
        "/node_modules/.vite/deps/react-router-dom.js?v=00f57254",
        "/src/components/Runout.jsx",
        "/src/components/Lbw.jsx",
        "/node_modules/.vite/deps/chunk-5ATQ7DAJ.js?v=af32fe9f",
        "/node_modules/.vite/deps/@mui_material_Typography.js?v=00f57254",
        "/node_modules/.vite/deps/@mui_material.js?v=00f57254",
        "/src/components/Footer.jsx",
        "/node_modules/.vite/deps/@mui_icons-material.js?v=00f57254",
        "/node_modules/.vite/deps/@mui_icons-material_SkipPrevious.js?v=00f57254",
        "/node_modules/.vite/deps/@mui_icons-material_SkipNext.js?v=00f57254",
        "/node_modules/.vite/deps/@mui_icons-material_PlayArrow.js?v=00f57254",
        "/node_modules/.vite/deps/@mui_icons-material_Pause.js?v=00f57254",
        "/node_modules/.vite/deps/chunk-HHCEMNSF.js?v=af32fe9f",
        "/node_modules/.vite/deps/chunk-FNJ65HGK.js?v=af32fe9f",
        "/node_modules/.vite/deps/chunk-3E7QXYNA.js?v=af32fe9f",
        "/node_modules/.vite/deps/chunk-RBYJO77Q.js?v=af32fe9f",
        "/node_modules/.vite/deps/chunk-EKI5HYH7.js?v=af32fe9f",
        "/node_modules/.vite/deps/chunk-G623ZASM.js?v=af32fe9f",
        "/node_modules/.vite/deps/@mui_material_Button.js?v=00f57254",
        "/node_modules/.vite/deps/react-dom_client.js?v=00f57254",
        '/node_modules/.vite/deps/react.js?v=00f57254',
        '/manifest.json',
        '/favicon.ico',
        "/index.html",
        "/",
      ]);
    })
  );
});

this.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((res) => {
      if (res) {
        return res;
      }
      return requestBackend(event);
    })
  );
});
