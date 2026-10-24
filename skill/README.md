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

## Status (P1 + P2 audio + P3 packaging, 2026-10-24)

Working and tested on this machine:

| Piece | Status |
|---|---|
| `ingest.py` | local file + yt-dlp; frames, scene cuts, contact sheet, audio, optional ASR (faster-whisper) |
| `analyze.py` | energy map, still/low ratios, cuts, bursts, longest quiet, palette; optional optical flow |
| `check.py` | static + runtime contract, deterministic seek, loop seam (when declared), console/network |
| `render.py` | Playwright capture; **shutter blur, parallel workers, fingerprint-checked resume**; ffmpeg encode, `render.json` |
| `frame_diff.py` | side-by-side pairs, mean-abs-diff, worst-5, sheet |
| `probe.py` | carry / framing / curves / reading at the element level |
| `verify.py` | rhythm/rest/burst/audio + probe legs; exit 1 on a failed leg |
| `tts.py` | edge-tts narration, per-line timings, portable `vo.json` |
| `audio.py` | numpy BGM + SFX + VO mix, ducking, `mix.wav` |
| `taste.py` | persist user corrections as rules |
| `compose.py` | manifest → film; shots, voice delays, SRT burn, adaptive subtitle style |
| `install.py` | copy to `~/.claude/skills`, `~/.agents/skills`, or `~/.dsh/skills` |
| `library/motion.js` | 36 deterministic moves: entrances, exits, seams, camera, contact, type |
| `library/scenes.js` | reusable title/cards/lines/chat/ledger/chart/end builders |
| `library/looks.js` | 8 look token sets |
| `library/adapters.js` | optional-library registry: `hint` / `missing` / `seek` / `wrap` / `register` |
| `styles/index.json` | 8 style recipes (look + scene mix + avoid list) |
| `tests/test_motion.js` | Node tests for the motion library (12 groups) |
| `tests/test_library.js` | Node checks for 8 looks / 7 builders / 8 recipes |
| `tests/test_adapters.js` | Node tests for the optional-library adapters (11 groups) |
| `tests/test_scripts.py` | CLI path/validation smoke tests (7) |
| demos | 8 s original, 6 s motion library, 9.4 s scene kit, 4 s looks, 4 s GSAP adapter, 2.6 s replication |

Verified: `check.py` PASS; re-render determinism PSNR `inf`; 240 frames in ~37 s; shutter
180° + 4 workers on 960 frames in ~204 s; `verify.py --comp` PASS on the promo (carry 1.0,
framing PASS, curves PASS with shutter).

Leftovers (deliberately out of scope): provider API calls for GEN/EDIT (the prompt pack and cut
manifest are local), DSH marketplace packaging, platform-level QA. CI lives in the project repo
(`.github/workflows/ci.yml`). See the project's [`docs/00-synthesis.md`](../docs/00-synthesis.md).

## Requirements

- `ffmpeg` (required). `ffprobe` optional — the probe falls back to `ffmpeg -i`.
- `playwright` for rendering / probe: `pip install playwright` (uses installed Chrome first).
- `numpy` + `Pillow` for shutter blur and `audio.py`.
- `edge-tts` for `tts.py` (`pip install edge-tts`).
- `opencv-python` optional for optical flow.
- Python 3.9+; ingest/analyze/compose/verify are stdlib-only.

## Install

```bash
python scripts/install.py --target claude   # or agents / dsh / --dest <dir>
```

## Layout

```
SKILL.md              entry: routing, 8-step loop, hard rules
AGENTS.md             short cross-agent entry
scripts/              ingest, analyze, check, render, frame_diff, probe, verify,
                      tts, audio, taste, compose, gen_prompts, install
library/              motion.js (36 moves), scenes.js (7 builders), looks.js (8 looks),
                      adapters.js (optional GSAP/Anime/Lottie/Motion/Three/Pixi/Chart/D3/p5)
styles/index.json     8 style recipes (look + scene mix + avoid list)
templates/comp.html   demo composition to copy
vendor/               optional pinned browser libraries (empty by default; provenance rules)
references/           route, contract, analyze, verify, styles, motion-library, scenes, audio,
                      js-libraries, dsh
examples/demo/        8-second original demo + REVIEW.md
examples/motion-demo/ 6-second motion library demo
examples/scene-demo/  9.4-second scene kit demo
examples/looks-demo/  4-second 8-look gallery
examples/gsap-demo/   4-second real GSAP timeline through adapters.js
examples/think-big/   2.6-second replication of a motion2code gallery clip + measured diff
tests/                Node tests for motion/looks/scenes/adapters + Python CLI tests
```

## Optional JS libraries

The engine ships no third-party JS. If a film needs GSAP, Anime.js, Lottie, Motion, Three.js,
PixiJS, Chart.js, D3 or p5, `library/adapters.js` drives the already-loaded library from `seek(t)`
(or gives the renderer recipe). The pinned versions, licenses and setup requirements are in
[`references/js-libraries.md`](references/js-libraries.md). A missing library is vendored under
`vendor/<name>@<version>/` with URL, SHA-256 and license recorded — never `@latest` in a render.

## License / credits

Original code and demo: MIT. Ideas synthesized from MIT/Apache-2.0 projects; OpenMontage (AGPL)
and onetake (PolyForm-NC) informed architecture only, no code copied. Full list:
`references/credits.md`.
