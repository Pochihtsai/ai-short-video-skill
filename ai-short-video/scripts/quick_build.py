"""輕量模式的組片腳本：讀內容表（spec.json）、台詞和逐詞時間，產生整支片的 index.html，
並配好字幕、音效和配樂。用法（在影片資料夾裡執行）：
  python3 -I <skill>/scripts/quick_build.py spec.json
執行前要先有 script.txt、assets/audio/voice.mp3、assets/audio/words.json（用 tts_words.py 產生）。
做完會印出片長和配樂音量；接著跑 check、render 和驗收（見 SKILL.md「輕量模式」）。

spec.json 欄位：
  template     "scene"（每個重點一幕畫面，建議）、"stack"（重點往上疊）或 "big"（大字主角）
  orientation  "h"（橫式 1920×1080）或 "v"（直式 1080×1920）
  style        "glass"（淺色玻璃）、"paper"（紙本編排）、"dark"（深色）
  music        "smile"、"closeup"、"clouds"、"september"
  title        標題，第 0 格就出現。用 *字* 標強調色，用 | 指定換行（標題、重點、結尾句都可以）
  title_icon   主題圖示（選填，建議填）：開場填滿空著的區域，stack 模板結尾再畫一次。"title_motion" 是它的動畫（選填）
  items        3–5 個（big、scene 橫式可到 6 個），每個 {"text": 畫面文字, "cue": 台詞裡的一段字, "icon": 圖示名稱（選填，建議填）,
               "motion": 圖示出場動畫（選填，預設 draw）}
               big 模板另外要 "key"：放大的字或詞（例如 Who、1、快）
               scene 模板另外要 "scene"：這一幕的畫面，欄位和字數上限見本說明最後一段
  ending       結尾句（畫面文字），可用 *字*；"ending_cue" 是台詞裡結尾句開頭的一段字
  lang         "zh" 或 "en"，預設 zh
  icon_set     圖示用哪一套（選填，預設 "lucide"），一支片只用一套："lucide"、"tabler"（線條）、"phosphor"（圓潤線條）、
               "phosphor-duotone"（線條加淡色塊）、"phosphor-fill"（實心）、"material"（圓角線條）
圖示名稱：每一套的名稱不同，用 scripts/icon_search.py --set <套名> 以英文關鍵字找。
motion：draw 畫出來、pop 彈出、drop 掉下來、spin 旋轉、flip 翻牌、slide 滑進、pulse 心跳、wiggle 搖晃。
每個 cue 要一字不差出現在 script.txt 裡，那個重點會在講到這段字時出現。
字太長、重點太多時會直接停下來說明上限，請改內容，不要改模板。字數上限都以「中文字寬」算，英文字母約半個字。

scene 模板每個重點挑一種畫面（"scene" 欄位），主角是固定的六角形笑臉角色：
  icon    大圖示：要 "icon"
  actor   主角＋道具：要 "icon"（道具）；"say" 對白泡泡選填（直式最多 6 字、橫式 9 字）
  split   錯的做法 vs 對的做法：要 "bad": {"icon", "label"}、"good": {"icon", "label"}（label 直式最多 6 字、橫式 9 字）
  tree    分工樹，一個帶頭的分給 2–4 個：要 "branches": ["研究", "寫稿", "查核"]
          每支最多：分 2 支 直式 7 字、橫式 9 字；3 支 5／7 字；4 支 3.5／6 字
  card    清單卡逐項打勾：要 "card_title"、"rows"（2–4 項，可以是字串或 {"text", "cue"}，有 cue 就在講到時出現）
          card_title 和每一項各一行，直式最多 11 字、橫式 14 字
  check   驗收蓋章：做的人交出幾份成果，檢查的人逐張蓋 ✓ 或 ✕；"marks" 選填，用 o、x 寫，2–4 個，預設 "oox"
  number  大數字或大字：要 "key"（最多 2 個中文字或 4–5 個英文字母，例如 3、80%、快），純數字會從 0 跳上去；"icon" 選填
  每一幕的排法由腳本決定，相鄰兩幕不重複：橫式 card、actor、icon、number 用左右分割輪流換邊，其他是字在下方或上方。文字用 | 標出適合斷行的地方，左右分割時照著斷、其他排法忽略
  每一幕那句字（"text"）：直式最多 12 字、橫式 20 字
  結尾句（"ending"）不設上限，字多時自動縮小字級，建議 2 行內"""
import html as _h, json, math, os, re, shutil, subprocess, sys, urllib.request
if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文和全形符號會出錯；統一用 UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
SFX_LIB = os.path.join(os.path.expanduser("~"), ".claude", "skills", "media-use", "audio", "assets", "sfx")

# 固定配樂：Mixkit 免費音樂授權，可商用、不用標示作者；不能把原始音檔另外散布，所以每次照網址下載
MUSIC = {
    "smile": ("https://assets.mixkit.co/music/1076/1076.mp3", 0, "Smile：明亮輕快"),
    "closeup": ("https://assets.mixkit.co/music/1167/1167.mp3", 0, "Close Up：穩重、有節奏"),
    "clouds": ("https://assets.mixkit.co/music/175/175.mp3", 0, "Digital Clouds：科技感"),
    "september": ("https://assets.mixkit.co/music/282/282.mp3", 0, "Sweet September：溫和放鬆"),
}

STYLES = {
    "glass": dict(bg="linear-gradient(180deg, #f6f7f8 0%, #eef1f3 100%)", bgc="#f1f3f4", ink="#22303a", ink2="#46545e",
                  em="#6b5012", fill="#aa8421", on="#ffffff", card="rgba(255,255,255,.86)", edge="1.5px solid rgba(255,255,255,.95)",
                  shadow="inset 0 2px 0 rgba(255,255,255,.9), 0 2px 4px rgba(28,42,52,.05), 0 24px 60px -16px rgba(28,42,52,.18)",
                  cap_bg="rgba(255,255,255,.86)", cap_ink="#22303a", cap_edge="1.5px solid rgba(255,255,255,.95)", radius=28,
                  glow1="rgba(222,164,18,.22)", glow2="rgba(18,128,172,.26)", chip_off="rgba(34,48,58,.08)", chip_off_ink="#46545e", alt="#2a7da1", bad="#d0553f"),
    "paper": dict(bg="#e9ecef", bgc="#e9ecef", ink="#22272c", ink2="#5f6870", em="#c63f20", fill="#e2502e", on="#ffffff",
                  card="#ffffff", edge="2px solid #d3d8dd", shadow="0 10px 28px rgba(34,39,44,.10)",
                  cap_bg="rgba(34,39,44,.88)", cap_ink="#ffffff", cap_edge="0 solid transparent", radius=22,
                  glow1="rgba(226,80,46,.10)", glow2="rgba(110,130,150,.16)", chip_off="#dde1e5", chip_off_ink="#5f6870", alt="#2f6f8f", bad="#b8402a"),
    "dark": dict(bg="#15181d", bgc="#15181d", ink="#f3f1ec", ink2="#a6adb6", em="#ffb547", fill="#ffb547", on="#15181d",
                 card="#1f242b", edge="2px solid #2e353e", shadow="0 0 0 1px rgba(255,255,255,.04), 0 30px 80px rgba(255,190,110,.10)",
                 cap_bg="rgba(31,36,43,.92)", cap_ink="#f3f1ec", cap_edge="1.5px solid #2e353e", radius=24,
                 glow1="rgba(255,200,130,.12)", glow2="", chip_off="#262c34", chip_off_ink="#a6adb6", alt="#6cc3e0", bad="#ef6b55"),
}

# 版面上限：(每行最多幾個中文字寬, 最多幾行)
LIMITS = {
    ("stack", "h"): dict(title=(8, 3), item=(13, 1), n=(3, 5)),
    ("stack", "v"): dict(title=(7, 2), item=(12, 1), n=(3, 5)),
    ("big", "h"): dict(title=(24, 1), item=(13, 2), n=(3, 6)),
    ("big", "v"): dict(title=(7, 2), item=(12, 2), n=(3, 6)),
    ("scene", "h"): dict(title=(14, 2), item=(20, 1), n=(3, 6)),
    ("scene", "v"): dict(title=(7, 2), item=(12, 1), n=(3, 5)),
}


ICON_DIR = os.path.join(HERE, "..", "references", "quick")
ICON_SETS = ["lucide", "tabler", "phosphor", "phosphor-duotone", "phosphor-fill", "material"]  # 授權在 references/quick/LICENSE_*.txt
ICON_CREDIT = {"lucide": "Lucide · ISC", "tabler": "Tabler Icons · MIT © 2020-2024 Paweł Kuna", "phosphor": "Phosphor Icons · MIT © 2023 Phosphor Icons", "material": "Material Symbols · Apache-2.0 Google"}
ICON_CREDIT.update({f"phosphor-{w}": ICON_CREDIT["phosphor"] for w in ("duotone", "fill")})
SEARCH_ICON = {"phosphor": "magnifying-glass", "phosphor-duotone": "magnifying-glass", "phosphor-fill": "magnifying-glass"}  # 放大鏡在各套的名稱，沒列的叫 search


def load_set(name):
    d = json.load(open(os.path.join(ICON_DIR, name + ".json"), encoding="utf-8"))
    return dict(icons=d["icons"], aliases=d.get("aliases", {}), mode=d.get("mode", "stroke"), box=d.get("viewBox", "0 0 24 24"))


LUCIDE = load_set("lucide")
SET = LUCIDE  # 內容圖示用的那一套，讀完 spec.json 後換成 icon_set 指定的；勾、叉這種介面小圖一律用 Lucide
SHAPES = r"<(path|circle|line|rect|polyline|polygon|ellipse)\b([^>]*?)/>"


