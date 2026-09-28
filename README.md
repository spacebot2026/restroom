# restroom

화장실 불편접수 시연판 — (주)스페이스

- 고객: 화장실 QR → `https://spacebot2026.github.io/restroom/#r-<칸 번호>` (예: `#r-3f-w1`) · 로그인 없이 익명 접수
- 담당자: `#staff` · 관리자: 첫 화면 — 등록된 Google 계정으로 로그인
- 데이터: Firebase `space-restroom` (Firestore, 서울). 누가 무엇을 읽고 쓰는지는 Firestore 보안 규칙이 정한다.
- 이 저장소에는 비밀 값이 없다. `index.html` 의 Firebase 웹 설정(apiKey 등)은 브라우저에 공개되도록 만들어진 식별값이다.
