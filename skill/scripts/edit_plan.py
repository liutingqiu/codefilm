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

The manifest resolves files to absolute paths so it can live anywhere. A relative
`out` in cuts.json is resolved next to the generated manifest; `--out` is relative
to the current working directory.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cf_common import CFError, die, probe, write_json  # noqa: E402


def _num(v, what: str) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        die(f"{what} must be a number, got {v!r}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cuts")
    ap.add_argument("-o", "--manifest", default="manifest.json")
    ap.add_argument("--out", default=None, help="output video path (overrides cuts.out; relative to cwd)")
    a = ap.parse_args()
    data = json.loads(Path(a.cuts).read_text(encoding="utf-8"))
    if isinstance(data, list):
        data = {"clips": data}
    if not isinstance(data, dict):
        die("cuts JSON must be an object or an array of clips")
    clips = data.get("clips") or data.get("shots") or []
    if not isinstance(clips, list) or not clips:
        die("cuts JSON has no clips")
    base = Path(a.cuts).resolve().parent
    shots = []
    total = 0.0
    for i, c in enumerate(clips):
        if not isinstance(c, dict) or not c.get("file"):
            die(f"clip {i}: missing file")
        f = Path(c["file"])
        src = f if f.is_absolute() else (base / f)
        if not src.exists():
            die(f"clip not found: {src}")
        info = probe(src)
        duration = float(info["duration"])
        t0 = _num(c.get("in", 0), f"clip {i} in")
        t1_raw = c.get("out")
        t1 = duration if t1_raw in (None, "") else _num(t1_raw, f"clip {i} out")
        t0 = max(0.0, min(t0, duration))
        t1 = max(0.0, min(t1, duration))
        if t1 <= t0 + 1e-3:
            die(f"clip {i}: out ({t1:g}s) must be after in ({t0:g}s)")
        shots.append({"file": str(src.resolve()), "trim_start": round(t0, 4), "trim_end": round(t1, 4)})
        total += t1 - t0
    manifest_path = Path(a.manifest).resolve()
    manifest_dir = manifest_path.parent
    if a.out:
        out_path = Path(a.out).expanduser()
        if not out_path.is_absolute():
            out_path = (Path.cwd() / out_path).resolve()
    else:
        out = data.get("out") or "edit.mp4"
        out_path = Path(out).expanduser()
        if not out_path.is_absolute():
            out_path = (manifest_dir / out_path).resolve()
    manifest = {
        "out": str(out_path),
        "width": int(_num(data.get("width", 1920), "width")),
        "height": int(_num(data.get("height", 1080), "height")),
        "fps": _num(data.get("fps", 30), "fps"),
        "total": round(total, 3),
        "shots": shots,
    }
    if manifest["width"] <= 0 or manifest["height"] <= 0 or manifest["fps"] <= 0:
        die("width, height and fps must be positive")
    if data.get("audio"):
        if not isinstance(data["audio"], list):
            die("audio must be a list")
        audio = []
        for i, au in enumerate(data["audio"]):
            if not isinstance(au, dict) or not au.get("file"):
                die(f"audio {i}: missing file")
            p = Path(au["file"])
            src = p if p.is_absolute() else (base / p)
            if not src.exists():
                die(f"audio not found: {src}")
            audio.append({**au, "file": str(src.resolve())})
        manifest["audio"] = audio
    if data.get("subtitles"):
        if not isinstance(data["subtitles"], str):
            die("subtitles must be a path string")
        p = Path(data["subtitles"])
        src = p if p.is_absolute() else (base / p)
        if not src.exists():
            die(f"subtitles not found: {src}")
        manifest["subtitles"] = str(src.resolve())
    if data.get("style"):
        manifest["style"] = data["style"]
    write_json(manifest_path, manifest)
    print(f"{len(shots)} shots, {total:.2f}s -> {manifest_path}  (video: {out_path})")


if __name__ == "__main__":
    try:
        main()
    except CFError as e:
        die(str(e))
