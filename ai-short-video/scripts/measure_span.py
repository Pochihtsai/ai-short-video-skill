"""量主畫面在畫面上用到多寬，檢查版面有沒有用到這個方向的空間。
用法：python -I measure_span.py video.mp4 秒數 [秒數...]（每一幕挑一個畫面都進場後的秒數）
做法：抽格→灰階→和大幅模糊版相減（柔光背景被消掉，物件邊緣留下）→排除字幕區→
每一欄邊緣像素超過 3 個就算有內容。輸出最左到最右的寬度佔可用範圍的比例，以及左半、右半各有多少欄有內容。
可用範圍：橫式 1536px（中央 80%），直式 768px（x 120–888）。"""
import io, subprocess, sys
import numpy as np
from PIL import Image, ImageFilter
if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文和全形符號會出錯；統一用 UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

video = sys.argv[1]
for t in sys.argv[2:]:
    png = subprocess.check_output(["ffmpeg", "-v", "error", "-ss", t, "-i", video, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"])
    im = Image.open(io.BytesIO(png)).convert("L")
    w, h = im.size
    usable, cap_top = (768, 1140) if h > w else (1536, 830)
    a = np.asarray(im, dtype=float)
    b = np.asarray(im.filter(ImageFilter.GaussianBlur(40)), dtype=float)
    cols = np.where((np.abs(a - b)[:cap_top] > 12).sum(0) > 3)[0]
    if cols.size == 0:
        print(f"t={t}s  沒有偵測到內容")
        continue
    l, r = int(cols.min()), int(cols.max())
    left, right = int((cols < w / 2).sum()), int((cols >= w / 2).sum())
    print(f"t={t}s  x {l}–{r}，寬度佔可用範圍 {100 * (r - l) / usable:.0f}%；有內容的欄：左半 {left}、右半 {right}")
