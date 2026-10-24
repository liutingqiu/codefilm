# REVIEW — GSAP adapter demo

## What was checked

| Check | Result |
|---|---|
| Contract (`check.py` static) | PASS — local GSAP + `adapters.js`, `__meta`, `__seek`, `__ready` |
| Runtime determinism | PASS — seek away and back: diff **0.00** |
| Console / network | PASS — no page errors; only local requests |
| Probe | carry **1.0** at t=1.5 (`#dot`), framing **PASS**, reading **0/2** short |
| Render | 120 frames, 4.00 s, 1920×1080, **11.6 s**, 203,351 B, no page errors |
| `verify.py --comp` | **PASS** — cadence CV 0.44, rest 0.604, burst 1, carry/framing/reading PASS |
| Audio | None in this demo |

## Adapter path

- GSAP 3.15.0 UMD is loaded from `vendor/gsap@3.15.0/gsap.min.js` (gitignored; license is not MIT).
- The timeline is created once with `paused: true`.
- Every frame calls `CF.adapters.seek('gsap', tl, t)` → `tl.pause(); tl.time(t, true)`.
- A real GSAP timeline is also tested in Node when the vendor build is present
  (`tests/test_adapters.js`): `x(t=0.5)=50`, seek to 0.8 and back to 0.5 → 50 again.

## Known limits

- No audio; this is an adapter/determinism check, not a finished spot.
- One timeline, four text pieces, no shutter pass. The adapter itself is independent of blur.
- The character split and layout are hard-coded for 1920×1080.
- GSAP Standard license: the vendored file keeps its own terms; this repository's MIT license
  does not cover it. See `vendor/README.md`.

## Reproduce

```bash
mkdir -p vendor/gsap@3.15.0
curl -L https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js \
  -o vendor/gsap@3.15.0/gsap.min.js
python scripts/check.py examples/gsap-demo/comp.html --root . --runtime
python scripts/render.py examples/gsap-demo/comp.html --root . -o examples/gsap-demo/out.mp4 --fps 30
python scripts/verify.py examples/gsap-demo/out.mp4 --shots 0,1.5,2.45,2.76 \
  --comp examples/gsap-demo/comp.html --root .
```
