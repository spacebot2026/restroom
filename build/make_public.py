# -*- coding: utf-8 -*-
"""시연판(아티팩트) → 공개판(GitHub Pages + Firebase) 변환"""
import re, sys, json
SRC = 'restroom-care.html'
s = open(SRC, encoding='utf-8').read()

def rep(a, b, count=1):
    global s
    n = s.count(a)
    assert n == count, (a[:80], n)
    s = s.replace(a, b)

def rep_between(start, end, new, keep_end=True):
    global s
    i = s.index(start); j = s.index(end, i)
    s = s[:i] + new + (s[j:] if keep_end else s[j + len(end):])

BASE = 'https://spacebot2026.github.io/restroom/'
CONFIG = open('public/firebase_config.json', encoding='utf-8').read().strip() if len(sys.argv) < 2 else sys.argv[1]

# ---------- 1. 문서 머리 ----------
style_i = s.index('<style>')
head = '''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="noindex,nofollow">
<meta name="theme-color" content="#111A26">
<title>화장실 불편접수</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600;700&family=IBM+Plex+Sans+KR:wght@400;500;600;700&display=swap">
'''
s = head + s[style_i:]
rep('<style>', '<style>\n[hidden]{display:none!important}\nimg{max-width:100%}\n:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px);color-scheme:light}\n', 1)
extra_css = '''
.gate{min-height:60vh;display:grid;place-items:center;padding:24px 16px}
.gate-card{width:min(400px,100%);display:grid;gap:12px;text-align:center;padding:28px 24px}
.gate-card h2{margin:0;font-size:20px}
.gate-card .brand{justify-content:center}
.gate-bad{margin:0;color:var(--new);font-size:13px}
.gate-btn{justify-content:center;padding:10px 14px;font-size:14px}
.acct{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--muted)}
.acct span{max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.acl{list-style:none;margin:0 0 10px;padding:0;display:grid;gap:6px}
.acl li{display:flex;align-items:center;gap:10px;font-size:13px}
.acl li .mono{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis}
'''
rep('</style>', extra_css + '</style>\n</head>\n<body>', 1)
s = s.rstrip() + '\n</body>\n</html>\n'

# 상단: 계정 표시 자리
rep('<div class="top-actions">\n      <label class="switch"', '<div class="top-actions">\n      <div class="acct" id="acct"></div>\n      <label class="switch"', 1)
rep('<small>시연판 · 판 <span id="buildNo"></span></small>', '<small>판 <span id="buildNo"></span></small>', 1)

# Firebase SDK
rep('<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>',
    '<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js"></script>\n'
    '<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-auth-compat.js"></script>\n'
    '<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore-compat.js"></script>\n'
    '<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>', 1)

# ---------- 2. 주소 ----------
rep("const ART_URL = 'https://claude.ai/artifact/6aWsRJYkd2TCtgHtb3QXmV';", "const BASE_URL = '" + BASE + "';", 1)
rep("const qrURL = roomId => ART_URL + '#r-' + roomId.toLowerCase();", "const qrURL = roomId => BASE_URL + '#r-' + roomId.toLowerCase();", 1)
rep("const STAFF_URL = ART_URL + '#staff';", "const STAFF_URL = BASE_URL + '#staff';", 1)

# 사진 주소 (photos 문서)
rep("const photoSrc = p => p ? (p.file ? '/_blob/' + p.file : (p.data || p.url || '')) : '';",
    "const photoSrc = p => { if (!p) return ''; if (p.pid) { if (PHOTO_CACHE[p.pid]) return PHOTO_CACHE[p.pid]; loadPhoto(p.pid); return BLANK; } return p.data || p.url || ''; };", 1)

