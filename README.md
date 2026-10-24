# codefilm

**Make videos by writing code.**
Reference in, editable code out, frame-checked film out.

[![codefilm promo preview — 拾光](assets/preview.gif)](promo/out/shiguang-promo.mp4)

▶ **[Watch the 32-second promo with sound](promo/out/shiguang-promo.mp4)** · 1920×1080 · 30 fps · 960 frames · all code

An open-source agent skill and a small deterministic video engine. It does two things:

- **Replicate** a reference video: measure it, route it honestly, rebuild the codeable parts as
  deterministic HTML/CSS/SVG/Canvas, and verify against the source frame by frame.
- **Create** an original film from a topic or style, with the same engine and quality gates.

It does not call a video model, and it does not claim to rebuild arbitrary footage. It routes
**CODE / EDIT / GEN / AVATAR / HYBRID** first, and says what will not be faithful.

---

## The promo: 拾光 (Shiguang)

`拾光` is a **fictional** product built for this demo: an AI workspace that turns scattered notes
into a clear plan. The 32-second film is a brand spot made entirely with this repo:

| | |
|---|---|
| Picture | 1920×1080, 30 fps, 960 frames, deterministic `window.__seek(t)` |
| Voice | Chinese narration, generated with edge-tts (`zh-CN-XiaoxiaoNeural`) |
| Music / SFX | synthesized with numpy — pluck, pad, bass, kick, hats, whooshes, clicks, chimes |
| Render | shutter 180° motion blur, 4 browser workers → FFmpeg, **204 s** (5,037 captures) |
| Audio master | −14.1 LUFS, −1.2 dBFS true peak |
| Quality | `verify.py --comp`: rest/audio/carry/framing/curves PASS; cadence WARN (calm brand film); reading WARN (advisory) |

The source is in [`promo/`](promo/), including the composition, narration script, timing,
audio builder and contact sheet.

> 拾光 is not a real company or product. It exists to demonstrate the engine.

---

## Quick start

```bash
# 1. Check the demo composition (contract + deterministic seek)
python skill/scripts/check.py skill/examples/demo/comp.html --runtime

# 2. Render it
python skill/scripts/render.py skill/examples/demo/comp.html -o out/demo.mp4 --fps 30

# 3. Verify rhythm / rest / audio (if the film has audio)
python skill/scripts/verify.py out/demo.mp4
```

For a reference video:

```bash
python skill/scripts/ingest.py <url-or-file> -o work/myfilm
python skill/scripts/analyze.py work/myfilm
# read work/myfilm/sheet.png, frames/, cuts/, analysis.json
```

Then write `STYLE.md`, `SPEC.md`, `beats.json`, copy `skill/templates/comp.html`, implement
`window.__seek(t)`, and run check → render → frame_diff.

Requirements: `ffmpeg`; `playwright` for rendering (`pip install playwright`, uses installed
Chrome first). Ingest, analyze, verify and compose are stdlib-only. `ffprobe` is optional.

---

## How it works

```
ROUTE → INGEST → ANALYZE → DIRECT → BUILD → VERIFY → RENDER → DELIVER
```

1. **Route.** Photoreal people, real locations, complex 3D → not CODE. Say so, then offer
   EDIT / GEN / AVATAR / HYBRID.
2. **Ingest.** Download or copy, extract frames, scene cuts, contact sheet, audio, optional ASR.
3. **Analyze.** Energy map, still/low ratios, cuts, bursts, longest quiet, palette; five-aspect
   shot notes (Subject / Motion / Scene / Framing / Camera) with evidence + confidence.
4. **Direct.** Three concepts, a numeric `SPEC.md`, a beat sheet, and a seam ledger.
5. **Build.** One HTML composition; `window.__seek(t)` is a pure function; no `Date.now()`, no
   unseeded randomness, no wall-clock animation on the render path.
6. **Verify.** Contract, determinism, loop seam, source-vs-code frame diff, rhythm/rest/audio oracle.
7. **Render.** Headless Chrome seeks each frame (optionally across a 180° shutter), one or more
   browser workers, screenshots, and FFmpeg encodes; audio is muxed and loudness-normalized.
