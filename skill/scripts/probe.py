#!/usr/bin/env python3
"""Probe a composition at the element level: carry, framing, curves, reading time.

  python scripts/probe.py comp.html --root . --json out/probe.json

Reads optional declarations from the page:
  window.__meta.carry   = [{t: 4.2, id: '#card'}, ...]
  window.__meta.inFrame = {'#title': [0, 1.4, 'whole'], '#end': [5, 6]}
  window.TEXTS(t)       = [{id, text, x0, y0, x1, y1}, ...]

Carry: the same element is visible just before and after a cut.
Framing: the declared element stays inside the canvas in its window.
Curves: if window.__motion(t0,t1) exists, its peak px/frame is reported; the caller
        decides whether a shutter was used (see verify.py --comp).
Reading: every text piece stays long enough for CJK/4.5 + other/15 + 1.5 s.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cf_common import CFError, die, write_json  # noqa: E402
from render import DUR_JS, FPS_JS, RAF_JS, READY_JS, SEEK_JS, launch, playwright, serve  # noqa: E402


def _rect(page, sel: str):
    return page.evaluate("""(sel) => {
      const e = document.querySelector(sel);
      if (!e) return null;
      const r = e.getBoundingClientRect();
      const cs = getComputedStyle(e);
      return {x0:r.left, y0:r.top, x1:r.right, y1:r.bottom,
              opacity: parseFloat(cs.opacity || '1'), display: cs.display, visibility: cs.visibility};
    }""", sel)


def _seek(page, t: float):
    page.evaluate(SEEK_JS, t)
    page.evaluate(RAF_JS)


def _is_cjk(ch: str) -> bool:
    o = ord(ch)
    return (0x3000 <= o <= 0x303F       # CJK punctuation
            or 0x3400 <= o <= 0x4DBF    # extension A
            or 0x4E00 <= o <= 0x9FFF    # unified ideographs
            or 0xF900 <= o <= 0xFAFF)   # compatibility ideographs


def analyze(comp: str | Path, root: str | Path | None = None, width: int = 1920,
            height: int = 1080, fps: float = 30.0) -> dict:
    comp = Path(comp).resolve()
    if not comp.exists():
        raise CFError(f"missing composition: {comp}")
    root = Path(root).resolve() if root else comp.parent
    if not root.is_dir():
        raise CFError(f"--root is not a folder: {root}")
    try:
        rel = urllib.parse.quote(comp.relative_to(root).as_posix())
    except ValueError:
        raise CFError(f"composition must be inside --root ({root}): {comp}")
    httpd, base = serve(root)
    out = {"comp": str(comp), "duration": None, "fps": fps,
           "carry": None, "framing": None, "curves": None, "reading": None, "errors": []}
    try:
        with playwright()() as p:
            browser = launch(p)
            try:
                page = browser.new_page(viewport={"width": width, "height": height})
                page.on("pageerror", lambda e: out["errors"].append(str(e)))
                page.goto(f"{base}/{rel}?external=1", wait_until="load")
                page.wait_for_function(READY_JS, timeout=30000)
                try:
                    page.evaluate("() => document.fonts && document.fonts.ready ? document.fonts.ready.then(() => true) : true")
                except Exception:
                    pass
                page.wait_for_timeout(120)
                dur = page.evaluate(DUR_JS)
                if not isinstance(dur, (int, float)) or dur <= 0:
                    raise CFError("page does not expose a positive duration (window.__meta.dur)")
                fps = float(page.evaluate(FPS_JS) or fps)
                if fps <= 0:
                    fps = 30.0
                out["duration"] = round(float(dur), 3)
                out["fps"] = fps
                meta = page.evaluate("() => window.__meta || {}")
                if not isinstance(meta, dict):
                    meta = {}

                carry = meta.get("carry") or []
                if carry:
                    if not isinstance(carry, list):
                        raise CFError("window.__meta.carry must be an array")
                    events = []
                    for item in carry:
                        if not isinstance(item, dict):
                            raise CFError("each carry item must be an object")
                        t = float(item.get("t", 0)); sel = str(item.get("id", "") or "")
                        _seek(page, max(0, t - .03)); a = _rect(page, sel)
                        _seek(page, min(float(dur) - 1e-6, t + .03)); b = _rect(page, sel)
                        vis = lambda r: bool(r and r["opacity"] > .02 and r["display"] != "none" and r["visibility"] != "hidden")
                        ok = vis(a) and vis(b)
                        moved = bool(ok and (abs(a["x0"] - b["x0"]) > .5 or abs(a["y0"] - b["y0"]) > .5
                                             or abs((a["x1"] - a["x0"]) - (b["x1"] - b["x0"])) > .5))
                        events.append({"t": t, "id": sel, "ok": ok, "moved": moved,
                                       "before": a, "after": b})
                    passed = sum(1 for e in events if e["ok"])
                    out["carry"] = {"score": round(passed / len(events), 2), "events": events}

                in_frame = meta.get("inFrame") or {}
                if in_frame:
                    if not isinstance(in_frame, dict):
                        raise CFError("window.__meta.inFrame must be an object")
                    frames = {}
                    for sel, win in in_frame.items():
                        if not isinstance(win, (list, tuple)) or len(win) < 2:
                            raise CFError(f"inFrame[{sel!r}] must be [start, end, ('whole')]")
                        t0, t1 = float(win[0]), float(win[1])
                        whole = len(win) > 2 and win[2] == "whole"
                        bad = []
                        for k in range(6):
                            t = t0 + (t1 - t0) * k / 5
                            _seek(page, t)
                            r = _rect(page, sel)
                            if not r:
                                bad.append({"t": round(t, 2), "why": "missing"}); continue
                            inside = (r["x0"] >= 0 and r["y0"] >= 0 and r["x1"] <= width and r["y1"] <= height) if whole \
                                else (r["x1"] > 0 and r["y1"] > 0 and r["x0"] < width and r["y0"] < height)
                            if not inside:
                                bad.append({"t": round(t, 2), "why": "off-frame", "rect": r})
                        frames[sel] = {"window": [t0, t1], "whole": whole, "bad": bad}
                    out["framing"] = frames

                if page.evaluate("() => typeof window.__motion === 'function'"):
                    peak, at = 0.0, 0.0
                    n = int(float(dur) / .1) + 1
                    for k in range(n):
                        t = k * .1
                        v = page.evaluate("(a) => window.__motion(a[0], a[1])",
                                          [t, min(float(dur), t + 1 / fps)]) or 0
                        if v > peak:
                            peak, at = float(v), t
                    out["curves"] = {"peak": round(peak, 1), "at": round(at, 2), "fps": fps}

                if page.evaluate("() => typeof window.TEXTS === 'function'"):
                    # One entry per contiguous appearance of a text id. If an id
                    # swaps copy (e.g. a subtitle line), each line is measured
                    # separately instead of only the last one surviving.
                    segments: dict[str, list[dict]] = {}
                    step = .1
                    n = int(float(dur) / step) + 1
                    for k in range(n):
                        t = k * step
                        _seek(page, t)
                        items = page.evaluate("() => window.TEXTS()") or []
                        if not isinstance(items, list):
                            continue
                        for it in items:
                            if not isinstance(it, dict):
                                continue
                            text = str(it.get("text") or "")
                            if not text:
                                continue
                            key = str(it.get("id") or text)
                            segs = segments.setdefault(key, [])
                            if segs and segs[-1]["text"] == text and abs(segs[-1]["last"] - (t - step)) < 1e-6:
                                segs[-1]["last"] = t
                            else:
                                segs.append({"text": text, "first": t, "last": t})
                    bad = []
                    checked = 0
                    for key, segs in segments.items():
                        for seg in segs:
                            checked += 1
                            cjk = sum(1 for ch in seg["text"] if _is_cjk(ch))
                            other = sum(1 for ch in seg["text"] if not ch.isspace() and not _is_cjk(ch))
                            need = 1.5 + cjk / 4.5 + other / 15
                            got = seg["last"] - seg["first"] + step
                            if got + 1e-6 < need:
                                bad.append({"id": key, "text": seg["text"], "first": round(seg["first"], 2),
                                            "need": round(need, 2), "got": round(got, 2)})
                    out["reading"] = {"checked": checked, "bad": bad}
            finally:
                browser.close()
    finally:
        httpd.shutdown()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comp")
    ap.add_argument("--root", default=None)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    res = analyze(a.comp, a.root, a.width, a.height, a.fps)
    print(f"{a.comp}: {res['duration']}s · {res['fps']} fps")
    if res["carry"]:
        print(f"  carry    score {res['carry']['score']} over {len(res['carry']['events'])} boundaries")
        for e in res["carry"]["events"]:
            print(f"    {'PASS' if e['ok'] else 'FAIL'}  t={e['t']}  {e['id']}  moved={e['moved']}")
    if res["framing"]:
        off = {k: v["bad"] for k, v in res["framing"].items() if v["bad"]}
        print(f"  framing  {'FAIL' if off else 'PASS'}  {off or 'all in frame'}")
    if res["curves"]:
        print(f"  curves   peak {res['curves']['peak']} px/frame @ {res['curves']['at']}s")
    if res["reading"]:
        print(f"  reading  {len(res['reading']['bad'])} too short of {res['reading']['checked']}")
        for b in res["reading"]["bad"][:5]:
            print(f"    {b['id']}: need {b['need']}s, got {b['got']}s")
    if res["errors"]:
        print("  errors:", res["errors"][:3])
    if a.json:
        write_json(a.json, res)
        print(f"  wrote {a.json}")


if __name__ == "__main__":
    try:
        main()
    except CFError as e:
        die(str(e))