# ---------- 3. 저장소 → Firebase ----------
store = r'''/* ================= 저장소 (Firebase) ================= */
const FIREBASE_CONFIG = __CONFIG__;
// 관리자 판정은 서버 규칙으로 한다(관리자만 읽을 수 있는 notes 를 읽어 본다) — 관리자 이메일을 공개 코드에 두지 않는다.
firebase.initializeApp(FIREBASE_CONFIG);
const AUTHX = firebase.auth();
const DB = firebase.firestore();
const FV = firebase.firestore.FieldValue;
const ASSETS = null;
const DL = { async save({ filename, data }) {
  const type = /\.csv$/.test(filename) ? 'text/csv;charset=utf-8' : /\.json$/.test(filename) ? 'application/json' : 'application/octet-stream';
  const blob = data instanceof Blob ? data : new Blob([data], { type });
  const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 8000);
  return { status: 'saved' };
} };
let STORE = 'wait';
const AUTH = { ready: false, user: null, role: 'none', email: '' };
let AUTH_WAIT = [];
const waitAuth = () => AUTH.user ? Promise.resolve() : new Promise((res, rej) => { AUTH_WAIT.push(res); setTimeout(() => rej({ code: 'auth-timeout' }), 12000); });
function toast(msg) { const t = $('#toast'); t.textContent = msg; t.hidden = false; clearTimeout(toast.tm); toast.tm = setTimeout(() => { t.hidden = true; }, 3400); }
const errCode = e => (e && e.code) || '오류';
function dispatch(evs) { MOUNTS.forEach(m => { try { m.refresh(evs || []); } catch (e) { console.error(e); } }); refreshDetail(); }
const stripUndef = o => { Object.keys(o).forEach(k => { if (o[k] === undefined) delete o[k]; }); return o; };
async function putTicket(t) { await DB.collection('tickets').doc(t.id).set(stripUndef(Object.assign({}, t))); trackTicket(t.id); }
async function patchTicket(id, patch) { await DB.doc('tickets/' + id).update(stripUndef(Object.assign({}, patch))); }
function diffEvents(prev, next) {
  const pm = new Map(prev.map(t => [t.id, t])), ev = [];
  next.forEach(t => {
    const p = pm.get(t.id);
    if (!p) { if (t.createdAt > Date.now() - 10 * M) ev.push({ type: 'new', t }); }
    else if ((t.reports || 1) > (p.reports || 1)) ev.push({ type: 'dup', t });
    else if (t.status === 'new' && p.status !== 'new') ev.push({ type: 'new', t });
  });
  return ev;
}
const PHOTO_CACHE = {}, PHOTO_LOADING = new Set();
const BLANK = 'data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==';
function loadPhoto(pid) {
  if (PHOTO_CACHE[pid] || PHOTO_LOADING.has(pid)) return;
  PHOTO_LOADING.add(pid);
  DB.doc('photos/' + pid).get().then(s => { if (s.exists) { PHOTO_CACHE[pid] = s.data().data; dispatch([]); } }).catch(() => {}).finally(() => PHOTO_LOADING.delete(pid));
}
async function toJpegData(img, maxEdge, maxLen) {
  const ow = img.naturalWidth, oh = img.naturalHeight, k = Math.min(1, maxEdge / Math.max(ow, oh));
  const c = document.createElement('canvas'); c.width = Math.round(ow * k); c.height = Math.round(oh * k);
  const g = c.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height); g.drawImage(img, 0, 0, c.width, c.height);
  let q = 0.86, data = c.toDataURL('image/jpeg', q);
  while (data.length > maxLen && q > 0.35) { q -= 0.1; data = c.toDataURL('image/jpeg', q); }
  return { data, w: c.width, h: c.height, ow, oh, shrunk: k < 1 };
}
async function storePhoto(blob) {
  const url0 = URL.createObjectURL(blob);
  let img; try { img = await loadImg(url0); } finally { URL.revokeObjectURL(url0); }
  const r = await toJpegData(img, 1600, 900000);
  const pid = 'p' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  await DB.doc('photos/' + pid).set({ data: r.data, w: r.w, h: r.h, ow: r.ow, oh: r.oh, at: Date.now(), uid: AUTH.user ? AUTH.user.uid : '' });
  PHOTO_CACHE[pid] = r.data;
  return { pid, w: r.w, h: r.h, ow: r.ow, oh: r.oh, shrunk: r.shrunk };
}

'''
store = store.replace('__CONFIG__', CONFIG)
rep_between('/* ================= 저장소 ================= */', '/* ================= 접수 처리 ================= */', store)

