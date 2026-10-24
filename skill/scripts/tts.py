#!/usr/bin/env python3
"""Generate narration with edge-tts and schedule line timings.

  python scripts/tts.py lines.json -o vo/ --voice zh-CN-XiaoxiaoNeural --gap 0.35
  python scripts/tts.py lines.json -o vo/ --starts starts.json

lines.json:
  [{"id":"s1","text":"脑子里，有一百个想法。","voice":"zh-CN-XiaoxiaoNeural",
    "rate":"-3%","pitch":"-1Hz"}, ...]

Writes <out>/<id>.mp3 and <out>/vo.json:
  [{"id","text","file","duration","start"}, ...]

No word boundaries: Chinese edge-tts does not emit them; scenes are scheduled per line.
Needs: pip install edge-tts; ffmpeg on PATH.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cf_common import CFError, die, ensure_dir, write_json  # noqa: E402


def audio_duration(path: Path) -> float:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path)],
                       capture_output=True, text=True, errors="replace")
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", (r.stderr or "") + (r.stdout or ""))
    if not m:
        raise CFError(f"cannot read audio duration: {path}")
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


async def gen(text: str, out: Path, voice: str, rate: str, pitch: str, volume: str):
    import edge_tts
    c = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume=volume)
    data = b""
    async for ch in c.stream():
        if ch["type"] == "audio":
            data += ch["data"]
    out.write_bytes(data)


async def run(lines: list[dict], out: Path, voice: str, rate: str, pitch: str, volume: str,
              starts: dict | None, gap: float, lead: float, force: bool):
    rows = []
    t = lead
    for line in lines:
        sid = str(line["id"])
        text = str(line["text"])
        v = line.get("voice") or voice
        r = line.get("rate") or rate
        p = line.get("pitch") or pitch
        vol = line.get("volume") or volume
        path = out / f"{sid}.mp3"
        if force or not path.exists() or path.stat().st_size < 1200:
            await gen(text, path, v, r, p, vol)
        dur = audio_duration(path)
        start = float(starts[sid]) if starts and sid in starts else round(t, 3)
        rows.append({"id": sid, "text": text, "file": str(path),
                     "duration": round(dur, 3), "start": start})
        t = start + dur + gap
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("lines", help="lines JSON")
    ap.add_argument("-o", "--out", default="vo", help="output folder")
    ap.add_argument("--voice", default="zh-CN-XiaoxiaoNeural")
    ap.add_argument("--rate", default="-3%")
    ap.add_argument("--pitch", default="-1Hz")
    ap.add_argument("--volume", default="+0%")
    ap.add_argument("--gap", type=float, default=.35, help="seconds between lines (default .35)")
    ap.add_argument("--lead", type=float, default=.2, help="silence before the first line")
    ap.add_argument("--starts", default=None, help="JSON mapping id to start seconds")
    ap.add_argument("--force", action="store_true", help="regenerate existing mp3s")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    try:
        lines = json.loads(Path(a.lines).read_text(encoding="utf-8"))
    except Exception as e:
        die(f"cannot read lines JSON: {e}")
    if not isinstance(lines, list) or not lines:
        die("lines JSON must be a non-empty array")
    starts = None
    if a.starts:
        starts = json.loads(Path(a.starts).read_text(encoding="utf-8"))
    out = ensure_dir(a.out)
    if a.dry_run:
        t = a.lead
        for line in lines:
            dur = 0.0
            p = out / f"{line['id']}.mp3"
            if p.exists():
                dur = audio_duration(p)
            print(f"{line['id']}: start {t:.2f}s (duration {dur:.2f}s)  {line['text']}")
            t += dur + a.gap
        return
    try:
        rows = asyncio.run(run(lines, out, a.voice, a.rate, a.pitch, a.volume,
                               starts, a.gap, a.lead, a.force))
    except ImportError:
        die("edge-tts is missing: pip install edge-tts")
    write_json(out / "vo.json", rows)
    total = max(r["start"] + r["duration"] for r in rows)
    for r in rows:
        print(f"{r['id']}  {r['start']:6.2f}s + {r['duration']:.2f}s  {r['text']}")
    print(f"total {total:.2f}s -> {out / 'vo.json'}")


if __name__ == "__main__":
    try:
        main()
    except CFError as e:
        die(str(e))
