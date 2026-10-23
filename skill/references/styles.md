# Styles: tokens, not templates

A style is a system of invariants plus slots for content. Do not paste a previous film's shots.

## Token file (`styles/<name>.json`)

```json
{
  "name": "paper-ink",
  "canvas": {"background": "#F2ECE1", "ink": "#1B1A17", "muted": "#8A8275",
             "accent": "#D9552B", "support": ["#2F7D5B", "#E7B84B", "#4C6FA8"]},
  "type": {
    "display": {"family": "Georgia", "weight": 700, "size": 168, "tracking": -0.035},
    "body": {"family": "Segoe UI", "weight": 400, "size": 25, "lineHeight": 1.4}
  },
  "material": {"grain": 0.035, "vignette": 0.0, "shadow": [16, 16, 0.13]},
  "motion": {
    "enter": {"ease": "power4.out", "duration": 0.55, "rise": 82},
    "move": {"ease": "power2.inOut", "duration": 0.5},
    "exit": {"ease": "power3.in", "duration": 0.35, "fall": 44},
    "stagger": {"word": 0.08, "line": 0.14, "item": 0.06}
  },
  "camera": {"default": "static", "push": "1.00 → 1.06 over 4 s"},
  "sound": {"voice": "none", "music": "pluck 96 BPM", "sfx": "sparse, on landings"}
}
```

## Eight starting looks

| Name | Ground / ink / accent | Material | Motion |
|---|---|---|---|
| `paper-ink` | #F2ECE1 / #1B1A17 / #D9552B | paper, hard shadow, grain | long ease-out, dead-still holds |
| `dark-tech` | #0B0B10 / #F0ECE4 / #4CC2A0 | glass, glow (rationed) | snaps, camera push, blur |
| `swiss` | #F7F7F5 / #111 / #E33 | grid, Helvetica-like, no shadow | cut-the-curve, precise timing |
| `riso` | paper / ink A / fluorescent ink B | misregistration, halftone | printed plate by plate |
| `pixel` | #0A1729 / #EAF3FF / #FF8A5C | 8-bit sprites, hard steps | stepped eases, typing, 8-bit SFX |
| `blueprint` | #0B2A4A / #E8F1FF / #FFD166 | white line work, grid | draw-on, dimension lines |
| `hand-drawn` | #FBF7EE / #2B2B2B / #D9552B | ink line, paper, wobble | draw-on, uneven timing |
| `vox-collage` | per beat color / black / red | torn paper, halftone, tape | poster assembled, camera drift |

## Rules

- One dominant direction per film; a direction change needs a visible cause.
- One hero move per shot; secondary moves travel 50–70 % as far and start 100–200 ms later.
- Land a title, then hold it dead still. No idle breathing on type or UI.
- 2–3 inter-scene transitions per film, repeated. Never crossfade worlds.
- The look comes from one medium's rules, not a palette dump.
- Keep the accent rationed: one highlighted word, the payoff, the end card.
