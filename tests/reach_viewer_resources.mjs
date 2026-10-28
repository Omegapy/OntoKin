// Selection must exercise the adopted action phase, including a paused scene.
import assert from 'node:assert/strict';
import {captureSamples} from '../tools/verify_reach_viewer.mjs';

const rows = times => times.map((time, index) => ({sample_id: 'fixture:selection:' + index, time_seconds: time, side: 'after'}));
const lifecycle = captureSamples('L01', rows([0, .5, 1, 1.5, 2, 4]), 4);
assert.equal(lifecycle.captures[2].sample.time_seconds, 1);
assert.equal(lifecycle.extra[0].sample.time_seconds, 2);
assert.deepEqual(lifecycle.captures.map(row => row.view), ['front', 'side', 'intermediate']);
console.log('PASS L01 paused capture and separate resumed numerical check');

assert.throws(() => captureSamples('P16', rows([0, 1, 2, 4]), 4), /action-specific/);
const release = captureSamples('P16', rows([0, 1, 2, 2.5, 4]), 4);
assert.equal(release.captures[2].sample.time_seconds, 2.5);
console.log('PASS release capture requires an actual post-release reference observation');

assert.throws(() => captureSamples('P01', rows([1, 2]), 2), /initial/);
assert.throws(() => captureSamples('L03', rows([0, 1, 2]), 2), /action-specific/);
console.log('PASS absent initial state or second-owner phase cannot be silently substituted');