# 중복 신고: 원자적 증가
rep("const patch = { reports: (open.reports || 1) + 1, log: (open.log || []).concat([{ t: now, text: '추가 신고 · QR' + (stall ? ' · ' + stallKo(stall) : '') }]) };",
    "const patch = { reports: FV.increment(1), log: FV.arrayUnion({ t: now, text: '추가 신고 · QR' + (stall ? ' · ' + stallKo(stall) : '') }) };", 1)
rep("await patchTicket(open.id, patch, 'dup');\n      return { dup: true, id: open.id };",
    "await patchTicket(open.id, patch, 'dup');\n      trackTicket(open.id);\n      return { dup: true, id: open.id };", 1)
rep("adminNote: '', dev: DEVICE, log: [{ t: now, text: '접수 · QR' }] };",
    "adminNote: '', dev: DEVICE, uid: AUTH.user ? AUTH.user.uid : '', log: [{ t: now, text: '접수 · QR' }] };", 1)
# 접수 전 로그인(익명) 대기
rep("async function createTicket({ roomId, issue, stall = null, note = '', photo = null, emergency = false }) {\n  const now = Date.now(), room = rById(roomId);",
    "async function createTicket({ roomId, issue, stall = null, note = '', photo = null, emergency = false }) {\n  await waitAuth();\n  const now = Date.now(), room = rById(roomId);", 1)
rep("""async function addClean(roomId) {
  const n = (FEEDBACK[roomId] || 0) + 1;
  if (DB) { try { await DB.doc('feedback/' + kstDate() + '_' + roomId).set({ day: kstDate(), roomId, n, at: Date.now() }); } catch (e) { /* 무시 */ } }
  else { FEEDBACK[roomId] = n; dispatch([]); }
}""", """async function addClean(roomId) {
  try { await waitAuth(); await DB.doc('feedback/' + kstDate() + '_' + roomId).set({ day: kstDate(), roomId, n: FV.increment(1), at: Date.now() }, { merge: true }); } catch (e) { /* 무시 */ }
}""", 1)
# 사진 올릴 때도 로그인 대기
rep("    try {\n      const photo = QS.pblob ? await storePhoto(QS.pblob) : null;",
    "    try {\n      await waitAuth();\n      const photo = QS.pblob ? await storePhoto(QS.pblob) : null;", 1)

# ---------- 4. 고객: 지난 접수 이어 보기 ----------
rep("if (QS.roomId !== ctx.roomId) { QS.roomId = ctx.roomId; resetQS(); QS.lang = 'ko'; QS.pendingLast = LS.get('rc-last-' + ctx.roomId); }",
    "if (QS.roomId !== ctx.roomId) { QS.roomId = ctx.roomId; resetQS(); QS.lang = 'ko'; QS.pendingLast = LS.get('rc-last-' + ctx.roomId); QS.plAt = Date.now(); if (QS.pendingLast) trackTicket(QS.pendingLast); }", 1)
rep("""    if (QS.step === 'home' && QS.pendingLast && DATA_READY) {
      const t = tById(QS.pendingLast); QS.pendingLast = null;
      if (t && (isOpen(t) || (t.status === 'done' && Date.now() - t.doneAt < 30 * M))) { QS.res = { tid: t.id, dup: false }; QS.step = 'sent'; }
    }""", """    if (QS.step === 'home' && QS.pendingLast && DATA_READY) {
      const t = tById(QS.pendingLast);
      if (t) { QS.pendingLast = null; if (isOpen(t) || (t.status === 'done' && Date.now() - t.doneAt < 30 * M)) { QS.res = { tid: t.id, dup: false }; QS.step = 'sent'; } }
      else if (Date.now() - (QS.plAt || 0) > 6000) QS.pendingLast = null;
    }""", 1)
