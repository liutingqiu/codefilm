import asyncio
import json
import re
import subprocess
from pathlib import Path

import edge_tts

LINES = [
    ("s1", "脑子里，有一百个想法。"),
    ("s2", "它们散落在便签、聊天和文档里。"),
    ("s3", "拾光，把它们收成一束光。"),
    ("s4", "先记下来。一句话，一张图，都可以。"),
    ("s5", "拾光会连起相关的内容，理出下一步。"),
    ("s6", "然后，把它做出来。"),
    ("s7", "从散落，到清晰。"),
    ("s8", "拾光，把想法变成下一步。"),
]
VOICE = "zh-CN-XiaoxiaoNeural"


def audio_duration(path: Path) -> float:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path)],
                       capture_output=True, text=True, errors="replace")
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", (r.stderr or "") + (r.stdout or ""))
    if not m:
        raise RuntimeError(f"cannot read duration: {path}")
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


async def gen(text: str, out: Path):
    c = edge_tts.Communicate(text, VOICE, rate="-3%", pitch="-1Hz")
    audio = b""
    async for ch in c.stream():
        if ch["type"] == "audio":
            audio += ch["data"]
    out.write_bytes(audio)


async def main():
    rows = []
    Path("vo").mkdir(exist_ok=True)
    for name, text in LINES:
        p = Path("vo") / f"{name}.mp3"
        if not p.exists() or p.stat().st_size < 1000:
            await gen(text, p)
        dur = audio_duration(p)
        rows.append({"id": name, "text": text, "file": str(p), "duration": round(dur, 3)})
        print(f"{name} {dur:.2f}s  {text}")
    Path("vo.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print("total", round(sum(r["duration"] for r in rows), 2), "s")


asyncio.run(main())
