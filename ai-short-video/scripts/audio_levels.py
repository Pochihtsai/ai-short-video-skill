"""量成品的整體響度、配音段音量、配音空檔（只剩音樂）的音量（Mac、Windows 都能跑，需要 ffmpeg）。
用法：python audio_levels.py video.mp4 空檔起點:長度 [空檔起點:長度 ...]
目標：空檔的音樂比配音段低 14–19 dB。"""
import re, subprocess, sys
if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文和全形符號會出錯；統一用 UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

video = sys.argv[1]

def run(args):
    return subprocess.run(["ffmpeg", "-hide_banner"] + args + ["-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr

m = re.findall(r"\bI:\s+(-?[\d.]+) LUFS", run(["-i", video, "-af", "ebur128=framelog=quiet"]))
print("整體響度：", (m[-1] + " LUFS") if m else "量不到")

def mean(start, dur):
    m = re.search(r"mean_volume: (-?[\d.]+) dB", run(["-ss", start, "-t", dur, "-i", video, "-af", "volumedetect", "-vn"]))
    return (m.group(1) + " dB") if m else "量不到"

print("配音段 5–7 秒：", mean("5", "2"))
for r in sys.argv[2:]:
    s, d = r.split(":")
    print(f"空檔 {r}：", mean(s, d))
