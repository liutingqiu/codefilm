# Styles

Eight style recipes, each a **system of invariants** (ground, ink, accent, type, material, motion),
not a template to paste. The visual tokens live in `library/looks.js`; this index adds the scene mix
and what to avoid.

| Style | Look | Best for |
|---|---|---|
| Paper & Ink | `paper-ink` | brand films, calm explainers |
| Dark Tech | `dark-tech` | developer tools, AI launches |
| Swiss | `swiss` | data stories, B2B |
| Risograph | `riso` | culture, music, indie |
| 16-bit Pixel | `pixel` | games, dev tools |
| Blueprint | `blueprint` | engineering, systems |
| Hand-drawn | `hand-drawn` | education, whiteboard |
| Vox Collage | `vox-collage` | news explainers, ads |

```js
CF.looks.apply(stage, 'dark-tech');
const s = CF.scenes.title(stage, {text:'SHIP IT', sub:'a code-made film'});
```

Rules:

- One style per film; do not mix two looks in one piece unless the story crosses worlds.
- Keep the style's palette and type; vary the content, not the house look.
- A new film in the template's beats reads as the template — write three concepts first.
- Do not reuse a successful film's shot order; reuse its invariants and invent the beats.
- If the reference uses a look not listed here, derive one from its measured palette and type
  (`analyze.py` + `STYLE.md`), then add it to this index.
