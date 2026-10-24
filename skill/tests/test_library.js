const assert = require('assert');
const fs = require('fs');
const path = require('path');
const CF = require('../library/motion.js');
const looks = require('../library/looks.js');
const scenes = require('../library/scenes.js');

assert.equal(looks.names.length, 8, '8 looks');
for (const name of looks.names) {
  const l = looks.get(name);
  assert.ok(l.colors && l.colors.paper && l.colors.ink && l.type.display, name);
  assert.ok(l.motion && l.motion.enter, name + ' motion');
}
for (const name of ['title', 'cards', 'lines', 'chat', 'ledger', 'chart', 'end']) {
  assert.equal(typeof scenes[name], 'function', 'scene builder ' + name);
}
const styles = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'styles', 'index.json'), 'utf8'));
assert.equal(Object.keys(styles).length, 8, '8 style recipes');
for (const key of Object.keys(styles)) assert.ok(looks.names.includes(styles[key].look), key + ' look');
assert.equal(typeof CF.scenes, 'object');
console.log('ok looks (8) + scene builders (7) + styles (8)');
