# 만화연재방 — 결이 이야기 생성

> **필독: [공통_역량_규약.md](../공통_역량_규약.md)**

## 코드방이 한 작업 (2026-08-14) — 이대로 따라함

### 1. Gemini API 연결
```bash
# secrets/gemini.json에 API 키 저장됨
# 브라우저 자동화로 Google Cloud 결제 활성화까지 완료
```

### 2. 이미지 생성 명령
```bash
# 단일 이미지
python3 scripts/gemini_image.py "프롬프트" output.png

# 6장 만화 (결이 이야기)
python3 scripts/manga_pipeline.py "대본 텍스트" --title "착한곱슬편"

# 파일에서 대본 읽기
python3 scripts/manga_pipeline.py --from-file content/manga/대본.txt --title "제목"

# 생성 후 코워크에 업로드
python3 scripts/manga_pipeline.py "대본" --title "제목" --upload
```

### 3. 결이 캐릭터 시트 (필수 준수)
- **결이**: 크림색 둥근 얼굴 + 오렌지 머리 뭉치
- **보리**: 손님 캐릭터 (매 편 4컷 이상 등장)
- **문제**: 얼굴 없는 사물로 그림 (매듭, 기계 등)
- **팔레트**: 크림 배경 · 브라운 · 오렌지 포인트

### 4. 6장 구조
1. **표지** — 훅 질문 + 결이 배지
2. **문제** — 보리 등장, 고민
3. **오해** — 통념 제시
4. **진실** — 재정의/아하 모먼트
5. **해결** — 변화 보여주기
6. **결론** — 재정의 한 줄

### 5. 품질 체크
- [ ] 결이 생김새 6장 일관성
- [ ] 보리 4컷 이상 등장
- [ ] 광고톤 아님
- [ ] 본문 2줄 이내

---

## 텍스트 먼저 규칙 (2026-08-14 이찬호 지시)

**대본/메시지 확정 전 이미지 생성 금지.**

1. 텍스트 받기 → 키워드/의도 정리
2. 6장 구성 확정 (형 승인)
3. 이미지 생성

---

## 실제 스크립트 위치

- `scripts/gemini_image.py` — 단일 이미지 생성
- `scripts/manga_pipeline.py` — 6장 만화 생성 (결이 캐릭터 시트 내장)
- `secrets/gemini.json` — API 키
