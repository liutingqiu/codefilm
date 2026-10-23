#!/usr/bin/env python3
"""Ingest a reference video: download/copy, probe, extract frames, cuts, audio, contact sheet.

  python scripts/ingest.py <url-or-file> -o work/myfilm [--fps 2] [--scene 0.3] [--no-asr]

Writes into the output folder:
  source.mp4            the local reference
  source.json           metadata, frame times, cut times, audio path
  frames/t0000.00.jpg   one frame every --fps seconds (960 px wide)
  cuts/cut0000.00_before.jpg / _after.jpg
  sheet.png             contact sheet (first 24 samples, 6x4)
  audio.wav             16 kHz mono (only if the source has audio)
  asr.json              word-level transcript (optional, if faster-whisper is installed)

ffprobe is optional: cf_common.probe falls back to parsing `ffmpeg -i`.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cf_common import CFError, die, ensure_dir, extract_frame, have, is_url, probe, run, write_json  # noqa: E402


def download(url: str, out: Path, max_height: int) -> Path:
    if not have("yt-dlp"):
        die("URL input needs yt-dlp: pip install yt-dlp")
    tmpl = str(out / "source.%(ext)s")
    run(["yt-dlp", "-f", f"bv*[height<={max_height}]+ba/b[height<={max_height}]",
         "--merge-output-format", "mp4", "--no-playlist", "--sleep-requests", "0.5",
         "-o", tmpl, url])
    for p in sorted(out.glob("source.*")):
        if p.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov", ".m4v"}:
            return p
    die("download finished but no video file was produced")


def local_copy(src: Path, out: Path) -> Path:
    if not src.exists():
        die(f"file not found: {src}")
    dst = out / f"source{src.suffix.lower() or '.mp4'}"
    if src.resolve() != dst.resolve():
        shutil.copy2(src, dst)
    return dst


def detect_cuts(video: Path, threshold: float) -> list[float]:
    r = run(["ffmpeg", "-v", "info", "-i", str(video), "-vf",
             f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"], check=False)
    text = (r.stderr or "") + (r.stdout or "")
    cuts = []
    for m in re.finditer(r"pts_time:([\d.]+)", text):
        t = round(float(m.group(1)), 3)
        if not cuts or t - cuts[-1] > 0.05:
            cuts.append(t)
    return cuts


def extract_frames(video: Path, out: Path, fps: float, width: int) -> list[float]:
    ensure_dir(out)
    for old in out.glob("t*.jpg"):
        old.unlink()
    tmp = out / "_f%05d.jpg"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf",
         f"fps={fps}:round=down,scale={width}:-2:flags=lanczos",
         "-q:v", "3", str(tmp)])
    times = []
    for i, f in enumerate(sorted(out.glob("_f*.jpg"))):
        t = round(i / fps, 3)
        f.rename(out / f"t{t:07.2f}.jpg")
        times.append(t)
    return times


def contact_sheet(video: Path, out: Path, every: float, cols: int = 6, rows: int = 4,
                  tile_w: int = 320) -> Path:
    run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf",
         f"fps=1/{every}:round=down,scale={tile_w}:-2,"
         f"tile={cols}x{rows}:padding=4:margin=4:color=0x111111",
         "-frames:v", "1", str(out)])
    return out


def extract_audio(video: Path, out: Path) -> Path | None:
    try:
        run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1",
             "-ar", "16000", "-c:a", "pcm_s16le", str(out)])
        return out if out.exists() and out.stat().st_size > 44 else None
    except CFError:
        return None


def transcribe(audio: Path, out: Path) -> dict | None:
    """Optional word-level ASR. Returns None when faster-whisper is absent."""
    try:
        from faster_whisper import WhisperModel  # noqa
    except Exception:
        return None
    try:
        model = WhisperModel("small", device="cpu", compute_type="int8")
        segments, info = model.transcribe(str(audio), word_timestamps=True, vad_filter=True)
        words, segs = [], []
        for seg in segments:
            segs.append({"start": round(seg.start, 3), "end": round(seg.end, 3), "text": seg.text.strip()})
            for w in (seg.words or []):
                words.append({"start": round(w.start, 3), "end": round(w.end, 3), "word": w.word})
        data = {"language": getattr(info, "language", ""), "segments": segs, "words": words}
        write_json(out, data)
        return data
    except Exception as exc:  # ASR is optional; never fail ingest because of it
        print(f"codefilm: ASR skipped ({exc})", file=sys.stderr)
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="URL or local video file")
    ap.add_argument("-o", "--out", required=True, help="project folder")
    ap.add_argument("--fps", type=float, default=2.0, help="analysis frames per second (default 2)")
    ap.add_argument("--width", type=int, default=960, help="analysis frame width (default 960)")
    ap.add_argument("--scene", type=float, default=0.3, help="scene-change threshold 0..1 (default 0.3)")
    ap.add_argument("--max-height", type=int, default=1080, help="max download height")
    ap.add_argument("--no-asr", action="store_true", help="skip speech recognition")
    a = ap.parse_args()

    out = ensure_dir(a.out)
    src = download(a.source, out, a.max_height) if is_url(a.source) else local_copy(Path(a.source), out)
    info = probe(src)
    print(f"{src.name}: {info['width']}x{info['height']} {info['fps']} fps {info['duration']} s, audio={info['has_audio']}")

    frames_dir = ensure_dir(out / "frames")
    times = extract_frames(src, frames_dir, a.fps, a.width)
    print(f"frames: {len(times)} every {a.fps}s -> {frames_dir}")

    cuts = detect_cuts(src, a.scene)
    cdir = ensure_dir(out / "cuts")
    for c in cuts:
        extract_frame(src, max(0.0, c - 1 / max(info["fps"], 1)), cdir / f"cut{c:07.2f}_before.jpg", a.width)
        extract_frame(src, c, cdir / f"cut{c:07.2f}_after.jpg", a.width)
    print(f"cuts: {len(cuts)} -> {cdir}")

    sheet = contact_sheet(src, out / "sheet.png", max(0.5, 1 / a.fps) * 2)
    print(f"contact sheet -> {sheet}")

    audio = extract_audio(src, out / "audio.wav") if info["has_audio"] else None
    asr = None
    if audio and not a.no_asr:
        asr = transcribe(audio, out / "asr.json")
        if asr:
            print(f"ASR: {len(asr['words'])} words -> {out / 'asr.json'}")
        else:
            print("ASR: skipped (install faster-whisper to enable)")

    write_json(out / "source.json", {
        **info,
        "source_file": src.name,
        "analysis_fps": a.fps,
        "frames": times,
        "cuts": cuts,
        "contact_sheet": "sheet.png",
        "audio": "audio.wav" if audio else None,
        "asr": "asr.json" if asr else None,
    })
    print(f"wrote {out / 'source.json'}")


if __name__ == "__main__":
    try:
        main()
    except CFError as e:
        die(str(e))
