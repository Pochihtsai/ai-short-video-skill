"""把 `npx hyperframes check --json` 的輸出濃縮成一行一個問題。用法：
  npx hyperframes check --json 2>&1 | python3 check_summary.py
預設略過三個這種單檔做法必有的警告。"""
import json, sys
if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文和全形符號會出錯；統一用 UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SKIP = {"nested_structure_needs_subcomposition", "font_face_local_only", "timeline_track_too_dense"}
t = sys.stdin.read()
d, _ = json.JSONDecoder().raw_decode(t[t.find("{"):])
print("ok", d.get("ok"))
seen = set()

def walk(o):
    if isinstance(o, dict):
        if o.get("severity") in ("error", "warning") and o.get("code") not in SKIP:
            k = (o.get("code"), (o.get("message") or "")[:90])
            if k not in seen:
                seen.add(k)
                print(o["severity"], o.get("code"), "|", (o.get("message") or "")[:220], "|", o.get("selector") or "", o.get("rect") or "")
        for v in o.values():
            walk(v)
    elif isinstance(o, list):
        for v in o:
            walk(v)

walk(d)
