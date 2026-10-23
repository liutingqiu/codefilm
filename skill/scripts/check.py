#!/usr/bin/env python3
"""Check a composition against the codefilm contract (static + optional runtime).

  python scripts/check.py comp.html              # static only
  python scripts/check.py comp.html --runtime    # + headless browser
  python scripts/check.py comp.html --runtime --allow-raster

Static: contract, external allowlist, raster usage, deterministic-clock warnings.
Runtime: console errors, network allowlist, loop seam, determinism, duration.
Exit code 1 when any error is found.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cf_common import CFError, die, image_rgb, mean_abs_diff, write_json  # noqa: E402
from render import DUR_JS, FPS_JS, READY_JS, SEEK_JS, launch, playwright, serve  # noqa: E402

SCRIPT_ALLOW = [
    "https://cdnjs.cloudflare.com/",
    "https://cdn.jsdelivr.net/",
    "https://unpkg.com/",
    "https://fonts.googleapis.com/",
]
HOST_ALLOW = {"cdnjs.cloudflare.com", "cdn.jsdelivr.net", "unpkg.com",
              "fonts.googleapis.com", "fonts.gstatic.com"}


def static_check(path: Path, allow_raster: bool) -> tuple[list[str], list[str]]:
    s = path.read_text(encoding="utf-8", errors="ignore")
    err, warn = [], []
    code = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    has_seek = ("__seek" in code or "anim.seek" in code
                or re.search(r"function\s+render\s*\(", code) or "window.render" in code)
    if not has_seek:
        err.append("no seek contract: expose window.__seek(t), window.anim.seek(t) or window.render(t)")
    if not re.search(r"__meta|anim\.duration|window\.DUR|duration\s*:", code):
        err.append("no duration: expose window.__meta.dur, window.anim.duration or window.DUR")
    if not re.search(r"__ready|data-ready|dataset\.ready", code):
        warn.append("no ready signal: expose window.__ready or set <html data-ready=\"1\">")
    if "external" not in code:
        warn.append("?external=1 is not handled; the page may autoplay while rendering")
    for src in re.findall(r"<script[^>]+src=[\"']([^\"']+)", code, flags=re.I):
        if src.startswith(("http:", "https:", "//")) and not any(src.startswith(p) for p in SCRIPT_ALLOW):
            warn.append(f"external script not in the default allowlist: {src}")
    raster = [(r"<img\b", "<img>"), (r"<video\b", "<video>"), (r"<image\b", "SVG <image>"),
              (r"\bdrawImage\s*\(", "canvas drawImage"),
              (r"url\(\s*['\"]?[^)'\"]+\.(png|jpe?g|webp|gif|avif)", "CSS url() raster"),
              (r"data:image/(png|jpe?g|webp|gif|avif)", "embedded raster data URI")]
    for pat, name in raster:
        if re.search(pat, code, flags=re.I):
            (warn if allow_raster else err).append(f"raster/video asset: {name}")
    for pat, name in [(r"Math\.random\s*\(", "Math.random()"), (r"Date\.now\s*\(", "Date.now()"),
                      (r"performance\.now\s*\(", "performance.now()")]:
        if re.search(pat, code):
            warn.append(f"{name} found: make it seeded/precomputed so seek(t) is pure")
    if re.search(r"/(Users|home)/[A-Za-z0-9_.-]+/", s):
        err.append("absolute personal path found")
    return err, warn


def runtime_check(browser, path: Path, root: Path, width: int, height: int,
                  fps: float, seam: float, seam_step: float) -> tuple[list[str], list[str], dict]:
    err, warn, stats = [], [], {}
    errors, requests = [], []
    page = browser.new_page(viewport={"width": width, "height": height})
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("request", lambda r: requests.append(r.url))
    httpd, base = serve(root)
    try:
        rel = urllib.parse.quote(path.relative_to(root).as_posix())
        page.goto(f"{base}/{rel}?external=1", wait_until="load")
        page.wait_for_function(READY_JS, timeout=30000)
        page.wait_for_timeout(100)
        dur = page.evaluate(DUR_JS)
        if not isinstance(dur, (int, float)) or dur <= 0:
            return ["duration is missing or not positive"], warn, stats
        page_fps = page.evaluate(FPS_JS)
        if isinstance(page_fps, (int, float)) and page_fps > 0:
            fps = float(page_fps)
        loop = bool(page.evaluate("() => !!(window.__meta && window.__meta.loop === true)"))
        def shot(t):
            page.evaluate(SEEK_JS, t)
            page.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
            return image_rgb(page.screenshot(type="png"))
        f0 = shot(0)
        fend = shot(dur)
        flast = shot(max(0.0, dur - 1 / fps))
        fmid = shot(dur / 2)
        shot(dur * 0.83)
        shot(dur * 0.11)
        fmid2 = shot(dur / 2)
        stats = {
            "duration": round(float(dur), 3), "fps": fps, "loop": loop,
            "seam_end": round(mean_abs_diff(f0, fend), 2),
            "seam_last_frame": round(mean_abs_diff(f0, flast), 2),
            "determinism": round(mean_abs_diff(fmid, fmid2), 2),
            "start_vs_mid": round(mean_abs_diff(f0, fmid), 2),
        }
        if loop:
            if stats["seam_end"] > seam:
                err.append(f"loop seam: frame(duration) != frame(0) (diff {stats['seam_end']} > {seam})")
            if stats["seam_last_frame"] > seam_step:
                err.append(f"loop jump: last frame != frame(0) (diff {stats['seam_last_frame']} > {seam_step})")
        else:
            warn.append("film is not declared as looping (window.__meta.loop=true); seam checks skipped")
        if stats["determinism"] > 0.5:
            err.append(f"seek is not deterministic (diff {stats['determinism']})")
        if stats["start_vs_mid"] < 0.5:
            warn.append("mid frame equals frame 0: is anything animating?")
    except Exception as e:
        err.append(f"runtime failed: {e}")
    finally:
        httpd.shutdown()
        page.close()
    for e in errors:
        err.append(f"console error: {e[:200]}")
    for u in requests:
        host = urllib.parse.urlparse(u).hostname
        if u.startswith(("http:", "https:")) and host not in ("127.0.0.1", "localhost") and host not in HOST_ALLOW:
            warn.append(f"request outside the default allowlist: {u}")
    return err, warn, stats


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html")
    ap.add_argument("--runtime", action="store_true")
    ap.add_argument("--allow-raster", action="store_true")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--seam", type=float, default=1.0)
    ap.add_argument("--seam-step", type=float, default=8.0)
    ap.add_argument("--json", default=None, help="write results to this JSON file")
    a = ap.parse_args()
    path = Path(a.html).resolve()
    if not path.exists():
        die(f"missing {path}")
    err, warn = static_check(path, a.allow_raster)
    stats = {}
    if a.runtime and not err:
        with playwright()() as p:
            browser = launch(p)
            try:
                e2, w2, stats = runtime_check(browser, path, path.parent, a.width, a.height,
                                              a.fps, a.seam, a.seam_step)
            finally:
                browser.close()
        err += e2; warn += w2
    status = "PASS" if not err else "FAIL"
    print(f"[{status}] {path}")
    for e in err:
        print(f"  error: {e}")
    for w in warn:
        print(f"  warn:  {w}")
    if stats:
        print("  stats: " + "  ".join(f"{k}={v}" for k, v in stats.items()))
    if a.json:
        write_json(a.json, {"status": status, "errors": err, "warnings": warn, "stats": stats})
    raise SystemExit(0 if not err else 1)


if __name__ == "__main__":
    try:
        main()
    except CFError as e:
        die(str(e))
