// Exercise the unchanged offline viewer with the GLB retrieved by the agent workflow.
import assert from 'node:assert/strict';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {chromium} from 'playwright';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const require = createRequire(import.meta.url);
const args = process.argv.slice(2);
let demoDir = path.join(root,'examples/agent');
let outputDir = path.join(root,'docs/engineering/agent-validation');
for (let index=0;index<args.length;index++) {
  const option = args[index];
  if (option==='--help') {
    console.log('Usage: node tools/verify_agent_viewer.mjs [--demo-dir DIR] [--output-dir DIR]');
    process.exit(0);
  }
  assert.ok(['--demo-dir','--output-dir'].includes(option),`Unknown option: ${option}`);
  assert.ok(args[index+1]&&!args[index+1].startsWith('--'),`${option} requires a directory`);
  const value = path.resolve(args[++index]);
  if (option==='--demo-dir') demoDir=value; else outputDir=value;
}

const sha256 = bytes => 'sha256:'+createHash('sha256').update(bytes).digest('hex');
const relative = filename => path.relative(root,filename).split(path.sep).join('/');
const files = {
  authoring_source:path.join(root,'examples/agent/authoring-demo.ok'),
  repaired_source:path.join(demoDir,'repaired.ok'),
  glb:path.join(demoDir,'repaired.glb'),
  export_report:path.join(demoDir,'repaired.export.json'),
  reference:path.join(demoDir,'repaired.reference.json'),
  workflow:path.join(demoDir,'workflow.json'),
  viewer_html:path.join(root,'examples/visual/viewer.html'),
  viewer_bundle:path.join(root,'examples/visual/viewer.bundle.js'),
  viewer_builtin_data:path.join(root,'examples/visual/demo-data.js'),
  verifier:fileURLToPath(import.meta.url),
  tooling_lock:path.join(root,'tools/package-lock.json'),
};
const input = Object.fromEntries(await Promise.all(Object.entries(files).map(async ([name,filename])=>[name,await readFile(filename)])));
const provenance = Object.fromEntries(Object.entries(files).map(([name,filename])=>[name,{
  path:relative(filename),byte_length:input[name].length,sha256:sha256(input[name]),
}]));
const exportReport = JSON.parse(input.export_report);
const reference = JSON.parse(input.reference);
const workflow = JSON.parse(input.workflow);
const glb = input.glb;
assert.ok(glb.length>=20,'The workflow artifact must contain a GLB header and JSON chunk');
assert.equal(glb.readUInt32LE(0),0x46546c67,'GLB magic');
assert.equal(glb.readUInt32LE(4),2,'glTF version');
assert.equal(glb.readUInt32LE(8),glb.length,'GLB declared byte length');
assert.equal(glb.readUInt32LE(16),0x4e4f534a,'GLB JSON chunk');
assert.ok(20+glb.readUInt32LE(12)<=glb.length,'GLB JSON must fit inside the artifact');
const document = JSON.parse(glb.subarray(20,20+glb.readUInt32LE(12)));
const sourceRevision = provenance.repaired_source.sha256;
const artifactHash = provenance.glb.sha256;
assert.equal(exportReport.schema_version,'ontokin.glb-report/0.1');
assert.equal(exportReport.target_contract,'ontokin.glb/0.1');
assert.equal(exportReport.validation.status,'passed');
assert.equal(exportReport.source.revision,sourceRevision,'Export report must describe the repaired source bytes');
assert.equal(exportReport.artifact.sha256,artifactHash,'Export report must describe the imported GLB bytes');
assert.equal(exportReport.artifact.byte_length,glb.length);
assert.equal(reference.schema_version,'ontokin.viewer-reference/0.1');
assert.equal(reference.source_revision,sourceRevision);
assert.equal(reference.artifact_sha256,artifactHash);
assert.equal(workflow.schema_version,'ontokin.agent-workflow/0.1');
assert.equal(workflow.status,'passed');
assert.equal(workflow.initial_revision,provenance.authoring_source.sha256);
assert.equal(workflow.accepted_revision,sourceRevision);
assert.equal(workflow.artifact_sha256,artifactHash);
assert.equal(document.extras.ontokin.source.revision,sourceRevision);
assert.notEqual(workflow.initial_revision,sourceRevision,'The demonstration must include an actual source edit');
assert.deepEqual(reference.tolerances,exportReport.tolerances);

