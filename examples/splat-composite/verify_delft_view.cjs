// Exercise both admitted variants with a fixed camera, clock, and software renderer.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_CORE || 'playwright-core');

const [executablePath, url, out, option] = process.argv.slice(2);
if (!out) throw Error('Usage: node verify_delft_view.cjs CHROMIUM SERVED_URL NEW_OUTPUT_DIR');
fs.mkdirSync(out);

async function run() {
  const flags = ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader',
    '--enable-unsafe-swiftshader', '--disable-dev-shm-usage'];
  const browser = await chromium.launch({executablePath, headless: true, args: flags});
  try {
    const page = await browser.newPage({viewport: {width: 640, height: 540}, deviceScaleFactor: 1});
    page.setDefaultTimeout(90000);
    const envRequests = [], pageErrors = [];
    page.on('request', req => {
      if (new URL(req.url()).pathname.endsWith('/delft.glb')) envRequests.push(req.resourceType());
    });
    page.on('pageerror', error => pageErrors.push(error.message));
    const status = page.locator('#status'), canvas = page.locator('#canvas');
    const environment = page.locator('#environment'), time = page.locator('#time');
    const play = page.locator('#play');
    const click = locator => locator.evaluate(button => button.click());
    const seek = value => time.evaluate((e,v) => { e.value=v; e.dispatchEvent(new Event('input')); },String(value));
    const show = value => environment.evaluate((e,v) => { e.checked=v; e.dispatchEvent(new Event('change')); },value);
    async function ready(name) {
      await page.waitForFunction(name => {
        if (document.querySelector('#status').dataset.error === 'true') return true;
        const s = document.querySelector('#metrics').textContent;
        return s.startsWith('{') && JSON.parse(s).variant === name;
      }, name);
      assert.equal(await status.getAttribute('data-error'), 'false', await status.textContent());
    }
    const settle = () => page.evaluate(() => new Promise(done =>
      requestAnimationFrame(() => requestAnimationFrame(done))));
    async function save(name) {
      await settle();
      await canvas.screenshot({path: path.join(out, name + '.png')});
      console.log('Captured ' + name);
    }
    async function measure() {
      await click(play);
      console.log('Measuring playback');
      const intervals = await page.evaluate(() => new Promise(done => {
        const values = [];
        let previous, first;
        const tick = now => {
          if (previous !== undefined) values.push(+(now - previous).toFixed(3));
          first ??= now;
          previous = now;
          if (values.length < 30 && now - first < 75000) requestAnimationFrame(tick);
          else done(values);
        };
        requestAnimationFrame(tick);
      }));
      const finalTime = Number(await time.inputValue());
      await click(play);
      const sorted = [...intervals].sort((a,b) => a-b);
      const viewer = JSON.parse(await page.locator('#metrics').textContent());
      assert.ok(intervals.length >= 5, 'Too few playback samples');
      assert.equal(viewer.backend, 'WebGL2');
      assert.ok(viewer.firstCompositeSubmitMs > 0);
      assert.ok(intervals.every(v => v > 0));
      return {viewer, playback: {camera: 'Cart view', startedAtSeconds: 0,
        endedAtSeconds: finalTime, intervalsMs: intervals, sampleCount: intervals.length,
        medianMs: sorted[Math.ceil(sorted.length * .5)-1], p95Ms: sorted[Math.ceil(sorted.length * .95)-1]}};
    }
    await page.goto(url);
    await ready('baseline');
    console.log('Verified baseline receipt and renderer');
    assert.equal(await page.title(), 'OntoKin · Cart at TU Delft');
    if (option === '--occlusion') {
      const poses = {early: 1.0, middle: 1.5, late: 1.99};
      for (const id of ['foreground', 'low']) {
        await page.locator('#' + id).evaluate(button => button.click());
        for (const [pose, t] of Object.entries(poses)) {
          for (const [suffix, site, authored] of [['on', true, true], ['off', false, true], ['site', true, false]]) {
            await page.evaluate(({t, site, authored}) => {
              const time = document.querySelector('#time');
              time.value = String(t); time.dispatchEvent(new Event('input'));
              for (const [id, checked] of [['environment', site], ['assembly', authored]]) {
                const toggle = document.getElementById(id);
                toggle.checked = checked; toggle.dispatchEvent(new Event('change'));
              }
            }, {t, site, authored});
            await save(id + '-' + pose + '-' + suffix);
          }
        }
      }
      fs.writeFileSync(path.join(out, 'views.json'), JSON.stringify({
        browser: browser.version(), posesSeconds: poses, cameraButtons: ['foreground', 'low'],
        canvas: await canvas.boundingBox(), environmentRequestCount: envRequests.length, pageErrors}, null, 2));
      assert.equal(envRequests.length, 1);
      assert.deepEqual(pageErrors, []);
      return;
    }
    await click(page.locator('#screen'));
    await seek('0');
    let baseline;
    await show(true);
    const poses = {early: 1.08, middle: 1.294, late: 1.8};
    for (const [pose, t] of Object.entries(poses)) {
      await seek(String(t));
      for (const visible of [true, false]) {
        await show(visible);
        await save(pose + (visible ? '-on' : '-off'));
      }
    }
    await show(true);
    for (const id of ['overview', 'reverse', 'campus']) {
      await click(page.locator('#' + id));
      await save(id);
    }
    await click(page.locator('#screen'));
    await seek('0');
    baseline = await measure();
    fs.writeFileSync(path.join(out, 'baseline-timing.json'), JSON.stringify(baseline, null, 2));
    await seek('1.8');
    await save('baseline');
    await click(page.locator('#widened'));
    await ready('widened');
    const switchTime = Number(await time.inputValue());
    assert.equal(switchTime, 1.8);
    await save('widened');
    await seek('0');
    const widened = await measure();
    const webgl = await canvas.evaluate(el => {
      const gl = el.getContext('webgl2');
      const ext = gl.getExtension('WEBGL_debug_renderer_info');
      return {version: gl.getParameter(gl.VERSION),
        renderer: ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER)};
    });
    const report = {browser: browser.version(), flags, webgl, viewport: page.viewportSize(),
      canvas: await canvas.boundingBox(), posesSeconds: poses, camera: 'Cart view',
      environmentRequestCount: envRequests.length, pageErrors, preservedEditTimeSeconds: switchTime,
      baseline, widened};
    fs.writeFileSync(path.join(out, 'browser.json'), JSON.stringify(report, null, 2) + '\n');
    assert.equal(envRequests.length, 1);
    assert.deepEqual(pageErrors, []);
    assert.equal(baseline.viewer.environmentSha256, widened.viewer.environmentSha256);
    assert.notEqual(baseline.viewer.authoredSha256, widened.viewer.authoredSha256);
  } finally {
    await browser.close();
  }
}

run().catch(error => { console.error(error.message); process.exitCode = 1; });