def icon(name, size, color, sw=2, ui=False):
    st = LUCIDE if ui else SET
    src = st["icons"].get(st["aliases"].get(name, name))
    if src is None:
        die(f"「{spec.get('icon_set', 'lucide')}」這套沒有「{name}」這個圖示：用 scripts/icon_search.py --set {spec.get('icon_set', 'lucide')} 以英文關鍵字找正確名稱")
    if st["mode"] == "fill":
        return f'<svg class="ico" viewBox="{st["box"]}" width="{size}" height="{size}" fill="{color}" style="display:block">{src}</svg>'
    parts = re.findall(SHAPES, src, re.S)
    inner = "".join("<" + tg + " " + " ".join(a.split()) + ' class="ln" pathLength="1" stroke-dasharray="1 1"/>' for tg, a in parts)
    return (f'<svg class="ico" viewBox="{st["box"]}" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round" style="display:block; overflow:visible">{inner}</svg>')


def draw(sel, t, ui=False):  # 線條一筆一筆畫出來；畫之前整個圖示先藏起來，否則線條端點的圓頭會先露出小點。填色的圖示沒有線條可畫，改成由左往右揭開
    t = max(t, 0)
    if not ui and SET["mode"] == "fill":
        return f'tl.set("{sel} .ico", {{ opacity: 1 }}, {t:.2f}); tl.fromTo("{sel} .ico", {{ clipPath: "inset(0% 100% 0% 0%)" }}, {{ clipPath: "inset(0% 0% 0% 0%)", duration: 0.5, ease: "power2.inOut" }}, {t:.2f});'
    return f'tl.set("{sel} .ico", {{ opacity: 1 }}, {t:.2f}); tl.fromTo("{sel} .ln", {{ attr: {{ "stroke-dashoffset": 1 }} }}, {{ attr: {{ "stroke-dashoffset": 0 }}, duration: 0.5, stagger: 0.06, ease: "power2.inOut" }}, {t:.2f});'


def burst_svg(color):  # Motion Prompt #003 Burst：圖示畫完時周圍迸出幾道短線
    import math as _m
    ls = "".join(f'<line x1="{50 + 36 * _m.cos(k * _m.pi / 4):.1f}" y1="{50 + 36 * _m.sin(k * _m.pi / 4):.1f}" '
                 f'x2="{50 + 47 * _m.cos(k * _m.pi / 4):.1f}" y2="{50 + 47 * _m.sin(k * _m.pi / 4):.1f}"/>' for k in range(8))
    return f'<svg viewBox="0 0 100 100" width="100%" height="100%" fill="none" stroke="{color}" stroke-width="2.6" stroke-linecap="round">{ls}</svg>'


def icon_block(ident, name, size, color, sw=1.6):  # 圖示＋爆點，外層可以整個移動、浮動
    return (f'<div id="{ident}" style="position:relative; width:{size}px; height:{size}px; flex:none;">{icon(name, size, color, sw)}'
            f'<div class="burst" style="position:absolute; left:{-size * 0.12:.0f}px; top:{-size * 0.12:.0f}px; width:{size * 1.24:.0f}px; height:{size * 1.24:.0f}px; opacity:0;">{burst_svg(color)}</div></div>')


def burst(sel, t):
    return (f'tl.fromTo("{sel} .burst", {{ opacity: 0, scale: 0.7 }}, {{ opacity: 1, scale: 1, duration: 0.12, ease: "power1.out" }}, {t:.2f}); '
            f'tl.to("{sel} .burst", {{ opacity: 0, scale: 1.1, duration: 0.35, ease: "power1.out" }}, {t + 0.12:.2f});')


def bob(sel, t0, t1):  # 停留時輕輕上下浮動，畫面不會整段靜止
    span = t1 - t0
    if span < 0.6:
        return ""
    r = max(1, round(span / 0.9) - 1)
    return f'tl.fromTo("{sel}", {{ y: 0 }}, {{ y: -12, duration: {span / (r + 1):.2f}, ease: "sine.inOut", yoyo: true, repeat: {r}, immediateRender: false }}, {t0:.2f});'


MOTIONS = ["draw", "pop", "drop", "spin", "flip", "slide", "pulse", "wiggle"]


def icon_in(sel, motion, t, t_end):
    """圖示出場動畫（sel 是 icon_block 的 id），停好後輕輕浮動到 t_end。效果改寫自 Motion Prompt #003 Burst、#010 Overshoot、#011 Squash & stretch"""
    m = motion or "draw"
    if m not in MOTIONS:
        die(f"motion「{m}」不在選單裡，只能用：" + "、".join(MOTIONS))
    js = [draw(sel, t)] if m in ("draw", "pulse", "wiggle") else [f'tl.set("{sel} .ico", {{ opacity: 1 }}, {t:.2f});']
    f = lambda a, b, at: f'tl.fromTo("{sel}", {{ {a} }}, {{ {b} }}, {at:.2f});'
    if m == "draw":
        js += [f("scale: 0.85", 'scale: 1, duration: 0.35, ease: "back.out(1.8)"', t), burst(sel, t + 0.5)]
        settle = t + 0.6
    elif m == "pop":
        js += [f("scale: 0", 'scale: 1, duration: 0.45, ease: "back.out(2.6)"', t), burst(sel, t + 0.28)]
        settle = t + 0.5
    elif m == "drop":
        js += [f("y: -260, scaleY: 1.15, scaleX: 0.9", 'y: 0, duration: 0.3, ease: "power2.in"', t),
               f'tl.to("{sel}", {{ scaleY: 0.8, scaleX: 1.15, duration: 0.07, ease: "power1.out" }}, {t + 0.3:.2f});',
               f'tl.to("{sel}", {{ scaleY: 1, scaleX: 1, duration: 0.35, ease: "elastic.out(1, 0.45)" }}, {t + 0.37:.2f});', burst(sel, t + 0.3)]
        settle = t + 0.75
    elif m == "spin":
        js += [f("rotation: -200, scale: 0.3", 'rotation: 0, scale: 1, duration: 0.6, ease: "back.out(1.4)"', t)]
        settle = t + 0.65
    elif m == "flip":
        js += [f("rotationY: -90, transformPerspective: 900", 'rotationY: 0, transformPerspective: 900, duration: 0.55, ease: "back.out(1.6)"', t)]
        settle = t + 0.6
    elif m == "slide":
        js += [f("x: -320, skewX: -14, opacity: 0", 'x: 0, skewX: 0, opacity: 1, duration: 0.45, ease: "expo.out"', t)]
        settle = t + 0.5
    elif m == "pulse":
        js += [f'tl.fromTo("{sel}", {{ scale: 1 }}, {{ scale: 1.14, duration: 0.14, yoyo: true, repeat: 3, ease: "power1.inOut", immediateRender: false }}, {t + 0.65:.2f});']
        settle = t + 1.25
    else:  # wiggle
        js += [f'tl.to("{sel}", {{ keyframes: {{ rotation: [0, -10, 9, -7, 5, -2, 0] }}, duration: 0.6, ease: "none" }}, {t + 0.65:.2f});']
        settle = t + 1.3
    js.append(bob(sel, settle, t_end))
    return js


SCENE_HELP = __doc__[__doc__.index("scene 模板每個重點"):]
SCENES = ["icon", "actor", "split", "tree", "card", "check", "number"]

HEX = "M39.6,12.0 Q50.0,6.0 60.4,12.0 L77.7,22.0 Q88.1,28.0 88.1,40.0 L88.1,60.0 Q88.1,72.0 77.7,78.0 L60.4,88.0 Q50.0,94.0 39.6,88.0 L22.3,78.0 Q11.9,72.0 11.9,60.0 L11.9,40.0 Q11.9,28.0 22.3,22.0 Z"
HEXIN = "M40.9,16.8 Q50.0,11.5 59.1,16.8 L74.2,25.5 Q83.3,30.8 83.3,41.2 L83.3,58.8 Q83.3,69.2 74.2,74.5 L59.1,83.2 Q50.0,88.5 40.9,83.2 L25.8,74.5 Q16.7,69.2 16.7,58.8 L16.7,41.2 Q16.7,30.7 25.8,25.5 Z"


def mascot_defs(S):  # 主角三種：w 一般（白底）、l 帶頭的（主色）、a 檢查的（第二色）
    face = lambda c: (f'<circle cx="40" cy="47" r="4.6" fill="{c}"/><circle cx="60" cy="47" r="4.6" fill="{c}"/>'
                      f'<path d="M41 60 Q50 66.5 59 60" fill="none" stroke="{c}" stroke-width="4" stroke-linecap="round"/>')
    solid = lambda c: f'<path d="{HEX}" fill="{c}"/><path d="{HEXIN}" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="2"/>'
    return (f'<svg width="0" height="0" style="position:absolute"><defs>'
            f'<symbol id="hx-w" viewBox="0 0 100 100"><path d="{HEX}" fill="{S["card"]}" stroke="{S["fill"]}" stroke-width="4.5"/>{face(S["ink"])}</symbol>'
            f'<symbol id="hx-l" viewBox="0 0 100 100">{solid(S["fill"])}{face(S["on"])}</symbol>'
            f'<symbol id="hx-a" viewBox="0 0 100 100">{solid(S["alt"])}{face("#ffffff")}</symbol></defs></svg>')


def mascot(ident, kind, size, extra=""):
    return (f'<div class="msc" id="{ident}" style="width:{size:.0f}px; height:{size:.0f}px; flex:none; {extra}">'
            f'<svg viewBox="0 0 100 100" width="100%" height="100%"><use href="#hx-{kind}"/></svg></div>')


def hop(sel, t):  # 主角跳進來：壓扁再彈起
    return f'tl.fromTo("{sel}", {{ opacity: 0, y: 70, scaleX: 1.18, scaleY: 0.78 }}, {{ opacity: 1, y: 0, scaleX: 1, scaleY: 1, duration: 0.5, ease: "back.out(2)" }}, {t:.2f});'


