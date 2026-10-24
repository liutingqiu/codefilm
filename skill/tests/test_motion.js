const assert = require('assert');
const CF = require('../library/motion.js');

let n = 0;
function ok(name, fn) { fn(); n++; console.log('ok', name); }

ok('clamp/lerp/map', () => {
  assert.equal(CF.clamp(2), 1);
  assert.equal(CF.clamp(-1), 0);
  assert.equal(CF.clamp(5, 0, 10), 5);
  assert.equal(CF.lerp(0, 10, .5), 5);
  assert.equal(CF.map(5, 0, 10, 0, 100), 50);
});

ok('eases are 0→1 and in range', () => {
  for (const [name, f] of Object.entries(CF.ease)) {
    assert.ok(Math.abs(f(0) - 0) < 1e-6, name + ' at 0');
    assert.ok(Math.abs(f(1) - 1) < 1e-6, name + ' at 1');
    for (let p = 0; p <= 1; p += .1) {
      const v = f(p);
      assert.ok(Number.isFinite(v), name + ' finite');
      if (name !== 'backOut' && name !== 'backIn' && name !== 'elasticOut') {
        assert.ok(v >= -1e-6 && v <= 1 + 1e-6, name + ' range at ' + p);
      }
    }
  }
});

ok('spring starts at 0, ends near 1', () => {
  assert.ok(Math.abs(CF.spring(0)) < 1e-9);
  assert.ok(Math.abs(CF.spring(2) - 1) < .02);
  assert.ok(CF.springValue(.5, 10, 20) > 10);
});

ok('kf numbers and arrays', () => {
  assert.equal(CF.kf(0, [[0, 0], [1, 10]]), 0);
  assert.ok(Math.abs(CF.kf(.5, [[0, 0], [1, 10]]) - 5) < 1e-6);
  const a = CF.kf(.5, [[0, [0, 10]], [1, [10, 20]]]);
  assert.ok(Math.abs(a[0] - 5) < 1e-6 && Math.abs(a[1] - 15) < 1e-6);
  assert.equal(CF.kf(9, [[0, 3], [1, 7]]), 7);
});

ok('rng is deterministic', () => {
  const a = CF.rng(42), b = CF.rng(42);
  for (let i = 0; i < 20; i++) assert.equal(a(), b());
});

ok('cutTheCurve: exit left, entry right, fade ends at cut', () => {
  const a = CF.cutTheCurve(1.995, 2, 'left', { dur: .3, travel: 230, fade: .22 });
  const b = CF.cutTheCurve(2.0, 2, 'left', { dur: .3, travel: 230, fade: .22 });
  const c = CF.cutTheCurve(2.05, 2, 'left', { dur: .3, travel: 230, fade: .22 });
  assert.ok(a.x < 0 && a.x > -230);
  assert.ok(a.opacity < .06, 'exit is nearly gone at the cut');
  assert.ok(Math.abs(b.opacity - .35) < .02, 'entry ignites at 0.35');
  assert.ok(c.x > 0, 'entry starts on the far side');
  assert.ok(c.opacity > .35);
});

ok('zoomThrough and inverseZoom', () => {
  const a = CF.zoomThrough(1.995, 2, { dur: .45 });
  const b = CF.zoomThrough(2.0, 2, { dur: .45 });
  assert.ok(a.scale > 1 && a.opacity < .25);
  assert.ok(b.scale <= .76 && b.opacity < .2);
  const c = CF.inverseZoom(2.0, 2, { dur: .7 });
  assert.ok(c.scale > 1.2);
});

ok('camera keys interpolate', () => {
  const k = [{ t: 0, x: 0, y: 0, scale: 1 }, { t: 2, x: 100, y: 50, scale: 2, ease: 'linear' }];
  const a = CF.camera(1, k);
  assert.ok(Math.abs(a.x - 50) < 1e-6 && Math.abs(a.scale - 1.5) < 1e-6);
  const b = CF.camera(3, k);
  assert.equal(b.x, 100);
});

ok('press / squash / impact', () => {
  const p = CF.press(1.0, 1.0, {});
  assert.ok(p.down);
  const s = CF.squash(0, 1000);
  assert.ok(s.sx > 1 && s.sy < 1);
  const i = CF.impact(1.05, 1.0, {});
  assert.ok(Number.isFinite(i.sx));
});

ok('typeOn / counter / stagger', () => {
  const t = CF.typeOn(1.5, 1, 'hello', { cps: 4 });
  assert.equal(t.str, 'he');
  assert.equal(CF.counter(0.5, 0, 1, 0, 100, 'linear'), 50);
  assert.equal(CF.stagger(1, 1, 0, { step: .1, dur: .4 }), 0);
  assert.ok(CF.stagger(1.2, 1, 1, { step: .1, dur: .4 }) > 0);
});

ok('visibility / frame', () => {
  assert.equal(CF.visible(0.5, 1, 2), 0);
  assert.ok(CF.visible(1.5, 1, 2) > 0);
  assert.ok(CF.inFrame({ x0: 10, y0: 10, x1: 20, y1: 20 }, 100, 100));
  assert.ok(!CF.inFrame({ x0: -30, y0: 10, x1: -5, y1: 20 }, 100, 100));
});

ok('all documented functions exist', () => {
  const names = ['clamp','lerp','map','smooth','smoother','ease','prog','spring','springValue','kf','rng',
    'place','splitChars','splitWords','rise','popIn','blurIn','slideIn','letterDrop','liftOut','fadeOut',
    'cutTheCurve','zoomThrough','inverseZoom','rackFocus','waterfall','camera','shake','drift','press',
    'squash','impact','typeOn','counter','stagger','inFrame','visible'];
  for (const name of names) assert.ok(CF[name] !== undefined, 'missing ' + name);
});

console.log('\n' + n + ' groups passed');
