"""依台詞標點和逐詞時間切字幕。用法：
  python -I make_captions.py script.txt words.json <zh|en> <v|h> captions.json [影片總秒數]
輸出 JSON：[{"start": 秒, "end": 秒, "text": "字幕"}]，直接用 UTF-8 寫進 captions.json，螢幕上也會印一份。
不要用 > 轉存：Windows 會改用 cp950 或 UTF-16 存檔，字幕會變亂碼。
規則：句號、冒號、分號必斷；一句裡優先在逗號處分組，分成最少組、而且最長那組盡量短；
逗號之間的一段本身就超過上限時，才在詞與詞之間平均切，不留孤字。中文用「視覺寬度」計算（英文字母約半個中文字）；
字幕文字取台詞原文（保留中英文之間的空格），中文逗號換成空格、句尾標點去掉。"""
import json, math, re, sys
if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文和全形符號會出錯；統一用 UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

script = open(sys.argv[1], encoding="utf-8").read().strip()
words = json.load(open(sys.argv[2], encoding="utf-8"))
lang, ori = sys.argv[3], sys.argv[4]
out_path = sys.argv[5]
total = float(sys.argv[6]) if len(sys.argv) > 6 else None
cap_max = {("zh", "v"): 12, ("zh", "h"): 16, ("en", "v"): 28, ("en", "h"): 42}[(lang, ori)]

pos = 0
for w in words:
    i = script.find(w["w"], pos)
    if i < 0:
        sys.exit(f"台詞裡找不到「{w['w']}」，請確認 words.json 是用同一份 script.txt 產生的")
    w["a"], w["b"] = i, i + len(w["w"])
    pos = w["b"]

HARD, SOFT = set("。！？.!?：:；;"), set("，、,—")
text_of = lambda idx: script[words[idx[0]]["a"]:words[idx[-1]]["b"]]

def width(t):  # 中文：中文字算 1、英文字母數字算 0.55、空白算 0.3；英文：直接算字元數
    if lang != "zh":
        return len(t)
    return sum(1 if ord(c) > 0x2E80 else 0.3 if c == " " else 0.55 for c in t)
W = lambda idx: width(text_of(idx))

def minmax(units, k):  # 把 units 依序分成 k 組，回傳（最長那組的寬度, 分組）
    n, memo = len(units), {}
    def solve(s, parts):
        if parts == 1:
            g = sum(units[s:], [])
            return W(g), [g]
        if (s, parts) not in memo:
            best = (10**9, None)
            for e in range(s + 1, n - parts + 2):
                m, rest = solve(e, parts - 1)
                g = sum(units[s:e], [])
                cand = max(W(g), m)
                if cand < best[0]:
                    best = (cand, [g] + rest)
            memo[(s, parts)] = best
        return memo[(s, parts)]
    return solve(0, k)

phrases, cur = [], [0]
for i in range(len(words) - 1):
    gap = script[words[i]["b"]:words[i + 1]["a"]]
    if any(c in HARD | SOFT for c in gap):
        phrases.append((cur, any(c in HARD for c in gap)))
        cur = []
    cur.append(i + 1)
phrases.append((cur, True))

def balanced(idx):  # 一段太長：在詞與詞之間切成最少段，最長那段盡量短
    units = [[j] for j in idx]
    for k in range(math.ceil(W(idx) / cap_max), len(idx) + 1):
        m, g = minmax(units, k)
        if m <= cap_max:
            return g
    return units

groups, sentence = [], []
for idx, hard_end in phrases:
    sentence.extend(balanced(idx) if W(idx) > cap_max else [idx])
    if hard_end:
        for k in range(1, len(sentence) + 1):
            m, g = minmax(sentence, k)
            if m <= cap_max or k == len(sentence):
                groups.extend(g)
                break
        sentence = []

def clean(t):
    if lang == "zh":
        t = re.sub(r"[，、；：]", " ", t)
    return t.strip(" 。.,，")

caps = []
for gi, g in enumerate(groups):
    last = words[g[-1]]
    end = words[groups[gi + 1][0]]["t"] if gi + 1 < len(groups) else last["t"] + last["d"] + 0.6
    if total:
        end = min(end, total)
    caps.append({"start": round(words[g[0]]["t"], 2), "end": round(end, 2), "text": clean(text_of(g))})
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(caps, f, ensure_ascii=False, indent=1)
print(json.dumps(caps, ensure_ascii=False, indent=1))
