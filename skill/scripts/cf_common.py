"""Shared helpers for codefilm scripts.

Stdlib only. ffmpeg is required; ffprobe is optional (fallback parses `ffmpeg -i`).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


class CFError(RuntimeError):
    pass


def die(msg: str, code: int = 1):
    print(f"codefilm: {msg}", file=sys.stderr)
    raise SystemExit(code)


def need(tool: str) -> str:
    p = shutil.which(tool)
    if not p:
        raise CFError(f"`{tool}` not found on PATH")
    return p


def run(cmd: list[str], *, cwd: str | Path | None = None, check: bool = True,
        capture: bool = True, text: bool = True) -> subprocess.CompletedProcess:
    kw = {"capture_output": capture}
    if text:
        kw.update(text=True, encoding="utf-8", errors="replace")
    r = subprocess.run([str(c) for c in cmd], cwd=str(cwd) if cwd else None, **kw)
    if check and r.returncode != 0:
        tail = (r.stderr or r.stdout or "")[-3000:]
        raise CFError(f"command failed ({r.returncode}): {' '.join(map(str, cmd))}\n{tail}")
    return r


def have(tool: str) -> bool:
    return shutil.which(tool) is not None


def ensure_dir(p: str | Path) -> Path:
    p = Path(p)
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_json(p: str | Path, obj) -> Path:
    p = Path(p)
    ensure_dir(p.parent)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def read_json(p: str | Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def fmt_sec(t: float) -> str:
    return f"{t:07.3f}"


def parse_rate(s: str | None) -> float:
    if not s:
        return 0.0
    if "/" in s:
        a, b = s.split("/", 1)
        try:
            return float(a) / float(b or 1)
        except ValueError:
            return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def probe(path: str | Path) -> dict:
    """Width, height, fps, duration, frame count, audio presence.

    Uses ffprobe when available; otherwise parses `ffmpeg -i`.
    """
    path = Path(path)
    if not path.exists():
        raise CFError(f"file not found: {path}")
    if have("ffprobe"):
        r = run(["ffprobe", "-v", "error", "-print_format", "json",
                 "-show_format", "-show_streams", str(path)])
        d = json.loads(r.stdout)
        streams = d.get("streams", [])
        v = next((s for s in streams if s.get("codec_type") == "video"), None)
        if not v:
            raise CFError(f"no video stream: {path}")
        fps = parse_rate(v.get("r_frame_rate")) or parse_rate(v.get("avg_frame_rate")) or 0.0
        duration = float(d.get("format", {}).get("duration") or v.get("duration") or 0.0)
        frames = int(v.get("nb_frames") or 0) or int(round(duration * fps))
        return {
            "width": int(v["width"]), "height": int(v["height"]),
            "fps": round(fps, 3), "duration": round(duration, 3), "frames": frames,
            "has_audio": any(s.get("codec_type") == "audio" for s in streams),
            "path": str(path),
        }
    # ffmpeg fallback: `ffmpeg -i file` exits 1 but prints the stream info to stderr
    r = run(["ffmpeg", "-hide_banner", "-i", str(path)], check=False)
    text = (r.stderr or "") + (r.stdout or "")
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", text)
    if not m:
        raise CFError(f"cannot read media info: {path}")
    duration = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    v = re.search(r"Stream #.*?Video:.*?(\d{2,5})x(\d{2,5})", text)
    if not v:
        raise CFError(f"no video stream: {path}")
    fps = 0.0
    fm = re.search(r"([\d.]+)\s+fps", text)
    if fm:
        fps = float(fm.group(1))
    else:
        rm = re.search(r"(\d+)/(\d+)\s*\(.*?\)?.*?fps", text)
        if rm:
            fps = float(rm.group(1)) / float(rm.group(2) or 1)
    return {
        "width": int(v.group(1)), "height": int(v.group(2)),
        "fps": round(fps, 3), "duration": round(duration, 3),
        "frames": int(round(duration * fps)) if fps else 0,
        "has_audio": "Audio:" in text,
        "path": str(path),
    }


def extract_frame(video: str | Path, t: float, out: str | Path,
                  width: int | None = None) -> Path:
    out = Path(out)
    ensure_dir(out.parent)
    vf = ["-vf", f"scale={width}:-2:flags=lanczos"] if width else []
    info = probe(video)
    if t >= info["duration"] - 1.5 / max(info.get("fps") or 24, 1):
        run(["ffmpeg", "-v", "error", "-y", "-sseof", "-0.5", "-i", str(video),
             "-update", "1", *vf, str(out)])
    else:
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0.0, t):.4f}",
             "-i", str(video), "-frames:v", "1", *vf, str(out)])
    return out


def video_frame_rgb(video: str | Path, t: float, w: int = 192, h: int = 108) -> bytes:
    r = run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, t):.4f}",
             "-i", str(video), "-frames:v", "1", "-vf", f"scale={w}:{h}:flags=area",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], text=False)
    data = r.stdout or b""
    return data[: w * h * 3]


def image_rgb(png: bytes | str | Path, w: int = 192, h: int = 108) -> bytes:
    ff = need("ffmpeg")
    if isinstance(png, (str, Path)):
        r = subprocess.run([ff, "-v", "error", "-i", str(png), "-vf",
                            f"scale={w}:{h}:flags=area", "-f", "rawvideo",
                            "-pix_fmt", "rgb24", "-"], capture_output=True)
        return (r.stdout or b"")[: w * h * 3]
    r = subprocess.run([ff, "-v", "error", "-f", "image2pipe", "-i", "-",
                        "-vf", f"scale={w}:{h}:flags=area", "-f", "rawvideo",
                        "-pix_fmt", "rgb24", "-"], input=png, capture_output=True)
    return (r.stdout or b"")[: w * h * 3]


def mean_abs_diff(a: bytes, b: bytes) -> float:
    n = min(len(a), len(b))
    if n == 0:
        return float("nan")
    return sum(abs(a[i] - b[i]) for i in range(n)) / n


def is_url(s: str) -> bool:
    return re.match(r"^https?://", s, re.I) is not None
