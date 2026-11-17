"""找可以商用、可以剪進影片的配樂候選。用法：
  python -I find_music.py openverse "英文關鍵字" [最短秒數] [筆數]
  python -I find_music.py mixkit 標籤 [最短秒數] [筆數]
例：python -I find_music.py openverse "upbeat corporate" 35 8
    python -I find_music.py mixkit corporate 35 8
- Openverse：彙整多個創用 CC 音樂庫的搜尋服務。只列 CC0、公共領域、CC BY、CC BY-SA；
  不用標示的排前面，CC BY-SA（相同方式分享，條款會延伸到整支影片）排最後並標出來。
- Mixkit：免費可商用、不用標示作者，但不能把原始音檔再散布出去。
  標籤用網址上的英文字，例如 corporate、happy、chill、cinematic、ambient、piano、hip-hop；
  標籤頁網址 https://mixkit.co/free-stock-music/tag/<標籤>/，打不開就換標籤。
兩個來源回傳的音檔網址都可以直接下載。"""
import json, re, sys, urllib.parse, urllib.request
if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文和全形符號會出錯；統一用 UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

src, q = sys.argv[1], sys.argv[2]
min_sec = float(sys.argv[3]) if len(sys.argv) > 3 else 0
n = int(sys.argv[4]) if len(sys.argv) > 4 else 8
UA = {"User-Agent": "Mozilla/5.0 (ai-short-video-skill)"}

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode("utf-8")

def iso_sec(d):  # PT2M4S → 124
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d or "")
    return sum(int(x or 0) * k for x, k in zip(m.groups(), (3600, 60, 1))) if m else 0

rows = []
if src == "openverse":
    params = {"q": q, "license_type": "commercial,modification", "category": "music", "page_size": 20}  # 未登入最多 20 筆，超過會回 401
    data = json.loads(get("https://api.openverse.org/v1/audio/?" + urllib.parse.urlencode(params)))
    rank = {"cc0": 0, "pdm": 0, "by": 1, "by-sa": 2}
    for r in sorted(data.get("results", []), key=lambda r: rank.get(r["license"], 3)):
        lic = r["license"]
        rows.append({
            "title": f'{r["title"]} — {r.get("creator") or "作者不明"}',
            "sec": (r.get("duration") or 0) / 1000,
            "lic": f'{lic} {r.get("license_version") or ""}'.strip() + ("（相同方式分享：條款會延伸到整支影片，先告訴使用者）" if lic == "by-sa" else ""),
            "credit": None if lic in ("cc0", "pdm") else r.get("attribution"),
            "url": r["url"], "page": r.get("foreign_landing_url"), "from": r["source"]})
elif src == "mixkit":
    page = f"https://mixkit.co/free-stock-music/tag/{q}/"
    html = get(page)
    def walk(x):
        if isinstance(x, dict):
            if x.get("@type") == "MusicRecording":
                rows.append({"title": x.get("name"), "sec": iso_sec(x.get("duration")), "lic": "Mixkit 免費音樂授權",
                             "credit": None, "url": x.get("url"), "page": page, "from": "mixkit"})
                return
            for v in x.values(): walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try: walk(json.loads(m.group(1)))
        except json.JSONDecodeError: pass
else:
    sys.exit("第一個參數要是 openverse 或 mixkit")

shown = 0
for r in rows:
    if r["sec"] < min_sec:
        continue
    shown += 1
    print(f'{shown}. {r["title"]}')
    print(f'   長度 {r["sec"]:.0f} 秒｜授權 {r["lic"]}｜{"不用標示" if not r["credit"] else "要標示作者"}｜來源 {r["from"]}')
    print(f'   音檔：{r["url"]}')
    print(f'   頁面：{r["page"]}')
    if r["credit"]:
        print(f'   標示文字：{r["credit"]}')
    if shown >= n:
        break
if shown == 0:
    print("沒有找到符合長度的結果：換個關鍵字或標籤，或縮短最短秒數再試")