rep("      LS.set('rc-last-' + ctx.roomId, r.id);\n      if (QS.purl",
    "      LS.set('rc-last-' + ctx.roomId, r.id); trackTicket(r.id);\n      if (QS.purl", 1)

# ---------- 5. 문구 ----------
rep('<small class="sk-url mono">시연용 · 로그인한 휴대폰에서만 열림</small>', '<small class="sk-url mono">${esc(BASE_URL.replace(/^https:\\/\\//, \'\').replace(/\\/$/, \'\'))}</small>', 1)
rep('<p class="hint" style="margin:0">지금은 시연판이라 이 아티팩트를 만든 계정으로 로그인한 휴대폰에서만 열립니다. 공개 주소로 옮기면 누구 휴대폰이든 열립니다.</p>',
    '<p class="hint" style="margin:0">누구 휴대폰이든 카메라로 찍으면 바로 열립니다. 화면의 QR을 찍어 확인해 보세요.</p>', 1)
rep('찍으면 담당자 앱이 휴대폰 화면 가득 열립니다. 위쪽에서 담당자 이름을 고르고 「알림음 켜기」를 누르세요.',
    '찍으면 담당자 앱이 휴대폰 화면 가득 열립니다. 처음 한 번 Google 로그인 → 위쪽에서 담당자 이름을 고르고 「알림음 켜기」를 누르세요.', 1)
rep("${STORE === 'on' ? '접수 기록은 이 아티팩트 저장소에 쌓여 모든 기기가 같이 봅니다.' : '저장소에 연결되지 않아 이 창에서만 보이는 예시 자료입니다.'}",
    "접수 기록은 Firebase(space-restroom)에 쌓여 모든 기기가 같이 봅니다.", 1)
rep("if (s) s.textContent = STORE === 'on' ? '· 저장소 연결됨 (모든 기기 공유)' : STORE === 'wait' ? '· 저장소 연결 중…' : '· 저장소 없음 — 이 창을 닫으면 사라집니다';",
    "if (s) s.textContent = STORE === 'on' ? '· 저장됨 (Firebase · 모든 기기 공유)' : '· 연결 중…';", 1)

# 설정: 로그인 허용 담당자
rep("""    <section class="card"><h3>시연 자료</h3>""", """    <section class="card"><h3>담당자 로그인 허용</h3><p class="hint" style="margin:0 0 10px">여기 등록한 Google 계정만 담당자 앱에 들어올 수 있습니다. 관리자 계정은 따로 등록하지 않아도 됩니다.</p>
      <ul class="acl">${STAFF_EMAILS.length ? STAFF_EMAILS.map(e => `<li><span class="mono">${esc(e)}</span><button type="button" class="b danger" data-act="aclDel" data-email="${esc(e)}">빼기</button></li>`).join('') : '<li class="hint">아직 없습니다</li>'}</ul>
      <form class="add-issue" id="aclAdd"><input type="email" id="aclEmail" placeholder="담당자 Google 이메일" required aria-label="담당자 이메일"><button type="submit" class="b primary">추가</button></form></section>
    <section class="card"><h3>시연 자료</h3>""", 1)
rep("el.onsubmit = e => { e.preventDefault(); if (e.target.id === 'addIssue') addIssue(); };",
    "el.onsubmit = e => { e.preventDefault(); if (e.target.id === 'addIssue') addIssue(); else if (e.target.id === 'aclAdd') aclAdd(); };", 1)
rep("  else if (act === 'demoFill') demoFill();",
    "  else if (act === 'demoFill') demoFill();\n  else if (act === 'aclDel') { const em = b.dataset.email; if (await askConfirm(em + ' 계정의 담당자 로그인을 막을까요?', '빼기')) { try { await DB.doc('staff/' + em).delete(); } catch (err) { toast('빼지 못했습니다 (' + errCode(err) + ')'); } } }", 1)
