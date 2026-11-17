"""曉臻配音＋逐詞時間。用法：
  python -I tts_words.py script.txt assets/audio/voice.mp3 assets/audio/words.json [voice] [rate]
需要 edge-tts（放在獨立 venv）。台詞會送到微軟的線上服務，不要放敏感內容。"""
import asyncio, json, sys, edge_tts
if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文和全形符號會出錯；統一用 UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

text = open(sys.argv[1], encoding="utf-8").read()
voice = sys.argv[4] if len(sys.argv) > 4 else "zh-TW-HsiaoChenNeural"
rate = sys.argv[5] if len(sys.argv) > 5 else "+10%"

async def main():
    c = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    words = []
    with open(sys.argv[2], "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append({"t": round(ch["offset"] / 1e7, 3), "d": round(ch["duration"] / 1e7, 3), "w": ch["text"]})
    json.dump(words, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False)
    print(" ".join(f"{w['w']}@{w['t']}" for w in words))

asyncio.run(main())