8. **Deliver.** MP4 + editable source + diff/QA evidence + `REVIEW.md` with known differences.

Quality gates: contract, determinism, loop, replication diff, rhythm, carry, curves, framing,
audio, text readability. `check.py`, `frame_diff.py` and `verify.py` automate 1–5 and 9;
`probe.py` / `verify.py --comp` automate 6–8 and 10 (reading time is advisory for display type and
VO subtitles).

---

## Status

This repository is the **P1 engine + P2 audio** slice of the plan, plus one finished film:

- **Done:** ingest, analyze (with optical flow), check, render (shutter/parallel/resume),
  frame_diff, probe (carry/framing/curves/reading), verify, TTS, audio synth, edit_plan (EDIT),
  gen_prompts (GEN), compose, taste, install; a motion library (36 moves), scene kit (7 builders),
  8 looks + 8 style recipes; demos for each; the 32 s 拾光 promo; GitHub Pages landing page prepared.
- **Not done yet (P3):** provider API calls for GEN/EDIT (the prompt pack and cut manifest are
  local), DSH marketplace packaging, broader platform QA.

No releases, tags or npm packages have been published. The GitHub Pages homepage is prepared but
not enabled; it waits for a human review.

---

## What's in the repo

```
skill/                  the portable agent skill (SKILL.md, scripts, templates, references)
  scripts/              ingest, analyze, check, render (shutter/parallel), frame_diff, probe,
                        verify, tts, audio, edit_plan, gen_prompts, taste, compose, install
  library/              motion.js (36 moves), scenes.js (7 builders), looks.js (8 looks)
  styles/               8 style recipes (look + scene mix + avoid list)
  examples/             8 s original, 6 s motion, 9.4 s scene kit, 4 s looks, 2.6 s replication
  tests/                Node tests for motion/looks/scenes/styles
promo/                  the 32 s 拾光 brand film
  comp.html             the composition (pure render(t), no external assets)
  vo.py                 Chinese narration via edge-tts
  audio_build.py        numpy BGM + SFX + mix
  vo/                   narration MP3s
  out/                  final MP4 + contact sheet + render evidence
docs/00-synthesis.md    the research behind the design (34 repos, 14 reusable mechanisms)
index.html              the landing page for GitHub Pages (hero video)
ATTRIBUTIONS.md         every referenced project, its license, and what was borrowed
```

Install the skill:

```bash
python skill/scripts/install.py --target claude   # or --target agents, or --dest <dir>
```

---

## What the engine borrows

`codefilm` is a clean-room synthesis. It borrows **contracts and ideas**, not code, from:

- **HyperFrames** (Apache-2.0): render contract, lint, motion doctrine, cut-the-curve.
- **motion2code** (MIT): minimal `window.anim` contract, study/palette/frame_diff.
- **onetake** (PolyForm-Noncommercial): `__seek(t)`, shutter, verify oracle — architecture only,
  **no code copied**.
- **lemo-opuscar** (MIT): `render(t)` + `TEXTS(t)` + readcheck, style library idea.
- **pixel-diary** (MIT): JSON → timeline, scene renderers, synthesized SFX/BGM.
- **ljq-broll** (MIT): evidence/confidence schema, stage attribution.
- **explainer-video / ghost-editor / dsh-video-pipeline** (MIT): Chinese script timing, approval
  gates, manifest compose, media verification.
- **OpenMontage** (AGPL-3.0): route, five aspects, capability audit, sample-first — **process
  inspiration only, no code copied**.
- Plus the rest of the 34-repo survey. See [ATTRIBUTIONS.md](ATTRIBUTIONS.md) for the full table.

---

## License

MIT — see [LICENSE](LICENSE). The license covers the code, composition and original artwork.
The narration is generated with edge-tts and is included as a demo asset (not relicensed under MIT);
see [ATTRIBUTIONS.md](ATTRIBUTIONS.md). The fictional 拾光 brand and its demo film are released under
the same MIT terms for the original work. Third-party names and licenses are listed in
[ATTRIBUTIONS.md](ATTRIBUTIONS.md).