const tolerances = {position_m:0.001,rotation_rad:0.001,time_seconds:0.000001};
for (const [name,maximum] of Object.entries(tolerances)) {
  const declared = reference.tolerances[name];
  assert.ok(Number.isFinite(declared)&&declared>0&&declared<=maximum,`Invalid or relaxed ${name} tolerance`);
  tolerances[name]=declared;
}
function compareVector(actual,expected,tolerance,label) {
  assert.equal(actual.length,expected.length,`${label}: component count`);
  assert.ok([...actual,...expected].every(Number.isFinite),`${label}: finite components`);
  const error = Math.max(...actual.map((value,index)=>Math.abs(value-expected[index])));
  assert.ok(error<=tolerance,`${label}: ${actual} differs from ${expected} by ${error} (limit ${tolerance})`);
  return error;
}
function rotationError(actual,expectedWxyz) {
  assert.equal(actual.length,4);
  assert.equal(expectedWxyz.length,4);
  assert.ok([...actual,...expectedWxyz].every(Number.isFinite));
  const expected = [expectedWxyz[1],expectedWxyz[2],expectedWxyz[3],expectedWxyz[0]];
  const norm = Math.hypot(...actual)*Math.hypot(...expected);
  assert.ok(norm>0,'Rotations must be nonzero quaternions');
  return 2*Math.acos(Math.min(1,Math.abs(actual.reduce((sum,value,index)=>sum+value*expected[index],0)/norm)));
}
const geometryMetadata = {};
for (const [name,expected] of Object.entries({'rig.head':[0.7,0.525,0.35],'reference.head':[0.4,0.3,0.2]})) {
  const matches = document.nodes.filter(node=>node.extras?.ontokin?.kind==='object'&&node.extras.ontokin.path===name);
  assert.equal(matches.length,1,`Unique source occurrence for ${name}`);
  const geometry = matches[0].extras.ontokin.geometry;
  assert.equal(geometry.kind,'box');
  compareVector(geometry.size,expected,1e-12,`${name} geometry metadata`);
  geometryMetadata[name]={kind:geometry.kind,full_size_m:geometry.size};
}
const installedPlaywright = JSON.parse(await readFile(require.resolve('playwright/package.json'))).version;
const tooling = JSON.parse(await readFile(path.join(root,'tools/package.json')));
assert.equal(installedPlaywright,tooling.devDependencies.playwright,'Use the pinned Playwright package');

await mkdir(outputDir,{recursive:true});
const checks = ['Exact source, workflow, inspection reference, GLB metadata and export-report identities agree.',
  'GLB metadata retains the repaired first head dimensions and the second head’s unchanged dimensions.'];