rep("function addIssue() {", """async function aclAdd() {
  const em = ($('#aclEmail').value || '').trim().toLowerCase();
  if (!/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(em)) { toast('이메일 형식을 확인해 주세요'); return; }
  try { await DB.doc('staff/' + em).set({ at: Date.now(), by: AUTH.email }); toast(em + ' 계정을 담당자로 등록했습니다'); } catch (e) { toast('등록하지 못했습니다 (' + errCode(e) + ')'); }
}
function addIssue() {""", 1)

# 시연 자료 지우기: 사진 문서도
rep("""        if (ASSETS) for (const p of [t.photo, t.afterPhoto]) { if (p && p.file) { try { await ASSETS.delete(p.file); } catch (e) { /* 무시 */ } } }""",
    """        for (const p of [t.photo, t.afterPhoto]) { if (p && p.pid) { try { await DB.doc('photos/' + p.pid).delete(); } catch (e) { /* 무시 */ } } }""", 1)

# ---------- 6. 화면 메모: 캡처는 noteShots 문서 ----------
rep("""    let file = null;
    if (ASSETS) { try { const r = await ASSETS.upload(s.blob, { type: s.mime }); file = r.id; } catch (e) { /* 원본은 이 창에만 */ } }
    if (!file) LOCALSHOT.set(s.at + s.name, s.url);
    shots.push({ file, name: s.name, mime: s.mime, kind: s.kind, bytes: s.bytes, at: s.at, w: s.w, h: s.h, thumb: s.thumb });""",
    """    let sid = null;
    try {
      const img = await loadImg(s.url);
      const r = await toJpegData(img, 4096, 900000);
      sid = 's' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
      await DB.doc('noteShots/' + sid).set({ data: r.data, w: r.w, h: r.h, ow: r.ow, oh: r.oh, name: s.name, at: s.at });
      SHOT_CACHE[sid] = r.data;
    } catch (e) { sid = null; LOCALSHOT.set(s.at + s.name, s.url); }
    shots.push({ sid, name: s.name, mime: 'image/jpeg', kind: s.kind, bytes: s.bytes, at: s.at, w: s.w, h: s.h, thumb: s.thumb });""", 1)
rep("toast(shots.some(s => !s.file) && DB ? '메모를 저장했습니다. 캡처 원본은 이 창에만 남았습니다.' : '화면 메모를 저장했습니다');",
    "toast(shots.some(s => !s.sid) ? '메모를 저장했습니다. 캡처 일부는 이 창에만 남았습니다.' : '화면 메모를 저장했습니다');", 1)
rep("const shotSrc = s => s.file ? '/_blob/' + s.file : (LOCALSHOT.get(s.at + s.name) || s.thumb || '');",
    """const SHOT_CACHE = {};
function loadShot(sid) { if (!sid || SHOT_CACHE[sid] !== undefined) return; SHOT_CACHE[sid] = ''; DB.doc('noteShots/' + sid).get().then(d => { if (d.exists) { SHOT_CACHE[sid] = d.data().data; drawMemoList(); } }).catch(() => {}); }
const shotSrc = s => { if (s.sid) { if (SHOT_CACHE[s.sid]) return SHOT_CACHE[s.sid]; loadShot(s.sid); return s.thumb || ''; } return LOCALSHOT.get(s.at + s.name) || s.thumb || ''; };""", 1)
rep("""      if (ASSETS) for (const s of (n.shots || [])) { if (s.file) { try { await ASSETS.delete(s.file); } catch (err) { /* 무시 */ } } }""",
    """      for (const s of (n.shots || [])) { if (s.sid) { try { await DB.doc('noteShots/' + s.sid).delete(); } catch (err) { /* 무시 */ } } }""", 1)
