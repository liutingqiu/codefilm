#!/usr/bin/env python3
"""Turn a cut list over existing footage into a compose manifest (EDIT route).

  python scripts/edit_plan.py cuts.json -o manifest.json

cuts.json (object or plain array):
{
  "out": "edit.mp4", "width": 1920, "height": 1080, "fps": 30,
  "clips": [
    {"file": "footage/a.mp4", "in": 3.0, "out": 8.0},
    {"file": "footage/b.mp4", "in": 0.0, "out": 5.0}
  ],
  "audio": [{"file": "vo.wav", "delay_ms": 0}],
  "subtitles": "subs.srt"
}

Then:
  python scripts/compose.py manifest.json

The manifest resolves files to absolute paths so it can live anywhere.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cf_common import CFError, die, probe, write_json  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cuts")
    ap.add_argument("-o", "--manifest", default="manifest.json")
    ap.add_argument("--out", default=None, help="output video path (overrides cuts.out)")
    a = ap.parse_args()
    data = json.loads(Path(a.cuts).read_text(encoding="utf-8"))
    if isinstance(data, list):
        data = {"clips": data}
    clips = data.get("clips") or data.get("shots") or []
    if not clips:
        die("cuts JSON has no clips")
    base = Path(a.cuts).resolve().parent
    shots = []
    total = 0.0
    for c in clips:
        f = Path(c["file"])
        src = f if f.is_absolute() else (base / f)
        if not src.exists():
            die(f"clip not found: {src}")
        info = probe(src)
        t0 = float(c.get("in", 0) or 0)
        t1 = float(c.get("out", info["duration"]) or info["duration"])
        t0 = max(0.0, min(t0, info["duration"]))
        t1 = max(t0 + 1e-3, min(t1, info["duration"]))
        shots.append({"file": str(src.resolve()), "trim_start": round(t0, 4), "trim_end": round(t1, 4)})
        total += t1 - t0
    out = a.out or data.get("out") or "edit.mp4"
    out_path = Path(out)
    if not out_path.is_absolute():
        out_path = (Path.cwd() / out_path).resolve()
    manifest = {
        "out": str(out_path),
        "width": int(data.get("width", 1920)),
        "height": int(data.get("height", 1080)),
        "fps": float(data.get("fps", 30)),
        "total": round(total, 3),
        "shots": shots,
    }
    if data.get("audio"):
        audio = []
        for au in data["audio"]:
            p = Path(au["file"])
            src = p if p.is_absolute() else (base / p)
            if not src.exists():
                die(f"audio not found: {src}")
            audio.append({**au, "file": str(src.resolve())})
        manifest["audio"] = audio
    if data.get("subtitles"):
        p = Path(data["subtitles"])
        src = p if p.is_absolute() else (base / p)
        if not src.exists():
            die(f"subtitles not found: {src}")
        manifest["subtitles"] = str(src.resolve())
    if data.get("style"):
        manifest["style"] = data["style"]
    write_json(a.manifest, manifest)
    print(f"{len(shots)} shots, {total:.2f}s -> {a.manifest}")


if __name__ == "__main__":
    try:
        main()
    except CFError as e:
        die(str(e))
