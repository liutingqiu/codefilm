/**
 * codefilm optional-library adapters.
 *
 * codefilm ships zero third-party JS. This file only knows how to *drive* a
 * library that is already loaded, and what to download if one is missing. It
 * never downloads at runtime: the agent vendors a pinned build (see
 * `references/js-libraries.md` and `vendor/README.md`).
 *
 *   <script src="../../library/adapters.js"></script>
 *   CF.adapters.hint('gsap')
 *   CF.adapters.missing(['gsap', 'three'])
 *   CF.adapters.seek('gsap', tl, 3.2)
 *   CF.adapters.wrap('gsap', tl).render(3.2)
 *
 * Timeline/player libraries get a generic `seek`. Renderer libraries have no
 * timeline; their `recipe` string is the pattern to implement in the page.
 */
(function (root) {
  'use strict';
  const CF = root.CF || (root.CF = {});

  const specs = {
    gsap: {
      version: '3.15.0',
      license: 'GSAP Standard (not MIT)',
      kind: 'timeline',
      global: 'gsap',
      build: 'dist/gsap.min.js',
      cdn: 'https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js',
      size: '73 KB min',
      setup: 'one script tag; no build',
      seek(tl, t) {
        if (!tl || typeof tl.time !== 'function' || typeof tl.pause !== 'function') {
          throw new TypeError('gsap timeline expected');
        }
        tl.pause();
        tl.time(Math.max(0, Number(t) || 0), true);
      },
      recipe: 'const tl = gsap.timeline({paused:true}); …; tl.time(t, true)'
    },

    anime: {
      version: '4.5.0',
      license: 'MIT',
      kind: 'timeline',
      global: 'anime',
      build: 'dist/bundles/anime.umd.min.js',
      cdn: 'https://cdn.jsdelivr.net/npm/animejs@4.5.0/dist/bundles/anime.umd.min.js',
      size: '118 KB min',
      setup: 'script tag; or ESM import',
      seek(tl, t) {
        if (!tl) throw new TypeError('anime timeline expected');
        if (typeof tl.pause === 'function') tl.pause();
        if (typeof tl.seek === 'function') {
          tl.seek(Math.max(0, Number(t) || 0) * 1000);
          return;
        }
        if (typeof tl.currentTime === 'number') {
          tl.currentTime = Math.max(0, Number(t) || 0) * 1000;
          return;
        }
        throw new TypeError('anime timeline has no seek/currentTime');
      },
      recipe: 'const tl = anime.createTimeline({autoplay:false}); …; tl.seek(t*1000)'
    },

    lottie: {
      version: '5.13.0',
      license: 'MIT',
      kind: 'player',
      global: 'lottie',
      build: 'build/player/lottie.min.js',
      cdn: 'https://cdn.jsdelivr.net/npm/lottie-web@5.13.0/build/player/lottie.min.js',
      size: '306 KB min',
      setup: 'script tag + JSON animation asset',
      seek(anim, t) {
        if (!anim || typeof anim.goToAndStop !== 'function') {
          throw new TypeError('lottie animation expected');
        }
        const fps = Number(anim.frameRate) || 30;
        anim.goToAndStop(Math.round(Math.max(0, Number(t) || 0) * fps), true);
      },
      recipe: 'animation.goToAndStop(Math.round(t * animation.frameRate), true)'
    },

    motion: {
      version: '14.6.0',
      license: 'MIT',
      kind: 'waapi',
      global: null,
      build: 'dist/motion.js',
      esm: 'https://cdn.jsdelivr.net/npm/motion@14.6.0/dist/motion.js',
      size: '172 KB',
      setup: 'ESM + import map or bundler; no UMD global',
      seek(anim, t) {
        if (!anim) throw new TypeError('motion animation controls expected');
        if (typeof anim.pause === 'function') anim.pause();
        const ms = Math.max(0, Number(t) || 0) * 1000;
        if (typeof anim.currentTime === 'number') {
          anim.currentTime = ms;
          return;
        }
        if (typeof anim.time === 'number') {
          anim.time = ms / 1000;
          return;
        }
        if (typeof anim.seek === 'function') {
          anim.seek(ms);
          return;
        }
        throw new TypeError('motion controls have no currentTime/time/seek');
      },
      recipe: 'a.pause(); a.currentTime = t*1000  (WAAPI controls)'
    },

    waapi: {
      version: 'browser built-in',
      license: 'n/a',
      kind: 'waapi',
      global: null,
      setup: 'no dependency; document.getAnimations()',
      detect() {
        return typeof document !== 'undefined'
          && typeof document.getAnimations === 'function';
      },
      seek(animations, t) {
        if (!animations) throw new TypeError('Animation or Animation[] expected');
        const list = (Array.isArray(animations) || typeof animations.length === 'number')
          ? Array.from(animations) : [animations];
        const ms = Math.max(0, Number(t) || 0) * 1000;
        for (const a of list) {
          if (typeof a.pause === 'function') a.pause();
          if ('currentTime' in a) a.currentTime = ms;
        }
      },
      recipe: 'document.getAnimations().forEach(a => { a.pause(); a.currentTime = t*1000; })'
    },

    three: {
      version: '0.186.1',
      license: 'MIT',
      kind: 'renderer',
      global: 'THREE',
      build: 'build/three.module.js',
      esm: 'https://cdn.jsdelivr.net/npm/three@0.186.1/build/three.module.js',
      size: '663 KB',
      setup: 'ESM + import map or bundler; no UMD build',
      recipe: 'renderer.setAnimationLoop(null); update(t); renderer.render(scene, camera)'
    },

    pixi: {
      version: '8.22.0',
      license: 'MIT',
      kind: 'renderer',
      global: 'PIXI',
      build: 'dist/pixi.min.js',
      cdn: 'https://cdn.jsdelivr.net/npm/pixi.js@8.22.0/dist/pixi.min.js',
      size: '841 KB min',
      setup: 'script tag or ESM; WebGL/WebGPU',
      recipe: 'app.ticker.stop(); update(t); app.renderer.render(app.stage)'
    },

    d3: {
      version: '7.9.0',
      license: 'ISC',
      kind: 'renderer',
      global: 'd3',
      build: 'dist/d3.min.js',
      cdn: 'https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js',
      size: '280 KB min',
      setup: 'script tag or ESM modules',
      recipe: 'use scales/shapes directly from t; never d3.transition() on the render path'
    },

    chart: {
      version: '4.6.1',
      license: 'MIT',
      kind: 'renderer',
      global: 'Chart',
      build: 'dist/chart.umd.js',
      cdn: 'https://cdn.jsdelivr.net/npm/chart.js@4.6.1/dist/chart.umd.js',
      size: '210 KB min',
      setup: 'script tag; canvas',
      recipe: 'new Chart(ctx,{options:{animation:false,responsive:false}}); update(t); chart.update("none")'
    },

    p5: {
      version: '2.3.4',
      license: 'LGPL-2.1',
      kind: 'renderer',
      global: 'p5',
      build: 'lib/p5.min.js',
      cdn: 'https://cdn.jsdelivr.net/npm/p5@2.3.4/lib/p5.min.js',
      size: '991 KB min',
      setup: 'script tag; canvas',
      recipe: 'p.noLoop(); set window.__p5t = t; p.redraw()'
    },

    konva: {
      version: '10.9.0',
      license: 'MIT',
      kind: 'renderer',
      global: 'Konva',
      build: 'konva.min.js',
      cdn: 'https://cdn.jsdelivr.net/npm/konva@10.9.0/konva.min.js',
      size: '196 KB min',
      setup: 'script tag; canvas',
      recipe: 'update(t); layer.draw()'
    },

    rough: {
      version: '4.6.6',
      license: 'MIT',
      kind: 'pure',
      global: 'rough',
      build: 'bundled/rough.js',
      cdn: 'https://cdn.jsdelivr.net/npm/roughjs@4.6.6/bundled/rough.js',
      size: '28 KB',
      setup: 'script tag; no clock',
      recipe: 'draw with rc.rectangle(...) from t; no animation loop'
    },

    remotion: {
      version: '4.0.538',
      license: 'Remotion License (not MIT; check company terms)',
      kind: 'framework',
      global: null,
      setup: 'npm + React + bundler + Node renderer',
      install: 'npm i remotion @remotion/cli react react-dom',
      recipe: 'separate route: React composition + npx remotion render'
    },

    motioncanvas: {
      version: '3.17.2',
      license: 'MIT',
      kind: 'framework',
      global: null,
      setup: 'Vite + TypeScript; generator functions',
      install: 'npm i @motion-canvas/core @motion-canvas/2d @motion-canvas/vite-plugin',
      recipe: 'separate route: scene generator + Motion Canvas renderer'
    }
  };

  function hint(name) {
    const s = specs[name];
    if (!s) {
      return { name, known: false, message: 'not in the adapter registry; see references/js-libraries.md' };
    }
    return {
      name, known: true, version: s.version, license: s.license, kind: s.kind,
      global: s.global, build: s.build, cdn: s.cdn, esm: s.esm, size: s.size,
      setup: s.setup, install: s.install, seekable: typeof s.seek === 'function',
      recipe: s.recipe
    };
  }

  function detect(name) {
    const s = specs[name];
    if (!s) return false;
    if (typeof s.detect === 'function') return !!s.detect();
    if (!s.global) return false;
    return !!root[s.global];
  }

  function missing(names) {
    return (names || []).filter((n) => !detect(n)).map(hint);
  }

  function seek(name, instance, t) {
    const s = specs[name];
    if (!s) throw new Error('unknown adapter: ' + name);
    if (typeof s.seek !== 'function') {
      throw new Error(name + ' is a ' + s.kind + '; no generic seek. ' + (s.recipe || ''));
    }
    s.seek(instance, Math.max(0, Number(t) || 0));
    return instance;
  }

  function wrap(name, instance) {
    return {
      render(t) { return seek(name, instance, t); }
    };
  }

  function register(name, spec) {
    if (!name || !spec || typeof spec !== 'object') {
      throw new TypeError('register(name, spec) needs a name and an object');
    }
    specs[name] = spec;
    return hint(name);
  }

  CF.adapters = {
    version: '2026-10-24',
    specs,
    hint,
    detect,
    missing,
    seek,
    wrap,
    register
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = CF.adapters;
})(typeof window !== 'undefined' ? window : globalThis);
