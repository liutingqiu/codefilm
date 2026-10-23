# codefilm

**Reference in, editable code out, frame-checked film out.**

A portable agent skill for making video by writing code. Two modes:

- **Replicate** — measure a reference, route it honestly, rebuild the codeable parts as
  deterministic HTML/CSS/SVG/Canvas, and verify against the source frame by frame.
- **Create** — direct an original film from a topic or style with the same engine and quality gates.

It does not call a video model, and it does not claim to rebuild arbitrary footage. It routes
CODE / EDIT / GEN / AVATAR / HYBRID first.

## Quick start

```bash
python scripts/check.py examples/demo/comp.html --runtime
python scripts/render.py examples/demo/comp.html -o examples/demo/out.mp4 --fps 30
python scripts/frame_diff.py examples/demo/out.mp4 examples/demo/out.mp4 -o diff/self
```

Open `examples/demo/comp.html` in a browser to preview. `?t=4.2` freezes a frame; `?play` loops.

For a reference:

```bash
python scripts/ingest.py <url-or-file> -o work/myfilm
python scripts/analyze.py work/myfilm
# read work/myfilm/sheet.png, frames/, cuts/, analysis.json
```

Then write `STYLE.md`, `SPEC.md`, `beats.json`, copy `templates/comp.html`, implement
`window.__seek(t)`, and run check → render → frame_diff.

## Status (P0, 2026-10-23)

Working and tested on this machine:

| Piece | Status |
|---|---|
| `ingest.py` | local file + yt-dlp; frames, scene cuts, contact sheet, audio, optional ASR (faster-whisper) |
| `analyze.py` | energy map, still/low ratios, cuts, bursts, longest quiet, palette |
| `check.py` | static + runtime contract, deterministic seek, loop seam (when declared), console/network |
| `render.py` | Playwright frame capture, 1920×1080, ffmpeg encode, `render.json` |
| `frame_diff.py` | side-by-side pairs, mean-abs-diff, worst-5, sheet |
| `verify.py` | rhythm/rest/burst/audio oracle; exit 1 on a failed leg |
| `compose.py` | manifest → film; shots, voice delays, SRT burn, adaptive subtitle style |
| `install.py` | copy to `~/.claude/skills/codefilm` or `~/.agents/skills/codefilm` |
| demo | 8 s, 240 frames, 1920×1080, deterministic (diff 0.00) |
| think-big example | 2.6 s replication; measured diff 1.5–18 on holds/text, known 51 at the multi-bar wipe |

Verified: `check.py` PASS; re-render determinism PSNR `inf`; render 240 frames in ~37 s;
third-party `window.anim` composition rendered by the same engine.

Not in P0: motion blur, optical flow, TTS/SFX synthesis, style library, GEN/AVATAR providers,
auto-annotation of shot cards. These are P1/P2 (see `../notes/00-synthesis.md`).

## Requirements

- `ffmpeg` (required). `ffprobe` optional — the probe falls back to `ffmpeg -i`.
- `playwright` for rendering: `pip install playwright` (uses installed Chrome first).
- Python 3.9+; stdlib only for ingest/analyze/compose.

## Install

```bash
python scripts/install.py --target claude   # or --target agents, or --dest <dir>
```

## Layout

```
SKILL.md              entry: routing, 8-step loop, hard rules
AGENTS.md             short cross-agent entry
scripts/              ingest, analyze, check, render, frame_diff, compose, install
templates/comp.html   demo composition to copy
references/           route, contract, analyze, verify, styles, credits
examples/demo/        8-second original demo + REVIEW.md
examples/think-big/   2.6-second replication of a motion2code gallery clip + measured diff
```

## License / credits

Original code and demo: MIT. Ideas synthesized from MIT/Apache-2.0 projects; OpenMontage (AGPL)
and onetake (PolyForm-NC) informed architecture only, no code copied. Full list:
`references/credits.md`.
