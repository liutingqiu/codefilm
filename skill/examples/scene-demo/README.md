# scene-demo

A 9.4-second, 1920×1080, 30 fps composition that exercises all seven scene builders:

| Time | Builder |
|---|---|
| 0.0–1.5 | `title` — per-character drop + subtitle |
| 1.5–3.0 | `cards` — three cards, stagger pop |
| 3.05–4.15 | `lines` — marker rows slide in |
| 4.25–5.5 | `chat` — three message bubbles |
| 5.6–6.75 | `ledger` — three counters |
| 6.85–7.95 | `chart` — four bars grow |
| 8.05–9.4 | `end` — dark brand card |

The scene root is gated by `start`/`out`, so labels and counters cannot leak into another scene.

```bash
python scripts/check.py examples/scene-demo/comp.html --root . --runtime
python scripts/render.py examples/scene-demo/comp.html --root . -o examples/scene-demo/out.mp4 --fps 30
```
