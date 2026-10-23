# Verify: the gates, and what each script prints

## 1. Contract + runtime

```bash
python scripts/check.py comp.html --runtime
```

Checks: contract globals, duration, deterministic seek, loop seam (t=0 vs t=duration), jump at the
wrap (t=0 vs duration-1/fps), console errors, network allowlist. Exit 1 on error.

## 2. Replication diff

```bash
python scripts/render.py comp.html -o out/draft.mp4
python scripts/frame_diff.py source.mp4 out/draft.mp4 -o diff/
```

Every 0.5 s by default. Writes `pair_tXXX.png` (source left, render right), `sheet.png`, `diff.json`.
Mean absolute RGB difference at 192×108:

| Typical score | Meaning |
|---|---|
| < 10 on holds | faithful flat rebuild |
| 10–30 during fast motion | motion blur/noise in the source, vector code is clean |
| > 40 | wrong shape, color, beat or timing — fix structure first |

**Scores rank moments; they are not a verdict.** A 3 px offset scores low but looks wrong; a correct
beat 2 frames late scores high. Open the pairs.

## 3. Rhythm / carry / curves / framing (original work)

```bash
python scripts/verify.py out/film.mp4 --shots 0,1.8,4.2,6.4
```

Checks: cadence (shot-length CV ≥ 0.25 varied; 0.15–0.25 is acceptable for a calm brand film;
below 0.15 reads as a slideshow), rest (still ≥ 25 %, quiet ≥ 1.0 s), burst (only FAILs
against a reference that has one), audio (peak ≤ -1.0 dBFS, 0 clipped, ≥ 15 % quiet), and an advisory
row-profile variation. Exit 1 on FAIL.

Then use this as a checklist for the things no script catches:

- **Cadence** — shot-length coefficient of variation ≥ 0.25. Equal lengths = slideshow.
- **Rest** — ≥ 25 % of frames dead-still; one quiet stretch ≥ 1.0 s.
- **Burst** — a 1.5 s window with ≥ 3 big changes, only if the reference has one.
- **Carry** — every boundary has a thing that survives and moves: cursor, card, subject, container,
  word group. A bare replacement is a slide change even with good rhythm.
- **Curves** — anything > 80 px/frame needs shutter blur, or it strobes into copies.
- **Framing** — declare `window.__meta.inFrame = {id: [t0, t1]}` and verify the subject never leaves.
- **Reading time** — CJK characters / 4.5 + other non-space / 15 + 1.5 s, per text piece.

## 4. Audio

- Peak ≤ -1.0 dBFS, 0 clipped samples.
- Voice at -14…-16 LUFS; music ducked under voice (≈ -10 dB) with 0.2–0.3 s fades.
- At least 15 % of 1/12 s windows quiet; no dead air longer than the design.
- Verify with `ffmpeg ... astats`; compare a published file against a reference WAV with NCC ≥ 0.9
  for "same version".

## 5. Review report

`REVIEW.md` must state: what was checked, the numbers, the worst times and why they remain, what
differs from the source, and what was not checked. Never write "pixel perfect".
