# 만드는 법

`restroom-care.html` 은 claude.ai 시연판(아티팩트) 원본이다. 공개판 `index.html` 은 여기서 자동 변환해 만든다 — 공개판을 직접 고치지 말고 원본을 고친 뒤 다시 만든다.

```
cd build
mkdir -p public
python3 make_public.py "$(cat firebase_config.json)"
node --check public/app_check.js      # 문법 확인
cp public/index.html ../index.html
```

- Firestore 보안 규칙 원본은 이 저장소에 두지 않는다(관리자 이메일 포함) — Drive `화장실 불편접수 개발` 폴더의 규칙 백업 파일.
