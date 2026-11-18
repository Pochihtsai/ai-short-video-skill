"""量成品的整體響度、配音段音量、配音空檔（只剩音樂）的音量（Mac、Windows 都能跑，需要 ffmpeg）。
用法：python audio_levels.py video.mp4 [words.json] 空檔起點:長度 [空檔起點:長度 ...]
目標：空檔的音樂比配音段低 14–19 dB。空檔要避開音效的時間點。
有給 words.json 時，配音段取最長的 5 段連續講話（和 music_volume.py 同一套量法）；
沒給時才用固定的 5–7 秒，但這兩秒裡如果有停頓，配音段會被量得太小聲（2026-11-18 升降桌片少算約 3 dB）。"""
import json, math, re, subprocess, sys
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

args = sys.argv[2:]
if args and args[0].endswith(".json"):
    words = json.load(open(args.pop(0), encoding="utf-8"))
    runs, s = [], words[0]["t"]
    for a, b in zip(words, words[1:]):
        if b["t"] - (a["t"] + a["d"]) >= 0.3:
            runs.append((s, a["t"] + a["d"])); s = b["t"]
    runs.append((s, words[-1]["t"] + words[-1]["d"]))
    runs = sorted(runs, key=lambda r: r[1] - r[0], reverse=True)[:5]
    vals = [float(x.split()[0]) for x in (mean(f"{a:.3f}", f"{b - a:.3f}") for a, b in runs) if x != "量不到"]
    print(f"配音段（最長的 {len(runs)} 段講話）：", f"{10 * math.log10(sum(10 ** (v / 10) for v in vals) / len(vals)):.1f} dB" if vals else "量不到")
else:
    print("配音段 5–7 秒：", mean("5", "2"))
for r in args:
    s, d = r.split(":")
    print(f"空檔 {r}：", mean(s, d))
