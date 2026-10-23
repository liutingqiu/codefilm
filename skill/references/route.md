# Route: what code can and cannot rebuild

## Decision tree

```
Does the reference contain photoreal people, real locations, animals,
organic textures, or complex 3D?
├─ NO → CODE
│   Flat 2D, UI, type, charts, maps, diagrams, pixel art, screen recordings,
│   logo motion, kinetic text, paper/ink, isometric infographics.
└─ YES
    ├─ The user owns the footage (their camera / their screen / licensed) → EDIT
    │   Keep the footage; code adds captions, charts, callouts, transitions.
    └─ The user does not own it
        ├─ They need a real person speaking / lip-sync / dubbing → AVATAR
        └─ Otherwise → GEN
            Shot list + prompts + reference images for a video model;
            code handles titles, lower-thirds, charts and the end card.
```

HYBRID is the normal case for product films: code for UI/type/charts, GEN for B-roll, EDIT for
the founder's own footage.

## Motion type is a routing signal

For every reference shot, record one:

| motion_type | Meaning | Route |
|---|---|---|
| `codeable` | flat shapes, type, UI, charts, maps, pixel art | CODE |
| `animated_still` | a still image with Ken Burns / pan-zoom / parallax | EDIT or CODE (if still is code-drawn) |
| `static_image` | a still held | EDIT |
| `motion_clip` | generated or real motion footage | EDIT / GEN |
| `avatar` | a presenter speaking | AVATAR |

Never guess. If the reference is mostly `motion_clip`, a code rebuild will fail no matter how good
the HTML is.

## What CODE can do well

- Kinetic typography, title cards, lower thirds, captions.
- UI walkthroughs (rebuild the screens from source/screenshots; do not screen-record).
- Charts, maps, diagrams, timelines, counters.
- Pixel art, paper/ink, riso, blueprint, isometric, flat character animation.
- Logo reveals, transitions, overlays, data films.
- Hybrid overlays on real footage.

## What CODE cannot do

- Photoreal faces, hands, hair, cloth, food, water, weather.
- Real camera movement through a real place.
- Complex 3D with realistic light (unless the reference is deliberately low-poly/stylized).
- Anything where the viewer must believe "this was filmed".

Say this in one sentence, then offer the nearest route. Do not silently downgrade.
