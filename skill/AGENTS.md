# codefilm — agent entry

Read `SKILL.md` first. It contains the route table, the eight-step loop and the hard rules.

Short version:

1. Route the request: CODE / EDIT / GEN / AVATAR / HYBRID. Say what will not be faithful.
2. `python scripts/ingest.py <source> -o work/<film>`
3. `python scripts/analyze.py work/<film>`; look at `sheet.png`, `frames/`, `cuts/`.
4. Write `STYLE.md`, `SPEC.md`, `beats.json`, `ledger.json`.
5. Copy `templates/comp.html`; write one pure `window.__seek(t)` composition.
6. `python scripts/check.py comp.html --runtime`
7. `python scripts/render.py comp.html -o out/draft.mp4`
8. `python scripts/frame_diff.py source.mp4 out/draft.mp4 -o diff/`; open the pairs.
9. Deliver mp4 + editable code + evidence + `REVIEW.md`.

Zero dependency is the default. If a composition needs a library that is not present, read
`references/js-libraries.md`, download the pinned version into `vendor/`, record URL/hash/license,
and drive it through `CF.adapters`. Never use `@latest` or an unpinned runtime CDN in a render.

Never claim "pixel perfect". Never embed the reference video in a CODE build. Never use
`Date.now()`, unseeded `Math.random()` or wall-clock animation on the render path.
