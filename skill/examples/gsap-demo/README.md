# gsap-demo — optional-library adapter check

A 4-second, 1920×1080, 30 fps composition driven by a **real GSAP 3.15 timeline** through
`CF.adapters`. It proves the adapter's `pause() + time(t)` path is deterministic frame to frame.

The GSAP build is **not committed**: its license is the GSAP Standard license, not MIT. Download
the pinned build into the gitignored `vendor/` folder before running:

```bash
mkdir -p vendor/gsap@3.15.0
curl -L https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js \
  -o vendor/gsap@3.15.0/gsap.min.js
# expected SHA-256:
# 92bb9a96476f983d212a2bc4f54c889039c1696dd4461d40a736860938570fbb
```

Run from the skill root:

```bash
python scripts/check.py examples/gsap-demo/comp.html --root . --runtime
python scripts/probe.py examples/gsap-demo/comp.html --root .
python scripts/render.py examples/gsap-demo/comp.html --root . -o examples/gsap-demo/out.mp4 --fps 30
python scripts/verify.py examples/gsap-demo/out.mp4 --shots 0,1.5,2.45,2.76 \
  --comp examples/gsap-demo/comp.html --root .
```

## What it exercises

| Time | Picture | GSAP / adapter |
|---|---|---|
| 0.0–1.7 | four `GSAP` characters rise + stagger; a dot travels along a rail | timeline `fromTo`, `stagger`, `x` tween |
| 1.5–2.45 | code card enters, progress bar fills | `fromTo` at absolute positions |
| 2.2–4.0 | dark end card; dot still visible | end `fromTo`; carrier survives the scene change |

`window.__seek(t)` is one line: `CF.adapters.seek('gsap', tl, t)`. The timeline is built once,
paused, and only its `time` changes during rendering. `?external=1` never plays; `?t=2.0` freezes
a preview frame.

## Measured

| Check | Result |
|---|---|
| `check.py --runtime` | PASS — determinism 0.00, no console/network errors |
| `probe.py` | carry 1.0, framing PASS, reading 0/2 short |
| `verify.py --comp` | PASS — cadence CV 0.44, rest 0.604, burst 1, carry/framing PASS |
| Render | 120 frames, 4.00 s, 1920×1080, 11.6 s, no page errors |
| GSAP license | GSAP Standard (**not MIT**); vendored locally, not relicensed |

See `REVIEW.md` for the detailed run and `contact.png` for eight sampled frames.
