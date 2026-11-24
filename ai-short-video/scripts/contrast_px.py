"""從實際畫面量文字和背景的對比，抓「字被背景吃掉」。要用裝了 numpy、pillow 的 edge-tts 環境：
  <edge-tts 環境的 python> -I <skill>/scripts/contrast_px.py <影片資料夾> <秒數,秒數,...> [門檻，預設 3]
做法：同一個時間點截兩張圖，一張正常、一張把字變透明，兩張的差就是字，字底下的就是真正的背景。
所以整塊變淡、光暈、圖片、疊在圖形上的字都算得到（hyperframes check 不會算整塊變淡，2026-11-24 實測畫面只有 2.49 仍判通過）。
秒數要挑東西都進場、停好的時候；正在淡入淡出的字會被量成低對比。寫在圖片裡的字、SVG 裡已轉成路徑的字量不到。"""
import glob, os, re, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image
if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950；統一用 UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if len(sys.argv) < 3:
    sys.exit(__doc__)
proj, at = os.path.abspath(sys.argv[1]), sys.argv[2]
MIN = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
CELL = 12
HIDE = ("<style>* { color: transparent !important; -webkit-text-fill-color: transparent !important; text-shadow: none !important; }"
        " svg text, svg tspan { fill: transparent !important; stroke: transparent !important; }</style>")


def shoot(hide):
    d = tempfile.mkdtemp(prefix="contrast_")
    for f in os.listdir(proj):
        if f not in ("renders", ".hyperframes", "snapshots", "index.html") and not f.startswith("."):
            s = os.path.join(proj, f)
            shutil.copytree(s, os.path.join(d, f)) if os.path.isdir(s) else shutil.copy(s, d)
    h = open(os.path.join(proj, "index.html"), encoding="utf-8").read()
    if hide:
        h = h.replace("</head>", HIDE + "</head>", 1)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(h)
    r = subprocess.run([shutil.which("npx"), "hyperframes", "snapshot", "--at", at, "--no-end", "-o", os.path.join(d, "snaps")], cwd=d, capture_output=True, text=True, encoding="utf-8", errors="replace")
    fs = {}
    for p in glob.glob(os.path.join(d, "snaps", "*.png")):
        m = re.search(r"at-([\d.]+)s\.png$", os.path.basename(p))
        if m:
            fs[float(m.group(1))] = np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
    shutil.rmtree(d, ignore_errors=True)
    if not fs:
        sys.exit("截圖失敗：\n" + (r.stdout + r.stderr)[-1500:])
    return fs


def lum(a):
    a = a / 255.0
    a = np.where(a <= 0.03928, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    return a @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def groups(mask):  # 相鄰的格子併成一塊文字
    h, w = mask.shape
    seen = np.zeros_like(mask)
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        st, cells = [(y0, x0)], []
        seen[y0, x0] = True
        while st:
            y, x = st.pop()
            cells.append((y, x))
            for yy in range(max(0, y - 1), min(h, y + 2)):
                for xx in range(max(0, x - 2), min(w, x + 3)):
                    if mask[yy, xx] and not seen[yy, xx]:
                        seen[yy, xx] = True
                        st.append((yy, xx))
        yield cells


full, bare = shoot(False), shoot(True)
bad, lowest, nbox = 0, None, 0
for t in sorted(full):
    if t not in bare:
        continue
    A, B = full[t], bare[t]
    la, lb = lum(A), lum(B)
    c = (np.maximum(la, lb) + 0.05) / (np.minimum(la, lb) + 0.05)
    diff = np.abs(A - B).max(axis=2) > 12
    H, W = diff.shape
    hc, wc = H // CELL, W // CELL
    cells = diff[:hc * CELL, :wc * CELL].reshape(hc, CELL, wc, CELL).sum(axis=(1, 3)) >= 4
    for g in groups(cells):
        ys, xs = [y for y, _ in g], [x for _, x in g]
        y0, y1, x0, x1 = min(ys) * CELL, (max(ys) + 1) * CELL, min(xs) * CELL, (max(xs) + 1) * CELL
        if (y1 - y0) < 18 or (x1 - x0) < 18:
            continue
        # 每個直條取最實的筆畫（避開反鋸齒的邊），再看最不利的那一段，字有一半壓在亮處也抓得到
        cols = []
        step = max(24, y1 - y0)
        for x in range(x0, x1, step):
            m = diff[y0:y1, x:min(x + step, x1)]
            if m.sum() >= 30:
                cols.append(np.percentile(c[y0:y1, x:min(x + step, x1)][m], 85))
        if not cols:
            continue
        v = float(min(cols))
        nbox += 1
        if lowest is None or v < lowest[0]:
            lowest = (v, t, x0, y0)
        if v < MIN:
            bad += 1
            print(f"不足 {MIN:g}：{v:.2f}  第 {t:g} 秒  左 {x0} 上 {y0} 寬 {x1 - x0} 高 {y1 - y0}")
print(f"量了 {len(full)} 個時間點、{nbox} 塊文字，不足 {MIN:g} 的 {bad} 塊" + (f"；最低 {lowest[0]:.2f}（第 {lowest[1]:g} 秒，左 {lowest[2]} 上 {lowest[3]}）" if lowest else ""))
