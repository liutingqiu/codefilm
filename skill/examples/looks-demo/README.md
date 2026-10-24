# looks-demo

A 4-second gallery of the eight looks in `library/looks.js`:

`paper-ink`, `dark-tech`, `swiss`, `riso`, `pixel`, `blueprint`, `hand-drawn`, `vox-collage`.

Each card applies `CF.looks.apply(card, name)`, so ground, ink, accent, muted, card, line and the
display/body font stack are all driven by the look's tokens.

```bash
python scripts/check.py examples/looks-demo/comp.html --root . --runtime
python scripts/render.py examples/looks-demo/comp.html --root . -o examples/looks-demo/out.mp4 --fps 30
```

`contact.png` is a still at 2.6 s; `styles/index.json` adds the scene mix and avoid list per style.
