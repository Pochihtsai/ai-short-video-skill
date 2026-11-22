"""從成品 mp4 抽格拼成一張圖，驗收用（Mac、Windows 都能跑，需要 ffmpeg）。
用法：python frame_sheet.py video.mp4 out.png [t1 t2 ...]
沒給秒數時，依影片長度平均取 8 格；自己給秒數時幾個都可以（每列 4 格，不滿的格子是黑色）。
直式每格寬 270，橫式每格寬 480。"""
import subprocess, sys, tempfile, os, math
if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文和全形符號會出錯；統一用 UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

video, out = sys.argv[1], sys.argv[2]
probe = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration", "-of", "default=nw=1:nk=1", video], text=True).split()
w, h, dur = int(probe[0]), int(probe[1]), float(probe[2])
times = sys.argv[3:] or [f"{dur * (i + 0.5) / 8:.2f}" for i in range(8)]
cell = 270 if h > w else 480
with tempfile.TemporaryDirectory() as tmp:
    frames = []
    for i, t in enumerate(times):
        f = os.path.join(tmp, f"f_{i}.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-nostdin", "-ss", t, "-i", video, "-frames:v", "1", "-vf", f"scale={cell}:-2", f], check=True)
        frames.append(f)
    cols = min(4, len(frames))
    rows = math.ceil(len(frames) / cols)
    # tile 濾鏡照順序排成 cols×rows 的格子，不滿的格子是黑色
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-nostdin", "-i", os.path.join(tmp, "f_%d.png"),
                    "-vf", f"tile={cols}x{rows}", "-frames:v", "1", out], check=True)
print(out)
