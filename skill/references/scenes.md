# Scene kit

`library/scenes.js` builds reusable scenes on top of `motion.js`. Each builder appends a root
element and returns `{el, render(t)}`; the caller owns the clock and the layout slot.

```html
<script src="../../library/motion.js"></script>
<script src="../../library/scenes.js"></script>
<script>
  const t1 = CF.scenes.title(stage, {text:'SHIP IT', sub:'a code-made film', start:0, out:1.4});
  const t2 = CF.scenes.chart(stage, {start:1.5, out:2.8, items:[
    {label:'still', value:.55}, {label:'cuts', value:.8}]});
  function render(t){ t1.render(t); t2.render(t); }
</script>
```

## Builders

| Builder | Options | Renders |
|---|---|---|
| `title` | `text, sub, start, out, stagger, dist` | per-character drop + subtitle rise |
| `cards` | `items:[{title,body}], start, out, stagger` | up to 4 cards, pop + stagger |
| `lines` | `items:[string|{text}], start, out, stagger` | marker rows slide in |
| `chat` | `messages:[{text,me}], start, out, stagger` | chat bubbles |
| `ledger` | `items:[{label,to,from,dur}], start, out` | counters |
| `chart` | `items:[{label,value}], start, out` | bars grow from the baseline |
| `end` | `brand, tagline, start` | dark end card, no out |

Every builder hides its whole root before `start` and after `out + 0.45s`, so scenes cannot leak
labels or counters into another scene. `end` has no out.

## Theming

The CSS uses `--cfs-paper / --cfs-ink / --cfs-accent / --cfs-muted / --cfs-card / --cfs-line`.
Apply a look from `library/looks.js`:

```js
CF.looks.apply(stage, 'dark-tech');   // 8 looks: paper-ink, dark-tech, swiss, riso,
                                      // pixel, blueprint, hand-drawn, vox-collage
```

## Rules

- One scene builder per idea; do not reuse a builder's default story as the film's story.
- Set `start`/`out` to the beat sheet, not to arbitrary equal lengths.
- Keep the scene root's CSS layout; `gate()` only toggles `display` between `''` and `none`.
- If you need a new scene type, add it here rather than copy-pasting a one-off in a composition.
