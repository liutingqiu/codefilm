/**
 * codefilm motion library — deterministic helpers for HTML/CSS/Canvas video.
 *
 * Everything here is a pure function of time (seconds). No Date.now(), no wall-clock,
 * no unseeded randomness. Load with <script src="motion.js"></script> and use window.CF.
 * Node tests: require('./motion.js').
 */
(function (root) {
  'use strict';
  const CF = {};

  // ── math ────────────────────────────────────────────────────────────────
  CF.clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  CF.lerp = (a, b, p) => a + (b - a) * p;
  CF.map = (v, a, b, c, d) => c + (d - c) * CF.clamp((v - a) / (b - a));
  CF.smooth = (p) => { p = CF.clamp(p); return p * p * (3 - 2 * p); };
  CF.smoother = (p) => { p = CF.clamp(p); return p * p * p * (p * (p * 6 - 15) + 10); };

  CF.ease = {
    linear: (p) => CF.clamp(p),
    inCubic: (p) => { p = CF.clamp(p); return p * p * p; },
    outCubic: (p) => { p = 1 - CF.clamp(p); return 1 - p * p * p; },
    inQuart: (p) => { p = CF.clamp(p); return p * p * p * p; },
    outQuart: (p) => { p = 1 - CF.clamp(p); return 1 - p * p * p * p; },
    inExpo: (p) => { p = CF.clamp(p); return p <= 0 ? 0 : Math.pow(2, 10 * (p - 1)); },
    outExpo: (p) => { p = CF.clamp(p); return p >= 1 ? 1 : 1 - Math.pow(2, -10 * p); },
    inOutCubic: (p) => { p = CF.clamp(p); return p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; },
    inOutQuart: (p) => { p = CF.clamp(p); return p < .5 ? 8 * p * p * p * p : 1 - Math.pow(-2 * p + 2, 4) / 2; },
    inOutSine: (p) => -(Math.cos(Math.PI * CF.clamp(p)) - 1) / 2,
    backOut: (p, s = 1.70158) => { p = CF.clamp(p) - 1; return 1 + (s + 1) * p * p * p + s * p * p; },
    backIn: (p, s = 1.70158) => { p = CF.clamp(p); return p * p * ((s + 1) * p - s); },
    elasticOut: (p) => {
      p = CF.clamp(p);
      if (p === 0 || p === 1) return p;
      return Math.pow(2, -10 * p) * Math.sin((p * 10 - .75) * (2 * Math.PI / 3)) + 1;
    }
  };

  CF.prog = (t, a, b, ease = 'outCubic') => CF.ease[ease](CF.clamp((t - a) / (b - a)));

  /** Damped spring step response 0 → 1. damping < 1 oscillates. */
  CF.spring = (t, opts = {}) => {
    const stiffness = opts.stiffness ?? 90;
    const damping = opts.damping ?? .86;
    const mass = opts.mass ?? 1;
    if (t <= 0) return 0;
    const w0 = Math.sqrt(stiffness / mass);
    if (damping < 1) {
      const wd = w0 * Math.sqrt(1 - damping * damping);
      return 1 - Math.exp(-damping * w0 * t) * (Math.cos(wd * t) + (damping * w0 / wd) * Math.sin(wd * t));
    }
    return 1 - Math.exp(-w0 * t) * (1 + w0 * t);
  };
  CF.springValue = (t, from, to, opts = {}) => from + (to - from) * CF.spring(t, opts);

  /** Keyframes: [[time, value, ease?], ...]. Value may be a number or an array. */
  CF.kf = (t, keys, defaultEase = 'inOutCubic') => {
    if (!keys || !keys.length) return 0;
    if (t <= keys[0][0]) return keys[0][1];
    for (let i = 1; i < keys.length; i++) {
      if (t <= keys[i][0]) {
        const [t0, v0] = keys[i - 1];
        const [t1, v1, e] = keys[i];
        const p = CF.ease[e || defaultEase]((t - t0) / Math.max(1e-6, t1 - t0));
        return Array.isArray(v0) ? v0.map((x, j) => CF.lerp(x, v1[j], p)) : CF.lerp(v0, v1, p);
      }
    }
    return keys[keys.length - 1][1];
  };

  /** Deterministic PRNG (mulberry32); call once at build time, not per frame. */
  CF.rng = (seed = 1) => {
    let s = seed >>> 0;
    return () => {
      s = (s + 0x6D2B79F5) >>> 0;
      let t = s;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };

  // ── DOM ─────────────────────────────────────────────────────────────────
  /** Apply a state {x,y,scale,rot,opacity,blur} to an element. */
  CF.place = (el, st = {}) => {
    if (!el) return st;
    const x = st.x ?? 0, y = st.y ?? 0, s = st.scale ?? 1, r = st.rot ?? 0;
    el.style.transform = `translate(${x.toFixed(2)}px,${y.toFixed(2)}px) scale(${s.toFixed(4)}) rotate(${r.toFixed(2)}deg)`;
    el.style.opacity = (st.opacity ?? 1).toFixed(3);
    el.style.filter = (st.blur ?? 0) > .05 ? `blur(${(st.blur).toFixed(2)}px)` : 'none';
    return st;
  };

  CF.splitChars = (el) => {
    if (el.__chars) return el.__chars;
    const text = el.dataset.text || el.textContent;
    el.dataset.text = text;
    el.textContent = '';
    const arr = [];
    for (const ch of text) {
      const s = document.createElement('span');
      s.className = 'char';
      s.textContent = ch === ' ' ? ' ' : ch;
      el.appendChild(s);
      arr.push(s);
    }
    el.__chars = arr;
    return arr;
  };

  CF.splitWords = (el) => {
    if (el.__words) return el.__words;
    const text = el.dataset.text || el.textContent;
    el.dataset.text = text;
    el.textContent = '';
    const arr = text.split(/(\s+)/).map((w) => {
      const s = document.createElement('span');
      s.className = 'word';
      s.textContent = w;
      el.appendChild(s);
      return s;
    });
    el.__words = arr;
    return arr;
  };

  // ── entrances ───────────────────────────────────────────────────────────
  CF.rise = (el, t, start, opts = {}) => {
    const dur = opts.dur ?? .55, dist = opts.dist ?? 64;
    const p = CF.ease[opts.ease || 'outCubic'](CF.clamp((t - start) / dur));
    const st = { x: 0, y: (1 - p) * dist, scale: 1, rot: 0,
                 opacity: p, blur: (1 - p) * (opts.blur ?? 6) };
    return el ? CF.place(el, st) : st;
  };

  CF.popIn = (el, t, start, opts = {}) => {
    const dur = opts.dur ?? .45, s0 = opts.s0 ?? .92, over = opts.over ?? 1.02;
    const p = CF.clamp((t - start) / dur);
    const s = p < .7 ? CF.lerp(s0, over, CF.ease.outCubic(p / .7))
                     : CF.lerp(over, 1, CF.ease.inOutCubic((p - .7) / .3));
    const st = { x: 0, y: (1 - CF.ease.outCubic(p)) * (opts.dist ?? 24), scale: s,
                 rot: 0, opacity: CF.ease.outCubic(p), blur: 0 };
    return el ? CF.place(el, st) : st;
  };

  CF.blurIn = (el, t, start, opts = {}) => {
    const dur = opts.dur ?? .35, p = CF.ease.outCubic(CF.clamp((t - start) / dur));
    const st = { x: 0, y: 0, scale: 1, rot: 0, opacity: p, blur: (1 - p) * (opts.blur ?? 10) };
    return el ? CF.place(el, st) : st;
  };

  CF.slideIn = (el, t, start, opts = {}) => {
    const dir = opts.dir || 'left';
    const dist = opts.dist ?? 80, dur = opts.dur ?? .45;
    const p = CF.ease.outCubic(CF.clamp((t - start) / dur));
    const sign = dir === 'left' ? -1 : dir === 'right' ? 1 : 0;
    const st = { x: sign * (1 - p) * dist, y: dir === 'up' ? (1 - p) * dist : dir === 'down' ? -(1 - p) * dist : 0,
                 scale: 1, rot: 0, opacity: p, blur: 0 };
    return el ? CF.place(el, st) : st;
  };

  CF.letterDrop = (chars, t, start, i, opts = {}) => {
    const stagger = opts.stagger ?? .045, dur = opts.dur ?? .4, dist = opts.dist ?? 48;
    const p = CF.ease.outCubic(CF.clamp((t - start - i * stagger) / dur));
    const st = { x: 0, y: (1 - p) * dist, scale: 1, rot: 0,
                 opacity: p, blur: (1 - p) * (opts.blur ?? 4) };
    if (chars && chars[i]) CF.place(chars[i], st);
    return st;
  };

  // ── exits ───────────────────────────────────────────────────────────────
  CF.liftOut = (el, t, start, opts = {}) => {
    const dur = opts.dur ?? .3, dist = opts.dist ?? 40;
    const p = CF.ease.inCubic(CF.clamp((t - start) / dur));
    const st = { x: 0, y: -p * dist, scale: 1 - p * .03, rot: 0,
                 opacity: 1 - p, blur: p * (opts.blur ?? 6) };
    return el ? CF.place(el, st) : st;
  };

  CF.fadeOut = (el, t, start, dur = .3) => {
    const p = CF.ease.inCubic(CF.clamp((t - start) / dur));
    const st = { x: 0, y: 0, scale: 1, rot: 0, opacity: 1 - p, blur: 0 };
    return el ? CF.place(el, st) : st;
  };

  // ── seams / carries ─────────────────────────────────────────────────────
  /**
   * A carrier crossing one cut: before the cut it accelerates out, after it decelerates in.
   * dir: left | right | up | down. Returns {x,y,opacity,blur}.
   */
  CF.cutTheCurve = (t, cut, dir = 'left', opts = {}) => {
    const dur = opts.dur ?? .3, travel = opts.travel ?? 230;
    const fade = opts.fade ?? .22, blur = opts.blur ?? 8;
    const sign = dir === 'left' ? -1 : dir === 'right' ? 1 : 0;
    const vert = dir === 'up' || dir === 'down';
    if (t < cut) {
      const p = CF.ease.inCubic(CF.clamp((t - (cut - dur)) / dur));
      const o = 1 - CF.clamp((t - (cut - fade)) / fade);
      return { x: vert ? 0 : sign * travel * p, y: vert ? (dir === 'up' ? -1 : 1) * travel * p : 0,
               opacity: o, blur: blur * p };
    }
    const p = CF.ease.outCubic(CF.clamp((t - cut) / dur));
    return { x: vert ? 0 : -sign * travel * (1 - p), y: vert ? (dir === 'up' ? 1 : -1) * travel * (1 - p) : 0,
             opacity: CF.clamp(.35 + .65 * p), blur: blur * (1 - p) };
  };

  CF.zoomThrough = (t, cut, opts = {}) => {
    const dur = opts.dur ?? .45, textBlur = opts.blur ?? 10;
    if (t < cut) {
      const p = CF.ease.inCubic(CF.clamp((t - (cut - dur * .45)) / (dur * .45)));
      return { scale: 1 + .2 * p, opacity: 1 - .85 * p, blur: textBlur * p };
    }
    const p = CF.ease.outExpo(CF.clamp((t - cut) / (dur * .55)));
    return { scale: .75 + .25 * p, opacity: .15 + .85 * p, blur: textBlur * (1 - p) };
  };

  CF.inverseZoom = (t, cut, opts = {}) => {
    const dur = opts.dur ?? .7, textBlur = opts.blur ?? 10;
    if (t < cut) {
      const p = CF.ease.inCubic(CF.clamp((t - (cut - dur * .3)) / (dur * .3)));
      return { scale: 1 - .2 * p, opacity: 1 - .85 * p, blur: textBlur * p };
    }
    const p = CF.ease.outExpo(CF.clamp((t - cut) / (dur * .7)));
    return { scale: 1.25 - .25 * p, opacity: .15 + .85 * p, blur: textBlur * (1 - p) };
  };

  CF.rackFocus = (t, start, opts = {}) => {
    const dur = opts.dur ?? .3, peak = opts.peak ?? 10;
    const p = CF.clamp((t - start) / dur);
    const b = p < .5 ? peak * CF.ease.inCubic(p * 2) : peak * (1 - CF.ease.outCubic((p - .5) * 2));
    return { blur: b, scale: 1 + .06 * Math.sin(Math.PI * p) };
  };

  /** Word-by-word cascade. Returns an array of states; apply to spans. */
  CF.waterfall = (t, start, count, opts = {}) => {
    const step = opts.step ?? .067, dur = opts.dur ?? .3;
    const dist = opts.dist ?? 230, out = [];
    for (let i = 0; i < count; i++) {
      const p = CF.ease.outCubic(CF.clamp((t - start - i * step) / dur));
      out.push({ x: dist * (1 - p), opacity: .35 + .65 * p, blur: (1 - p) * (opts.blur ?? 0) });
    }
    return out;
  };

  // ── camera / contact ────────────────────────────────────────────────────
  /** Interpolate camera keys: [{t,x,y,scale,rot,ease}] → state. */
  CF.camera = (t, keys) => {
    if (!keys || !keys.length) return { x: 0, y: 0, scale: 1, rot: 0 };
    if (t <= keys[0].t) return { x: keys[0].x || 0, y: keys[0].y || 0, scale: keys[0].scale ?? 1, rot: keys[0].rot || 0 };
    for (let i = 1; i < keys.length; i++) {
      if (t <= keys[i].t) {
        const a = keys[i - 1], b = keys[i];
        const p = CF.ease[b.ease || 'inOutCubic']((t - a.t) / Math.max(1e-6, b.t - a.t));
        return { x: CF.lerp(a.x || 0, b.x || 0, p), y: CF.lerp(a.y || 0, b.y || 0, p),
                 scale: CF.lerp(a.scale ?? 1, b.scale ?? 1, p), rot: CF.lerp(a.rot || 0, b.rot || 0, p) };
      }
    }
    const z = keys[keys.length - 1];
    return { x: z.x || 0, y: z.y || 0, scale: z.scale ?? 1, rot: z.rot || 0 };
  };

  /** Deterministic decaying shake. */
  CF.shake = (t, start, opts = {}) => {
    const dur = opts.dur ?? .4, amp = opts.amp ?? 8;
    if (t < start || t > start + dur) return { x: 0, y: 0 };
    const p = (t - start) / dur, k = Math.pow(1 - p, 2);
    return { x: Math.sin(t * 61 + 1.7) * amp * k, y: Math.cos(t * 53 + .3) * amp * k };
  };

  CF.drift = (t, a, b, amp = .06) => {
    const p = CF.smooth((t - a) / (b - a));
    return 1 + amp * p;
  };

  CF.press = (t, t0, opts = {}) => {
    const depth = opts.depth ?? .08, flash = opts.flash ?? .3;
    const down = t >= t0 && t < t0 + (opts.hold ?? .16);
    const sq = down ? depth * CF.ease.outCubic((t - t0) / .1) : depth * (1 - CF.ease.outCubic(Math.max(0, t - t0 - (opts.hold ?? .16)) / .2));
    return { down, sq, active: t >= t0 && t < t0 + flash };
  };

  CF.squash = (vx, vy) => {
    const speed = Math.hypot(vx, vy);
    const k = CF.clamp(speed / 1200, 0, 1);
    return { ang: Math.atan2(vy, vx) * 180 / Math.PI,
             sx: 1 + k * .18, sy: 1 - k * .18 };
  };

  CF.impact = (t, t0, opts = {}) => {
    const decay = opts.decay ?? 7, omega = opts.omega ?? 22;
    const u = Math.max(0, t - t0);
    const e = Math.exp(-decay * u) * Math.sin(omega * u);
    return { sx: 1 + (opts.sqx ?? .16) * e, sy: 1 + (opts.sqy ?? .20) * e };
  };

  // ── type / data ─────────────────────────────────────────────────────────
  CF.typeOn = (t, start, text, opts = {}) => {
    const cps = opts.cps ?? 30;
    const n = Math.floor(CF.clamp((t - start) * cps, 0, text.length));
    return { str: text.slice(0, n), caret: t >= start && n < text.length, done: n >= text.length };
  };

  CF.counter = (t, start, dur, from, to, ease = 'outCubic') => {
    const p = CF.ease[ease](CF.clamp((t - start) / dur));
    return from + (to - from) * p;
  };

  CF.stagger = (t, start, i, opts = {}) => {
    const step = opts.step ?? .08, dur = opts.dur ?? .4;
    return CF.ease[opts.ease || 'outCubic'](CF.clamp((t - start - i * step) / dur));
  };

  // ── layout checks ───────────────────────────────────────────────────────
  CF.inFrame = (rect, w, h, whole = false) => {
    if (!rect) return false;
    if (whole) return rect.x0 >= 0 && rect.y0 >= 0 && rect.x1 <= w && rect.y1 <= h;
    return rect.x1 > 0 && rect.y1 > 0 && rect.x0 < w && rect.y0 < h;
  };

  CF.visible = (t, a, b, fade = .2) => {
    if (t < a || t > b) return 0;
    return Math.min(CF.clamp((t - a) / fade), CF.clamp((b - t) / fade));
  };

  root.CF = CF;
  if (typeof module !== 'undefined' && module.exports) module.exports = CF;
})(typeof window !== 'undefined' ? window : globalThis);
