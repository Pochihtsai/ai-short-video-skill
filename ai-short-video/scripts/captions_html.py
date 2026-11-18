"""把 make_captions.py 產生的 captions.json 放進 index.html 的字幕區。用法：
  python -I captions_html.py captions.json index.html [最後一組延長到第幾秒]
index.html 的 #captions 裡要有兩行標記：<!-- captions:begin --> 和 <!-- captions:end -->（templates 都有）。
腳本只換掉兩行標記中間的內容，可以重複執行。每組字幕寫成 <div class="cap" data-s="起" data-e="訖">，
出現和消失交給 templates 裡的字幕迴圈。直接用 UTF-8 寫回 index.html，不要用 > 轉存。
最後一組字幕想停到片尾時，給第三個參數，例如片長 45 秒就給 44.6。"""
import html, json, re, sys
if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文和全形符號會出錯；統一用 UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

caps = json.load(open(sys.argv[1], encoding="utf-8"))
path = sys.argv[2]
if len(sys.argv) > 3:
    caps[-1]["end"] = float(sys.argv[3])

src = open(path, encoding="utf-8").read()
m = re.search(r"([ \t]*)<!-- captions:begin -->.*?<!-- captions:end -->", src, re.S)
if not m:
    sys.exit("index.html 裡找不到 <!-- captions:begin --> 和 <!-- captions:end -->：先把這兩行標記放進 #captions 裡")
ind = m.group(1)
rows = "".join(f'\n{ind}<div class="cap" data-s="{c["start"]}" data-e="{c["end"]}"><span>{html.escape(c["text"])}</span></div>' for c in caps)
block = f"{ind}<!-- captions:begin -->{rows}\n{ind}<!-- captions:end -->"
open(path, "w", encoding="utf-8").write(src[:m.start()] + block + src[m.end():])
print(f"已寫入 {len(caps)} 組字幕，{caps[0]['start']}–{caps[-1]['end']} 秒")
