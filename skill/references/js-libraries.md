# Optional JS libraries: configuration and seek recipes

codefilm ships **no third-party JavaScript**. The adapter layer
([`library/adapters.js`](../library/adapters.js)) only knows how to drive a library you have
already loaded. This page is the survey behind that decision, plus the pattern for each family.

The default is zero dependency: CSS/SVG/Canvas + `CF.motion`. Add a library only when the film
genuinely needs it.

## Survey (npm metadata + browser builds, 2026-10-24)

| Library | Version | License | Browser build / size | Configuration need | Deterministic seek | Adapter |
|---|---|---|---|---|---|---|
| GSAP | 3.15.0 | GSAP Standard (**not MIT**) | `dist/gsap.min.js` · 73 KB | one `<script>`; no build; global `gsap` | `tl.pause(); tl.time(t, true)` | `timeline` |
| Anime.js | 4.5.0 | MIT | `dist/bundles/anime.umd.min.js` · 118 KB | `<script>` or ESM; global `anime` | `tl.pause(); tl.seek(t * 1000)` | `timeline` |
| Lottie-web | 5.13.0 | MIT | `build/player/lottie.min.js` · 306 KB | `<script>` + JSON animation asset; global `lottie` | `anim.goToAndStop(round(t*fps), true)` | `player` |
| Motion | 14.6.0 | MIT | `dist/motion.js` · 172 KB | ESM + import map/bundler; no UMD global | `a.pause(); a.currentTime = t*1000` | `waapi` |
| Web Animations API | built-in | n/a | 0 KB | none | `document.getAnimations()` → pause + `currentTime` | `waapi` |
| Three.js | 0.186.1 | MIT | `build/three.module.js` · 663 KB | ESM only; import map or bundler; no UMD | no timeline — update objects, `renderer.render(scene, camera)` | `renderer` recipe |
| PixiJS | 8.22.0 | MIT | `dist/pixi.min.js` · 841 KB | `<script>` or ESM; WebGL/WebGPU | `app.ticker.stop(); app.renderer.render(app.stage)` | `renderer` recipe |
| D3 | 7.9.0 | ISC | `dist/d3.min.js` · 280 KB | `<script>` or ESM modules; global `d3` | no timeline — use scales/shapes from `t`; no `d3.transition()` | `renderer` recipe |
| Chart.js | 4.6.1 | MIT | `dist/chart.umd.js` · 210 KB | `<script>`; canvas; global `Chart` | `animation:false`; update data; `chart.update('none')` | `renderer` recipe |
| p5.js | 2.3.4 | **LGPL-2.1** | `lib/p5.min.js` · 991 KB | `<script>`; global `p5` | `p.noLoop(); p.redraw()` per `t` | `renderer` recipe |
| Konva | 10.9.0 | MIT | `konva.min.js` · 196 KB | `<script>`; global `Konva` | update nodes; `layer.draw()` | `renderer` recipe |
| Rough.js | 4.6.6 | MIT | `bundled/rough.js` · 28 KB | `<script>`; global `rough` | draw from `t`; no clock | `pure` |
| Remotion | 4.0.538 | Remotion License (**not MIT**) | npm + React + bundler | separate Node renderer; not a browser adapter | React frame driven by `useCurrentFrame` | `framework` |
| Motion Canvas | 3.17.2 | MIT | npm + Vite + TypeScript | generator functions; build step | scene generator + renderer | `framework` |

Sizes are unminified/minified bundle sizes from the published package, not gzip. Versions are
pinned suggestions; update the table and the adapter registry together.

## Use the adapter

```html
<script src="../../library/adapters.js"></script>
<script>
  // Is it missing? Put this in a build log, not in the render path.
  console.log(CF.adapters.missing(['gsap', 'lottie']));

  // Timeline libraries: one call per frame.
  const tl = gsap.timeline({ paused: true });
  tl.to('#card', { x: 240, duration: 1 }, 0);
  window.__seek = async (t) => CF.adapters.seek('gsap', tl, t);

  // Or wrap it:
  const clock = CF.adapters.wrap('gsap', tl);
  window.__seek = async (t) => clock.render(t);
</script>
```

