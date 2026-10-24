#!/usr/bin/env python3
"""Compose a finished film from a manifest: shots + voice timeline + optional SRT.

  python scripts/compose.py manifest.json [--keep-build]

manifest.json:
{
  "out": "final.mp4",
  "width": 720, "height": 1280, "fps": 24, "total": 32,
  "shots": [{"file": "v1.mp4"}, {"file": "v2.mp4"}],
  "audio": [{"file": "vo0.wav", "delay_ms": 0, "volume": 1.0}],
  "subtitles": "subs.srt",
  "style": "FontName=Microsoft YaHei,FontSize=10,Outline=1.5,MarginV=90"
}

Paths resolve relative to the manifest. Shots are normalized, concatenated, voices are
delayed/mixed, subtitles burned (falling back to no-subtitles on failure), +faststart.
`total` is optional: when absent it is summed from the probed shot durations.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cf_common import CFError, die, ensure_dir, need, probe, run  # noqa: E402

DEFAULT_STYLE_V = ("FontName=Microsoft YaHei,FontSize=28,PrimaryColour=&H00FFFFFF,"
                   "OutlineColour=&H00000000,BorderStyle=1,Outline=2,Alignment=2,MarginV=90")
DEFAULT_STYLE_H = ("FontName=Microsoft YaHei,FontSize=36,PrimaryColour=&H00FFFFFF,"
                   "OutlineColour=&H00000000,BorderStyle=1,Outline=2,Alignment=2,MarginV=48")


def _num(v, what: str) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        die(f"{what} must be a number, got {v!r}")


def default_style(width: int, height: int) -> str:
    return DEFAULT_STYLE_V if height >= width else DEFAULT_STYLE_H


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest")
    ap.add_argument("--keep-build", action="store_true")
    a = ap.parse_args()
    need("ffmpeg")
    mpath = Path(a.manifest).resolve()
    m = json.loads(mpath.read_text(encoding="utf-8"))
    if not isinstance(m, dict):
        die("manifest must be a JSON object")
    base = mpath.parent
    out_name = m.get("out") or "final.mp4"
    if not isinstance(out_name, (str, Path)):
        die("out must be a path string")
    out = (base / out_name).resolve() if not Path(out_name).is_absolute() else Path(out_name)
    ensure_dir(out.parent)
    width = int(_num(m.get("width", 720), "width"))
    height = int(_num(m.get("height", 1280), "height"))
    fps = _num(m.get("fps", 24), "fps")
    if width <= 0 or height <= 0 or fps <= 0:
        die("width, height and fps must be positive")
    if width % 2 or height % 2:
        die("width and height must be even for yuv420p output")
    total = _num(m.get("total") or 0, "total")
    shots = m.get("shots") or []
    audio = m.get("audio") or []
    if not isinstance(shots, list) or not shots:
        die("manifest has no shots")
    if not isinstance(audio, list):
        die("manifest audio must be a list")
    build = ensure_dir(out.parent / (out.stem + ".build"))

    try:
        paths = []
        computed = 0.0
        for i, s in enumerate(shots):
            if not isinstance(s, dict) or not s.get("file"):
                die(f"shot {i}: missing file")
            src = (base / s["file"]).resolve() if not Path(s["file"]).is_absolute() else Path(s["file"])
            if not src.exists():
                die(f"shot not found: {src}")
            info = probe(src)
            src_dur = float(info["duration"])
            trim_start = _num(s.get("trim_start", 0), f"shot {i} trim_start")
            trim_end_raw = s.get("trim_end")
            trim_end = src_dur if trim_end_raw in (None, "") else _num(trim_end_raw, f"shot {i} trim_end")
            trim_start = max(0.0, min(trim_start, src_dur))
            trim_end = max(0.0, min(trim_end, src_dur))
            if trim_end <= trim_start + 1e-3:
                die(f"shot {i}: trim_end ({trim_end:g}s) must be after trim_start ({trim_start:g}s)")
            shot = build / f"shot{i:02d}.mp4"
            cmd = ["ffmpeg", "-v", "error", "-y"]
            if trim_start > 0:
                cmd += ["-ss", f"{trim_start:.4f}"]
            cmd += ["-i", str(src), "-t", f"{trim_end - trim_start:.4f}"]
            cmd += ["-vf",
                    f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                    f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,"
                    f"fps={fps:g},format=yuv420p",
                    "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(shot)]
            run(cmd, cwd=build)
            paths.append(shot)
            computed += trim_end - trim_start
        (build / "shots.txt").write_text("".join(f"file '{p.name}'\n" for p in paths), encoding="utf-8")

        if total <= 0:
            total = round(computed, 3)
        elif total > computed + 0.05:
            print(f"codefilm: total {total:g}s exceeds the shots ({computed:.2f}s); "
                  f"using {computed:.2f}s", file=sys.stderr)
            total = round(computed, 3)
        if total <= 0:
            die("total duration is zero")

        subs_src = m.get("subtitles")
        has_subs = False
        if subs_src:
            if not isinstance(subs_src, str):
                die("subtitles must be a path string")
            sp = (base / subs_src).resolve() if not Path(subs_src).is_absolute() else Path(subs_src)
            if sp.exists():
                shutil.copyfile(sp, build / "subs.srt")
                has_subs = True
            else:
                print(f"codefilm: subtitles missing, skipping: {sp}", file=sys.stderr)

        for i, au in enumerate(audio, 1):
            if not isinstance(au, dict) or not au.get("file"):
                die(f"audio {i}: missing file")
            ap_ = (base / au["file"]).resolve() if not Path(au["file"]).is_absolute() else Path(au["file"])
            if not ap_.exists():
                die(f"audio not found: {ap_}")
            shutil.copyfile(ap_, build / f"vo{i}{ap_.suffix or '.wav'}")

        n = len(audio)
        parts = []
        for i, au in enumerate(audio, 1):
            delay = int(_num(au.get("delay_ms", 0), f"audio {i} delay_ms"))
            vol = _num(au.get("volume", 1.0), f"audio {i} volume")
            parts.append(f"[{i}:a]adelay={delay}:all=1,volume={vol}[a{i}]")
        mix = "".join(f"[a{i}]" for i in range(1, n + 1)) + f"amix=inputs={n}:normalize=0:duration=longest,apad[out]"

        def build_cmd(subs: bool, dest: Path):
            cmd = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "shots.txt"]
            for i, au in enumerate(audio, 1):
                ext = Path(au["file"]).suffix or ".wav"
                cmd += ["-i", f"vo{i}{ext}"]
            cmd += ["-map", "0:v"]
            if n:
                cmd += ["-filter_complex", ";".join(parts + [mix]), "-map", "[out]"]
            if subs:
                style = m.get("style") or default_style(width, height)
                cmd += ["-vf", f"subtitles=subs.srt:force_style='{style}'"]
            cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20"]
            if n:
                cmd += ["-c:a", "aac", "-b:a", "192k"]
            cmd += ["-t", f"{total:.6f}", "-movflags", "+faststart", str(dest)]
            return cmd

        tmp = build / "out.mp4"
        ok = False
        if has_subs:
            try:
                run(build_cmd(True, tmp), cwd=build)
                ok = True
            except CFError:
                print("codefilm: subtitle burn failed, retrying without subtitles", file=sys.stderr)
        if not ok:
            run(build_cmd(False, tmp), cwd=build)
        shutil.copyfile(tmp, out)
        print(f"OK {out} {out.stat().st_size}B "
              f"(total={total}s, shots={len(shots)}, voices={n}, subs={has_subs})")
    finally:
        if not a.keep_build:
            shutil.rmtree(build, ignore_errors=True)


if __name__ == "__main__":
    try:
        main()
    except CFError as e:
        die(str(e))
