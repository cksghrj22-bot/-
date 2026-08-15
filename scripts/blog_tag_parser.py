#!/usr/bin/env python3
"""블로그 태그 파서 — content/blog/원고/*.txt → 네이버 발행용 구조
태그: [COLOR] [H] [B] [BOLD] [QUOTE] [CENTER] [SMALL] [IMG:NN]
"""
import re, json, sys
from pathlib import Path

TAG = re.compile(r"^\[(H|B|BOLD|POINT|QUOTE|CENTER|SMALL|COLOR|IMG:(\d+))\]\s*(.*)$")

def parse(txt_path: Path) -> dict:
    post = {"title": "", "color": "", "blocks": [], "images": {}}
    cur, buf = None, []

    def flush():
        nonlocal cur, buf
        if cur and buf:
            t = "\n".join(buf).strip()
            if t:
                post["blocks"].append({"type": cur, "text": t})
        cur, buf = None, []

    for line in txt_path.read_text(encoding="utf-8").strip().split("\n"):
        m = TAG.match(line)
        if m:
            flush()
            tag, img, rest = m.group(1), m.group(2), m.group(3).strip()
            if tag == "H":
                if not post["title"]:
                    post["title"] = rest
                elif rest:
                    post["blocks"].append({"type": "heading", "text": rest})
            elif tag == "COLOR":
                post["color"] = rest
            elif tag in ("B", "BOLD", "POINT", "QUOTE", "CENTER", "SMALL"):
                cur = {"B": "body", "BOLD": "bold", "POINT": "point", "QUOTE": "quote",
                       "CENTER": "center", "SMALL": "small"}[tag]
                if rest:
                    buf.append(rest)
            elif img:
                slot = int(img)
                f = None
                for ext in ("png", "jpg", "jpeg"):
                    p = txt_path.parent / f"{img}.{ext}"
                    if p.exists():
                        f = str(p); break
                if f:
                    post["images"][slot] = f
                post["blocks"].append({"type": "image", "slot": slot, "path": f})
        elif cur:
            buf.append(line)
    flush()
    return post

def export(post: dict, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "title.txt").write_text(post["title"], encoding="utf-8")
    (out_dir / "blocks.json").write_text(json.dumps(post["blocks"], ensure_ascii=False, indent=2), encoding="utf-8")
    parts = []
    for b in post["blocks"]:
        if b["type"] == "quote":
            parts.append(f'"{b["text"]}"')
        elif b["type"] == "image":
            continue
        else:
            parts.append(b["text"])
    (out_dir / "body.txt").write_text("\n\n".join(parts), encoding="utf-8")
    counts = {}
    for b in post["blocks"]:
        counts[b["type"]] = counts.get(b["type"], 0) + 1
    meta = {"title": post["title"], "color": post["color"],
            "block_count": len(post["blocks"]), "type_counts": counts,
            "images": post["images"]}
    (out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta

if __name__ == "__main__":
    src = Path(sys.argv[1])
    root = Path(__file__).parent.parent
    out = root / "_publish_jobs/blog_parsed" / src.stem
    m = export(parse(src), out)
    print(json.dumps(m, ensure_ascii=False, indent=2))
    print(f"→ {out}")
