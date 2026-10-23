# think-big — a 2.6-second replication

Reference: `source.mp4` (854×480, 24 fps, 10.13 s; from motion2code's `think-big` gallery, MIT).
This example rebuilds the opening **2.6 s** as code, then measures how close it got.

## What the reference does

| Time | Picture |
|---|---|
| 0.00–0.98 | blue field #007BE1; a yellow #F3DE00 square grows in the centre |
| 0.98–2.10 | hard cut to white #FBFBF7; heavy blue "THINK"; a yellow square sits on the I; the word grows |
| 2.10–2.60 | a yellow bar wipes across the white field; the source also flashes secondary blue/yellow bars |

## What the code does

`comp.html` — 1920×1080, 24 fps, one `render(t)` function:

- 0–0.98: square scale 0.35 → 1.30, ease-out.
- 0.98–2.10: `THINK` (Arial Black 300 px) scales 0.94 → 1.36; yellow dot lifts and grows.
- 2.10–2.60: yellow bar translates 0 → 1000 px, smoothstep.

## Measured difference

`frame_diff.py --every 0.25 --end 2.5`:

| t | diff | note |
|---|---|---|
| 0.00 | 1.49 | blue field matches |
| 0.25 | 11.03 | square growth timing |
| 0.50 | 11.44 | square size |
| 0.75 | 4.13 | near match |
| 1.00 | 13.25 | font/letterform difference |
| 1.25 | 18.00 | text scale |
| 1.50 | 17.17 | text scale |
| 1.75 | 16.64 | text scale |
| 2.00 | **51.05** | source has a bottom bar + THINK; code has THINK only |
| 2.25 | **50.09** | source has multiple bars; code has one |
| 2.50 | 14.93 | bar position close |

Worst: 2.00 s (51.05), 2.25 s (50.09). `diff/sheet.png` is included; regenerate pairs with `frame_diff.py`.

## Known differences (honest)

1. **Font.** The source uses a heavy condensed grotesque; the rebuild uses Arial Black. Letterforms and
   widths differ; this is the dominant error from 1.0–1.75 s.
2. **Transition.** The source's 2.0–2.6 s wipe uses multiple bars (yellow/blue). The rebuild has one
   yellow bar; 2.0–2.25 s therefore score ~50.
3. **Timing/scale.** The square growth and text scale were fitted by eye from 2 fps frames; sub-frame
   easing is approximate.
4. **No audio.** The source has no audio track.

## What would improve it

- Measure the source font (or use the closest available heavy grotesque) and match tracking.
- Split the transition into the source's two/three bar layers and key each one from dense frames.
- Run `frame_diff --every 1/24` around 0.9–1.1 s and 2.0–2.6 s, fix the worst frame first.

## Reproduce

```bash
python scripts/check.py examples/think-big/comp.html --runtime
python scripts/render.py examples/think-big/comp.html -o examples/think-big/out.mp4 --fps 24
python scripts/frame_diff.py examples/think-big/source.mp4 \
  examples/think-big/out.mp4 -o examples/think-big/diff --every 0.25 --end 2.5
```
