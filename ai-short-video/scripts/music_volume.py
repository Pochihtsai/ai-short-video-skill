"""輸出影片之前，先算配樂的 data-volume 要設多少。用法：
  python -I music_volume.py voice.mp3 words.json bgm.mp3 [目標差距 dB，預設 16]
做法：用 words.json 找出配音連續講話的段落，和 0.5 秒以上的空檔。
分別量講話段的配音音量、空檔裡配樂檔（已用 prep_music.py 處理過）的音量，
算出讓空檔的音樂比配音低「目標差距」的 data-volume。規則是低 14–19 dB，取中間的 16。
不用先輸出影片，也不會量到音效。個別空檔超出 14–19 dB 時會逐一列出。輸出影片後仍要用 audio_levels.py 複查。需要 ffmpeg。"""
import json, math, re, subprocess, sys
if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文和全形符號會出錯；統一用 UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

voice, words_path, bgm = sys.argv[1], sys.argv[2], sys.argv[3]
target = float(sys.argv[4]) if len(sys.argv) > 4 else 16
words = json.load(open(words_path, encoding="utf-8"))

def mean_db(path, s, d):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{s:.3f}", "-t", f"{d:.3f}", "-i", path, "-af", "volumedetect", "-vn", "-f", "null", "-"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    m = re.search(r"mean_volume: (-?[\d.]+) dB", err)
    return float(m.group(1)) if m else None

def avg_db(xs):  # 用能量平均，不是直接平均 dB 數字
    xs = [x for x in xs if x is not None]
    return 10 * math.log10(sum(10 ** (x / 10) for x in xs) / len(xs)) if xs else None

# 講話段：詞與詞間隔不到 0.3 秒就算同一段；空檔：間隔 0.5 秒以上
runs, gaps, s = [], [], words[0]["t"]
for a, b in zip(words, words[1:]):
    end, nxt = a["t"] + a["d"], b["t"]
    if nxt - end >= 0.3:
        runs.append((s, end)); s = nxt
    if nxt - end >= 0.5:
        gaps.append((end + 0.05, nxt - end - 0.1))
runs.append((s, words[-1]["t"] + words[-1]["d"]))
runs = sorted(runs, key=lambda r: r[1] - r[0], reverse=True)[:5]

v = avg_db([mean_db(voice, a, b - a) for a, b in runs])
gap_db = []
if gaps:
    gap_db = [mean_db(bgm, a, d) for a, d in gaps]
    m = avg_db(gap_db)
    where = f"{len(gaps)} 個 0.5 秒以上的空檔"
else:
    m = mean_db(bgm, 0, words[-1]["t"])
    where = "整段（沒有 0.5 秒以上的空檔）"
if v is None or m is None:
    sys.exit("量不到音量：確認檔案路徑和 words.json 是不是同一份配音產生的")
vol = min(1.0, 10 ** ((v - target - m) / 20))
# 依平均算出的音量，最大聲那段空檔可能只比配音低不到 14 dB（曲子某段特別重時常見），這時再往下調到那段低 15 dB（輸出後實測會比這裡估的少約 0.5 dB，留一點餘裕）
loud = max([x for x in gap_db if x is not None], default=None)
lowered = loud is not None and v - (loud + 20 * math.log10(vol)) < 15
if lowered:
    vol = 10 ** ((v - 15 - loud) / 20)
print(f"配音（最長的 {len(runs)} 段講話）：{v:.1f} dB")
print(f"配樂原檔在{where}：{m:.1f} dB")
print(f"建議 data-volume = {vol:.2f}（空檔的音樂會比配音低約 {target:g} dB" + ("；為了讓最大聲的空檔也低 15 dB，已再調低）" if lowered else "）"))
# 依平均算的音量，個別空檔可能超出 14–19 dB（曲子前奏輕、副歌重時常見），逐一列出提醒
off = [(a, v - (x + 20 * math.log10(vol))) for (a, d), x in zip(gaps, gap_db) if x is not None]
bad = [(a, diff) for a, diff in off if not 14 <= diff <= 19]
if bad:
    print("注意：這些空檔的音樂和配音差距超出 14–19 dB（秒數：差距）：" + "、".join(f"{a:.1f} 秒：{diff:.1f} dB" for a, diff in bad))
    print("　　差太多（音樂太小聲）通常是曲子那段比較輕，可以接受；差太少（音樂太大聲）要換起點或降一點音量")
