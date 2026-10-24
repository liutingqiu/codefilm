/**
 * codefilm scene kit — small reusable scene builders on top of motion.js.
 *
 *   <script src="../../library/motion.js"></script>
 *   <script src="../../library/scenes.js"></script>
 *   const s = CF.scenes.title(host, {text:'...', sub:'...'});
 *   s.render(t);          // pure function of t
 *
 * Each builder returns {el, render(t)}. The caller owns the clock and the layout slot.
 * CSS is injected once; override --cfs-* variables on the scene root to theme it.
 */
(function (root) {
  'use strict';
  const CF = root.CF;
  if (!CF) throw new Error('codefilm scenes.js needs motion.js loaded first');

  const CSS = `
  .cfs{--cfs-ink:#1B1A17;--cfs-paper:#F2ECE1;--cfs-accent:#D9552B;--cfs-muted:#8A8275;
    --cfs-card:#FFFDF8;--cfs-line:#D8CFC0;position:absolute;inset:0;color:var(--cfs-ink);
    font-family:"Segoe UI",system-ui,sans-serif;overflow:hidden}
  .cfs *{box-sizing:border-box}
  .cfs-title{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:26px;text-align:center}
  .cfs-title h1{margin:0;font-family:Georgia,serif;font-size:clamp(84px,9vw,170px);line-height:1.02;
    letter-spacing:-.05em;font-weight:700;white-space:nowrap}
  .cfs-title .char{display:inline-block;will-change:transform,opacity,filter}
  .cfs-title .sub{font-size:clamp(18px,2vw,30px);letter-spacing:.18em;color:var(--cfs-muted);text-transform:uppercase}
  .cfs-cards{display:flex;align-items:center;justify-content:center;gap:24px}
  .cfs-card{width:360px;min-height:230px;background:var(--cfs-card);border:2px solid var(--cfs-ink);
    box-shadow:10px 10px 0 rgba(27,26,23,.12);padding:28px 30px;transform-origin:50% 50%;will-change:transform,opacity}
  .cfs-card .num{font:700 12px/1 monospace;letter-spacing:.12em;color:var(--cfs-accent);margin-bottom:24px}
  .cfs-card h3{margin:0 0 10px;font-size:24px;letter-spacing:-.02em}
  .cfs-card p{margin:0;font-size:15px;line-height:1.7;color:var(--cfs-muted)}
  .cfs-lines{display:flex;flex-direction:column;justify-content:center;gap:26px;padding:0 120px}
  .cfs-line{display:flex;align-items:center;gap:22px;font-size:clamp(24px,3vw,46px);font-weight:700;
    letter-spacing:-.02em;will-change:transform,opacity}
  .cfs-line .mk{width:18px;height:18px;background:var(--cfs-accent);border-radius:50%;flex:none}
  .cfs-chat{display:flex;flex-direction:column;justify-content:center;gap:18px;padding:0 160px}
  .cfs-msg{max-width:70%;padding:16px 22px;background:var(--cfs-card);border:2px solid var(--cfs-ink);
    font-size:22px;line-height:1.5;box-shadow:6px 6px 0 rgba(27,26,23,.08);will-change:transform,opacity}
  .cfs-msg.me{align-self:flex-end;background:var(--cfs-accent);color:var(--cfs-card);border-color:var(--cfs-ink)}
  .cfs-ledger{display:flex;align-items:center;justify-content:center;gap:56px}
  .cfs-stat{text-align:center}
  .cfs-stat b{display:block;font-family:Georgia,serif;font-size:clamp(54px,7vw,120px);line-height:1;letter-spacing:-.05em}
  .cfs-stat span{font-size:14px;letter-spacing:.16em;color:var(--cfs-muted);text-transform:uppercase}
  .cfs-chart{display:flex;align-items:flex-end;justify-content:center;gap:54px;padding:0 120px 90px}
  .cfs-bar{width:120px;background:var(--cfs-accent);border:2px solid var(--cfs-ink);
    transform-origin:50% 100%;will-change:transform}
  .cfs-bar:nth-child(2){background:#E7B84B}
  .cfs-bar:nth-child(3){background:#2F7D5B}
  .cfs-bar:nth-child(4){background:#3B6EA5}
  .cfs-chart .col{display:flex;flex-direction:column;align-items:center;gap:14px;height:100%;justify-content:flex-end}
  .cfs-chart label{font-size:13px;letter-spacing:.12em;color:var(--cfs-muted);text-transform:uppercase}
  .cfs-end{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:22px;
    background:var(--cfs-ink);color:var(--cfs-paper)}
  .cfs-end b{font-family:Georgia,serif;font-size:clamp(120px,13vw,240px);line-height:1;letter-spacing:-.06em}
  .cfs-end span{font-size:clamp(16px,1.8vw,26px);letter-spacing:.22em;color:#C9C1B3;text-transform:uppercase}
  .cfs-end i{width:14px;height:14px;border-radius:50%;background:var(--cfs-accent);display:block}
  `;

  let injected = false;
  function injectCSS() {
    if (injected || !document) return;
    const s = document.createElement('style');
    s.id = 'cf-scenes-css';
    s.textContent = CSS;
    document.head.appendChild(s);
    injected = true;
  }

  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function scene(parent, cls) {
    injectCSS();
    const e = el('div', 'cfs ' + (cls || ''));
    (parent || document.body).appendChild(e);
    return e;
  }

  function apply(el, st) { if (el) CF.place(el, st); return st; }

  /** Whole-scene visibility gate: hidden before start, after out + grace. */
  function gate(el, t, start, out, grace = .45) {
    const end = (out == null || !isFinite(out)) ? Infinity : out + grace;
    const on = t >= start && t < end;
    el.style.display = on ? '' : 'none';
    return on;
  }

  const S = {};

  S.title = function (parent, opts = {}) {
    const rootEl = scene(parent, 'cfs-title');
    const h = el('h1', '', opts.text || '');
    h.dataset.text = opts.text || '';
    rootEl.appendChild(h);
    const chars = CF.splitChars(h);
    const sub = el('div', 'sub', opts.sub || '');
    if (opts.sub) rootEl.appendChild(sub);
    const start = opts.start ?? 0;
    return {
      el: rootEl,
      render(t) {
        if (!gate(rootEl, t, start, opts.out ?? start + 1.4)) return;
        chars.forEach((c, i) => CF.letterDrop(chars, t, start, i, { stagger: opts.stagger ?? .06, dur: .5, dist: opts.dist ?? 64 }));
        const out = CF.ease.inCubic(CF.clamp((t - (opts.out ?? start + 1.4)) / .3));
        rootEl.style.opacity = (1 - out).toFixed(3);
        rootEl.style.transform = `translateY(${(-out * 36).toFixed(1)}px)`;
        if (opts.sub) {
          const p = CF.ease.outCubic(CF.clamp((t - start - .35) / .5));
          sub.style.opacity = (p * (1 - out)).toFixed(3);
          sub.style.transform = `translateY(${((1 - p) * 22).toFixed(1)}px)`;
        }
      }
    };
  };

  S.cards = function (parent, opts = {}) {
    const rootEl = scene(parent, 'cfs-cards');
    const items = opts.items || [];
    const cards = items.slice(0, 4).map((it, i) => {
      const c = el('div', 'cfs-card');
      c.appendChild(el('div', 'num', String(i + 1).padStart(2, '0')));
      c.appendChild(el('h3', '', it.title || ''));
      c.appendChild(el('p', '', it.body || ''));
      rootEl.appendChild(c);
      return c;
    });
    const start = opts.start ?? 0;
    return {
      el: rootEl,
      render(t) {
        if (!gate(rootEl, t, start, opts.out ?? start + 1.8)) return;
        cards.forEach((c, i) => {
          const st = CF.popIn(c, t, start + i * (opts.stagger ?? .14), { s0: .92, over: 1.015, dist: 36 });
          const out = CF.ease.inCubic(CF.clamp((t - (opts.out ?? start + 1.8)) / .3));
          c.style.opacity = (st.opacity * (1 - out)).toFixed(3);
          c.style.transform += ` translateY(${(-out * 30).toFixed(1)}px)`;
        });
      }
    };
  };

  S.lines = function (parent, opts = {}) {
    const rootEl = scene(parent, 'cfs-lines');
    const rows = (opts.items || []).map((it) => {
      const r = el('div', 'cfs-line');
      r.appendChild(el('i', 'mk'));
      r.appendChild(el('span', '', typeof it === 'string' ? it : it.text));
      rootEl.appendChild(r);
      return r;
    });
    const start = opts.start ?? 0;
    return {
      el: rootEl,
      render(t) {
        if (!gate(rootEl, t, start, opts.out ?? start + 1.8)) return;
        rows.forEach((r, i) => {
          const p = CF.ease.outCubic(CF.clamp((t - start - i * (opts.stagger ?? .12)) / .4));
          r.style.opacity = p.toFixed(3);
          r.style.transform = `translateX(${(-(1 - p) * 50).toFixed(1)}px)`;
        });
        const out = CF.ease.inCubic(CF.clamp((t - (opts.out ?? start + 1.8)) / .3));
        rootEl.style.opacity = (1 - out).toFixed(3);
      }
    };
  };

  S.chat = function (parent, opts = {}) {
    const rootEl = scene(parent, 'cfs-chat');
    const msgs = (opts.messages || []).map((m, i) => {
      const e = el('div', 'cfs-msg' + (m.me ? ' me' : ''), m.text || '');
      rootEl.appendChild(e);
      return e;
    });
    const start = opts.start ?? 0;
    return {
      el: rootEl,
      render(t) {
        if (!gate(rootEl, t, start, opts.out ?? start + 2.4)) return;
        msgs.forEach((m, i) => {
          const st = CF.popIn(m, t, start + i * (opts.stagger ?? .35), { s0: .94, over: 1.01, dist: 26 });
          const out = CF.ease.inCubic(CF.clamp((t - (opts.out ?? start + 2.4)) / .3));
          m.style.opacity = (st.opacity * (1 - out)).toFixed(3);
        });
      }
    };
  };

  S.ledger = function (parent, opts = {}) {
    const rootEl = scene(parent, 'cfs-ledger');
    const stats = (opts.items || []).map((it) => {
      const wrap = el('div', 'cfs-stat');
      const b = el('b', '', '0');
      wrap.appendChild(b);
      wrap.appendChild(el('span', '', it.label || ''));
      rootEl.appendChild(wrap);
      return { b, from: it.from ?? 0, to: it.to ?? 100, dur: it.dur ?? 1.0, start: it.start ?? 0 };
    });
    const start = opts.start ?? 0;
    return {
      el: rootEl,
      render(t) {
        if (!gate(rootEl, t, start, opts.out ?? start + 1.8)) return;
        stats.forEach((s, i) => {
          const n = CF.counter(t, start + (s.start || i * .15), s.dur, s.from, s.to);
          s.b.textContent = Math.round(n).toLocaleString('en-US');
          const p = CF.ease.outCubic(CF.clamp((t - start - i * .15) / .45));
          s.b.style.opacity = p.toFixed(3);
        });
        const out = CF.ease.inCubic(CF.clamp((t - (opts.out ?? start + 1.8)) / .3));
        rootEl.style.opacity = (1 - out).toFixed(3);
      }
    };
  };

  S.chart = function (parent, opts = {}) {
    const rootEl = scene(parent, 'cfs-chart');
    const bars = (opts.items || []).map((it, i) => {
      const col = el('div', 'col');
      const bar = el('div', 'cfs-bar');
      bar.style.height = '360px';
      col.appendChild(bar);
      col.appendChild(el('label', '', it.label || ''));
      rootEl.appendChild(col);
      return { bar, value: it.value ?? .6, i };
    });
    const start = opts.start ?? 0;
    return {
      el: rootEl,
      render(t) {
        if (!gate(rootEl, t, start, opts.out ?? start + 1.8)) return;
        bars.forEach(({ bar, value, i }) => {
          const p = CF.ease.outCubic(CF.clamp((t - start - i * .14) / .55));
          bar.style.transform = `scaleY(${(value * p).toFixed(4)})`;
        });
        const out = CF.ease.inCubic(CF.clamp((t - (opts.out ?? start + 1.8)) / .3));
        rootEl.style.opacity = (1 - out).toFixed(3);
      }
    };
  };

  S.end = function (parent, opts = {}) {
    const rootEl = scene(parent, 'cfs-end');
    const dot = el('i');
    const b = el('b', '', opts.brand || '');
    const tag = el('span', '', opts.tagline || '');
    rootEl.appendChild(dot); rootEl.appendChild(b); rootEl.appendChild(tag);
    const start = opts.start ?? 0;
    return {
      el: rootEl,
      render(t) {
        if (!gate(rootEl, t, start, null)) return;
        const p = CF.ease.outCubic(CF.clamp((t - start) / .5));
        rootEl.style.opacity = p.toFixed(3);
        rootEl.style.transform = `scale(${(0.98 + .02 * p).toFixed(3)})`;
        b.style.transform = `translateY(${((1 - p) * 24).toFixed(1)}px)`;
        tag.style.opacity = CF.ease.outCubic(CF.clamp((t - start - .25) / .5)).toFixed(3);
        dot.style.transform = `scale(${CF.ease.outCubic(CF.clamp((t - start - .1) / .3)).toFixed(3)})`;
      }
    };
  };

  CF.scenes = S;
  if (typeof module !== 'undefined' && module.exports) module.exports = S;
})(typeof window !== 'undefined' ? window : globalThis);
