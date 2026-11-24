"""在圖示庫裡找圖示名稱。用英文關鍵字，可以一次給好幾個：
  python3 -I <skill>/scripts/icon_search.py coffee "time" deadline
  python3 -I <skill>/scripts/icon_search.py --set phosphor coffee deadline
套名：lucide（預設，約 2,100 個）、tabler（約 4,900 個）、phosphor（約 1,500 個，phosphor-duotone、phosphor-fill 名稱相同）、material（約 3,500 個）。
每個關鍵字列出最符合的 8 個名稱：名稱本身含關鍵字的排前面，再來是標籤含關鍵字的。material 沒有標籤，只能找名稱。
找到的名稱直接填進 spec.json 的 icon、title_icon，spec.json 的 icon_set 要填同一套。"""
import json, os, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

args, name = sys.argv[1:], "lucide"
if args[:1] == ["--set"] and len(args) > 1:
    name, args = args[1], args[2:]
if not args:
    sys.exit(__doc__)
f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "quick", ("phosphor" if name.startswith("phosphor") else name) + ".json")
if not os.path.exists(f):
    sys.exit(f"沒有「{name}」這一套")
DATA = json.load(open(f, encoding="utf-8"))
for q in args:
    q = q.lower().strip()
    hits = []
    for n in DATA["icons"]:
        tags = DATA["tags"].get(n, [])
        if " " in q:  # 多個字：每個字都要出現在名稱或標籤裡；連起來剛好是名稱的排最前面
            hay = n.replace("_", " ") + " " + " ".join(tags)
            if q.replace(" ", "") == n.replace("-", "").replace("_", "") or q.replace(" ", "-") == n.replace("_", "-"):
                hits.append((0, len(n), n))
            elif all(w in hay for w in q.split()):
                hits.append((3, len(n), n))
            continue
        if n == q:
            s = 0
        elif q in n.replace("_", "-").split("-"):
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
