# Demo — 8-second codefilm

An 8-second, 1920×1080, 30 fps original composition that exercises the whole P0 loop:
three-line kinetic opener → checklist card with progress and counter → measured bar chart →
end card. No raster assets; every pixel is CSS/SVG/DOM driven by `window.__seek(t)`.

## Run it

From the skill root:

```bash
python scripts/check.py examples/demo/comp.html --runtime
python scripts/render.py examples/demo/comp.html -o examples/demo/out.mp4 --fps 30
```

Open `examples/demo/comp.html` in a browser to preview. `?t=4.2` freezes a frame;
`?play` loops in real time; `?external=1` does not autoplay (renderers use it).

## What to look at

- `out.mp4` — 240 frames, 8.00 s, 1920×1080.
- `out.render.json` — frame count, fps, seconds, page errors.
- `REVIEW.md` — what was checked and what was not.
- The composition itself — ~250 lines, one `render(t)` function, no per-frame state.

## Reuse

Copy `comp.html` to a new project folder, change the text and palette constants at the top,
then run `check.py` and `render.py`. Every scene is a block inside `render(t)` keyed to absolute
time; add a scene by adding a time window and setting styles from `t`.

The demo is original work, MIT-licensed like the rest of this skill.
