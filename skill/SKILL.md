---
name: codefilm
description: >
  Make or replicate short videos by writing deterministic HTML/CSS/SVG/Canvas code, rendering
  frame by frame, and verifying against the reference or a quality oracle. Two modes: replicate
  a reference video (measure it, route it, rebuild the codeable parts) and create an original
  film from a topic/style. Routes live-action/generative content honestly instead of pretending
  code can rebuild it. Use for motion graphics, UI demos, kinetic type, charts, maps, pixel art,
  logo animation, explainers, product films, and reference-video teardown.
---

# codefilm

**Reference in, editable code out, frame-checked film out.**
A portable agent skill for making video by writing code — not by calling a video model.

It does two things:

1. **Replicate** a reference video's structure, pacing, style and (where code can) its picture.
2. **Create** an original film from a topic, script or named style.

It does **not** claim to rebuild any video. It routes first.

---

## Before anything: route the reference

| The reference is mostly… | Route | What you build |
|---|---|---|
| flat 2D motion graphics, UI, typography, charts, maps, pixel art, screen recording | **CODE** | HTML/SVG/Canvas + GSAP, rendered frame by frame |
| real footage the user owns | **EDIT** | keep the footage, add code overlays (captions, charts, callouts, transitions) |
| real footage the user does not own, photoreal people, complex 3D, organic texture | **GEN** | shot list + prompts + reference images for a video model; code only for titles/overlays |
| a talking presenter, lip-sync, dubbing, face replacement | **AVATAR** | TTS/clone + lip-sync + composition |
| a mix of the above | **HYBRID** | CODE for graphics, GEN/EDIT for the rest |

Write the route to `ROUTE.md` and tell the user what will and will not be faithful. Never silently
promise a carbon copy: OpenMontage's rule applies — offer 2–3 differentiated directions, not one clone.

Route adapters:

- **GEN** — `scripts/gen_prompts.py shots.json -o prompts.md --format seedance` produces the
  copy-paste prompt pack; no API call, no invented reference assets.
- **EDIT** — `scripts/edit_plan.py cuts.json -o manifest.json` turns clip in/out points into a
  manifest; `scripts/compose.py manifest.json` trims, concatenates, mixes voice and burns SRT.

---

## The eight-step loop

```
0 ROUTE   →  1 INGEST  →  2 ANALYZE  →  3 DIRECT
                                              ↓
          7 DELIVER ←  6 RENDER  ←  5 VERIFY  ←  4 BUILD
```

### 0 · Route
Classify the reference (table above). If code cannot carry the subject, say so before spending time.

### 1 · Ingest
```bash
python scripts/ingest.py <url-or-file> -o work/<film>
```
Produces `source.json`, `frames/`, `cuts/`, `audio.wav`, `sheet.png`, optional `asr.json`.
`ffprobe` is optional; the script falls back to `ffmpeg -i`.

### 2 · Analyze
```bash
python scripts/analyze.py work/<film>
```
Produces `analysis.json` + `energy.txt`: duration, still/low ratios, cuts, bursts, longest quiet
stretch, palette. Read the energy map before writing any beat.

Then *you* (the agent) look at `sheet.png`, the frames, and the cut frames. Write:
- **`STYLE.md`** — every adjective as a number: palette hex, type family/weight/size/tracking,
  shadow offset/blur/opacity, grain/vignette, easings, durations, staggers.
- **`analysis.json`** additions — shot list with five aspects: Subject / Subject Motion / Scene
  (overlays separately) / Spatial Framing / Camera. Mark `motion_type`:
  `motion_clip` | `animated_still` | `static_image` | `codeable`.
- **Evidence tags** — `measured` | `observed` | `inferred` | `default`, plus confidence.

### 3 · Direct
Write three concepts that differ in their central idea (not three titles on one film). Pick one
(or let the user pick). Then write `SPEC.md`:

```
GOAL / OUTPUT / TIME / LOOK / OBJECTS / MOTION / SHOTS / BANNED / QA
```

and `beats.json`: one row per beat — time range, scene type, text, motion, sound, what carries
into the next beat. Add `ledger.json` for seams: cut time, exit/entry axis+direction, carrier.

### 4 · Build
Copy `templates/comp.html` and write one composition. Rules:

