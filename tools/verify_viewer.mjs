// Render the actual GLBs, exercise the offline viewer, and save inspectable evidence.
import assert from 'node:assert/strict';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {chromium} from 'playwright';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const outIndex = process.argv.indexOf('--output-dir');
const output = outIndex < 0 ? path.join(root,'docs/engineering/visual-validation') : path.resolve(process.argv[outIndex+1]);
await mkdir(output,{recursive:true});
const browser = await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page = await browser.newPage({viewport:{width:1440,height:1060},deviceScaleFactor:1,reducedMotion:'reduce'});
const errors = [], networkRequests = [], captures = [], checks = [];
page.on('pageerror',error => errors.push(error.message));
page.on('request',request => {if (/^https?:/.test(request.url())) networkRequests.push(request.url());});
const compare = (actual,expected) => expected.forEach((value,index) => assert.ok(Math.abs(actual[index]-value)<0.001,`${actual} differs from ${expected}`));
try {
  await page.goto(pathToFileURL(path.join(root,'examples/visual/viewer.html')).href);
  await page.waitForFunction(()=>window.ontokinViewer?.ready);
  assert.equal(await page.evaluate(()=>window.ontokinViewer.state.playing),false);
  await page.click('#fit');
  await page.locator('#timeline').fill('1.5');
  let state = await page.evaluate(()=>window.ontokinViewer.state);
  compare(state.objects['rig.head'].position_m,[1.5,1,0]);
  compare(state.objects['rig.arm.hand'].position_m,[2.575,0.5,0]);
  assert.equal(await page.locator('#time').textContent(),'1.500');
  checks.push('Timeline scrub updates displayed time and actual head/hand world poses.');
  await page.click('#play');
  await page.waitForFunction(()=>window.ontokinViewer.state.time>1.5);
  await page.click('#play');
  assert.equal(await page.evaluate(()=>window.ontokinViewer.state.playing),false);
  checks.push('Play advances time; Pause stops playback.');
  await page.locator('#timeline').fill('1.5');
  await page.screenshot({path:path.join(output,'independent-parts.png'),fullPage:true});
  captures.push({file:'independent-parts.png',demo:'independent-parts',time_seconds:1.5});
  await page.click('#demo-1');
  await page.waitForFunction(()=>window.ontokinViewer.ready&&window.ontokinViewer.state.demo==='gravity-and-release');
  await page.locator('#timeline').fill('1.5');
  state = await page.evaluate(()=>window.ontokinViewer.state);
  compare(state.objects.payload.position_m,[1.92,0.77375,0]);
  compare(state.objects.carrier.position_m,[1.25,2,0]);
  checks.push('Release playback matches the free sphere and stopped carrier at 1.5 seconds.');
  await page.screenshot({path:path.join(output,'gravity-and-release.png'),fullPage:true});
  captures.push({file:'gravity-and-release.png',demo:'gravity-and-release',time_seconds:1.5});
  await page.locator('#timeline').fill('2');
  state = await page.evaluate(()=>window.ontokinViewer.state);
  compare(state.objects.payload.position_m,[2.42,-2.905,0]);
  compare(state.objects.carrier.position_m,[1.25,2,0]);
  checks.push('Endpoint keeps the carrier stopped and the sphere below the reference grid.');
  await page.selectOption('#object-select','carrier');
  assert.equal(await page.locator('#position-x').textContent(),'1.250');
  assert.equal(await page.locator('#position-y').textContent(),'2.000');
  checks.push('Object selection displays the selected object’s decoded world coordinates.');
  await page.uncheck('#show-helpers'); await page.uncheck('#show-trails'); await page.uncheck('#show-grid');
  assert.equal(await page.locator('#show-helpers').isChecked(),false);
  await page.check('#show-helpers'); await page.check('#show-trails'); await page.check('#show-grid');
  checks.push('Helper, path, and grid controls can be toggled.');
  const [download] = await Promise.all([page.waitForEvent('download'),page.click('#download-glb')]);
  const exported = await readFile(await download.path());
  const original = await readFile(path.join(root,'examples/visual/02-gravity-and-release.glb'));
  assert.equal(createHash('sha256').update(exported).digest('hex'),createHash('sha256').update(original).digest('hex'));
  checks.push('Save GLB downloads the exact checked-in exported artifact.');
  await page.setViewportSize({width:720,height:1000});
  await page.locator('#timeline').fill('1.5'); await page.click('#fit');
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:path.join(output,'viewer-narrow.png'),fullPage:true});
  captures.push({file:'viewer-narrow.png',demo:'gravity-and-release',time_seconds:1.5,viewport_width:720});
  checks.push('Narrow 720-pixel layout has no horizontal overflow.');
  await page.locator('#local-file').setInputFiles(path.join(root,'examples/visual/01-independent-parts.glb'));
  await page.waitForFunction(()=>window.ontokinViewer.ready&&window.ontokinViewer.state.demo===null);
  assert.match(await page.locator('#asset-badge').textContent(),/unknown/);
  assert.equal(await page.locator('#download-source').isDisabled(),true);
  checks.push('A local import plays without inheriting the built-in demo’s conformance claim or source.');
  assert.deepEqual(errors,[]); assert.deepEqual(networkRequests,[]);
  checks.push('No page JavaScript errors or network requests during file-based playback.');
  const report={schema_version:'ontokin.visual-validation/0.1',status:'passed',
    renderer:'Three.js 0.180.0 / WebGL2',browser:await browser.version(),playwright:'1.56.1',
    environment:`Headless Chromium on ${process.platform} (${process.arch}) with SwiftShader software rendering`,
    delivery:'Local file viewer with bundled Three.js and embedded exported GLB bytes',
    checks,captures,page_errors:errors,network_requests:networkRequests,
    limits:['Blender import was not run.','Screenshots and functional checks are bounded evidence for these demonstrations.']};
  await writeFile(path.join(output,'viewer-results.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({status:'passed',checks:checks.length,screenshots:captures.length,browser:report.browser,output},null,2));
} finally { await browser.close(); }
