"""把選好的配樂剪成影片長度、統一響度、結尾淡出。用法：
  python -I prep_music.py 原曲.mp3 assets/bgm/bgm.mp3 影片秒數 [從原曲第幾秒開始]
做法：從起點剪「影片秒數」那麼長，用 loudnorm 正規化到 -20 LUFS，最後 2 秒淡出。需要 ffmpeg。
原曲開頭太安靜時，給第四個參數跳過，例如從第 5 秒開始。"""
import subprocess, sys
if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文和全形符號會出錯；統一用 UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

src, out, dur = sys.argv[1], sys.argv[2], float(sys.argv[3])
start = float(sys.argv[4]) if len(sys.argv) > 4 else 0
af = f"loudnorm=I=-20:TP=-2:LRA=11,afade=t=out:st={max(0, dur - 2):.2f}:d=2"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", str(dur), "-i", src,
                "-af", af, "-ar", "44100", "-b:a", "192k", out], check=True)
print(f"已輸出 {out}：{dur:g} 秒（原曲第 {start:g} 秒起），-20 LUFS，結尾 2 秒淡出")