rep("""  const data = JSON.stringify({ exported_at: new Date().toISOString(), build: BUILD, ui, notes: NOTES }, null, 2);
  if (!DL) { toast('이 보기에서는 파일 저장이 안 됩니다. 메모는 Claude가 저장소에서 바로 읽습니다.'); return; }""",
    """  toast('캡처까지 모으는 중…');
  const shots = {};
  for (const n of NOTES) for (const s of (n.shots || [])) { if (s.sid && !shots[s.sid]) { try { const d = await DB.doc('noteShots/' + s.sid).get(); if (d.exists) shots[s.sid] = d.data().data; } catch (e) { /* 무시 */ } } }
  const data = JSON.stringify({ exported_at: new Date().toISOString(), build: BUILD, ui, notes: NOTES, shots }, null, 2);""", 1)

# ---------- 7. 권한별 화면 ----------
rep("""  document.body.classList.toggle('fullmode', !!S.full);
  $('#fab').hidden = !S.full;
  renderRoles();
  if (S.full === 'customer') { st.innerHTML = '<div class="full" id="fullC"></div>'; mountQR($('#fullC'), { roomId: S.fullRoom, full: true }); }
  else if (S.full === 'staff') { st.innerHTML = '<div class="full" id="fullS"></div>'; mountStaff($('#fullS'), { full: true }); }
  else if (S.view === 'overview') viewOverview(st);""",
    """  document.body.classList.toggle('fullmode', !!S.full);
  applyRoleUI();
  const isAdmin = AUTH.role === 'admin', isStaffish = isAdmin || AUTH.role === 'staff';
  if (S.full === 'customer') { $('#roles').innerHTML = ''; st.innerHTML = '<div class="full" id="fullC"></div>'; mountQR($('#fullC'), { roomId: S.fullRoom, full: true }); }
  else if (S.full === 'staff') { $('#roles').innerHTML = ''; if (isStaffish) { st.innerHTML = '<div class="full" id="fullS"></div>'; mountStaff($('#fullS'), { full: true }); } else st.innerHTML = `<div class="full">${gateHTML('staff')}</div>`; }
  else if (!isAdmin) { $('#roles').innerHTML = ''; st.innerHTML = gateHTML('admin'); }
  else if (renderRoles(), S.view === 'overview') viewOverview(st);""", 1)