def pop_in(sel, t, ease="back.out(2.4)"):
    return f'tl.fromTo("{sel}", {{ opacity: 0, scale: 0.4 }}, {{ opacity: 1, scale: 1, duration: 0.32, ease: "{ease}" }}, {t:.2f});'


def die(msg):
    sys.exit("停下來：" + msg)


def vis(t):  # 視覺寬度：中文字 1、英文字母數字 0.55、空白 0.3
    t = t.replace("*", "").replace("|", "")
    return sum(0.3 if c == " " else 0.55 if ord(c) < 128 else 1 for c in t)


def em(t):
    import html
    return re.sub(r"\*(.+?)\*", r"<em>\1</em>", html.escape(t)).replace("|", "<br>")


def check_len(label, t, per_line, lines):
    if "|" in t:  # 自己指定換行時，逐行檢查
        parts = t.split("|")
        if len(parts) > lines:
            die(f"{label}「{t}」分成 {len(parts)} 行，這個模板最多 {lines} 行")
        for s in parts:
            if vis(s) > per_line + 0.01:
                die(f"{label}的「{s}」這一行約 {vis(s):.0f} 個字寬，每行最多 {per_line} 個字寬。請縮短或換個位置斷行")
        return
    w = vis(t)
    if w > per_line * lines + 0.01:
        die(f"{label}「{t}」約 {w:.0f} 個字寬，這個模板最多 {per_line * lines} 個字寬（每行 {per_line}、最多 {lines} 行）。請縮短。")


def run(args):
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        die(" ".join(os.path.basename(a) for a in args[:2]) + " 失敗：\n" + r.stdout + r.stderr)
    return r.stdout


# ---------- 讀資料 ----------
spec = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "spec.json", encoding="utf-8"))
T, O = spec.get("template"), spec.get("orientation")
if (T, O) not in LIMITS:
    die('template 要是 "stack" 或 "big"，orientation 要是 "h" 或 "v"')
S = STYLES.get(spec.get("style"))
if not S:
    die('style 要是 "glass"、"paper" 或 "dark"')
if spec.get("music") not in MUSIC:
    die('music 要是 "smile"、"closeup"、"clouds" 或 "september"')
if spec.get("icon_set", "lucide") not in ICON_SETS:
    die(f"icon_set「{spec['icon_set']}」不在選單裡，只能用：" + "、".join(ICON_SETS))
SET = load_set(spec.get("icon_set", "lucide"))
lang = spec.get("lang", "zh")
TLH = 1.3 if lang == "zh" else 1.2  # 標題行高：中文字是方的，兩行以上要鬆一點才不會黏在一起
L = LIMITS[(T, O)]
items = spec["items"]
if not L["n"][0] <= len(items) <= L["n"][1]:
    die(f"這個模板放 {L['n'][0]}–{L['n'][1]} 個重點，現在有 {len(items)} 個。內容不合時改走一般流程。")
check_len("標題", spec["title"], *L["title"])
for i, it in enumerate(items, 1):
    check_len(f"第 {i} 個重點", it["text"].replace("|", "") if T == "scene" else it["text"], *L["item"])
    if T == "big":
        if not it.get("key"):
            die(f"big 模板每個重點都要有 key（第 {i} 個沒有）")
        if vis(it["key"]) > 4.5:
            die(f"第 {i} 個 key「{it['key']}」太長，最多 2 個中文字或 4–5 個英文字母")

TI = spec.get("title_icon")
for mo in [spec.get("title_motion")] + [it.get("motion") for it in items]:
    if mo and mo not in MOTIONS:
        die(f"motion「{mo}」不在選單裡，只能用：" + "、".join(MOTIONS))
for nm in [TI] + [it.get("icon") for it in items]:
    if nm:
        icon(nm, 10, "#000")
if T == "scene":  # 每一幕的欄位先檢查完，錯了在配音、下載之前就停
    lab_max = 6 if O == "v" else 9
    for i, it in enumerate(items, 1):
        sc = it.get("scene")
        if sc not in SCENES:
            die(f"第 {i} 個重點的 scene「{sc}」不對。\n" + SCENE_HELP)
        need = {"icon": ["icon"], "actor": ["icon"], "split": ["bad", "good"], "tree": ["branches"],
                "card": ["card_title", "rows"], "check": [], "number": ["key"]}[sc]
        miss = [f for f in need if not it.get(f)]
        if sc == "icon" and not it.get("icon") and TI:
            miss = []
        if miss:
            die(f"第 {i} 個重點（{sc}）缺 " + "、".join(miss) + "。\n" + SCENE_HELP)
        if sc == "actor" and it.get("say") and vis(it["say"]) > lab_max:
            die(f"第 {i} 個重點的 say「{it['say']}」太長，最多 {lab_max} 個字寬")
        if sc == "split":
            for side in ("bad", "good"):
                d = it[side]
                if not d.get("icon") or not d.get("label"):
                    die(f"第 {i} 個重點的 {side} 要有 icon 和 label")
                if vis(d["label"]) > lab_max:
                    die(f"第 {i} 個重點的 {side}.label「{d['label']}」太長，最多 {lab_max} 個字寬")
                icon(d["icon"], 10, "#000")
        if sc == "tree":
            b = it["branches"]
            if not 2 <= len(b) <= 4:
                die(f"第 {i} 個重點的 branches 要 2–4 個，現在 {len(b)} 個")
            cap = {2: 7, 3: 5, 4: 3.5}[len(b)] if O == "v" else {2: 9, 3: 7, 4: 6}[len(b)]
            for x in b:
                if vis(x) > cap:
                    die(f"第 {i} 個重點的分支「{x}」太長：分 {len(b)} 支時每支最多 {cap:g} 個字寬")
        if sc == "card":
            rows = it["rows"]
            if not 2 <= len(rows) <= 4:
                die(f"第 {i} 個重點的 rows 要 2–4 項，現在 {len(rows)} 項")
            rcap = 11 if O == "v" else 14
            check_len(f"第 {i} 個重點的 card_title", it["card_title"], rcap, 1)
            for r_ in rows:
                check_len(f"第 {i} 個重點的清單項", r_["text"] if isinstance(r_, dict) else r_, rcap, 1)
        if sc == "check":
            mk = it.get("marks", "oox")
            if not re.fullmatch(r"[ox]{2,4}", mk):
                die(f"第 {i} 個重點的 marks 只能用 o、x，2–4 個（例如 oox）")
        if sc == "number" and vis(it["key"]) > 4.5:
            die(f"第 {i} 個重點的 key「{it['key']}」太長，最多 2 個中文字或 4–5 個英文字母")

script = open("script.txt", encoding="utf-8").read().strip()
words = json.load(open("assets/audio/words.json", encoding="utf-8"))
pos = 0
for w in words:
    i = script.find(w["w"], pos)
    if i < 0:
        die(f"script.txt 裡找不到「{w['w']}」：words.json 要用同一份 script.txt 產生")
    w["a"], pos = i, i + len(w["w"])


def cue_time(cue, label):
    i = script.find(cue)
    if i < 0:
        die(f"{label}的 cue「{cue}」不在 script.txt 裡，要一字不差")
    for w in words:
        if w["a"] + len(w["w"]) > i:
            return round(w["t"], 2)
    return round(words[-1]["t"], 2)


ts = [cue_time(it["cue"], f"第 {k} 個重點") for k, it in enumerate(items, 1)]
te = cue_time(spec["ending_cue"], "結尾句")
if any(b <= a for a, b in zip(ts, ts[1:])) or te <= ts[-1]:
    die("cue 的順序要和台詞一樣：重點依序出現，結尾句在最後")
speech_end = words[-1]["t"] + words[-1]["d"]
TOTAL = round(speech_end + 1.6, 2)  # 輕量模式節奏較快：結尾句講完停住約 1 秒，最後 0.5 秒淡出

W, H = (1920, 1080) if O == "h" else (1080, 1920)

# ---------- 素材：音效、配樂、字幕 ----------
os.makedirs("assets/sfx", exist_ok=True)
man = json.load(open(os.path.join(SFX_LIB, "manifest.json"), encoding="utf-8"))
sfx = []  # (時間, 名稱)
sfx.append((0.05, "whoosh-short"))
for t in ts:
    sfx.append((t, "pop" if T == "stack" else "ping"))
sfx.append((te, "chime"))
for _, n in sfx:
    shutil.copy(os.path.join(SFX_LIB, man[n]["file"]), os.path.join("assets/sfx", man[n]["file"]))
sfx_html = "\n".join(
    f'      <audio id="sfx-{k}" class="clip" src="assets/sfx/{man[n]["file"]}" data-start="{t}" data-duration="{man[n]["duration"]}" '
    f'data-track-index="{7 + k % 3}" data-volume="0.35"></audio>' for k, (t, n) in enumerate(sfx))

url, start, mname = MUSIC[spec["music"]]
os.makedirs("assets/bgm/source", exist_ok=True)
src = os.path.join("assets/bgm/source", spec["music"] + ".mp3")
if not os.path.exists(src):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r, open(src, "wb") as f:
        f.write(r.read())
run([PY, "-I", os.path.join(HERE, "prep_music.py"), src, "assets/bgm/bgm.mp3", str(TOTAL), str(start)])
vol_out = run([PY, "-I", os.path.join(HERE, "music_volume.py"), "assets/audio/voice.mp3", "assets/audio/words.json", "assets/bgm/bgm.mp3"])
m = re.search(r"data-volume = ([\d.]+)", vol_out)
VOL = m.group(1) if m else "0.2"

