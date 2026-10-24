#!/usr/bin/env python3
"""Render a deterministic HTML composition to MP4, frame by frame.

  python scripts/render.py comp.html -o out.mp4 [--fps 30] [--shutter 180] [--workers 4]

The page must expose one of:
  window.__seek(t) -> Promise      (preferred)
  window.anim.seek(t)              (motion2code contract)
  window.render(t)                 (lemo contract)
and may expose window.__meta = {dur, fps, w, h}. `?external=1` is appended so the page
does not autoplay. A local HTTP server serves the page's folder (CDN fonts/scripts work).

Motion blur (--shutter, degrees; 0 = off): each frame seeks several times across the open
shutter and averages the captures in linear light. A page that defines
`window.__motion(t0,t1) -> px` gets an adaptive sample count; a hard cut between samples
keeps only the side at the frame time. Needs numpy + Pillow (optional).

Parallel: --workers N launches N browser processes, each taking every n-th frame.
Resume: --resume keeps _frames/ and renders only missing frames.

Dependencies: ffmpeg + Playwright (`pip install playwright`, uses installed Chrome first).
"""
from __future__ import annotations

import argparse
import functools
import http.server
import io
import multiprocessing as mp
import os
import socketserver
import sys
import threading
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cf_common import CFError, die, ensure_dir, need, run, write_json  # noqa: E402


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve(directory: Path):
    handler = functools.partial(_Quiet, directory=str(directory))
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


def playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except Exception:
        die("Playwright is missing: pip install playwright  (uses installed Chrome; no browser download needed)")


def launch(p):
    last = None
    for kw in ({"channel": "chrome"}, {"channel": "msedge"}, {}):
        try:
            return p.chromium.launch(**kw)
        except Exception as e:
            last = e
    die(f"could not launch a browser: {last}")


READY_JS = """() => {
  const hasSeek = typeof window.__seek === 'function'
    || (window.anim && typeof window.anim.seek === 'function')
    || typeof window.render === 'function';
  const hasMeta = window.__meta || window.anim || window.DUR;
  return hasSeek && hasMeta || document.documentElement.dataset.ready === '1';
}"""

SEEK_JS = """async (t) => {
  if (typeof window.__seek === 'function') { await window.__seek(t); return; }
  if (window.anim && typeof window.anim.seek === 'function') { window.anim.seek(t); return; }
  if (typeof window.render === 'function') { window.render(t); return; }
  throw new Error('no seek function');
}"""

DUR_JS = """() => (window.__meta && window.__meta.dur)
  || (window.anim && window.anim.duration)
  || window.DUR || null"""

FPS_JS = """() => (window.__meta && window.__meta.fps) || 30"""

HAS_MOTION_JS = "() => typeof window.__motion === 'function'"

RAF_JS = "() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"


def _open_page(browser, job):
    page = browser.new_page(viewport={"width": job["width"], "height": job["height"]},
                            device_scale_factor=job["scale"])
    page.on("console", lambda m: job["errors"].append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: job["errors"].append(str(e)))
    url = f"{job['base']}/{job['rel']}?external=1"
    page.goto(url, wait_until="load")
    page.wait_for_function(READY_JS, timeout=job["timeout"])
    try:
        page.evaluate("() => document.fonts && document.fonts.ready ? document.fonts.ready.then(() => true) : true")
    except Exception:
        pass
    page.wait_for_timeout(150)
    return page


