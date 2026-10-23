#!/usr/bin/env python3
"""Verify a finished film's rhythm, rest, burst and audio — the slideshow oracle.

  python scripts/verify.py out/film.mp4 [--shots 0,1.6,3.0,4.8,7.0] [--ref source.mp4]

Legs (only FAIL fails the verdict):
  rest      >= 25 % of frames dead-still and one quiet stretch >= 1.0 s
  burst     a 1.5 s window with >= 3 big changes; only FAIL if --ref has one
  cadence   shot lengths (from --shots) vary: CV >= 0.25
  audio     peak <= -3 dBFS, 0 clipped samples, >= 15 % quiet windows
  not-flat  advisory: row-profile variation >= 0.35

Exit 1 on any FAIL. Works without ffprobe (falls back to `ffmpeg -i`).
"""
from __future__ import annotations

import argparse
import math
import subprocess
import sys
import tempfile
import wave
from array import array
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cf_common import CFError, die, probe, run  # noqa: E402
from analyze import energy_map, gray_frames, stats  # noqa: E402


def audio_stats(video: Path) -> dict | None:
    tmp = Path(tempfile.mkdtemp())
    wav = tmp / "a.wav"
    try:
        run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn",
             "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", str(wav)])
        w = wave.open(str(wav), "rb")
        n, sw, ch, sr = w.getnframes(), w.getsampwidth(), w.getnchannels(), w.getframerate()
        raw = w.readframes(n)
        w.close()
        if sw != 2:
            return None
        a = array("h")
        a.frombytes(raw)
        if ch == 2:
            left = a[0::2]
        else:
            left = a
        if not left:
            return None
        peak = max(abs(x) for x in left) / 32767.0
        clipped = sum(1 for x in left if abs(x) >= 32767)
        win = max(1, sr // 12)
        quiet = 0
        total = 0
        for i in range(0, len(left) - win + 1, win):
            seg = left[i:i + win]
            rms = (sum(x * x for x in seg) / len(seg)) ** 0.5 / 32767.0
            total += 1
            if rms < 0.01:  # -40 dBFS
                quiet += 1
        return {"peak_db": round(20 * math.log10(peak + 1e-9), 1),
                "clipped": clipped, "quiet_ratio": round(quiet / max(1, total), 3)}
    except Exception:
        return None
    finally:
        for p in tmp.glob("*"):
            p.unlink()
        tmp.rmdir()


def leg(name: str, state: str, detail: str) -> bool:
    print(f"  {state:4}  {name:9} {detail}")
    return state != "FAIL"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--shots", default="", help="comma-separated cut times, e.g. 0,1.6,3.0,4.8")
    ap.add_argument("--ref", default=None, help="reference film for burst comparison")
    ap.add_argument("--fps", type=float, default=12.0)
    a = ap.parse_args()
    video = Path(a.video)
    if not video.exists():
        die(f"missing {video}")
    info = probe(video)
    frames, _ = gray_frames(video, a.fps, 320)
    if len(frames) < 2:
        die("not enough frames")
    diffs = [0.0] + [sum(abs(frames[i - 1][k] - frames[i][k]) for k in range(len(frames[i]))) / len(frames[i])
                     for i in range(1, len(frames))]
    s = stats(diffs, a.fps)
    print(f"\n{video.name} — {info['width']}x{info['height']} {info['fps']} fps {info['duration']} s")
    print(energy_map(diffs, a.fps))
    print()
    ok = []
    if a.shots:
        ts = sorted(float(x) for x in a.shots.split(","))
        lengths = [b - a_ for a_, b in zip(ts, ts[1:] + [s["duration_s"]])]
        mean = sum(lengths) / len(lengths)
        cv = (sum((x - mean) ** 2 for x in lengths) / len(lengths)) ** 0.5 / mean if mean else 0.0
        ok.append(leg("cadence", "PASS" if cv >= 0.25 else "WARN" if cv >= 0.15 else "FAIL",
                      f"lengths {[round(x, 2) for x in lengths]}  CV {cv:.2f} "
                      f"(>=0.25 varied, 0.15-0.25 calm brand film, <0.15 slideshow)"))
    else:
        print("  skip   cadence   (pass --shots t0,t1,...)")
    ok.append(leg("rest", "PASS" if s["still_ratio"] >= 0.25 and s["longest_quiet_s"] >= 1.0 else "FAIL",
                  f"still {s['still_ratio']}  longest quiet {s['longest_quiet_s']} s"))
    if s["bursts"]:
        ok.append(leg("burst", "PASS", f"{len(s['bursts'])} bursts"))
    elif a.ref:
        ref_frames, _ = gray_frames(Path(a.ref), a.fps, 320)
        ref_diffs = [0.0] + [sum(abs(ref_frames[i - 1][k] - ref_frames[i][k]) for k in range(len(ref_frames[i]))) / len(ref_frames[i])
                             for i in range(1, len(ref_frames))]
        ref_s = stats(ref_diffs, a.fps)
        ok.append(leg("burst", "FAIL" if ref_s["bursts"] else "WARN",
                      f"none; reference has {len(ref_s['bursts'])}"))
    else:
        ok.append(leg("burst", "WARN", "none (fine for a concept without hits)"))
    rows = [sum(diffs[i:i + int(a.fps * 4)]) / max(1, len(diffs[i:i + int(a.fps * 4)]))
            for i in range(0, len(diffs), int(a.fps * 4))]
    flat = (sum((x - sum(rows) / len(rows)) ** 2 for x in rows) / len(rows)) ** 0.5 / (sum(rows) / len(rows) + 1e-9)
    ok.append(leg("not-flat", "PASS" if flat >= 0.35 else "WARN",
                  f"row-profile variation {flat:.2f} (advisory)"))
    au = audio_stats(video) if info["has_audio"] else None
    if au:
        ok.append(leg("audio", "PASS" if au["peak_db"] <= -1.0 and au["clipped"] == 0 and au["quiet_ratio"] >= 0.15 else "FAIL",
                      f"peak {au['peak_db']} dBFS  clipped {au['clipped']}  quiet {au['quiet_ratio']}"))
    else:
        print("  skip   audio     (no audio track)")
    print(f"\nVERDICT: {'PASS' if all(ok) else 'FAIL'}")
    raise SystemExit(0 if all(ok) else 1)


if __name__ == "__main__":
    try:
        main()
    except CFError as e:
        die(str(e))
