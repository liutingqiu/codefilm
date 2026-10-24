# motion-demo

A 6-second, 1920×1080, 30 fps composition that exercises the motion library:

| Time | Move |
|---|---|
| 0.0–1.4 | `letterDrop` + `rise` (title + subtitle) |
| 1.4–2.8 | `popIn` card, `counter` 0→100, `press` button |
| 2.8–4.2 | `zoomThrough` text swap, `cutTheCurve` carrier (`#dot`) |
| 4.2–6.0 | `camera` push + `shake` + end card |

Files:

- `comp.html` — the composition (`window.__seek(t)`, `window.__meta.carry`, `inFrame`).
- `out.mp4` — 180 frames, no shutter.
- `out-blur.mp4` — 180 frames, shutter 180°, 4 workers, 1,203 captures, 47.5 s.
- `out-blur.render.json` — render evidence.
- `contact.png` — 2 fps contact sheet.

```bash
python scripts/check.py examples/motion-demo/comp.html --root . --runtime
python scripts/render.py examples/motion-demo/comp.html --root . -o examples/motion-demo/out.mp4 --fps 30
python scripts/render.py examples/motion-demo/comp.html --root . -o examples/motion-demo/out-blur.mp4 \
  --fps 30 --shutter 180 --samples 4 --workers 4
python scripts/probe.py examples/motion-demo/comp.html --root .
```