def _probe_page(html: Path, root: Path, base: str, width: int, height: int,
                scale: float, timeout: int) -> tuple[float, float, bool]:
    rel = urllib.parse.quote(html.relative_to(root).as_posix())
    with playwright()() as p:
        browser = launch(p)
        try:
            page = browser.new_page(viewport={"width": width, "height": height},
                                    device_scale_factor=scale)
            page.goto(f"{base}/{rel}?external=1", wait_until="load")
            page.wait_for_function(READY_JS, timeout=timeout)
            try:
                page.evaluate("() => document.fonts && document.fonts.ready ? document.fonts.ready.then(() => true) : true")
            except Exception:
                pass
            page.wait_for_timeout(120)
            dur = page.evaluate(DUR_JS)
            fps = float(page.evaluate(FPS_JS) or 30)
            motion = bool(page.evaluate(HAS_MOTION_JS))
            if not isinstance(dur, (int, float)) or dur <= 0:
                die("page does not expose duration: set window.__meta.dur or pass --duration")
            return float(dur), fps, motion
        finally:
            browser.close()


def _grab(page, t: float) -> bytes:
    page.evaluate(SEEK_JS, t)
    page.evaluate(RAF_JS)
    return page.screenshot(type="png")


def _lut():
    import numpy as np
    u = np.arange(256) / 255.0
    to_lin = np.where(u <= 0.04045, u / 12.92, ((u + 0.055) / 1.055) ** 2.4).astype(np.float32)
    l = np.arange(65536) / 65535.0
    to_srgb = np.clip(np.rint(np.where(l <= 0.0031308, l * 12.92,
                                      1.055 * np.power(l, 1 / 2.4) - 0.055) * 255.0),
                      0, 255).astype(np.uint8)
    return to_lin, to_srgb


def _integrate(pngs: list[bytes]) -> tuple[bytes, bool]:
    """Average captures in linear light. If one step is a cut, keep the side at the frame time."""
    import numpy as np
    from PIL import Image
    to_lin, to_srgb = _lut()
    if len(pngs) >= 4:
        grays = [np.asarray(Image.open(io.BytesIO(p)).convert("L").resize((64, 36)), np.int16) for p in pngs]
        d = np.abs(np.diff(np.stack(grays), axis=0)).mean(axis=(1, 2))
        j = int(d.argmax())
        other = np.delete(d, j)
        if d[j] > 0 and other.size and d[j] >= 3 * float(other.max()):
            keep = range(j + 1, len(pngs)) if j < len(pngs) // 2 else range(0, j + 1)
        else:
            keep = range(len(pngs))
    else:
        keep = range(len(pngs))
    acc = None
    for k in keep:
        lin = to_lin[np.asarray(Image.open(io.BytesIO(pngs[k])).convert("RGB"))]
        acc = lin if acc is None else acc + lin
    avg = acc / max(1, len(list(keep)))
    idx = np.clip(np.rint(avg * 65535.0), 0, 65535).astype(np.uint16)
    out = Image.fromarray(to_srgb[idx])
    buf = io.BytesIO()
    out.save(buf, format="PNG", compress_level=1)
    return buf.getvalue(), len(list(keep)) < len(pngs)


