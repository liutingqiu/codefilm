#!/usr/bin/env python3
"""Read a reference in numbers: energy map, cuts, shot stats, palette.

  python scripts/analyze.py work/myfilm [--fps 12] [--width 320] [--flow]

Reads <project>/source.json (from ingest.py), writes:
  analysis.json   duration, still/low ratios, cuts, bursts, longest quiet stretch, palette, flow (optional)
  energy.txt      one character per 1/12 s, rows of 4 s

Pure stdlib. Optical flow needs opencv-python; without it the flow field stays null.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cf_common import CFError, die, need, probe, read_json, run, write_json  # noqa: E402

CHARS = " .:-=+*#%@"


def gray_frames(video: Path, fps: float, width: int) -> tuple[list[bytes], int]:
    h = max(2, int(round(width * 9 / 16 / 2) * 2))
    # use the real aspect ratio when known
    try:
        from cf_common import probe
        info = probe(video)
        h = max(2, int(round(width * info["height"] / max(1, info["width"]) / 2) * 2))
    except Exception:
        pass
    r = run(["ffmpeg", "-v", "error", "-i", str(video), "-vf",
             f"fps={fps},scale={width}:{h},format=gray", "-f", "rawvideo", "-"], text=False)
    data = r.stdout or b""
    n = width * h
    return [data[i:i + n] for i in range(0, len(data) - n + 1, n)], h


def rgb_frames(video: Path, times: list[float], width: int = 320, height: int = 180) -> list[bytes]:
    out = []
    for t in times:
        r = run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, t):.3f}", "-i", str(video),
                 "-frames:v", "1", "-vf", f"scale={width}:{height}:flags=area",
                 "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], text=False)
        out.append((r.stdout or b"")[: width * height * 3])
    return out


def mad(a: bytes, b: bytes) -> float:
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    return sum(abs(a[i] - b[i]) for i in range(n)) / n


def stats(diffs: list[float], fps: float) -> dict:
    cuts = [round(i / fps, 2) for i in range(1, len(diffs)) if diffs[i] > 18.0]
    still = sum(1 for d in diffs if d < 0.5) / max(1, len(diffs))
    low = sum(1 for d in diffs if d < 2.0) / max(1, len(diffs))
    big = [i for i, d in enumerate(diffs) if d > 8]
    bursts = []
    for i in big:
        win = [j for j in big if i <= j < i + int(1.5 * fps)]
        if len(win) >= 3 and (not bursts or i / fps > bursts[-1][1]):
            bursts.append((round(i / fps, 2), round(win[-1] / fps, 2)))
    best = cur = 0
    for d in diffs:
        cur = cur + 1 if d < 2.0 else 0
        best = max(best, cur)
    return {
        "duration_s": round(len(diffs) / fps, 2),
        "still_ratio": round(still, 3),
        "low_ratio": round(low, 3),
        "cuts": cuts,
        "bursts": bursts,
        "longest_quiet_s": round(best / fps, 2),
        "mean_energy": round(sum(diffs) / max(1, len(diffs)), 3),
    }


def energy_map(diffs: list[float], fps: float, row_s: int = 4) -> str:
    per = max(1, int(fps * row_s))
    lines = []
    for r in range(0, len(diffs), per):
        row = diffs[r:r + per]
        lines.append(f"{r / fps:5.1f}s |" + "".join(CHARS[min(9, int(v / 3))] for v in row) + "|")
    return "\n".join(lines)


def palette(frames: list[bytes], merge: float = 26.0, min_share: float = 0.004, top: int = 12) -> list[dict]:
    bins: dict[tuple, list] = {}
    total = 0
    for data in frames:
        for i in range(0, len(data) - 2, 3):
            r, g, b = data[i], data[i + 1], data[i + 2]
            k = (r >> 3, g >> 3, b >> 3)
            e = bins.get(k)
            if e is None:
                bins[k] = [1, r, g, b]
            else:
                e[0] += 1; e[1] += r; e[2] += g; e[3] += b
            total += 1
    groups: list[list] = []
    for c, sr, sg, sb in sorted(bins.values(), key=lambda e: -e[0]):
        mr, mg, mb = sr / c, sg / c, sb / c
        for gr in groups:
            gr_r, gr_g, gr_b = gr[1] / gr[0], gr[2] / gr[0], gr[3] / gr[0]
            if ((mr - gr_r) ** 2 + (mg - gr_g) ** 2 + (mb - gr_b) ** 2) ** 0.5 < merge:
                gr[0] += c; gr[1] += sr; gr[2] += sg; gr[3] += sb
                break
        else:
            groups.append([c, sr, sg, sb])
    out = []
    for c, sr, sg, sb in sorted(groups, key=lambda g: -g[0]):
        share = c / max(1, total)
        if share < min_share:
            continue
        out.append({"hex": "#{:02X}{:02X}{:02X}".format(round(sr / c), round(sg / c), round(sb / c)),
                    "share": round(share, 4)})
    return out[:top]


def flow(video: Path, sample_fps: float = 10.0, width: int = 320) -> dict | None:
    """Optional optical-flow fingerprint: peak/mean px per sampled frame, fast share."""
    try:
        import cv2
        import numpy as np
    except Exception:
        return None
    try:
        info = probe(video)
        h = max(2, int(round(width * info["height"] / max(1, info["width"]) / 2) * 2))
        r = run(["ffmpeg", "-v", "error", "-i", str(video), "-vf",
                 f"fps={sample_fps},scale={width}:{h},format=gray",
                 "-f", "rawvideo", "-"], text=False)
        frames = np.frombuffer(r.stdout or b"", np.uint8)
        n = width * h
        if len(frames) < n * 3:
            return None
        frames = frames[: (len(frames) // n) * n].reshape(-1, h, width)
        dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
        speeds = []
        for i in range(1, len(frames)):
            f = dis.calc(frames[i - 1], frames[i], None)
            mag = np.hypot(f[..., 0], f[..., 1])
            moving = mag > 0.5
            if moving.mean() < 0.002:
                speeds.append(0.0)
                continue
            gx = cv2.Sobel(frames[i], cv2.CV_32F, 1, 0, ksize=3)
            gy = cv2.Sobel(frames[i], cv2.CV_32F, 0, 1, ksize=3)
            edges = moving & (np.hypot(gx, gy) > 20)
            v = float(np.median(mag[edges] if edges.sum() > 20 else mag[moving]))
            speeds.append(v * (1920.0 / width) * (sample_fps / 30.0))
        if not speeds:
            return None
        arr = np.asarray(speeds)
        return {"sample_fps": sample_fps, "peak": round(float(arr.max()), 1),
                "mean": round(float(arr.mean()), 1),
                "fast_share": round(float((arr > 24).mean()), 3)}
    except Exception as e:
        print(f"codefilm: flow skipped ({e})", file=sys.stderr)
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", help="project folder containing source.json")
    ap.add_argument("--fps", type=float, default=12.0, help="analysis sampling fps (default 12)")
    ap.add_argument("--width", type=int, default=320, help="analysis width (default 320)")
    ap.add_argument("--flow", action="store_true", help="enable optical-flow metrics (needs opencv)")
    a = ap.parse_args()
    need("ffmpeg")
    proj = Path(a.project)
    src_json = proj / "source.json"
    if not src_json.exists():
        die(f"missing {src_json}; run ingest.py first")
    meta = read_json(src_json)
    video = proj / meta["source_file"]

    frames, h = gray_frames(video, a.fps, a.width)
    if len(frames) < 2:
        die("not enough frames to analyze")
    diffs = [0.0] + [mad(frames[i - 1], frames[i]) for i in range(1, len(frames))]
    s = stats(diffs, a.fps)
    emap = energy_map(diffs, a.fps)
    (proj / "energy.txt").write_text(emap + "\n", encoding="utf-8")

    times = [meta["duration"] * (i + 0.5) / 12 for i in range(12)]
    pal = palette(rgb_frames(video, times))
    fl = flow(video) if a.flow else None
    data = {**s, "palette": pal, "flow": fl,
            "analysis_fps": a.fps, "analysis_width": a.width}
    write_json(proj / "analysis.json", data)

    print(emap)
    print()
    print(f"still {s['still_ratio']}  low {s['low_ratio']}  quiet {s['longest_quiet_s']}s  "
          f"cuts {len(s['cuts'])}  bursts {len(s['bursts'])}")
    print("palette " + "  ".join(f"{c['hex']} {c['share'] * 100:.0f}%" for c in pal))
    if fl:
        print(f"motion  peak {fl['peak']} px/frame · mean {fl['mean']} · fast {fl['fast_share'] * 100:.0f}%")
    elif a.flow:
        print("motion  skipped (opencv-python not installed)")
    print(f"\nwrote {proj / 'analysis.json'} and {proj / 'energy.txt'}")


if __name__ == "__main__":
    try:
        main()
    except CFError as e:
        die(str(e))