auth = r'''
/* ================= 로그인 · 권한 ================= */
function gateHTML(kind) {
  const u = AUTH.user, google = u && !u.isAnonymous;
  if (!AUTH.ready) return '<div class="gate"><p class="loading">확인하는 중…</p></div>';
  const title = kind === 'admin' ? '관리자 로그인' : '담당자 로그인';
  const denied = google ? `<p class="gate-bad">${esc(u.email || '')} 계정은 ${kind === 'admin' ? '관리자' : '담당자'}로 등록돼 있지 않습니다.${kind === 'staff' ? ' 관리자에게 이 이메일을 알려 주세요.' : ''}</p>` : '';
  return `<div class="gate"><div class="card gate-card"><div class="brand"><span class="logo">SPACE</span><div style="text-align:left"><b>화장실 불편접수</b><small>판 ${BUILD}</small></div></div><h2>${title}</h2><p class="hint" style="margin:0">등록된 Google 계정으로 로그인합니다.</p>${denied}<button type="button" class="b primary gate-btn" data-act="login">Google로 로그인</button>${google ? '<button type="button" class="b" data-act="logout">다른 계정으로</button>' : ''}</div></div>`;
}
function applyRoleUI() {
  const admin = AUTH.role === 'admin';
  const sw = $('#editToggle').closest('label'); if (sw) sw.hidden = !admin;
  if (!admin && S.editing) setEditing(false);
  $('#fab').hidden = !(S.full && admin);
  const a = $('#acct'), u = AUTH.user;
  if (a) a.innerHTML = u && !u.isAnonymous ? `<span title="${esc(u.email || '')}">${esc(u.email || '')}</span><button type="button" class="b" data-act="logout">로그아웃</button>` : '';
}
async function doLogin() {
  const p = new firebase.auth.GoogleAuthProvider();
  p.setCustomParameters({ prompt: 'select_account' });
  try { await AUTHX.signInWithPopup(p); }
  catch (e) {
    const c = e && e.code;
    if (c === 'auth/popup-blocked' || c === 'auth/operation-not-supported-in-this-environment') { try { await AUTHX.signInWithRedirect(p); } catch (e2) { toast('로그인하지 못했습니다 (' + errCode(e2) + ')'); } }
    else if (c !== 'auth/popup-closed-by-user' && c !== 'auth/cancelled-popup-request') toast('로그인하지 못했습니다 (' + errCode(e) + ')');
  }
}
async function doLogout() { try { await AUTHX.signOut(); } catch (e) { /* 무시 */ } }
document.addEventListener('click', e => {
  const b = e.target.closest('[data-act="login"],[data-act="logout"]'); if (!b) return;
  e.preventDefault(); e.stopPropagation();
  if (b.dataset.act === 'login') doLogin(); else doLogout();
}, true);

let UNSUBS = [];
const TRACKED = {}, TRACK_UNSUB = {};
let CUST_MERGE = null;
let STAFF_EMAILS = [];
function unsubAll() { UNSUBS.forEach(u => { try { u(); } catch (e) { /* 무시 */ } }); UNSUBS = []; Object.keys(TRACK_UNSUB).forEach(k => delete TRACK_UNSUB[k]); CUST_MERGE = null; }
function trackTicket(id) {
  if (!id || TRACK_UNSUB[id] || !AUTH.user || AUTH.role === 'admin' || AUTH.role === 'staff') return;
  TRACK_UNSUB[id] = DB.doc('tickets/' + id).onSnapshot(s => { if (s.exists) TRACKED[id] = s.data(); else delete TRACKED[id]; if (CUST_MERGE) CUST_MERGE(); }, () => {});
  UNSUBS.push(TRACK_UNSUB[id]);
}
function startSubs() {
  unsubAll(); DATA_READY = false; TICKETS = [];
  UNSUBS.push(DB.doc('config/ops').onSnapshot(s => { applyOps(s.exists ? s.data() : null); dispatch([]); if (S.view === 'admin' && AS.sub === 'settings' && AS.el && !S.full) drawAdmMain(); }, () => {}));
  UNSUBS.push(DB.doc('config/ui').onSnapshot(s => {
    if (uiSaving || uiDirty || (s.metadata && s.metadata.hasPendingWrites)) return;
    const next = normUI(s.exists ? s.data() : null);
    if (JSON.stringify(next) !== JSON.stringify(ui)) { ui = next; rerender(); }
  }, () => {}));
  if (AUTH.role === 'admin' || AUTH.role === 'staff') {
    UNSUBS.push(DB.collection('tickets').orderBy('createdAt', 'desc').limit(600).onSnapshot(q => {
      const next = q.docs.map(d => d.data());
      const ev = DATA_READY ? diffEvents(TICKETS, next) : [];
      TICKETS = next; DATA_READY = true; dispatch(ev);
    }, e => toast('접수 기록을 불러오지 못했습니다 (' + errCode(e) + ')')));
    UNSUBS.push(DB.collection('feedback').onSnapshot(q => {
      const f = {}, day = kstDate();
      q.docs.forEach(d => { const x = d.data(); if (x.day === day) f[x.roomId] = x.n || 0; });
      FEEDBACK = f; dispatch([]);
    }, () => {}));
    if (AUTH.role === 'admin') {
      UNSUBS.push(DB.collection('notes').orderBy('at', 'desc').limit(500).onSnapshot(q => { NOTES = q.docs.map(d => Object.assign({}, d.data(), { id: d.id })); updateEditbar(); drawMemoList(); }, () => {}));
      UNSUBS.push(DB.collection('staff').onSnapshot(q => { STAFF_EMAILS = q.docs.map(d => d.id).sort(); if (S.view === 'admin' && AS.sub === 'settings' && AS.el && !S.full) drawAdmMain(); }, () => {}));
    }
  } else {
    const parts = { new: [], going: [] }, got = { new: false, going: false };
    CUST_MERGE = () => {
      if (!got.new || !got.going) return;
      const m = new Map();
      parts.new.concat(parts.going).forEach(t => m.set(t.id, t));
      Object.values(TRACKED).forEach(t => m.set(t.id, t));
      const next = Array.from(m.values());
      const ev = DATA_READY ? diffEvents(TICKETS, next) : [];
      TICKETS = next; DATA_READY = true; dispatch(ev);
    };
    ['new', 'going'].forEach(stt => UNSUBS.push(DB.collection('tickets').where('status', '==', stt).onSnapshot(q => { parts[stt] = q.docs.map(d => d.data()); got[stt] = true; CUST_MERGE(); }, e => { got[stt] = true; if (CUST_MERGE) CUST_MERGE(); })));
    if (S.fullRoom) { const last = LS.get('rc-last-' + S.fullRoom); if (last) trackTicket(last); }
    if (QS.res && QS.res.tid) trackTicket(QS.res.tid);
  }
  STORE = 'on'; updateEditbar();
}
AUTHX.getRedirectResult().catch(e => { if (e && e.code) toast('로그인하지 못했습니다 (' + e.code + ')'); });
AUTHX.onAuthStateChanged(async u => {
  AUTH.user = u; AUTH.email = (u && u.email || '').toLowerCase();
  let role = 'none';
  if (u) {
    if (u.isAnonymous) role = 'customer';
    else if (!u.emailVerified) role = 'denied';
    else {
      try { await DB.collection('notes').limit(1).get(); role = 'admin'; }
      catch (e) { try { const d = await DB.doc('staff/' + AUTH.email).get(); role = d.exists ? 'staff' : 'denied'; } catch (e2) { role = 'denied'; } }
    }
  }
  AUTH.role = role; AUTH.ready = true;
  if (u) { const w = AUTH_WAIT; AUTH_WAIT = []; w.forEach(f => f()); }
  if (!u) {
    unsubAll(); TICKETS = []; DATA_READY = false;
    if (S.full === 'customer') { try { await AUTHX.signInAnonymously(); } catch (e) { toast('접속하지 못했습니다. 새로 고쳐 주세요. (' + errCode(e) + ')'); } return; }
  } else startSubs();
  render();
});
'''
rep("/* ================= 이벤트 연결 ================= */", auth + "\n/* ================= 이벤트 연결 ================= */", 1)

