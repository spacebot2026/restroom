/* 화장실 불편접수 — 앱 설치용 최소 서비스워커.
   아무것도 저장하지 않는다(늘 서버의 최신 화면). 인터넷이 끊겼을 때 안내 한 줄만 보여 준다. */
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e => {
  if (e.request.mode !== 'navigate') return;
  e.respondWith(fetch(e.request).catch(() => new Response(
    '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>연결 끊김</title>' +
    '<body style="font-family:sans-serif;padding:32px 20px;text-align:center;color:#18222F"><h2>인터넷 연결이 끊겼습니다</h2><p>연결되면 다시 열어 주세요.</p></body>',
    { headers: { 'Content-Type': 'text/html; charset=utf-8' } })));
});
