// C272 playback inspection (TASK-026, DEC-009): load one regenerated GLB from its actual bytes
// in the project's offline viewer, capture frames at stated times and during real playback.
// Usage: node docs/engineering/localized-repair-c272/inspect_playback.mjs GLB OUTPUT_DIR
// The frames are for a person to look at; they establish no numerical result.
import {mkdir, readFile, writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const {chromium} = createRequire(path.join(root, 'tools/package.json'))('playwright');
const [glb, outputDir] = process.argv.slice(2).map(value => path.resolve(value));
if (!glb || !outputDir) throw new Error('Usage: inspect_playback.mjs GLB OUTPUT_DIR');
await mkdir(outputDir, {recursive: true});
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const viewer = path.join(root, 'examples/visual/viewer.html');
const report = {schema: 'ontokin.c272.playback-capture/1', glb: path.basename(glb), glb_sha256: sha256(await readFile(glb)),
  viewer: {html: 'examples/visual/viewer.html', html_sha256: sha256(await readFile(viewer)),
           bundle_sha256: sha256(await readFile(path.join(root, 'examples/visual/viewer.bundle.js')))},
  frames: [], playback: null, page_errors: [], console_errors: [], network_requests: []};
const browser = await chromium.launch({headless: true, args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
try {
  report.browser = await browser.version();
  const page = await browser.newPage({viewport: {width: 1440, height: 1060}, deviceScaleFactor: 1});
  page.on('pageerror', error => report.page_errors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') report.console_errors.push(message.text()); });
  page.on('request', request => { if (/^https?:/.test(request.url())) report.network_requests.push(request.url()); });
  await page.route(/^https?:\/\//, route => route.abort());
  await page.goto(pathToFileURL(viewer).href);
  await page.waitForFunction(() => window.ontokinViewer?.ready);
  await page.locator('#local-file').setInputFiles(glb);
  await page.waitForFunction(() => window.ontokinViewer.ready && window.ontokinViewer.state.demo === null);
  report.scene_title = await page.locator('#scene-title').textContent();
  report.error_visible = await page.locator('#error').isVisible();
  await page.click('#fit');
  const settle = () => page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  for (const seconds of [0, 0.5, 1, 1.5, 2]) {
    await page.locator('#timeline').fill(String(seconds));
    await settle();
    const state = await page.evaluate(() => window.ontokinViewer.state);
    const file = `frame-${seconds.toFixed(2)}s.png`;
    await page.screenshot({path: path.join(outputDir, file)});
    const blade = state.objects['first.fingers["middle"].blade'];
    report.frames.push({file, sha256: sha256(await readFile(path.join(outputDir, file))), requested_seconds: seconds,
      displayed_time_seconds: state.time, displayed_time_label: await page.locator('#time').textContent(),
      selected_blade_world_position_m: blade?.position_m, objects_listed: Object.keys(state.objects).length});
  }
  await page.locator('#timeline').fill('0');
  await page.click('#play');
  await page.waitForFunction(() => window.ontokinViewer.state.playing && window.ontokinViewer.state.time > 0.6);
  await page.click('#play');
  await settle();
  const paused = await page.evaluate(() => window.ontokinViewer.state);
  await page.screenshot({path: path.join(outputDir, 'playback-paused.png')});
  report.playback = {started_at_seconds: 0, paused_at_seconds: paused.time, playing_after_pause: paused.playing,
    file: 'playback-paused.png', sha256: sha256(await readFile(path.join(outputDir, 'playback-paused.png')))};
  report.webgl = await page.evaluate(() => {
    const gl = document.querySelector('#viewport canvas').getContext('webgl2');
    if (!gl) return null; const debug = gl.getExtension('WEBGL_debug_renderer_info');
    return {version: gl.getParameter(gl.VERSION), renderer: debug ? gl.getParameter(debug.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER)};
  });
} finally {
  await browser.close();
}
await writeFile(path.join(outputDir, 'capture.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({frames: report.frames.length, playback: report.playback, page_errors: report.page_errors.length,
  console_errors: report.console_errors.length, network_requests: report.network_requests.length, browser: report.browser}));
