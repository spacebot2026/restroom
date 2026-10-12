# restroom

화장실 불편접수 시연판 — (주)스페이스

- 고객: 화장실 QR → `https://spacebot2026.github.io/restroom/#r-<칸 번호>` (예: `#r-3f-w1`) · 로그인 없이 익명 접수
- 담당자: `#staff` · 관리자: 첫 화면 — 등록된 Google 계정으로 로그인
- 데이터: Firebase `space-restroom` (Firestore, 서울). 누가 무엇을 읽고 쓰는지는 Firestore 보안 규칙이 정한다.
- 이 저장소에는 비밀 값이 없다. `index.html` 의 Firebase 웹 설정(apiKey 등)은 브라우저에 공개되도록 만들어진 식별값이다.
- 글꼴: [Pretendard](https://github.com/orioncactus/pretendard) v1.3.9 (SIL Open Font License 1.1) 를 `fonts/` 에서 직접 내려준다(외부 글꼴 서버 없음). 필요한 글자 조각만 받는 동적 서브셋이라 첫 화면에 쓰는 양은 수백 KB 안팎. 라이선스 전문은 `fonts/LICENSE-Pretendard.txt`.
- 담당자 로그인: Google 계정 또는 ID/비밀번호(Firebase 이메일/비밀번호 방식, 가짜 주소 `<ID>@staff.space-dust.com`). 쓰려면 Firebase 콘솔에서 「이메일/비밀번호」 로그인 방법을 켜고 규칙 3판을 게시해야 한다.