`hint(name)` returns the pinned version, license, CDN URL, build path, configuration note,
whether a generic `seek` exists, and the recipe. `missing(names)` returns the absent ones.
`register(name, spec)` adds a private adapter without editing this file.

## Timeline recipes

**GSAP** — load `vendor/gsap@3.15.0/dist/gsap.min.js`, build a paused timeline, seek with
`tl.time(t, true)`. GSAP plugins are separate files and may have their own license terms.

**Anime.js 4** — `const tl = anime.createTimeline({ autoplay: false });` then
`tl.pause(); tl.seek(t * 1000)`. Do not copy a v3 tutorial: v4 renamed the timeline factory and
the import paths.

**Lottie-web** — load the JSON asset, not just the runtime:
`lottie.loadAnimation({ container, renderer: 'svg', loop: false, autoplay: false, path: 'vendor/anim.json' })`.
Then `goToAndStop(Math.round(t * animation.frameRate), true)`. The animation JSON has its own
license; record it.

**Motion / WAAPI** — Motion is ESM only. Pause the returned controls and set `currentTime` in
milliseconds. For plain CSS/WAAPI animations, `document.getAnimations()` plus the same assignment
works; remember that the contract still prefers `render(t)` over CSS animation.

## Renderer recipes

These libraries have no single timeline object. Do **not** try to force a generic seek; update
the scene from `t` and call the renderer once.

**Three.js** — `renderer.setAnimationLoop(null)`, update camera/objects/uniforms from `t`, then
`renderer.render(scene, camera)`. Use an import map or a bundler; there is no UMD build.
Headless Chrome may need SwiftShader for WebGL; test `render.py` before committing to a long render.

**PixiJS** — stop `app.ticker`, update the stage, then `app.renderer.render(app.stage)`.
Pixi v8 can use WebGL or WebGPU; check the headless browser flags.

**D3** — use `d3.scale*`, `d3.shape*`, `d3.axis*` directly from `t`. `d3.transition()` and
`d3.timer()` are wall-clock APIs; never put them on the render path.

**Chart.js** — create the chart with `animation: false, responsive: false`; rewrite the datasets
for `t`; call `chart.update('none')`. Do not let Chart.js own a timer.

**p5.js** — `p.noLoop()`, set a global `t`, and call `p.redraw()`. p5 is LGPL-2.1: if you vendor
or modify it, keep its license and comply with the LGPL.

**Konva / Rough.js** — Konva: update nodes and `layer.draw()`. Rough.js: draw shapes from `t`
with no animation loop; it is a pure drawing library.

## Frameworks are a different route

**Remotion** and **Motion Canvas** are build systems, not drop-in browser scripts. They bring
React/TypeScript, a bundler, and their own renderer. Treat them as an alternative backend/route,
not as an adapter. Remotion's license is not MIT; check the company-size terms before using it
in a commercial product.

## Missing-library policy

If a composition needs a library that is not present:

1. Read this page and `CF.adapters.hint(name)` for the pinned version, license, and URL.
2. Download that **exact** version into `vendor/<name>@<version>/` from the official npm tarball
   or the pinned CDN URL. Never use `@latest`, a random mirror, or an unpinned URL in a render.
   Do not run postinstall scripts from an unfamiliar package.
3. Load it from the local vendor path (`<script src="vendor/...">` or an import map), not from a
   runtime CDN, for the final render.
4. Record the version, source URL, SHA-256, and license in `vendor/README.md`; keep the license
   file next to the vendored code.
5. Re-run `check.py` and `render.py`. Confirm the page still has a pure `seek(t)`, no console
   errors, and no network requests outside the allowlist.

If the network is blocked or the license is unclear, stop and report the missing library. Do not
fake an API or copy code from a repository with an incompatible license.
