"""從成品 mp4 抽 8 格拼成一張圖，驗收用（Mac、Windows 都能跑，需要 ffmpeg）。
用法：python frame_sheet.py video.mp4 out.png [t1 t2 ... t8]
沒給秒數時，依影片長度平均取 8 格；直式每格寬 270，橫式每格寬 480。"""
import subprocess, sys, tempfile, os
if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文和全形符號會出錯；統一用 UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

video, out = sys.argv[1], sys.argv[2]
probe = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration", "-of", "default=nw=1:nk=1", video], text=True).split()
w, h, dur = int(probe[0]), int(probe[1]), float(probe[2])
times = sys.argv[3:] or [f"{dur * (i + 0.5) / 8:.2f}" for i in range(8)]
cell = 270 if h > w else 480
with tempfile.TemporaryDirectory() as tmp:
    frames = []
    for i, t in enumerate(times[:8]):
        f = os.path.join(tmp, f"f_{i}.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", t, "-i", video, "-frames:v", "1", "-vf", f"scale={cell}:-2", f], check=True)
        frames.append(f)
    args = ["ffmpeg", "-v", "error", "-y"]
    for f in frames:
        args += ["-i", f]
    args += ["-filter_complex", "[0][1][2][3]hstack=4[a];[4][5][6][7]hstack=4[b];[a][b]vstack", out]
    subprocess.run(args, check=True)
print(out)
