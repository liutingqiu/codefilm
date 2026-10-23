#!/usr/bin/env python3
"""Render a deterministic HTML composition to MP4, frame by frame.

  python scripts/render.py comp.html -o out.mp4 [--fps 30] [--duration 8] [--audio audio.wav]

The page must expose one of:
  window.__seek(t) -> Promise      (preferred)
  window.anim.seek(t)              (motion2code contract)
  window.render(t)                 (lemo contract)
and may expose window.__meta = {dur, fps, w, h}. `?external=1` is appended so the page
does not autoplay. A local HTTP server serves the page's folder (CDN fonts/scripts work).

Dependencies: ffmpeg + Playwright (`pip install playwright`, uses installed Chrome first).
"""
from __future__ import annotations

import argparse
import functools
import http.server
import os
import socket
import socketserver
import sys
import threading
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cf_common import CFError, die, ensure_dir, need, probe, run, write_json  # noqa: E402


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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", help="composition HTML")
    ap.add_argument("-o", "--out", default="out.mp4")
    ap.add_argument("--fps", type=float, default=0, help="output fps (default: page __meta.fps)")
    ap.add_argument("--duration", type=float, default=0, help="seconds (default: page duration)")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--scale", type=float, default=1.0, help="device scale factor (2 = 4K from 1920x1080 CSS)")
    ap.add_argument("--crf", type=int, default=16)
    ap.add_argument("--audio", default=None, help="optional wav/mp3 to mux")
    ap.add_argument("--keep-frames", action="store_true")
    ap.add_argument("--timeout", type=int, default=30000, help="page ready timeout ms")
    a = ap.parse_args()
    need("ffmpeg")
    html = Path(a.html).resolve()
    if not html.exists():
        die(f"missing {html}")
    root = html.parent
    if a.audio and not Path(a.audio).exists():
        die(f"missing audio {a.audio}")
    out = Path(a.out).resolve()
    ensure_dir(out.parent)
    frames_dir = ensure_dir(out.parent / "_frames")
    for old in frames_dir.glob("*.png"):
        old.unlink()

    httpd, base = serve(root)
    errors = []
    t0 = time.time()
    try:
        with playwright()() as p:
            browser = launch(p)
            page = browser.new_page(viewport={"width": a.width, "height": a.height},
                                    device_scale_factor=a.scale)
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            rel = urllib.parse.quote(html.relative_to(root).as_posix())
            page.goto(f"{base}/{rel}?external=1", wait_until="load")
            page.wait_for_function(READY_JS, timeout=a.timeout)
            try:
                page.evaluate("() => document.fonts && document.fonts.ready ? document.fonts.ready.then(() => true) : true")
            except Exception:
                pass
            page.wait_for_timeout(150)
            dur = a.duration or page.evaluate(DUR_JS)
            if not dur:
                die("page does not expose duration: set window.__meta.dur or pass --duration")
            fps = a.fps or float(page.evaluate(FPS_JS) or 30)
            n = int(round((float(dur) - a.start) * fps))
            if n <= 0:
                die(f"nothing to render (duration={dur}, start={a.start}, fps={fps})")
            print(f"{n} frames · {fps:g} fps · {a.width}x{a.height} @{a.scale:g}x · {float(dur):.2f}s", flush=True)
            for i in range(n):
                t = a.start + i / fps
                page.evaluate(SEEK_JS, t)
                page.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
                page.screenshot(path=str(frames_dir / f"{i:05d}.png"), type="png")
                if i % max(1, n // 10) == 0:
                    print(f"  {i}/{n}  t={t:.3f}", flush=True)
            browser.close()
    finally:
        httpd.shutdown()

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
    meta = {"comp": str(html), "out": str(out), "fps": fps, "size": [a.width, a.height],
            "scale": a.scale, "frames": n, "duration": round(n / fps, 3), "seconds": secs,
            "audio": str(a.audio) if a.audio else None, "errors": errors[:10]}
    write_json(out.with_suffix(".render.json"), meta)
    print(f"wrote {out} ({out.stat().st_size} B) in {secs}s; page errors: {errors[:3] or 'none'}")


if __name__ == "__main__":
    try:
        main()
    except CFError as e:
        die(str(e))
