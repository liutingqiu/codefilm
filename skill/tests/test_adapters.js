/**
 * Node tests for library/adapters.js — no browser, no third-party code.
 */
const assert = require('assert');
const A = require('../library/adapters.js');

let passed = 0;
function ok(name, fn) {
  fn();
  passed += 1;
  console.log('ok ' + name);
}

ok('hint exposes pinned version, license and setup', () => {
  const h = A.hint('gsap');
  assert.strictEqual(h.known, true);
  assert.strictEqual(h.version, '3.15.0');
  assert.ok(h.license.includes('not MIT'));
  assert.ok(h.cdn.includes('gsap@3.15.0'));
  assert.strictEqual(h.seekable, true);
});

ok('gsap seek pauses and sets time', () => {
  const calls = [];
  const tl = {
    pause() { calls.push('pause'); },
    time(t, suppress) { calls.push([t, suppress]); }
  };
  A.seek('gsap', tl, 2.5);
  assert.deepStrictEqual(calls, ['pause', [2.5, true]]);
});

ok('anime seek converts seconds to milliseconds', () => {
  let ms = null;
  const tl = { pause() {}, seek(v) { ms = v; } };
  A.seek('anime', tl, 1.25);
  assert.strictEqual(ms, 1250);
});

ok('lottie seek uses frameRate', () => {
  let frame = null;
  let isFrame = null;
  const anim = { frameRate: 25, goToAndStop(f, byFrame) { frame = f; isFrame = byFrame; } };
  A.seek('lottie', anim, 2);
  assert.strictEqual(frame, 50);
  assert.strictEqual(isFrame, true);
});

ok('motion/WAAPI controls accept currentTime', () => {
  const a = { paused: false, currentTime: 0, pause() { this.paused = true; } };
  A.seek('motion', a, 1.5);
  assert.strictEqual(a.paused, true);
  assert.strictEqual(a.currentTime, 1500);
});

ok('waapi accepts a single Animation and an array', () => {
  const one = { paused: false, currentTime: 0, pause() { this.paused = true; } };
  A.seek('waapi', one, 0.5);
  assert.strictEqual(one.currentTime, 500);
  const two = [
    { currentTime: 0, pause() {} },
    { currentTime: 0, pause() {} }
  ];
  A.seek('waapi', two, 2);
  assert.deepStrictEqual(two.map((x) => x.currentTime), [2000, 2000]);
});

ok('renderer libraries refuse a generic seek', () => {
  assert.strictEqual(A.hint('three').seekable, false);
  assert.throws(() => A.seek('three', {}, 1), /no generic seek/);
  assert.throws(() => A.seek('chart', {}, 1), /no generic seek/);
});

ok('missing() reports unknown libraries and absent globals', () => {
  delete globalThis.gsap;
  const m = A.missing(['gsap', 'nope']);
  assert.strictEqual(m.length, 2);
  assert.strictEqual(m[0].known, true);
  assert.strictEqual(m[1].known, false);
});

ok('detect() sees a loaded global', () => {
  globalThis.gsap = {};
  assert.strictEqual(A.detect('gsap'), true);
  delete globalThis.gsap;
  assert.strictEqual(A.detect('gsap'), false);
});

ok('register() adds a custom adapter', () => {
  A.register('custom', { kind: 'timeline', version: '1', license: 'MIT', seek(i, t) { i.t = t; } });
  const i = {};
  A.wrap('custom', i).render(3);
  assert.strictEqual(i.t, 3);
});

ok('framework entries carry install instructions, not a seek', () => {
  const r = A.hint('remotion');
  assert.strictEqual(r.kind, 'framework');
  assert.ok(r.install.includes('remotion'));
  assert.strictEqual(r.seekable, false);
});

// The vendored build is gitignored (third-party license); when it is present,
// verify the real GSAP timeline, not just the mock.
let gsap = null;
try {
  const pkg = require('../vendor/gsap@3.15.0/gsap.min.js');
  gsap = pkg.default || pkg;
} catch (e) {
  gsap = null;
}
if (gsap) {
  ok('real GSAP timeline seeks deterministically', () => {
    const obj = { x: 0 };
    const tl = gsap.timeline({ paused: true });
    tl.to(obj, { x: 100, duration: 1, ease: 'none' }, 0);
    A.seek('gsap', tl, 0.5);
    assert.strictEqual(obj.x, 50);
    A.seek('gsap', tl, 0.8);
    A.seek('gsap', tl, 0.5);
    assert.strictEqual(obj.x, 50);
    assert.strictEqual(gsap.version, '3.15.0');
  });
} else {
  console.log('skip real GSAP timeline (vendor/gsap@3.15.0 not present)');
}

console.log(`\n${passed} adapter groups passed`);
