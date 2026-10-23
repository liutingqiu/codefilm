# Analyze: what to measure, and how to write it down

## Metrics (`analysis.json`)

| Field | Meaning | Typical reading |
|---|---|---|
| `still_ratio` | share of 1/12 s samples with mean frame diff < 0.5 | high = holds, low = constant motion |
| `low_ratio` | share with diff < 2.0 | calm film |
| `cuts` | times where diff > 18 | hard cuts |
| `bursts` | 1.5 s windows with ≥ 3 changes > 8 | montage / staccato |
| `longest_quiet_s` | longest stretch < 2.0 | rests that make bursts land |
| `palette` | dominant hex + share | use the measured colors, not guesses |

## The five aspects (per shot)

1. **Subject** — type, count, age, role, costume, distinguishing features; transitions across shots
   (revealing / disappearing / switching / complex-alternating).
2. **Subject Motion** — actions in temporal order; group/interaction pattern; locomotion vs gesture
   vs facial.
3. **Scene** — overlays separately (text, lower thirds, graphics, watermark) + POV + setting +
   time of day + dynamics.
4. **Spatial Framing** — shot size (ECU/CU/MS/WS/EWS), subject position, depth layers,
   height-relative, and how each changes.
5. **Camera** — playback speed, lens, height, angle, focus/DoF, steadiness, movement
   (push/pull/pan/tilt/dolly/truck/crane/orbit).

Mark `N/A` explicitly. Silent omission is the most common analysis failure.

## Evidence tags

Every claim is one of:

- `measured` — a script printed a number / a frame shows it at a known time;
- `observed` — you looked at a frame and describe it;
- `inferred` — reasoned from adjacent frames or audio;
- `default` — chosen because nothing else was available.

Keep a confidence (`high` / `medium` / `low`) and the frame/time. Do not turn an inference into a
measured fact.

## Motion fingerprint (P1, needs opencv)

- peak px/frame at the film's fps, normalized to 1920 wide;
- `t80`: share of a move's duration before 80 % of travel is done — `.23` is an expo snap,
  `.67` a symmetric S-curve;
- `smear`: gradient energy along motion / across motion on changed pixels; `< .78` indicates
  shutter blur, `~.9+` a sharp render;
- soft-curve share: percentage of travel on moves with `t80 ≥ .55`.

Without opencv, fall back to the energy map and frame diffs; state that flow was not measured.

## Output template

```
STYLE.md
- palette: bg #..., ink #..., accent #..., support #...
- type: display family / weight / size px / tracking; body family / size / line-height
- material: paper/ink, riso, blueprint, pixel, flat, glass, clay; grain %, vignette %
- motion: enter ease / move ease / exit ease; durations in seconds; staggers in frames
- camera: lens/height/angle/movement; what each shot needs
- sound: voice/no voice, music mood/BPM, SFX density

analysis.json
- metrics + palette + shots[] with five aspects, motion_type, evidence, confidence
```
