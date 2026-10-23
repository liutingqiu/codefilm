#!/usr/bin/env python3
"""Compare a rendered film with the reference, frame against frame.

  python scripts/frame_diff.py source.mp4 out.mp4 -o diff/ [--every 0.5]
  python scripts/frame_diff.py source.mp4 out.mp4 --at 0.5 3 6 9

Writes diff/pair_tXXX.png (source left | render right), diff/sheet.png, diff/diff.json.
The score is mean absolute RGB difference at 192x108: a pointer, not a verdict.
Open the pair images; fix the worst times first.
"""
from __future__ import annotations

import argparse
import math
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cf_common import CFError, die, ensure_dir, extract_frame, image_rgb, mean_abs_diff, probe, run, write_json  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("render")
    ap.add_argument("-o", "--out", default="diff")
    ap.add_argument("--at", type=float, nargs="*", help="exact times in seconds")
    ap.add_argument("--every", type=float, default=0.5)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=0.0)
    ap.add_argument("--pair-width", type=int, default=960)
    a = ap.parse_args()
    src, ren = Path(a.source), Path(a.render)
    info_s, info_r = probe(src), probe(ren)
    end = a.end or min(info_s["duration"], info_r["duration"])
    out = ensure_dir(a.out)
    for old in out.glob("pair_*.png"):
        old.unlink()
    if a.at:
        times = a.at
    else:
        n = int((end - a.start) / a.every + 1e-6) + 1
        times = [round(a.start + i * a.every, 3) for i in range(n)]
    pw = a.pair_width
    ph = max(2, int(round(pw * info_s["height"] / max(1, info_s["width"]) / 2) * 2))
    rows = []
    for t in times:
        tag = f"t{t:07.3f}"
        s = out / f"_src_{tag}.png"
        r = out / f"_ren_{tag}.png"
        extract_frame(src, t, s, pw)
        extract_frame(ren, t, r, pw)
        d = mean_abs_diff(image_rgb(s), image_rgb(r))
        pair = out / f"pair_{tag}.png"
        run(["ffmpeg", "-v", "error", "-y", "-i", str(s), "-i", str(r), "-filter_complex",
             f"[0:v]scale={pw}:{ph},setsar=1[a];[1:v]scale={pw}:{ph},setsar=1[b];"
             f"[a]pad={pw + 8}:{ph}:0:0:color=0x111111[a2];[a2][b]hstack", str(pair)])
        s.unlink(); r.unlink()
        rows.append({"t": t, "diff": round(d, 2), "pair": pair.name})
        print(f"t={t:7.3f}  diff {d:6.2f}  {'#' * min(40, int(d / 3))}")
    if len(rows) > 1:
        # This Windows ffmpeg build has no glob support: copy to a numeric sequence first.
        seq = ensure_dir(out / "_seq")
        for i, r in enumerate(rows):
            shutil.copyfile(out / r["pair"], seq / f"{i:04d}.png")
        run(["ffmpeg", "-v", "error", "-y", "-i", str(seq / "%04d.png"),
             "-vf", f"scale=800:-2,tile=2x{math.ceil(len(rows) / 2)}:padding=6:color=0x000000",
             "-frames:v", "1", str(out / "sheet.png")])
        shutil.rmtree(seq, ignore_errors=True)
    worst = sorted(rows, key=lambda r: -r["diff"])[:5]
    write_json(out / "diff.json", {"rows": rows, "worst": worst,
                                   "source": str(src), "render": str(ren)})
    print("worst: " + ", ".join(f"{r['t']} s ({r['diff']})" for r in worst))
    print(f"pairs: {out}/pair_*.png   sheet: {out / 'sheet.png'}")


if __name__ == "__main__":
    try:
        main()
    except CFError as e:
        die(str(e))
