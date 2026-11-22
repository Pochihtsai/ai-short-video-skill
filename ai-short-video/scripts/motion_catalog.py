"""查 Motion Prompt（MIT 授權的動態效果目錄，https://showheyohtaki.github.io/motion-prompt/）。用法：
  python -I motion_catalog.py search 關鍵字 [關鍵字…] [--all]   找效果，印出編號、名稱、一句說明、示範連結
  python -I motion_catalog.py get 編號 [--code]                印出那個效果的規格（加 --code 連程式碼一起印）
關鍵字用英文，例如 stagger、counter、line-draw、zoom、wipe、flow。任一個關鍵字對到標籤、名稱或說明就列出，最多 12 筆；多個字寫在同一個引號裡也會拆開來找。
預設只找做影片用得到的五組（motion、motion2、camera、camera2、diagram）；--all 連網頁互動、介面、照片、畫風也找。
只讀需要的幾行，不用整份目錄讀進對話。需要網路。"""
import sys, urllib.request
if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文和全形符號會出錯；統一用 UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://showheyohtaki.github.io/motion-prompt"
VIDEO_PACKS = {"motion", "motion2", "camera", "camera2", "diagram"}

def fetch(path):
    with urllib.request.urlopen(f"{BASE}/api/v1/{path}", timeout=30) as r:
        return r.read().decode("utf-8")

args = [a for a in sys.argv[1:] if not a.startswith("--")]
flags = {a for a in sys.argv[1:] if a.startswith("--")}
if len(args) < 2 or args[0] not in ("search", "get"):
    sys.exit(__doc__)

if args[0] == "search":
    kws = [w.lower() for a in args[1:] for w in a.split()]  # 包在同一個引號或 shell 變數裡的多個字也拆開（2026-11-22 四個分身踩過）
    hits = []
    for line in fetch("en/catalog.tsv").splitlines():
        if line.startswith("#"):
            continue
        c = line.split("\t")
        if len(c) < 6 or c[0] == "id":
            continue
        eid, pack, cat, title, tags, summary = c[:6]
        if "--all" not in flags and pack not in VIDEO_PACKS:
            continue
        text = f"{title} {tags} {summary} {cat}".lower()
        if any(k in text for k in kws):
            hits.append(f"#{eid}　{title}（{pack}／{cat}）\n　　{summary}\n　　示範：{BASE}/#{eid}")
    print("\n".join(hits[:12]) if hits else "沒有找到：換個英文關鍵字，或加 --all 擴大範圍")
    if len(hits) > 12:
        print(f"（共 {len(hits)} 筆，只列前 12 筆；關鍵字再具體一點）")
else:
    eid = args[1].lstrip("#").zfill(3)
    text = fetch(f"en/e/{eid}.txt")
    if "--code" not in flags:
        text = text.split("// Element code starts here.")[0].rstrip()
    print(text)
