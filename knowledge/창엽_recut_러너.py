"""창엽 쇼츠 완결 아크 재컷 (2026-07-29 형 지시: 내용 해결=완결, 45초는 결과).
각 아이템 = 한 개념이 셋업→설명→시연→결과까지 해결되는 아크. 자막=diar_p 전사 그대로.
사용: python3 recut.py [name1 name2 ...]  (인자 없으면 전체)
"""
import sys, json
sys.path.insert(0, "/home/user/-")
import shorts.creator_short as CS

SRC = "/tmp/claude-0/-home-user--/4c303924-cd2a-54ae-bace-87654ed6e323/scratchpad/cy2"
OUT = SRC + "/recut"

# (name, clip, A, B, yellow, white)  — clip = hq_<clip>.mp4, diar = diar_<clip>p.json
# 제목 = 메인키워드 하나(2026-07-30 형). 컷 = 계기(질문/커트중)→키워드 설명→마무리(완결 아크).
ARCS = [
    # ── 웻컷(베이스커트) ──
    ("01_45도베이스",   "8999", 439.1, 558.7, "45도 베이스",   ""),
    ("02_오버디렉션",   "8999", 560.0, 642.1, "오버디렉션",     ""),
    ("03_도해도함정",   "9004",  81.9, 203.7, "도해도의 함정",  ""),
    ("04_웨이트라인",   "9004", 204.3, 331.4, "웨이트라인",     ""),
    ("05_플로우",       "9004", 332.0, 394.5, "플로우",         ""),
    ("06_레이어볼륨",   "9000", 130.5, 198.8, "레이어 볼륨",    ""),
    ("07_라운드레이어", "9000",   1.9, 128.4, "라운드 레이어",  ""),
    # ── 질감처리 ── (08=계기 질문 "부드러움 만들려면?"부터)
    ("08_질감처리",     "9005",  29.4, 108.0, "질감처리",       ""),
    ("09_모질",         "9006",   0.1, 103.2, "모질",           ""),
    ("10_명암",         "9006", 278.3, 327.6, "명암",           ""),
    ("11_시스루",       "9006", 348.0, 423.7, "시스루",         ""),
    ("12_슬라이싱",     "9006", 458.5, 538.8, "슬라이싱",       ""),
    ("13_하이레이어",   "9006", 695.6, 773.8, "하이레이어",     ""),
    # ── 마무리·성장 ──
    ("14_질감양감",     "9007",   2.7,  69.8, "질감 vs 양감",   ""),
    ("15_마무리스텝",   "9007", 168.7, 261.7, "마무리 스텝",    ""),
    ("16_성장베이직",   "9007", 456.0, 603.8, "베이직",         ""),
]


def item(name, clip, A, B, yellow, white):
    cues3, tea = CS.cues_from_diar(f"{SRC}/diar_{clip}p.json", A, B, teacher_only=False)
    cues4 = [(s, e, t, None) for (s, e, t) in cues3]
    return dict(clip=f"hq_{clip}", A=A, B=B, yellow=yellow, white=white,
                name=name, cues=cues4)


if __name__ == "__main__":
    pick = set(sys.argv[1:])
    items = [item(*a) for a in ARCS if not pick or a[0] in pick]
    print(f"렌더 {len(items)}편:", [i['name'] for i in items], flush=True)
    CS.render_batch(items, SRC, OUT)
    print("DONE", flush=True)
