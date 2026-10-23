# Page contract

## The four globals

```js
window.__meta = {dur, fps, w, h};        // required
window.__seek = async (t) => { ... };    // required (or anim.seek / render)
window.__ready = Promise.resolve(true);  // required (or <html data-ready="1">)
window.__motion = (t0, t1) => px;        // optional
window.TEXTS = (t) => [{id, text, x0, y0, x1, y1}]; // optional
```

Accepted alternatives:
- `window.anim = {duration, seek(t), play, pause}` (motion2code)
- `window.render(t)` (lemo)

## Determinism rules

1. `seek(t)` is a pure function of `t`. Seeking to 5 s after 9 s must equal seeking to 5 s after 0 s.
2. No `Date.now()`, `performance.now()`, unseeded `Math.random()` on the render path.
3. No wall-clock `requestAnimationFrame` loop, `setTimeout` choreography, or CSS transitions that
   cannot be seeked. `?play` may use rAF for human preview only.
4. Precompute particles/sims with a seeded PRNG in `build()`, or make them closed-form functions of `t`.
5. One timeline / one clock. If you use GSAP, `tl.pause(); tl.time(t)`; register the root timeline
   on `window.__timelines` when targeting HyperFrames.

## Scene structure

- One scene per section; absolute times (`data-start` / `data-duration`, or direct `render(t)` math).
- Stable ids: `#hook-title`, `#card`, `#bar-0`. Never `nth-child` selectors for animation targets.
- Draw objects around their own origin (center or contact point) so scale/rotate behave.
- Animate transforms and opacity; avoid `left/top/width/height` on the render path.
- A timed video must not sit inside another timed element. Put `<video>` at the root.
- Opaque stage ground: `#root { background: var(--canvas) }` or a full-bleed child; otherwise a
  mid-transition opacity dip can flash white.

## Common failures

| Symptom | Cause | Fix |
|---|---|---|
| Blank/frozen scene | timeline registered before async build; wrong id | register after build; match ids |
| Jump at a cut | outgoing/incoming states differ at the seam | snapshot ±0.1 s; match position/scale/velocity |
| Stutter | layout measured in `onUpdate`; two clocks | measure once; one timeline |
| Loop jumps | last frame != first | tween back to the opening values; pad to exact duration |
| Text unreadable | too small / too fast | ≥ 28 px at 1080; 0.5 s + 0.3 s per word |
| White flash at cut | no opaque stage ground | paint `#root` |
| Raster in a code build | `<img>`/`<video>`/`drawImage` | redraw as SVG/CSS, or move to EDIT/HYBRID |
