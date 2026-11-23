"""在 Lucide 全套圖示（約 2,100 個）裡找圖示名稱。用英文關鍵字，可以一次給好幾個：
  python3 -I <skill>/scripts/icon_search.py coffee "time" deadline
每個關鍵字列出最符合的 8 個名稱：名稱本身含關鍵字的排前面，再來是標籤含關鍵字的。
找到的名稱直接填進 spec.json 的 icon、title_icon。"""
import json, os, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "quick", "lucide.json"), encoding="utf-8"))
if len(sys.argv) < 2:
    sys.exit(__doc__)
for q in sys.argv[1:]:
    q = q.lower().strip()
    hits = []
    for n in DATA["icons"]:
        tags = DATA["tags"].get(n, [])
        if " " in q:  # 多個字：每個字都要出現在名稱或標籤裡；連起來剛好是名稱的排最前面
            hay = n + " " + " ".join(tags)
            if q.replace(" ", "") == n.replace("-", "") or q.replace(" ", "-") == n:
                hits.append((0, len(n), n))
            elif all(w in hay for w in q.split()):
                hits.append((3, len(n), n))
            continue
        if n == q:
            s = 0
        elif q in n.split("-"):
            s = 1
        elif q in n:
            s = 2
        elif q in tags:
            s = 3
        elif any(q in t for t in tags):
            s = 4
        else:
            continue
        hits.append((s, len(n), n))
    hits.sort()
    print(f"{q}：" + ("、".join(n for _, _, n in hits[:8]) if hits else "找不到，換個英文說法（例如同義字、具體物品）"))