# 라우팅: 고객 화면으로 들어오면 익명 로그인
rep("  closeDetail();\n  render();\n}\nfunction notesHTML",
    "  closeDetail();\n  render();\n  if (S.full === 'customer' && AUTH.ready && !AUTH.user) AUTHX.signInAnonymously().catch(() => {});\n}\nfunction notesHTML", 1)
rep("$('#fab').onclick = () => setEditing(!S.editing);", "$('#fab').onclick = () => { if (AUTH.role === 'admin') setEditing(!S.editing); };", 1)
rep("  if (v && !e.target.closest('.pen')) { S.view = v.dataset.view; S.full = null; closeDetail(); render(); window.scrollTo(0, 0); }",
    "  if (v && !e.target.closest('.pen')) { S.view = v.dataset.view; S.full = null; if (location.hash) history.replaceState(null, '', location.pathname); closeDetail(); render(); window.scrollTo(0, 0); }", 1)

# ---------- 8. 시작부: 아티팩트 저장소 연결 코드 제거 ----------
i = s.index('(async function initStore() {')
j = s.index('})();\n})();', i)
s = s[:i] + s[j + len('})();\n'):]

open('public/index.html', 'w', encoding='utf-8').write(s)
# 문법 확인용 추출
a = s.index('<script>\n(function () {'); b = s.index('</script>', a)
open('public/app_check.js', 'w', encoding='utf-8').write(s[a + 8:b])
print('ok', len(s.encode()))