- **One clock.** `window.__seek(t)` must be a pure function of `t`.
- No `Date.now()`, no unseeded `Math.random()`, no wall-clock rAF, no CSS animations you cannot seek.
- One scene = one section; absolute times; stable ids.
- Every timed element has `data-start` / `data-duration` (or is driven directly by `render(t)`).
- Words exactly as the source; no tracing, no embedding the reference video as a texture.
- Prefer transform/opacity; animate the wrapper, never the timed media element.
- A landed title holds still; motion moves on to the next thing.
- **Zero dependency by default.** If the film genuinely needs a JS library, use the adapter
  registry and a locally vendored, pinned build — never `@latest` on the render path.

### 5 · Verify
```bash
python scripts/check.py comp.html --runtime
python scripts/render.py comp.html -o out/draft.mp4
python scripts/frame_diff.py source.mp4 out/draft.mp4 -o diff/
python scripts/probe.py comp.html --root . --json out/probe.json
python scripts/verify.py out/draft.mp4 --shots 0,1.8,4.2,6.4 --comp comp.html --root .
```
- `check.py`: contract, deterministic seek, loop seam, console/network errors.
- `frame_diff.py`: side-by-side pairs + score. **Open the pairs.** Score is a pointer, not a verdict.
- `probe.py`: carry / framing / curves / reading at the element level.
- `verify.py`: rhythm (shot-length CV, rest, burst), audio (peak/clipping/quiet), plus the probe legs
  when `--comp` is given.
- Read the worst times first; fix structure before polish.

### 6 · Render
```bash
python scripts/render.py comp.html -o out/film.mp4 --fps 30
python scripts/render.py comp.html -o out/film.mp4 --shutter 180 --workers 4   # quality pass
# optional audio:
python scripts/compose.py manifest.json
```
Draft at 1080p30. A `--shutter 180` render adds real motion blur (numpy + Pillow);
`--workers 4` renders in parallel; `--resume` fills missing frames after an interrupted run
(it clears stale frames when the composition or settings change). `--audio` pads a short track
with silence and cuts to picture length. Only render 4K60 after the cut is accepted.
`render.py` writes `<out>.render.json` (fps, actual pixel size, frames, shutter, captures, workers,
page errors).

### 7 · Deliver
Ship:
- `out/film.mp4`
- `comp.html` + `assets/` (editable)
- `diff/` or `qa/` evidence
- `REVIEW.md`: what was checked, worst scores, known differences — never say "pixel perfect".

---

## Page contract

```js
window.__meta = {dur: 8, fps: 30, w: 1920, h: 1080};
window.__seek = async (t) => { render(t); };   // preferred
// accepted alternatives:
// window.anim = {duration, seek(t), play, pause}
// window.render = (t) => { ... }
window.__ready = Promise.resolve(true);          // or <html data-ready="1">
window.__motion = (t0, t1) => px;                // optional, for motion blur
window.TEXTS = (t) => [{id, text, size, x0, y0, x1, y1}]; // optional, for reading-time checks
window.__meta.carry = [{t: 3.5, id: '#dot'}];    // optional, same carrier across a cut
window.__meta.inFrame = {'#title': [0, 1.4, 'whole']}; // optional, framing windows
```

Query parameters:
- `?t=6.5` freeze at 6.5 s
- `?external=1` do not autoplay (renderers/compare pages use this)
- `?play` real-time preview for humans

---

## Optional JS libraries (download on demand)

codefilm bundles no third-party JS. `library/adapters.js` only drives a library that is already
present, and `references/js-libraries.md` has the pinned versions, licenses and seek recipes.

If a composition genuinely needs a missing library:

1. Read `references/js-libraries.md` and `CF.adapters.hint(name)` for the version, license and
   pinned URL.
2. Download that exact version into `vendor/<name>@<version>/` from the official npm tarball or
   the pinned CDN URL. Do this as part of the build step; don't stop and ask the user to install
   it manually. Never use `@latest`, a random mirror, or a runtime CDN for the final render. Do
   not run postinstall scripts from an unfamiliar package.
3. Load it from the local vendor path (`<script src="vendor/...">` or an import map). Use
   `CF.adapters.seek(name, instance, t)` for timeline/player libraries; for Three/Pixi/Chart/D3/p5
   follow the renderer recipe instead of inventing a generic seek.