def _frame(page, t: float, path: Path, job: dict) -> tuple[int, int, int]:
    """Write one frame. Returns (captures, cut_flag, still_flag)."""
    if job["shutter"] <= 0:
        path.write_bytes(_grab(page, t))
        return 1, 0, 0
    open_s = (job["shutter"] / 360.0) / job["fps"]
    t0 = max(0.0, t - open_s / 2)
    t1 = min(job["dur"] - 1e-6, t + open_s / 2)
    S = job["samples"]
    if job["adaptive"]:
        try:
            far = float(page.evaluate("(a) => window.__motion(a[0], a[1])", [t0, t1]) or 0)
            S = max(job["smin"], min(job["smax"], int(-(-far * job["scale"] // job["gap"]))))
        except Exception:
            S = job["samples"]
    S = max(2, S)
    times = [min(max(t + open_s * ((k + 0.5) / S - 0.5), 0.0), job["dur"] - 1e-6) for k in range(S)]
    pngs = [_grab(page, tk) for tk in times]
    if pngs[0] == pngs[-1]:
        path.write_bytes(pngs[0])
        return len(pngs), 0, 1
    data, cut = _integrate(pngs)
    path.write_bytes(data)
    return len(pngs), int(cut), 0


def _worker(job: dict) -> dict:
    from playwright.sync_api import sync_playwright  # noqa: F401
    stats = {"frames": 0, "captures": 0, "still": 0, "cuts": 0, "errors": [], "relaunched": 0}
    job = dict(job)
    job["errors"] = stats["errors"]
    with sync_playwright() as p:
        browser = launch(p)
        page = _open_page(browser, job)
        done = 0
        for i in range(job["k"], job["n"], job["workers"]):
            path = job["frames_dir"] / f"{i:05d}.png"
            if job["resume"] and path.exists():
                continue
            if job["recycle"] and done and done % job["recycle"] == 0:
                browser.close()
                browser = launch(p)
                page = _open_page(browser, job)
                stats["relaunched"] += 1
            t = job["start"] + i / job["fps"]
            for attempt in range(4):
                try:
                    caps, cut, still = _frame(page, t, path, job)
                    stats["captures"] += caps
                    stats["still"] += still
                    stats["cuts"] += cut
                    stats["frames"] += 1
                    break
                except Exception as e:
                    if "closed" not in str(e) or attempt == 3:
                        raise
                    try:
                        browser.close()
                    except Exception:
                        pass
                    browser = launch(p)
                    page = _open_page(browser, job)
                    stats["relaunched"] += 1
            done += 1
            if done % max(1, (job["n"] // job["workers"]) // 5) == 0:
                print(f"  worker {job['k']}: {done} frames", flush=True)
        browser.close()
    return stats


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", help="composition HTML")
    ap.add_argument("-o", "--out", default="out.mp4")
    ap.add_argument("--fps", type=float, default=0, help="output fps (default: page __meta.fps)")
    ap.add_argument("--duration", type=float, default=0, help="seconds to render from --start (default: to the page end)")
    ap.add_argument("--end", type=float, default=0, help="absolute end time (overrides --duration)")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--scale", type=float, default=1.0, help="device scale factor (2 = 4K from 1920x1080 CSS)")
    ap.add_argument("--crf", type=int, default=16)
    ap.add_argument("--audio", default=None, help="optional wav/mp3 to mux")
    ap.add_argument("--shutter", type=float, default=0.0, help="shutter angle in degrees; 0 = no motion blur")
    ap.add_argument("--samples", type=int, default=8, help="captures per moving frame when __motion is absent")
    ap.add_argument("--samples-min", type=int, default=4)
    ap.add_argument("--samples-max", type=int, default=48)
    ap.add_argument("--gap", type=float, default=6.0, help="px between captures with adaptive sampling")
    ap.add_argument("--workers", type=int, default=1, help="browser processes (default 1; try 4)")
    ap.add_argument("--recycle", type=int, default=300, help="relaunch a browser after N frames (0 = never)")
    ap.add_argument("--resume", action="store_true", help="keep _frames/ and render only missing frames")
    ap.add_argument("--keep-frames", action="store_true")
    ap.add_argument("--timeout", type=int, default=30000, help="page ready timeout ms")
    ap.add_argument("--root", default=None, help="folder to serve (default: the page's folder)")
    a = ap.parse_args()
    need("ffmpeg")
    html = Path(a.html).resolve()
    if not html.exists():
        die(f"missing {html}")
    root = Path(a.root).resolve() if a.root else html.parent
    if a.audio and not Path(a.audio).exists():
        die(f"missing audio {a.audio}")
    out = Path(a.out).resolve()
    ensure_dir(out.parent)
    frames_dir = ensure_dir(out.parent / "_frames")

    if a.shutter > 0:
        try:
            import numpy  # noqa
            from PIL import Image  # noqa
        except ImportError:
            print("codefilm: --shutter needs numpy + Pillow; rendering without blur", file=sys.stderr)
            a.shutter = 0

    httpd, base = serve(root)
    errors: list[str] = []
    t0 = time.time()
    try:
        rel = urllib.parse.quote(html.relative_to(root).as_posix())
        page_dur, fps, has_motion = _probe_page(html, root, base, a.width, a.height, a.scale, a.timeout)
        fps = float(a.fps or fps)
        end = a.end if a.end > 0 else (a.start + a.duration if a.duration > 0 else page_dur)
        end = min(float(end), page_dur)
        n = int(round((end - a.start) * fps))
        if n <= 0:
            die(f"nothing to render (start={a.start}, end={end}, fps={fps})")
        workers = max(1, min(int(a.workers), n))
        if not a.resume:
            for old in frames_dir.glob("*.png"):
                old.unlink()
        else:
            for old in frames_dir.glob("*.png"):
                try:
                    if int(old.stem) >= n:
                        old.unlink()
                except ValueError:
                    old.unlink()
        adaptive = a.shutter > 0 and has_motion
        how = "no shutter" if a.shutter <= 0 else (
            f"shutter {a.shutter:g}°, " + ("adaptive samples" if adaptive else f"{a.samples} samples"))
        print(f"{n} frames · {fps:g} fps · {a.width}x{a.height} @{a.scale:g}x · "
              f"{a.start:.2f}–{end:.2f}s · {workers} worker(s) · {how}", flush=True)

        job = dict(html=str(html), root=str(root), base=base, rel=rel, width=a.width, height=a.height,
                   scale=a.scale, start=a.start, fps=fps, dur=page_dur, n=n, frames_dir=frames_dir,
                   shutter=a.shutter, samples=max(2, a.samples), smin=max(2, a.samples_min),
                   smax=max(2, a.samples_max), gap=max(1.0, a.gap), adaptive=adaptive,
                   resume=a.resume, recycle=a.recycle, timeout=a.timeout)
        jobs = [dict(job, k=k, workers=workers) for k in range(workers)]
        if workers == 1:
            results = [_worker(jobs[0])]
        else:
            with mp.get_context("spawn").Pool(workers) as pool:
                results = pool.map(_worker, jobs)
        for r in results:
            errors.extend(r["errors"][:20])
    finally:
        httpd.shutdown()

    missing = [i for i in range(n) if not (frames_dir / f"{i:05d}.png").exists()]
    if missing:
        die(f"{len(missing)} frames missing (first: {missing[0]}); re-run with --resume")
    cmd = ["ffmpeg", "-v", "error", "-y", "-framerate", f"{fps:g}",
           "-i", str(frames_dir / "%05d.png")]
    if a.audio:
        cmd += ["-i", str(Path(a.audio).resolve())]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", str(a.crf),
            "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart"]
    if a.audio:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += [str(out)]
    run(cmd)
    if not a.keep_frames:
        for f in frames_dir.glob("*.png"):
            f.unlink()
        try:
            frames_dir.rmdir()
        except OSError:
            pass
    secs = round(time.time() - t0, 1)
    caps = sum(r["captures"] for r in results)
    still = sum(r["still"] for r in results)
    cuts = sum(r["cuts"] for r in results)
    meta = {"comp": str(html), "out": str(out), "fps": fps, "size": [a.width, a.height],
            "scale": a.scale, "frames": n, "duration": round(n / fps, 3), "seconds": secs,
            "audio": str(a.audio) if a.audio else None, "workers": workers,
            "shutter": a.shutter if a.shutter > 0 else 0,
            "samples": "adaptive" if adaptive else (max(2, a.samples) if a.shutter > 0 else 1),
            "captures": caps, "still_frames": still, "cut_frames": cuts,
            "errors": errors[:10]}
    write_json(out.with_suffix(".render.json"), meta)
    print(f"wrote {out} ({out.stat().st_size} B) in {secs}s; "
          f"{caps} captures, {still} still, {cuts} cut frames; page errors: {errors[:3] or 'none'}")


if __name__ == "__main__":
    try:
        main()
    except CFError as e:
        die(str(e))