run([PY, "-I", os.path.join(HERE, "make_captions.py"), "script.txt", "assets/audio/words.json", lang, O, "captions.json", str(TOTAL)])
caps = json.load(open("captions.json", encoding="utf-8"))
# 結尾大字出現後，和大字重複的字幕拿掉。以「一整句」為單位決定：只拿掉半句會留下斷在「就」這種沒講完的字幕
end_chars = set(re.sub(r"[\s*|，。！？、,.!?]", "", spec["ending"]))
def sent_id(c):  # 這組字幕屬於台詞的第幾句（數它前面有幾個句號、問號、驚嘆號）
    w0 = min(words, key=lambda w: abs(w["t"] - c["start"]))
    return sum(script[:w0["a"]].count(x) for x in "。！？.!?")
sents = {}
for c in caps:
    if c["start"] >= te - 0.05:
        sents.setdefault(sent_id(c), []).append(c)
drop_ids = set()
for sid, cs in sents.items():
    t_ = re.sub(r"[\s，。！？、,.!?]", "", "".join(c["text"] for c in cs))
    if t_ and sum(ch in end_chars for ch in t_) / len(t_) >= 0.6:
        drop_ids.add(sid)
dropped = [c["text"] for c in caps if c["start"] >= te - 0.05 and sent_id(c) in drop_ids]
caps = [c for c in caps if not (c["start"] >= te - 0.05 and sent_id(c) in drop_ids)]
json.dump(caps, open("captions.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- 版面 ----------
# 中文片一律用思源黑體（references/fonts，開放字型授權），Mac、Windows 做出來一樣；純英文片用 HyperFrames 內建的 Inter
FONT = '"TC", sans-serif' if lang == "zh" else '"Inter", "TC", sans-serif'
os.makedirs("assets/fonts", exist_ok=True)
shutil.copy(os.path.join(HERE, "..", "references", "fonts", "NotoSansTC.ttf"), "assets/fonts/NotoSansTC.ttf")
R = S["radius"]
css_common = f"""
      @font-face {{ font-family: "TC"; src: url("assets/fonts/NotoSansTC.ttf"); font-weight: 100 900; ascent-override: 108%; descent-override: 32%; }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: {W}px; height: {H}px; overflow: hidden; background: {S["bgc"]}; }}
      #root {{ position: relative; width: {W}px; height: {H}px; overflow: hidden; font-family: {FONT}; font-weight: 500; color: {S["ink"]}; background: {S["bg"]}; }}
      #world {{ position: absolute; inset: 0; transform-origin: {W // 2 if O == "h" else 450}px {H // 2 if O == "h" else 700}px; }}
      .ico {{ opacity: 0; }}
      em {{ font-style: normal; font-weight: 600; color: {S["em"]}; }}
      .glow {{ position: absolute; border-radius: 50%; }}
      .card {{ position: absolute; display: flex; align-items: center; background: {S["card"]}; border: {S["edge"]}; box-shadow: {S["shadow"]}; border-radius: {R}px; }}
      .num {{ flex: none; width: 64px; height: 64px; border-radius: 32px; background: {S["fill"]}; color: {S["on"]}; font-weight: 600; font-size: 36px; line-height: 64px; text-align: center; margin: 0 26px 0 28px; }}
      .card span {{ font-weight: 500; white-space: nowrap; }}
      .row .num {{ width: 44px; height: 44px; border-radius: 22px; font-size: 28px; line-height: 44px; margin: 0 16px 0 10px; }}
      .end {{ position: absolute; text-align: center; font-weight: 600; line-height: 1.3; text-wrap: balance; opacity: 0; }}
      #title, #head, .exp {{ text-wrap: balance; }}
      .scn {{ position: absolute; opacity: 0; }}
      .msc svg {{ display: block; overflow: visible; filter: drop-shadow(0 10px 16px rgba(28,42,52,.16)); }}
      .bub {{ position: relative; padding: 0.45em 0.8em; border-radius: 28px; background: {S["card"]}; border: {S["edge"]}; box-shadow: {S["shadow"]}; font-weight: 600; white-space: nowrap; opacity: 0; }}
      .badge {{ position: absolute; top: -24px; right: -24px; width: 84px; height: 84px; border-radius: 42px; display: flex; align-items: center; justify-content: center; opacity: 0; box-shadow: 0 8px 20px -6px rgba(28,42,52,.35); }}
      .dot {{ display: block; width: 16px; height: 16px; border-radius: 8px; background: {S["chip_off"]}; }}
      #fade {{ position: absolute; inset: 0; background: {S["bgc"]}; opacity: 0; }}
      #captions {{ position: absolute; inset: 0; }}
      .cap {{ position: absolute; text-align: center; opacity: 0; }}
      .cap span {{ display: inline-block; padding: {"16px 40px" if O == "h" else "14px 36px"}; border-radius: 18px; background: {S["cap_bg"]}; color: {S["cap_ink"]}; border: {S["cap_edge"]}; font-weight: 500; line-height: 1.25; white-space: nowrap; }}
      .chip {{ display: inline-block; margin: 0 12px; padding: 0 26px; height: 70px; line-height: 70px; border-radius: 35px; font-weight: 600; font-size: 40px; background: {S["chip_off"]}; color: {S["chip_off_ink"]}; }}
"""
if O == "h":
    css_common += """      .cap { left: 360px; width: 1200px; top: 850px; } .cap span { font-size: 48px; max-width: 1200px; }
      .chip { height: 80px; line-height: 80px; border-radius: 40px; font-size: 48px; padding: 0 30px; }\n"""
else:
    css_common += """      .cap { left: 120px; width: 660px; top: 1152px; } .cap span { font-size: 46px; max-width: 660px; }
      .chip { margin: 0 8px 14px; padding: 0 20px; height: 56px; line-height: 56px; border-radius: 28px; font-size: 32px; }\n"""

glows = ""
if S["glow1"]:
    g1 = (1150, -200, 1100, 760) if O == "h" else (380, 120, 900, 900)
    glows += f'<div class="glow" id="g1" style="left:{g1[0]}px; top:{g1[1]}px; width:{g1[2]}px; height:{g1[3]}px; background: radial-gradient(closest-side, {S["glow1"]}, transparent);"></div>'
if S["glow2"]:
    g2 = (-300, 520, 1220, 800) if O == "h" else (-360, 1100, 1100, 1000)
    glows += f'<div class="glow" id="g2" style="left:{g2[0]}px; top:{g2[1]}px; width:{g2[2]}px; height:{g2[3]}px; background: radial-gradient(closest-side, {S["glow2"]}, transparent);"></div>'


def fit(text, width, max_px, max_lines):  # 結尾句字級：塞得進 max_lines 行的最大字級
    w = vis(text)
    for px in range(max_px, 39, -2):
        if math.ceil(w * px / (width * 0.96)) <= max_lines:
            return px
    die(f"結尾句「{text}」太長，請縮短")


n = len(items)
body, js = [], []
ease_in = "back.out(1.7)"  # Motion Prompt #010 Overshoot：衝過頭再回來停好

if T == "stack":
    # 舞台版面：講到哪個重點，那個重點的大圖示和那句字就在舞台中間；講下一個時縮小飛進旁邊的清單
    # 元素放大、在標題到字幕之間上下置中，減少留白；清單行高依重點數量撐滿
    def nlines(txt, per):
        return len(txt.split("|")) if "|" in txt else max(1, math.ceil(vis(txt) / per))
    if O == "h":
        body.append(f'<div id="title" style="position:absolute; left:192px; top:140px; width:720px; font-size:88px; font-weight:500; line-height:{TLH};">{em(spec["title"])}</div>')
        tb = 140 + nlines(spec["title"], 8) * 88 * TLH
        sx, sw_, isz, spx = 950, 778, 350, 84
        itop = 120 + (830 - 120 - (isz + 56 + spx * 1.2)) / 2
        ttop = itop + isz + 56
        lx, lw, rgap = 192, 680, 16
        ltop = tb + 44
        rh = min(76, (830 - ltop - rgap * (n - 1)) / n)
    else:
        body.append(f'<div id="title" style="position:absolute; left:120px; top:312px; width:660px; text-align:center; font-size:80px; font-weight:500; line-height:{TLH};">{em(spec["title"])}</div>')
        tb = 312 + nlines(spec["title"], 7) * 80 * TLH
        sx, sw_, isz, spx = 120, 660, 200, 52
        itop = tb + 28
        ttop = itop + isz + 22
        lx, lw, rgap = 120, 660, 12
        ltop = ttop + spx * 1.2 + 28
        rh = min(62, (1116 - ltop - rgap * (n - 1)) / n)
    rpx = int(max(28, min(44 if O == "h" else 36, rh * 0.58)))
    icx = sx + (sw_ - isz) / 2
    scx, scy = icx + isz / 2, itop + isz / 2
    tcx, tcy = sx + sw_ / 2, ttop + spx * 0.6
    for k, it in enumerate(items):
        nm = it.get("icon") or TI
        if nm:
            body.append(f'<div class="stg" id="si{k}" style="position:absolute; left:{icx:.0f}px; top:{itop}px;">{icon_block(f"sib{k}", nm, isz, S["fill"])}</div>')
        else:
            body.append(f'<div class="stg" id="si{k}" style="position:absolute; left:{icx:.0f}px; top:{itop}px; width:{isz}px; height:{isz}px; line-height:{isz}px; text-align:center; font-size:{isz * 0.7:.0f}px; font-weight:600; color:{S["em"]}; opacity:0;">{k + 1}</div>')
        spk = int(min(spx, sw_ * 0.95 / max(vis(it["text"]), 1)))  # 字少就放大，字多就縮到放得下
        body.append(f'<div class="stt" id="st{k}" style="position:absolute; left:{sx}px; top:{ttop + (spx - spk) * 0.6:.0f}px; width:{sw_}px; text-align:center; font-size:{spk}px; font-weight:600; line-height:1.2; white-space:nowrap; opacity:0;">{em(it["text"])}</div>')
        rt = ltop + k * (rh + rgap)
        body.append(f'<div class="card row" id="it{k}" style="left:{lx}px; top:{rt:.0f}px; width:{lw}px; height:{rh:.0f}px; opacity:0;"><b class="num">{k + 1}</b><span style="font-size:{rpx}px">{em(it["text"])}</span></div>')
        t0 = ts[k]
        nxt = ts[k + 1] if k + 1 < n else te
        if nm:
            js += icon_in(f"#sib{k}", it.get("motion"), t0, nxt - 0.4)
        else:
            js.append(f'tl.fromTo("#si{k}", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "{ease_in}" }}, {t0:.2f});')
        js.append(f'tl.fromTo("#st{k}", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.3, ease: "power3.out" }}, {t0 + 0.05:.2f});')
        if k + 1 < n:  # 換下一個重點：舞台上的這一個縮小飛進清單
            rcx, rcy = lx + lw / 2, rt + rh / 2
            js.append(f'tl.to("#si{k}", {{ x: {rcx - scx:.0f}, y: {rcy - scy:.0f}, scale: 0.2, opacity: 0, duration: 0.32, ease: "power2.in" }}, {nxt - 0.32:.2f});')
            js.append(f'tl.to("#st{k}", {{ x: {rcx - tcx:.0f}, y: {rcy - tcy:.0f}, scale: 0.5, opacity: 0, duration: 0.32, ease: "power2.in" }}, {nxt - 0.32:.2f});')
            js.append(f'tl.fromTo("#it{k}", {{ opacity: 0, x: -20 }}, {{ opacity: 1, x: 0, duration: 0.3, ease: "{ease_in}" }}, {nxt - 0.08:.2f});')
    if TI:  # 開場：主題大圖示先站上舞台
        body.append(f'<div id="hico" style="position:absolute; left:{icx:.0f}px; top:{itop}px;">{icon_block("hib", TI, isz, S["fill"])}</div>')
        js += icon_in("#hib", spec.get("title_motion"), 0.1, ts[0] - 0.35)
        js.append(f'tl.to("#hico", {{ opacity: 0, scale: 0.8, duration: 0.25, ease: "power2.in" }}, {max(ts[0] - 0.3, 0.6):.2f});')
    js.append(f'tl.fromTo("#title", {{ y: 16 }}, {{ y: 0, duration: 0.6, ease: "power3.out" }}, 0);')
    js.append(f'tl.to(["#title", ".row", ".stt", ".stg"], {{ opacity: 0, y: -24, duration: 0.3, ease: "power2.in" }}, {te - 0.3:.2f});')
    # 結尾：圖示＋結尾句整組在可用範圍裡上下置中
    ew_, emax, elines, a0, a1, ecx = (1400, 96, 2, 120, 830, 960) if O == "h" else (660, 84, 4, 288, 1150, 450)
    epx = fit(spec["ending"], ew_, emax, elines)
    nl = len(spec["ending"].split("|")) if "|" in spec["ending"] else math.ceil(vis(spec["ending"]) * epx / (ew_ * 0.96))
    gh = (210 if TI else 0) + nl * epx * 1.3
    gtop = a0 + (a1 - a0 - gh) / 2
    etop = gtop + (210 if TI else 0)
    body.append(f'<div class="end" id="end" style="left:{ecx - ew_ // 2}px; width:{ew_}px; top:{etop:.0f}px; font-size:{epx}px;">{em(spec["ending"])}</div>')
    if TI:
        body.append(f'<div id="eico" style="position:absolute; left:{ecx - 90}px; top:{gtop:.0f}px;">{icon(TI, 180, S["fill"], 1.8)}</div>')
        js.append(draw("#eico", te + 0.1))
elif T == "scene":
    # 每個重點一幕畫面：開場大標題＋主角 → 標題縮成頁首、旁邊小圓點標進度 → 一幕一幕換 → 結尾主角＋結尾句
    if O == "v":
        sx, sy, sw_, sh_, ty, tpx, msz, isz, lab = 120, 410, 660, 560, 1000, 52, 230, 300, 40
    else:
        sx, sy, sw_, sh_, ty, tpx, msz, isz, lab = 192, 200, 1536, 490, 712, 64, 300, 340, 50
    plain = spec["title"].replace("|", " ")
    body.insert(0, mascot_defs(S))
    # 開場
    if O == "v":
        body.append(f'<div id="title" style="position:absolute; left:120px; top:330px; width:660px; text-align:center; font-size:84px; font-weight:500; line-height:{TLH};">{em(spec["title"])}</div>')
        ogt, ogh = 640, 340
    else:
        body.append(f'<div id="title" style="position:absolute; left:192px; top:170px; width:1536px; text-align:center; font-size:96px; font-weight:500; line-height:{TLH};">{em(spec["title"])}</div>')
        ogt, ogh = 480, 360
    op = icon_block("hib", TI, msz * 0.8, S["fill"]) if TI else ""
    body.append(f'<div id="og" style="position:absolute; left:{sx}px; top:{ogt}px; width:{sw_}px; height:{ogh}px; display:flex; align-items:center; justify-content:center; gap:{int(msz * 0.25)}px;">{mascot("om", "w", msz)}{op}</div>')
    js.append(f'tl.fromTo("#title", {{ y: 16 }}, {{ y: 0, duration: 0.6, ease: "power3.out" }}, 0);')
    js.append(hop("#om", 0.2))
    js.append(bob("#om", 0.8, ts[0] - 0.4))
    if TI:
        js += icon_in("#hib", spec.get("title_motion"), 0.5, ts[0] - 0.4)
    js.append(f'tl.to(["#title", "#og"], {{ opacity: 0, y: -30, duration: 0.3, ease: "power2.in" }}, {ts[0] - 0.35:.2f});')
    # 頁首：標題縮小＋進度圓點
    if O == "v":
        hpx = int(min(36, 640 / max(vis(plain), 1)))
        body.append(f'<div id="head" style="position:absolute; left:120px; top:296px; width:660px; text-align:center; font-size:{hpx}px; font-weight:500; color:{S["ink2"]}; white-space:nowrap; opacity:0;">{em(plain)}</div>')
        body.append(f'<div id="dots" style="position:absolute; left:120px; top:356px; width:660px; display:flex; justify-content:center; gap:14px; opacity:0;">' + "".join(f'<i class="dot" id="d{k}"></i>' for k in range(n)) + "</div>")
    else:
        hpx = int(min(38, 1100 / max(vis(plain), 1)))
        body.append(f'<div id="head" style="position:absolute; left:192px; top:112px; width:1200px; font-size:{hpx}px; font-weight:500; color:{S["ink2"]}; white-space:nowrap; opacity:0;">{em(plain)}</div>')
        body.append(f'<div id="dots" style="position:absolute; left:1400px; top:128px; width:328px; display:flex; justify-content:flex-end; gap:16px; opacity:0;">' + "".join(f'<i class="dot" id="d{k}"></i>' for k in range(n)) + "</div>")
    js.append(f'tl.fromTo(["#head", "#dots"], {{ opacity: 0, y: -12 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: "power3.out" }}, {ts[0] - 0.1:.2f});')

    def beat(t0, dur, need):  # 這一幕的時間不夠時，把幕裡的小動作等比例壓緊
        f = min(1.0, max(0.35, (dur - 0.7) / need))
        return lambda off: t0 + off * f

    # 每一幕的排法：相鄰兩幕不一樣。橫式的 card、actor、icon、number 放得進半邊，用左右分割並且輪流換邊；
    # 其他要整個寬度的，字在畫面下方或上方輪流。直式只有上下兩種
    lays, side = [], "left"
    for it in items:
        prev = lays[-1] if lays else ""
        if O == "h" and it["scene"] in ("card", "actor", "icon", "number"):
            lays.append(side)
            side = "right" if side == "left" else "left"
        else:
            lays.append("above" if prev == "below" else "below")
    # 進退場方向跟著排法走，不要每一幕都同一個方向：(字從哪裡進來, 整幕往哪裡離開)
    MOVE = {"left": ("x: -36, y: 0", "x: -60"), "right": ("x: 36, y: 0", "x: 60"), "below": ("x: 0, y: 24", "y: -40"), "above": ("x: 0, y: -20", "y: 40")}

    shots = []
    for k, it in enumerate(items):
        t0 = ts[k]
        lay = lays[k]
        if O == "v":
            sx, sw_, sh_, tpx = 120, 660, 560, 60
            sy, ty = (410, 996) if lay == "below" else (540, 426)
        elif lay in ("left", "right"):
            sy, sh_, sw_, tpx = 190, 590, 880, 80
            sx, tx, tw = (848, 192, 600) if lay == "left" else (192, 1128, 600)
        else:
            sx, sw_, sh_, tpx = 192, 1536, 490, 80
            sy, ty = (200, 700) if lay == "below" else (324, 194)
        nar = O == "v" or lay in ("left", "right")  # 畫面只有半邊寬，卡片旁邊放不下主角，主角改站在卡片角落
        t1 = ts[k + 1] if k + 1 < n else te
        dur, hold = t1 - t0, t1 - 0.4
        sc = it["scene"]
        h_, j_ = "", []
        full = 'position:absolute; inset:0; display:flex; align-items:center; justify-content:center;'
        if sc == "icon":
            h_ = f'<div style="{full}">{icon_block(f"p{k}", it.get("icon") or TI, isz, S["fill"])}</div>'
            j_ += icon_in(f"#p{k}", it.get("motion"), t0 + 0.05, hold)
        elif sc == "actor":
            bub = f'<div class="bub" id="b{k}" style="font-size:{lab}px">{em(it["say"])}</div>' if it.get("say") else ""
            h_ = (f'<div style="{full} gap:{int(sw_ * 0.06)}px;"><div style="display:flex; flex-direction:column; align-items:center; gap:16px;">{bub}{mascot(f"m{k}", "w", msz)}</div>'
                  f'{icon_block(f"p{k}", it["icon"], msz * 0.9, S["fill"])}</div>')
            j_ += [hop(f"#m{k}", t0)] + icon_in(f"#p{k}", it.get("motion"), t0 + 0.3, hold)
            if bub:
                j_.append(pop_in(f"#b{k}", t0 + 0.65))
            j_.append(bob(f"#m{k}", t0 + 0.75, hold))
        elif sc == "split":
            gap = 44 if O == "v" else 80
            pw, ph = (sw_ - gap) / 2, (470 if O == "v" else 430)
            ic2 = min(pw * 0.55, ph * 0.48)
            def panel(side, d, col, tc, bg, glyph):
                return (f'<div class="card pan" id="{side}{k}" style="position:relative; width:{pw:.0f}px; height:{ph}px; flex-direction:column; justify-content:center; gap:26px;">'
                        f'{icon_block(f"{side}i{k}", d["icon"], ic2, col)}<div style="font-size:{lab}px; font-weight:600; color:{tc}; white-space:nowrap;">{em(d["label"])}</div>'
                        f'<div class="badge" id="{side}x{k}" style="background:{bg}">{icon(glyph, 46, "#ffffff", 3.2, ui=True)}</div></div>')
            h_ = (f'<div style="{full} gap:{gap}px;">' + panel("pb", it["bad"], S["ink2"], S["ink2"], S["bad"], "x")
                  + panel("pg", it["good"], S["fill"], S["ink"], S["fill"], "check") + "</div>")
            b = beat(t0, dur, 2.4)
            j_.append(f'tl.fromTo("#pb{k}", {{ opacity: 0, x: -40 }}, {{ opacity: 1, x: 0, duration: 0.4, ease: "power3.out" }}, {t0:.2f});')
            j_ += icon_in(f"#pbi{k}", it["bad"].get("motion"), t0 + 0.1, b(1.0))
            j_ += [pop_in(f"#pbx{k}", b(0.6)), draw(f"#pbx{k}", b(0.62), ui=True)]
            j_.append(f'tl.to("#pb{k}", {{ opacity: 0.8, scale: 0.92, duration: 0.3, ease: "power2.out" }}, {b(1.2):.2f});')
            j_.append(f'tl.fromTo("#pg{k}", {{ opacity: 0, x: 40 }}, {{ opacity: 1, x: 0, duration: 0.4, ease: "power3.out" }}, {b(1.2):.2f});')
            j_ += icon_in(f"#pgi{k}", it["good"].get("motion") or "pop", b(1.3), hold)
            j_ += [pop_in(f"#pgx{k}", b(1.8)), draw(f"#pgx{k}", b(1.82), ui=True)]
        elif sc == "tree":
            br = it["branches"]
            m_ = len(br)
            slot = sw_ / m_
            L = 170 if O == "v" else 180
            C = min(140 if O == "v" else 160, slot * 0.8)
            lf = 34 if O == "v" else 44
            ct = sh_ - C - lf * 1.6 - (48 if O == "v" else 40)  # 分支名稱和底下那行字之間要留一段距離
            xs_ = [slot * (i + 0.5) for i in range(m_)]
            lines = "".join(f'<line class="tl{k}" x1="{sw_ / 2:.0f}" y1="{L * 0.92:.0f}" x2="{cx:.0f}" y2="{ct + C * 0.1:.0f}" pathLength="1" stroke-dasharray="1 1"/>' for cx in xs_)
            h_ = (f'<svg width="{sw_}" height="{sh_}" style="position:absolute; left:0; top:0; overflow:visible" fill="none" stroke="{S["fill"]}" stroke-width="4" stroke-linecap="round" stroke-opacity=".55">{lines}</svg>'
                  + mascot(f"m{k}", "l", L, f"position:absolute; left:{(sw_ - L) / 2:.0f}px; top:0;")
                  + "".join(mascot(f"c{k}_{i}", "w", C, f"position:absolute; left:{cx - C / 2:.0f}px; top:{ct:.0f}px;") for i, cx in enumerate(xs_))
                  + "".join(f'<div class="lb" id="l{k}_{i}" style="position:absolute; left:{cx - slot / 2:.0f}px; top:{ct + C + 18:.0f}px; width:{slot:.0f}px; text-align:center; font-size:{lf}px; font-weight:600; white-space:nowrap; opacity:0;">{em(x)}</div>' for i, (cx, x) in enumerate(zip(xs_, br))))
            b = beat(t0, dur, 1.2)
            j_.append(hop(f"#m{k}", t0))
            j_.append(f'tl.fromTo(".tl{k}", {{ attr: {{ "stroke-dashoffset": 1 }} }}, {{ attr: {{ "stroke-dashoffset": 0 }}, duration: 0.4, stagger: 0.08, ease: "power2.inOut" }}, {b(0.35):.2f});')
            for i in range(m_):
                j_.append(pop_in(f"#c{k}_{i}", b(0.6 + i * 0.13)))
                j_.append(f'tl.fromTo("#l{k}_{i}", {{ opacity: 0, y: 10 }}, {{ opacity: 1, y: 0, duration: 0.25, ease: "power2.out" }}, {b(0.7 + i * 0.13):.2f});')
            j_.append(bob(f"#m{k}", t0 + 0.6, hold))
        elif sc == "card":
            rows = it["rows"]
            cw = 640 if O == "v" else (780 if nar else 880)
            hf, rf, cb, rg = (44, 40, 50, 26) if O == "v" else ((50, 44, 54, 26) if len(rows) < 4 else (44, 40, 50, 20))
            peek = mascot(f"m{k}", "w", 130, "position:absolute; right:-36px; top:-48px;") if nar else ""
            beside = "" if nar else mascot(f"m{k}", "w", 280)
            rws = "".join(f'<div class="crow" id="r{k}_{j}" style="display:flex; align-items:center; gap:22px; font-size:{rf}px; font-weight:500; opacity:0;">'
                          f'<div id="ck{k}_{j}" style="flex:none; width:{cb}px; height:{cb}px; border-radius:{cb // 2}px; border:3px solid {S["fill"]}; display:flex; align-items:center; justify-content:center;">{icon("check", cb * 0.62, S["fill"], 3, ui=True)}</div>'
                          f'<span style="white-space:nowrap">{em(r_["text"] if isinstance(r_, dict) else r_)}</span></div>' for j, r_ in enumerate(rows))
            h_ = (f'<div style="{full} gap:70px;">{beside}<div class="card" id="cd{k}" style="position:relative; width:{cw}px; flex-direction:column; align-items:stretch; padding:{"42px 52px" if O == "v" else "36px 56px"}; gap:{rg}px;">'
                  f'{peek}<div style="font-size:{hf}px; font-weight:600; color:{S["em"]}; white-space:nowrap;">{em(it["card_title"])}</div><div style="height:2px; background:{S["chip_off"]}"></div>{rws}</div></div>')
            j_.append(f'tl.fromTo("#cd{k}", {{ opacity: 0, y: 40 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: "back.out(1.6)" }}, {t0:.2f});')
            j_.append(hop(f"#m{k}", t0 + 0.15))
            step = min(0.6, max(0.25, (dur - 1.2) / len(rows)))
            for j, r_ in enumerate(rows):
                rt = cue_time(r_["cue"], f"第 {k + 1} 個重點的清單項") if isinstance(r_, dict) and r_.get("cue") else t0 + 0.45 + j * step
                j_.append(f'tl.fromTo("#r{k}_{j}", {{ opacity: 0, x: -20 }}, {{ opacity: 1, x: 0, duration: 0.3, ease: "power3.out" }}, {rt:.2f});')
                j_.append(draw(f"#ck{k}_{j}", rt + 0.15, ui=True))
            j_.append(bob(f"#m{k}", t0 + 0.8, hold))
        elif sc == "check":
            mk = it.get("marks", "oox")
            cw, ch = (176, 132) if O == "v" else (200, 150)
            ms = 160 if O == "v" else 220
            d_ = ch * 0.66
            cards = "".join(f'<div class="card" id="cc{k}_{i}" style="position:relative; width:{cw}px; height:{ch}px; flex-direction:column; align-items:flex-start; justify-content:center; gap:{ch * 0.12:.0f}px; padding:0 {cw * 0.14:.0f}px;">'
                            + "".join(f'<i style="display:block; height:{ch * 0.08:.0f}px; width:{w}%; border-radius:6px; background:{S["fill"] if w == 55 else S["chip_off"]}"></i>' for w in (55, 100, 80))
                            + f'<div id="cs{k}_{i}" style="position:absolute; left:50%; top:50%; width:{d_:.0f}px; height:{d_:.0f}px; margin:-{d_ / 2:.0f}px 0 0 -{d_ / 2:.0f}px; border-radius:50%; background:{S["fill"] if c == "o" else S["bad"]}; display:flex; align-items:center; justify-content:center; opacity:0;">'
                            f'{icon("check" if c == "o" else "x", d_ * 0.56, "#ffffff", 3.2, ui=True)}</div></div>' for i, c in enumerate(mk))
            row = f'<div style="display:flex; gap:{24 if O == "v" else 30}px;">{cards}</div>'
            rev = f'<div style="display:flex; align-items:center; gap:12px;">{mascot(f"a{k}", "a", ms)}{icon_block(f"q{k}", SEARCH_ICON.get(spec.get("icon_set"), "search"), ms * 0.6, S["alt"])}</div>'
            dirn = "column" if O == "v" else "row"
            h_ = f'<div style="{full} flex-direction:{dirn}; gap:{40 if O == "v" else 80}px;">{mascot(f"m{k}", "w", ms)}{row}{rev}</div>'
            need = 1.1 + len(mk) * 0.32 + 0.3
            b = beat(t0, dur, need)
            j_.append(hop(f"#m{k}", t0))
            j_.append(f'tl.fromTo("#cc{k}_0, ' + ", ".join(f"#cc{k}_{i}" for i in range(1, len(mk))) + f'", {{ opacity: 0, y: 24 }}, {{ opacity: 1, y: 0, duration: 0.3, stagger: 0.1, ease: "power3.out" }}, {b(0.25):.2f});')
            j_.append(hop(f"#a{k}", b(0.6)))
            j_ += icon_in(f"#q{k}", "draw", b(0.75), hold)
            for i, c in enumerate(mk):
                st_ = b(1.1 + i * 0.32)
                j_.append(f'tl.set("#cs{k}_{i} .ico", {{ opacity: 1 }}, {st_:.2f});')
                j_.append(f'tl.fromTo("#cs{k}_{i}", {{ opacity: 0, scale: 1.8 }}, {{ opacity: 1, scale: 1, duration: 0.2, ease: "power3.in" }}, {st_:.2f});')
                if c == "x":
                    j_.append(f'tl.to("#cc{k}_{i}", {{ keyframes: {{ x: [0, -10, 10, -6, 6, 0] }}, duration: 0.4, ease: "none" }}, {st_ + 0.2:.2f});')
            j_.append(bob(f"#a{k}", t0 + 1.2, hold))
        else:  # number
            key = it["key"]
            mnum = re.fullmatch(r"(\d+)(.*)", key)
            kw = len(key) * 0.62 if re.search(r"[A-Za-z0-9]", key) else vis(key)
            kpx = int(min(230 if O == "v" else 320, (560 if O == "v" else 780 if not it.get("icon") else 430 if nar else 520) / max(kw, 0.8)))
            kh = f'<span id="nv{k}" style="display:inline-block; min-width:{len(mnum.group(1))}ch; text-align:right; font-variant-numeric:tabular-nums">{mnum.group(1)}</span>{_h.escape(mnum.group(2))}' if mnum else em(key)
            ic_ = icon_block(f"p{k}", it["icon"], 170 if O == "v" else 220, S["fill"]) if it.get("icon") else ""
            dirn = "column" if O == "v" else "row"
            h_ = f'<div style="{full} flex-direction:{dirn}; gap:{30 if O == "v" else 56}px;">{ic_}<div id="nk{k}" style="font-size:{kpx}px; font-weight:600; color:{S["em"]}; line-height:1; white-space:nowrap;">{kh}</div></div>'
            j_.append(f'tl.fromTo("#nk{k}", {{ opacity: 0, y: -140, scaleY: 1.15, scaleX: 0.9 }}, {{ opacity: 1, y: 0, scaleY: 1.15, scaleX: 0.9, duration: 0.22, ease: "power2.in" }}, {t0:.2f});')
            j_.append(f'tl.to("#nk{k}", {{ scaleY: 0.82, scaleX: 1.14, duration: 0.06, ease: "power1.out" }}, {t0 + 0.22:.2f});')
            j_.append(f'tl.to("#nk{k}", {{ scaleY: 1, scaleX: 1, duration: 0.28, ease: "elastic.out(1, 0.45)" }}, {t0 + 0.28:.2f});')
            if mnum:
                j_.append(f'const cnt{k} = {{ v: 0 }}; tl.fromTo(cnt{k}, {{ v: 0 }}, {{ v: {int(mnum.group(1))}, duration: 0.8, ease: "power2.out", onUpdate: () => {{ document.getElementById("nv{k}").textContent = Math.round(cnt{k}.v); }} }}, {t0:.2f});')
            if ic_:
                j_ += icon_in(f"#p{k}", it.get("motion"), t0 + 0.3, hold)
        body.append(f'<div class="scn" id="sc{k}" style="left:{sx}px; top:{sy}px; width:{sw_}px; height:{sh_}px;">{h_}</div>')
        if O == "h" and lay in ("left", "right"):
            ls_ = it["text"].split("|")
            spk = int(min(tpx, tw * 0.96 / max(map(vis, ls_)))) if len(ls_) > 1 else int(min(tpx, 3 * tw * 0.92 / max(vis(it["text"]), 1)))
            body.append(f'<div class="stt" id="st{k}" style="position:absolute; left:{tx}px; top:{sy}px; width:{tw}px; height:{sh_}px; display:flex; align-items:center; font-size:{spk}px; font-weight:600; line-height:{TLH}; opacity:0;"><div style="text-wrap:balance">{em(it["text"])}</div></div>')
        else:
            spk = int(min(tpx, sw_ * 0.95 / max(vis(it["text"]), 1)))
            body.append(f'<div class="stt" id="st{k}" style="position:absolute; left:{sx}px; top:{ty + (tpx - spk) * 0.6:.0f}px; width:{sw_}px; text-align:center; font-size:{spk}px; font-weight:600; line-height:1.2; white-space:nowrap; opacity:0;">{em(it["text"].replace("|", ""))}</div>')
        js.append(f'tl.set("#sc{k}", {{ opacity: 1 }}, {t0:.2f});')
        js += j_
        js.append(f'tl.fromTo("#st{k}", {{ opacity: 0, {MOVE[lay][0]} }}, {{ opacity: 1, x: 0, y: 0, duration: 0.45, ease: "expo.out" }}, {t0 + 0.1:.2f});')
        js.append(f'tl.set("#d{k}", {{ backgroundColor: "{S["fill"]}" }}, {t0:.2f}); tl.fromTo("#d{k}", {{ scale: 1 }}, {{ scale: 1.5, duration: 0.15, yoyo: true, repeat: 1, ease: "power1.out", immediateRender: false }}, {t0:.2f});')
        js.append(f'tl.to(["#sc{k}", "#st{k}"], {{ opacity: 0, {MOVE[lay][1]}, duration: 0.24, ease: "power2.in" }}, {t1 - 0.24:.2f});')  # 退場比進場快
        shots.append(t1 - 0.5)  # 這一幕所有東西都進場後、離場前
    js.append(f'tl.to(["#head", "#dots"], {{ opacity: 0, duration: 0.3 }}, {te - 0.3:.2f});')
    # 結尾：帶頭的主角＋結尾句，整組在可用範圍裡上下置中
    ew_, emax, elines, a0, a1, ecx = (1400, 96, 2, 120, 830, 960) if O == "h" else (660, 84, 4, 288, 1150, 450)
    epx = fit(spec["ending"], ew_, emax, elines)
    nl = len(spec["ending"].split("|")) if "|" in spec["ending"] else math.ceil(vis(spec["ending"]) * epx / (ew_ * 0.96))
    ems = 200 if O == "v" else 180
    gh = ems + 40 + nl * epx * 1.3
    gtop = a0 + (a1 - a0 - gh) / 2
    body.append(mascot("em_", "l", ems, f"position:absolute; left:{ecx - ems / 2:.0f}px; top:{gtop:.0f}px; opacity:0;"))
    body.append(f'<div class="end" id="end" style="left:{ecx - ew_ // 2}px; width:{ew_}px; top:{gtop + ems + 40:.0f}px; font-size:{epx}px;">{em(spec["ending"])}</div>')
    # 結尾在最後一幕淡出時就進場，兩者交疊；原本等最後一幕淡完才進場，中間空白約 0.3 秒（2026-11-23 試做E 發現）
    end_t = te - 0.1
    js.append(hop("#em_", te - 0.05))
    js.append(f'tl.fromTo("#em_", {{ rotation: 0 }}, {{ keyframes: {{ rotation: [0, -8, 8, -4, 0] }}, duration: 0.6, ease: "none", immediateRender: false }}, {te + 0.7:.2f});')
else:  # big
    keys = [it["key"] for it in items]
    if O == "h":
        body.append(f'<div id="title" style="position:absolute; left:192px; width:1536px; top:{560 if TI else 360}px; text-align:center; font-size:96px; font-weight:500; line-height:1.2;">{em(spec["title"])}</div>')
        if TI:
            body.append(f'<div id="hico" style="position:absolute; left:830px; top:250px;">{icon_block("hib", TI, 260, S["fill"], 1.5)}</div>')
        body.append(f'<div id="head" style="position:absolute; left:240px; top:140px; width:1440px; font-size:60px; font-weight:500; color:{S["ink2"]}; opacity:0;">{em(spec["title"])}</div>')
        hx, hw, hy, hh = 240, 680, 235, 440
        ex, ew, ey = 980, 748, 490
        epx_item = 64
        chips_y = 706
    else:
        body.append(f'<div id="title" style="position:absolute; left:120px; top:312px; width:660px; text-align:center; font-size:80px; font-weight:500; line-height:{TLH};">{em(spec["title"])}</div>')
        if TI:
            body.append(f'<div id="hico" style="position:absolute; left:290px; top:620px;">{icon_block("hib", TI, 320, S["fill"], 1.5)}</div>')
        hx, hw, hy, hh = 160, 580, 705, 250  # 寬度留給壓扁變寬時不出安全範圍； 直式：標題 → 進度列（最多兩行）→ 大字 → 說明
        ex, ew, ey = 120, 660, 985
        epx_item = 52
        chips_y = 552
    for k, it in enumerate(items):
        kw = vis(it["key"]) if not re.search(r"[A-Za-z0-9]", it["key"]) else len(it["key"]) * 0.62
        kpx = int(min(340 if O == "h" else 240, hw * 0.92 / max(kw, 0.8)))
        body.append(f'<div class="hero" id="k{k}" style="position:absolute; left:{hx}px; top:{hy}px; width:{hw}px; height:{hh}px; display:flex; align-items:center; justify-content:{"flex-end" if O == "h" else "center"}; '
                    f'font-size:{kpx}px; font-weight:600; color:{S["em"]}; line-height:1; opacity:0;">{em(it["key"])}</div>')
        if O == "h":  # 說明文字和大字垂直置中對齊，左右排成一組
            ic = f'<div style="margin-bottom:38px">{icon_block(f"eb{k}", it["icon"], 180, S["fill"])}</div>' if it.get("icon") else ""
            body.append(f'<div class="exp" id="e{k}" style="position:absolute; left:{ex}px; top:{hy}px; width:{ew}px; height:{hh}px; display:flex; flex-direction:column; justify-content:center; font-size:{epx_item}px; font-weight:500; line-height:1.25; opacity:0;">{ic}<div>{em(it["text"])}</div></div>')
        else:
            ic = icon_block(f"eb{k}", it["icon"], 130, S["fill"]) if it.get("icon") else ""
            body.append(f'<div class="exp" id="e{k}" style="position:absolute; left:{ex}px; top:{ey}px; width:{ew}px; display:flex; justify-content:center; align-items:center; gap:30px; font-size:{epx_item}px; font-weight:500; line-height:1.25; opacity:0;">{ic}<div>{em(it["text"])}</div></div>')
    chips = "".join(f'<span class="chip" id="c{k}">{em(key)}</span>' for k, key in enumerate(keys))
    cpx = 1536 if O == "h" else 660
    cw_est = sum(vis(key) * (48 if O == "h" else 32) + (84 if O == "h" else 56) for key in keys)
    if cw_est > cpx * (1 if O == "h" else 1.9):
        die("key 加起來太長，進度列放不下：請縮短 key")
    cl = 192 if O == "h" else 120
    body.append(f'<div id="chips" style="position:absolute; left:{cl}px; width:{cpx}px; top:{chips_y}px; text-align:center;">{chips}</div>')
    js.append(f'tl.fromTo("#title", {{ y: 16 }}, {{ y: 0, duration: 0.6, ease: "power3.out" }}, 0);')
    if TI:
        js += icon_in("#hib", spec.get("title_motion"), 0.1, ts[0] - 0.45)
        js.append(f'tl.to("#hico", {{ opacity: 0, scale: 0.8, duration: 0.25, ease: "power2.in" }}, {max(ts[0] - 0.4, 0.6):.2f});')
    if O == "h":
        js.append(f'tl.to("#title", {{ opacity: 0, y: -30, duration: 0.3, ease: "power2.in" }}, {ts[0] - 0.35:.2f});')
        js.append(f'tl.fromTo("#head", {{ opacity: 0, x: -30 }}, {{ opacity: 1, x: 0, duration: 0.4, ease: "power3.out" }}, {ts[0] - 0.1:.2f});')
    js.append(f'tl.fromTo("#chips .chip", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, stagger: 0.05 }}, {ts[0] - 0.3:.2f});')
    for k in range(n):
        t = ts[k]
        # Motion Prompt #011 Squash & stretch：落地時壓扁再彈回
        js.append(f'tl.fromTo("#k{k}", {{ opacity: 0, y: -140, scaleY: 1.15, scaleX: 0.9 }}, {{ opacity: 1, y: 0, scaleY: 1.15, scaleX: 0.9, duration: 0.22, ease: "power2.in" }}, {t - 0.22:.2f});')
        js.append(f'tl.to("#k{k}", {{ scaleY: 0.82, scaleX: 1.14, duration: 0.06, ease: "power1.out" }}, {t:.2f});')
        js.append(f'tl.to("#k{k}", {{ scaleY: 1, scaleX: 1, duration: 0.28, ease: "elastic.out(1, 0.45)" }}, {t + 0.06:.2f});')
        dx, dy = (40, 0) if O == "h" else (0, 30)
        js.append(f'tl.fromTo("#e{k}", {{ opacity: 0, x: {dx}, y: {dy} }}, {{ opacity: 1, x: 0, y: 0, duration: 0.3, ease: "power3.out" }}, {t + 0.1:.2f});')
        if items[k].get("icon"):
            js += icon_in(f"#eb{k}", items[k].get("motion"), t + 0.15, (ts[k + 1] if k + 1 < n else te) - 0.35)
        js.append(f'tl.set("#c{k}", {{ backgroundColor: "{S["fill"]}", color: "{S["on"]}" }}, {t:.2f});')
        js.append(f'tl.fromTo("#c{k}", {{ scale: 1 }}, {{ scale: 1.15, duration: 0.12, yoyo: true, repeat: 1, ease: "power1.out", immediateRender: false }}, {t:.2f});')
        nxt = ts[k + 1] if k + 1 < n else te
        js.append(f'tl.to(["#k{k}", "#e{k}"], {{ opacity: 0, y: -40, duration: 0.2, ease: "power2.in" }}, {nxt - 0.26:.2f});')
    js.append(f'tl.to(["#head", "#title"], {{ opacity: 0, duration: 0.3 }}, {te - 0.3:.2f});')
    if O == "h":
        js.append(f'tl.to("#chips", {{ y: {300 - chips_y}, scale: 1.2, duration: 0.6, ease: "power3.inOut" }}, {te - 0.3:.2f});')
        epx = fit(spec["ending"], 1400, 96, 2)
        body.append(f'<div class="end" id="end" style="left:260px; width:1400px; top:450px; font-size:{epx}px;">{em(spec["ending"])}</div>')
    else:
        js.append(f'tl.to("#chips", {{ y: {400 - chips_y}, duration: 0.6, ease: "power3.inOut" }}, {te - 0.3:.2f});')
        epx = fit(spec["ending"], 660, 80, 4)
        body.append(f'<div class="end" id="end" style="left:120px; width:660px; top:590px; font-size:{epx}px;">{em(spec["ending"])}</div>')

js.append(f'tl.fromTo("#end", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: "power3.out" }}, {(end_t if T == "scene" else te + 0.05):.2f});')
js.append(f'tl.fromTo("#world", {{ scale: 1 }}, {{ scale: 1.03, duration: {TOTAL - te:.2f}, ease: "sine.inOut" }}, {te:.2f});  // 結尾輕輕推近')
js.append(f'tl.to("#fade", {{ opacity: 1, duration: 0.5, ease: "power1.in" }}, {TOTAL - 0.5:.2f});')
rep = max(1, math.ceil(TOTAL / 4) - 1)
if S["glow1"]:
    js.insert(0, f'tl.fromTo("#g1", {{ scale: 0.94 }}, {{ scale: 1.06, duration: 4, ease: "sine.inOut", yoyo: true, repeat: {rep} }}, 0);')
if S["glow2"]:
    js.insert(0, f'tl.fromTo("#g2", {{ scale: 1.05 }}, {{ scale: 0.95, duration: 4.6, ease: "sine.inOut", yoyo: true, repeat: {max(1, rep - 1)} }}, 0);')

cap_rows = "".join(f'\n        <div class="cap" data-s="{c["start"]}" data-e="{c["end"]}"><span>{_h.escape(c["text"])}</span></div>' for c in caps)
page = f"""<!doctype html>
<html lang="{'zh-Hant' if lang == 'zh' else 'en'}">
  <!-- 輕量模式產生（scripts/quick_build.py，模板 {T}、風格 {spec["style"]}）。要改內容請改 spec.json 再重跑，不要手改這份。
       Motion Prompt #003、#010、#011 · MIT © 2026 Shohei Ohtaki；圖示 {ICON_CREDIT[spec.get("icon_set", "lucide")]} -->
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>{css_common}    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{W}" data-height="{H}">
      <div id="world">
        {glows}
        {chr(10).join("        " + b for b in body).lstrip()}
      </div>
      <div id="fade"></div>
      <div id="captions">
        <!-- captions:begin -->{cap_rows}
        <!-- captions:end -->
      </div>
      <audio id="voice" class="clip" src="assets/audio/voice.mp3" data-start="0" data-track-index="5" data-volume="1"></audio>
      <audio id="bgm" class="clip" src="assets/bgm/bgm.mp3" data-start="0" data-track-index="6" data-volume="{VOL}"></audio>
{sfx_html}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      {(chr(10) + "      ").join(js)}
      document.querySelectorAll(".cap").forEach((g) => {{
        tl.set(g, {{ opacity: 1 }}, +g.dataset.s);
        tl.set(g, {{ opacity: 0 }}, +g.dataset.e);
      }});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
open("index.html", "w", encoding="utf-8").write(page)
print(f"已產生 index.html：{'橫式' if O == 'h' else '直式'}、模板 {T}、風格 {spec['style']}、{n} 個重點，片長 {TOTAL} 秒")
print(f"配樂 {mname}，data-volume {VOL}；字幕 {len(caps)} 組；音效 {len(sfx)} 個")
if ts[0] > 4.3:
    print(f"提醒：第一個重點在第 {ts[0]:.1f} 秒才出現。輕量模式要第一句就帶出主題、約 4 秒內進第一個重點，考慮把開場台詞縮短")
if dropped:
    print("和結尾大字重複、已拿掉的字幕：" + "、".join(dropped))
# 給 audio_levels.py 的空檔：詞與詞間隔 0.5 秒以上，避開音效
sfx_t = [x for x, _ in sfx]
gaps = []
for w1, w2 in zip(words, words[1:]):
    s, g = w1["t"] + w1["d"] + 0.05, w2["t"] - (w1["t"] + w1["d"]) - 0.1
    if g >= 0.4 and all(not (x - 0.1 <= s <= x + 0.8) for x in sfx_t):
        gaps.append((g, s))
gaps.sort(reverse=True)
if gaps:
    print("量音量的空檔（給 audio_levels.py）：" + " ".join(f"{s:.2f}:{min(g, 1.0):.2f}" for g, s in gaps[:3]))
snap = [0.5] + (shots + [te] if T == "scene" else [t + 0.8 for t in ts[-1:]]) + [te + 1.0]  # scene：每一幕各一張，加上換到結尾那一刻
print("截圖秒數（直接給 snapshot --at）：" + ",".join(f"{x:.1f}" for x in snap))