4. Record version, source URL, SHA-256 and license in `vendor/README.md`; keep the license file.
5. Re-run `check.py` and `render.py`; confirm deterministic seek and no unexpected network calls.

If the network is blocked or the license is unclear, stop and report the missing library. Do not
fake an API or copy code from an incompatible license.

Renderer/ framework notes: Three.js and Motion are ESM-only (import map or bundler); Pixi v8 is
WebGL/WebGPU (check headless Chrome flags); Remotion and Motion Canvas are separate build-system
routes, not browser adapters.

---

## Quality gates (hard)

1. **Contract** — `check.py` 0 errors.
2. **Determinism** — same `t` after other seeks produces the same pixels.
3. **Loop** — `frame(duration) == frame(0)` when the film loops; no jump at the wrap.
4. **Replication** — holds < 10, fast motion < 30, worst < 40 on mean-abs-diff; pairs reviewed.
5. **Rhythm** — shot-length CV ≥ 0.25; still ratio ≥ 25 %; one quiet stretch ≥ 1 s.
6. **Carry** — every scene boundary has a carrier; no bare replacement.
7. **Curves** — > 80 px/frame needs shutter blur or a deliberate staccato.
8. **Framing** — declared subjects never leave frame inside their window.
9. **Audio** — peak ≤ -1 dBFS; no clipping; music ducks under voice; -14…-16 LUFS.
10. **Text** — on-screen long enough to read; never over the subject; no clipped lines.

Automated today: 1–5 by `check.py` / `frame_diff.py` / `verify.py`; 9 by `verify.py`;
6–8 and 10 by `probe.py` (and `verify.py --comp`; reading time is advisory for large display type
and VO subtitles).

---

## Files

```
scripts/ingest.py      download/copy, frames, cuts, audio, contact sheet, optional ASR
scripts/analyze.py     energy map, shot stats, palette, optional optical flow
scripts/render.py      deterministic frame capture + shutter blur + parallel + resume + ffmpeg
scripts/frame_diff.py  source vs render, side-by-side + score
scripts/check.py       static + runtime contract checks
scripts/probe.py       carry / framing / curves / reading at the element level
scripts/verify.py      rhythm/rest/burst/audio oracle + probe legs
scripts/compose.py     manifest → finished film (shots + voice + SRT)
scripts/tts.py         edge-tts narration + per-line timings
scripts/audio.py       numpy BGM + SFX + VO mix
scripts/taste.py       persist user corrections as rules
scripts/edit_plan.py   cut list → compose manifest (EDIT route)
scripts/gen_prompts.py shot list → prompt pack (GEN route)
scripts/install.py     install to Claude / Codex / DSH skill directories
library/motion.js      36 deterministic motion helpers
library/scenes.js      reusable title/cards/lines/chat/ledger/chart/end builders
library/looks.js       8 look token sets
library/adapters.js    optional-library registry: seek / wrap / hint / missing / register
styles/index.json      8 style recipes (look + scene mix + avoid list)
templates/comp.html    a complete demo composition (8 s, 1920×1080)
vendor/                optional pinned browser libraries (empty by default; see vendor/README)
tests/test_motion.js   node tests for the motion library
tests/test_adapters.js node tests for the optional-library adapters
references/            route, contract, analyze, verify, styles, motion-library, scenes, audio,
                       js-libraries (versions, licenses, setup, seek recipes)
```

## Install

Copy this folder to any of:
- `~/.claude/skills/codefilm`
- `~/.agents/skills/codefilm`
- a DSH plugin's `skills/` directory

The scripts need `ffmpeg`; rendering needs `playwright` (`pip install playwright`; it uses the
installed Chrome first). Analysis and composition are stdlib-only.

## Credits

Ideas and contracts are synthesized from MIT/Apache-2.0 projects: HyperFrames (Apache-2.0),
motion2code (MIT), lemo-opuscar (MIT), pixel-diary (MIT), ljq-broll (MIT), explainer-video (MIT),
ghost-editor (MIT), dsh-video-pipeline (MIT), OpenMontage (AGPL — process inspiration only).
`onetake` is PolyForm Noncommercial; its architecture informed this skill but no code is copied.
See `references/credits.md`.
