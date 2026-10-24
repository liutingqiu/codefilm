# Motion library

`library/motion.js` exposes `window.CF` (and `module.exports` in Node). Everything is a pure
function of time in seconds; no wall clock, no unseeded randomness.

```html
<script src="../../library/motion.js"></script>
<script>
  const s = CF.rise(el, t, 0.4, {dist: 60});   // applies styles, returns {x,y,scale,rot,opacity,blur}
  const z = CF.zoomThrough(t, 3.5, {dur: .45, blur: 10});
  CF.place(el, {x: 10, y: 0, scale: 1.02, rot: 0, opacity: .8, blur: 2});
</script>
```

## Math / easing

| Function | Result |
|---|---|
| `clamp(v,a=0,b=1)` | clamp |
| `lerp(a,b,p)` / `map(v,a,b,c,d)` | interpolation |
| `smooth(p)` / `smoother(p)` | smoothstep / smootherstep |
| `ease.linear / inCubic / outCubic / inQuart / outQuart / inExpo / outExpo / inOutCubic / inOutQuart / inOutSine / backOut / backIn / elasticOut` | 0→1 curves |
| `prog(t,a,b,ease)` | normalized progress |
| `spring(t,{stiffness,damping,mass})` | damped spring 0→1 |
| `springValue(t,from,to,opts)` | spring between values |
| `kf(t,[[time,value,ease],...])` | keyframe interpolation (numbers or arrays) |
| `rng(seed)` | deterministic mulberry32 PRNG; call at build time |

## Entrances / exits

| Function | Use |
|---|---|
| `rise(el,t,start,{dur,dist,ease,blur})` | text/element rises in |
| `popIn(el,t,start,{s0,over,dist})` | card pops with a small overshoot |
| `blurIn(el,t,start,{dur,blur})` | blur-to-sharp entrance |
| `slideIn(el,t,start,{dir,dist,dur})` | directional entrance |
| `letterDrop(chars,t,start,i,{stagger,dur,dist})` | per-character drop |
| `liftOut(el,t,start,{dur,dist,blur})` | exit up |
| `fadeOut(el,t,start,dur)` | exit fade |

## Seams / carries

| Function | Use |
|---|---|
| `cutTheCurve(t,cut,dir,{dur,travel,fade,blur})` | one carrier crossing a cut; exit accelerates, entry decelerates |
| `zoomThrough(t,cut,{dur,blur})` | Z push: 1→1.2 out, .75→1 in, blur peak at the cut |
| `inverseZoom(t,cut,{dur,blur})` | Z pull: 1→.8 out, 1.25→1 in |
| `rackFocus(t,start,{dur,peak})` | blur spike hiding a same-surface swap |
| `waterfall(t,start,count,{step,dur,dist})` | word-by-word cascade states |

`cutTheCurve` returns entry opacity 0.35 at the cut so the incoming side ignites mid-flight; the
outgoing side is nearly 0. That is intentional — the fade is the velocity trick, not a crossfade.

## Camera / contact

| Function | Use |
|---|---|
| `camera(t,[{t,x,y,scale,rot,ease},...])` | keyed camera |
| `shake(t,start,{amp,dur})` | deterministic decaying shake |
| `drift(t,a,b,amp)` | slow scale drift |
| `press(t,t0,{depth,hold,flash})` | button press squash |
| `squash(vx,vy)` | squash/stretch from velocity |
| `impact(t,t0,{decay,omega,sqx,sqy})` | landing impact |

## Type / data / layout

`typeOn(t,start,text,{cps})`, `counter(t,start,dur,from,to,ease)`,
`stagger(t,start,i,{step,dur,ease})`, `inFrame(rect,w,h,whole)`, `visible(t,a,b,fade)`.

## Rules

- One clock: call these from your single `render(t)` / `seek(t)`.
- `rng(seed)` only at build time; never inside `render`.
- For a looping film, the last shot must return to the opening values.
- Prefer `cutTheCurve` / `zoomThrough` over crossfades; a crossfade has no carrier.