const report = {
  schema_version:'ontokin.visual-validation/0.1',status:'running',
  scenario:'agent-authoring-custom-import',generated_at_utc:new Date().toISOString(),
  source_revision:sourceRevision,artifact_sha256:artifactHash,provenance,
  agent_implementation:workflow.implementation,exporter:exportReport.exporter,
  exporter_source_code_sha256:exportReport.source_code_sha256,
  renderer:`Three.js ${tooling.devDependencies.three} / WebGL2`,playwright:installedPlaywright,
  environment:{platform:process.platform,architecture:process.arch,node:process.version,
    rendering:'Headless Chromium with ANGLE SwiftShader software rendering'},
  delivery:'Existing local file viewer, custom Open GLB input, exact agent-retrieved artifact bytes',
  tolerances,geometry_metadata:geometryMetadata,checks,samples:[],captures:[],
  page_errors:[],console_errors:[],network_requests:[],failed_requests:[],
  limits:[
    'Browser world-pose comparisons cover 1.5 and 2 seconds for this artifact; the export report and independent importer checks provide separate evidence.',
    'The custom-import UI receives only the GLB and correctly makes no source or numerical-conformance claim; this external harness verifies the sidecar provenance.',
    'Geometry dimensions above are retained source metadata; the screenshot is a rendering observation, not a complete mesh validator.',
    'No Blender import, model-authoring efficiency, or general rendering-quality certification is claimed.',
  ],
};
let browser;
try {
  browser = await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  report.browser=await browser.version();
  const page = await browser.newPage({viewport:{width:1440,height:1060},deviceScaleFactor:1,reducedMotion:'reduce'});
  page.on('pageerror',error=>report.page_errors.push(error.message));
  page.on('console',message=>{if (message.type()==='error') report.console_errors.push(message.text());});
  page.on('request',request=>{if (/^https?:/.test(request.url())) report.network_requests.push(request.url());});
  page.on('requestfailed',request=>report.failed_requests.push({url:request.url(),error:request.failure()?.errorText}));
  await page.route(/^https?:\/\//,route=>route.abort());
  await page.goto(pathToFileURL(files.viewer_html).href);
  await page.waitForFunction(()=>window.ontokinViewer?.ready);
  assert.equal(await page.evaluate(()=>window.ontokinViewer.state.playing),false);
  await page.locator('#local-file').setInputFiles(files.glb);
  await page.waitForFunction(()=>window.ontokinViewer.ready&&window.ontokinViewer.state.demo===null);
  assert.equal(await page.locator('#scene-title').textContent(),'repaired.glb');
  assert.equal(await page.locator('#error').isVisible(),false);
  await page.click('#fit');
  checks.push('The unchanged offline viewer loads the repaired artifact through its custom Open GLB input.');

  const fixedExpectations = {
    '1.5':{'rig.head':[1.5,1,0],'rig.arm.hand':[2.575,0.5,0],'reference.head':[0,1,1.5]},
    '2':{'rig.head':[2,1,0],'rig.arm.hand':[3.2,0.5,0],'reference.head':[0,1,1.5]},
  };
  for (const seconds of ['1.5','2']) {
    const expectedPositions = fixedExpectations[seconds];
    await page.locator('#timeline').fill(seconds);
    const state = await page.evaluate(()=>window.ontokinViewer.state);
    assert.ok(Math.abs(state.time-Number(seconds))<=tolerances.time_seconds);
    assert.equal(state.demo,null);
    assert.equal(state.playing,false);
    assert.equal(await page.locator('#time').textContent(),Number(seconds).toFixed(3));
    const matches = reference.samples.filter(sample=>Number(sample.time_seconds)===Number(seconds));
    assert.equal(matches.length,1,`One inspection reference sample at ${seconds} seconds`);
    assert.deepEqual(Object.keys(state.objects).sort(),Object.keys(matches[0].objects).sort());
    const observations = {};
    for (const [name,expected] of Object.entries(matches[0].objects)) {
      const actual = state.objects[name];
      const positionError = compareVector(actual.position_m,expected.position_m,tolerances.position_m,`${name} at ${seconds}s`);
      const orientationError = rotationError(actual.orientation_xyzw,expected.orientation_wxyz);
      assert.ok(orientationError<=tolerances.rotation_rad,`${name} orientation at ${seconds}s differs by ${orientationError}`);
      observations[name]={...actual,expected_position_m:expected.position_m,expected_orientation_wxyz:expected.orientation_wxyz,
        position_error_m:positionError,rotation_error_rad:orientationError};
    }
    for (const [name,expected] of Object.entries(expectedPositions)) {
      compareVector(state.objects[name].position_m,expected,tolerances.position_m,`${name} analytical expectation at ${seconds}s`);
    }
    report.samples.push({time_seconds:seconds,displayed_time_seconds:state.time,objects:observations});
  }
  checks.push('At 1.5 and 2 seconds, actual Three.js world positions and orientations match revision-bound inspection samples and fixed head/hand/reference position expectations.');

  await page.locator('#timeline').fill('1.5');
  await page.click('#play');
  await page.waitForFunction(()=>window.ontokinViewer.state.playing&&window.ontokinViewer.state.time>1.5);
  await page.click('#play');
  const paused = await page.evaluate(()=>window.ontokinViewer.state);
  assert.equal(paused.playing,false);
  assert.ok(paused.time>1.5&&paused.time<3,'Playback must advance before reaching the loop boundary');
  const later = await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(window.ontokinViewer.state)))));
  assert.equal(later.time,paused.time,'Paused time stays fixed across rendered frames');
  assert.deepEqual(later.objects,paused.objects,'Paused world poses stay fixed across rendered frames');
  report.playback={started_at_seconds:1.5,paused_at_seconds:paused.time,stable_across_rendered_frames:true};
  checks.push('Play advances the imported animation; Pause holds both time and world poses across rendered frames.');

  await page.locator('#timeline').fill('1.5');
  await page.selectOption('#object-select','reference');
  for (const [axis,expected] of Object.entries({x:'0.000',y:'0.000',z:'1.500'})) {
    assert.equal(await page.locator('#position-'+axis).textContent(),expected);
  }
  assert.match(await page.locator('#object-status').textContent(),/OntoKin object.*Rig/);
  checks.push('Selecting the unchanged reference assembly displays its decoded world position (0, 0, 1.5) metres.');

  const unclaimed = {
    'asset-badge':'Local GLB · numerical status unknown',
    'load-status':'Three.js loaded · no conformance report',
    'source-code':'The editable source is not embedded in this imported GLB.',
    'export-report':'No export report was supplied. Loading a file does not establish numerical conformance.',
    'position-tolerance':'Unknown','rotation-tolerance':'Unknown','time-tolerance':'Unknown',
    'evidence-note':'This file has not been compared with an OntoKin source program.',
    'event-label':'Local GLB playback',
  };
  const ui = {};
  for (const [id,expected] of Object.entries(unclaimed)) {
    ui[id]=await page.locator('#'+id).textContent();
    assert.equal(ui[id],expected,`${id} must not inherit the built-in demo evidence`);
  }
  assert.equal(await page.locator('#download-source').isDisabled(),true);
  assert.deepEqual(await page.locator('.demo-tab').evaluateAll(buttons=>buttons.map(button=>button.getAttribute('aria-pressed'))),['false','false']);
  report.local_import_ui={...ui,source_download_disabled:true,builtin_demo_selected:false};
  checks.push('Custom import keeps source download disabled, every tolerance unknown, both built-in demos unselected, and the source/conformance text unclaimed.');

  report.webgl=await page.evaluate(()=>{
    const gl=document.querySelector('#viewport canvas').getContext('webgl2');
    if (!gl) return null;
    const debug=gl.getExtension('WEBGL_debug_renderer_info');
    return {version:gl.getParameter(gl.VERSION),vendor:gl.getParameter(gl.VENDOR),renderer:gl.getParameter(gl.RENDERER),
      unmasked_renderer:debug?gl.getParameter(debug.UNMASKED_RENDERER_WEBGL):null};
  });
  assert.ok(report.webgl,'The displayed scene must use a real WebGL2 context');
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  const capture = path.join(outputDir,'agent-authoring.png');
  await page.screenshot({path:capture,fullPage:true});
  report.captures.push({file:'agent-authoring.png',sha256:sha256(await readFile(capture)),time_seconds:1.5,
    selected_object:'reference',viewport:{width:1440,height:1060},source_revision:sourceRevision,artifact_sha256:artifactHash});
  assert.deepEqual(report.page_errors,[],'Page JavaScript errors');
  assert.deepEqual(report.console_errors,[],'Browser console errors');
  assert.deepEqual(report.network_requests,[],'HTTP(S) requests during offline playback');
  assert.deepEqual(report.failed_requests,[],'Failed local or remote requests');
  checks.push('A WebGL2 frame is captured with no page errors, console errors, HTTP(S) requests, or failed resource requests.');
  report.status='passed';
} catch (error) {
  report.status='failed';
  report.failure={name:error.name,message:error.message};
  throw error;
} finally {
  if (browser) await browser.close();
  await writeFile(path.join(outputDir,'viewer-results.json'),JSON.stringify(report,null,2)+'\n');
}
console.log(JSON.stringify({status:report.status,checks:checks.length,samples:report.samples.length,
  screenshots:report.captures.length,browser:report.browser,source_revision:sourceRevision,
  artifact_sha256:artifactHash,output_dir:outputDir},null,2));
