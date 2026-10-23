# REVIEW — demo composition

## What was checked

| Check | Result |
|---|---|
| Contract (`check.py` static) | PASS — `__meta`, `__seek`, `__ready` present |
| Runtime determinism | PASS — seek to mid, seek away, seek back: diff **0.00** |
| Loop seam | N/A — `window.__meta.loop = false`; film is linear |
| Console / network | PASS — no page errors; no external requests |
| Render | 240 frames at 30 fps, 1920×1080, **37.0 s**, 1,045,211 B |
| Visual review | Contact sheet at 1 fps reviewed: scenes, labels and end card land as designed |
| Audio | None in this demo |
| Reference diff | N/A — original composition, no reference |

## Known differences / limits

- Not a replica of any reference; this is the engine demo.
- No motion blur (P0 renderer); fast moves would need the shutter path in P1.
- No audio track; `compose.py` can mux voice/SRT when provided.
- `start_vs_mid = 5.11` confirms the picture changes between the opening and the midpoint.

## How to reproduce

```bash
python scripts/check.py examples/demo/comp.html --runtime
python scripts/render.py examples/demo/comp.html -o examples/demo/out.mp4 --fps 30
```
