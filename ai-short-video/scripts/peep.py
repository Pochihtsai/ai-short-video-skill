"""組 Open Peeps 人物（Pablo Stanley 的手繪人物，CC0），產生可以直接貼進 index.html 的 <svg>。
用法：
  python3 -I <skill>/scripts/peep.py list
      列出所有姿勢、表情、髮型、鬍子、配件的名稱。長相看 references/peeps/ 的一覽圖
  python3 -I <skill>/scripts/peep.py make <角色代號> --pose RestingWB,PointingFingerWB --face Calm,Concerned
         --hair ShortVolumed [--beard FullMajestic] [--acc GlassRound] [--ink "#1d2730"] [--fill "#ffffff"]
         [--height 820] -o <輸出檔>
      角色代號用英文小寫（例如 boss、amy），同一支片有好幾個角色時用來分開 id。
      --pose、--face 可以給好幾個，用逗號隔開，第一個是一開始顯示的那個。
      --ink 是線條色。--fill 是填色，會同時染到衣服、皮膚和淺色頭髮，只能用接近白的顏色，不能拿來區分角色。
      人物都面向右邊；要面向左邊時，在 <svg> 外面包一層只負責翻轉的 div 加 transform: scaleX(-1)（GSAP 不要動這層），轉頭角度正負相反。
      --height 是畫面上的高度（像素），寬度依姿勢自動算。

產生的 <svg> 有這幾層（以代號 boss 為例），用 GSAP 控制：
  #boss_b_<姿勢>  每個姿勢一層，只有第一個看得到
  #boss_f_<表情>  每個表情一層，只有第一個看得到
  #boss_head      整顆頭（頭髮＋表情）
換表情、換姿勢：tl.set("#boss_f_Calm", { opacity: 0 }, t); tl.set("#boss_f_Concerned", { opacity: 1 }, t);
轉頭、點頭：tl.to("#boss_head", { rotation: 6, svgOrigin: "410 460", duration: 0.35 }, t);（410 460 是脖子的位置，每個角色都一樣）
同一個角色只用身材、衣服相近的姿勢：每個姿勢本來是不同的人，換姿勢會像換了一個人。"""
import argparse, json, os, re, sys
if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950；統一用 UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "peeps")
P = os.path.join(R, "pieces")
POSES = json.load(open(os.path.join(R, "poses.json"), encoding="utf-8"))
CATS = {"face": "表情", "hair": "髮型", "facialHair": "鬍子", "accessories": "配件"}


def names(cat):
    return sorted(f[len(cat) + 2:-4] for f in os.listdir(P) if f.startswith(cat + "__"))


def piece(cat, name):
    f = os.path.join(P, f"{cat}__{name}.svg")
    if not os.path.exists(f):
        sys.exit(f"找不到{CATS.get(cat, cat)}「{name}」。可以用的有：" + "、".join(names(cat)))
    return open(f, encoding="utf-8").read()


if len(sys.argv) < 2 or sys.argv[1] not in ("list", "make"):
    sys.exit(__doc__)

if sys.argv[1] == "list":
    for c, label in (("standing", "全身站姿"), ("bust", "半身"), ("sitting", "坐姿")):
        print(f"姿勢．{label}：" + "、".join(sorted(n for n, v in POSES.items() if v["cat"] == c)))
    for c, label in CATS.items():
        print(f"{label}：" + "、".join(names(c)))
    print("姿勢名稱結尾的 WB 是上白下黑、BW 是上黑下白；一覽圖在 references/peeps/")
    sys.exit()

ap = argparse.ArgumentParser()
ap.add_argument("cmd"); ap.add_argument("id")
ap.add_argument("--pose", required=True); ap.add_argument("--face", required=True); ap.add_argument("--hair", required=True)
ap.add_argument("--beard"); ap.add_argument("--acc")
ap.add_argument("--ink", default="#1d2730"); ap.add_argument("--fill", default="#ffffff")
ap.add_argument("--height", type=float, default=820); ap.add_argument("-o", required=True)
a = ap.parse_args()
if not re.fullmatch(r"[a-z][a-z0-9]*", a.id):
    sys.exit("角色代號只能用英文小寫和數字，開頭是字母，例如 boss、amy2")
poses, faces = [x.strip() for x in a.pose.split(",")], [x.strip() for x in a.face.split(",")]
for n in poses:
    if n not in POSES:
        sys.exit(f"找不到姿勢「{n}」。用 peep.py list 看名稱")
cats = {POSES[n]["cat"] for n in poses}
if len(cats) > 1:
    sys.exit("同一個角色的姿勢要同一類（全身站姿、半身、坐姿擇一），換類別時頭的位置會跳")

# 外框：所選姿勢的聯集，四周留一點空間給比較大的髮型
M = 60
x0 = min(POSES[n]["x"] for n in poses) - M
y0 = min(POSES[n]["y"] for n in poses) - M - 40
x1 = max(POSES[n]["x"] + POSES[n]["w"] for n in poses) + M
y1 = max(POSES[n]["y"] + POSES[n]["h"] for n in poses) + 10
vw, vh = x1 - x0, y1 - y0
h = a.height
w = h * vw / vh
col = lambda s: s.replace('"INK"', f'"{a.ink}"').replace('"FILL"', f'"{a.fill}"')

body = "".join(f'<g id="{a.id}_b_{n}" opacity="{1 if i == 0 else 0}">{col(piece("pose_" + POSES[n]["cat"], n))}</g>' for i, n in enumerate(poses))
face = "".join(f'<g id="{a.id}_f_{n}" opacity="{1 if i == 0 else 0}">{col(piece("face", n))}</g>' for i, n in enumerate(faces))
extra = ""
if a.beard:
    extra += f'<g transform="translate(123 338)">{col(piece("facialHair", a.beard))}</g>'
if a.acc:
    extra += f'<g transform="translate(47 241)">{col(piece("accessories", a.acc))}</g>'
head = f'<g id="{a.id}_head"><g transform="translate(225 0)"><g>{col(piece("hair", a.hair))}</g><g transform="translate(159 186)">{face}</g>{extra}</g></g>'
svg = (f'<!-- Open Peeps 人物「{a.id}」：插圖 Pablo Stanley（CC0），零件取自 react-peeps（MIT © Emre Çakır） -->\n'
       f'<svg id="{a.id}" viewBox="{x0} {y0} {vw} {vh}" width="{w:.0f}" height="{h:.0f}" style="overflow:visible">{body}{head}</svg>\n')
open(a.o, "w", encoding="utf-8").write(svg)
foot = (y1 - 10 - y0) / vh * h
print(f"已產生 {a.o}：寬 {w:.0f}、高 {h:.0f} 像素，人物最下緣（全身是腳底）約在 svg 頂端往下 {foot:.0f} 像素")
print(f"姿勢層：" + "、".join(f"#{a.id}_b_{n}" for n in poses))
print(f"表情層：" + "、".join(f"#{a.id}_f_{n}" for n in faces))
print(f'轉頭：tl.to("#{a.id}_head", {{ rotation: 6, svgOrigin: "410 460", duration: 0.35, ease: "power2.out" }}, 秒數);')
