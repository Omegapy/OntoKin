// Exercise the real bundle-produced GLB in the existing offline viewer.
import assert from 'node:assert/strict';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {chromium} from 'playwright';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const require=createRequire(import.meta.url);
const args=process.argv.slice(2);
let demoDir=path.join(root,'examples/construction');
let outputDir=path.join(root,'docs/engineering/construction-validation');
for (let index=0;index<args.length;index++) {
  const option=args[index];
  if (option==='--help') {
    console.log('Usage: node tools/verify_construction_viewer.mjs [--demo-dir DIR] [--output-dir DIR]');
    process.exit(0);
  }
  assert.ok(['--demo-dir','--output-dir'].includes(option),`Unknown option: ${option}`);
  assert.ok(args[index+1]&&!args[index+1].startsWith('--'),`${option} requires a directory`);
  const value=path.resolve(args[++index]);
  if (option==='--demo-dir') demoDir=value; else outputDir=value;
}
const sha256=bytes=>'sha256:'+createHash('sha256').update(bytes).digest('hex');
const relative=filename=>path.relative(root,filename).split(path.sep).join('/');
const files={
  source_bundle:path.join(demoDir,'program.bundle.json'),
  entry_source:path.join(demoDir,'main.ok'),
  library_source:path.join(demoDir,'hinges.ok'),
  glb:path.join(demoDir,'keyed-rack.glb'),
  export_report:path.join(demoDir,'keyed-rack.export.json'),
  reference:path.join(demoDir,'keyed-rack.reference.json'),
  workflow:path.join(demoDir,'workflow.json'),
  oracle:path.join(root,'docs/language-design/construction-v0.1/01-keyed-rack/expected.json'),
  viewer_html:path.join(root,'examples/visual/viewer.html'),
  viewer_bundle:path.join(root,'examples/visual/viewer.bundle.js'),
  viewer_builtin_data:path.join(root,'examples/visual/demo-data.js'),
  verifier:fileURLToPath(import.meta.url),
  tooling_lock:path.join(root,'tools/package-lock.json'),
};
const input=Object.fromEntries(await Promise.all(Object.entries(files).map(async ([name,filename])=>[name,await readFile(filename)])));
const provenance=Object.fromEntries(Object.entries(files).map(([name,filename])=>[name,{
  path:relative(filename),byte_length:input[name].length,sha256:sha256(input[name]),
}]));
const exportReport=JSON.parse(input.export_report);
const reference=JSON.parse(input.reference);
const workflow=JSON.parse(input.workflow);
const oracle=JSON.parse(input.oracle);
const bundle=JSON.parse(input.source_bundle);
const glb=input.glb;
assert.ok(glb.length>=20);
assert.equal(glb.readUInt32LE(0),0x46546c67);
assert.equal(glb.readUInt32LE(4),2);
assert.equal(glb.readUInt32LE(8),glb.length);
assert.equal(glb.readUInt32LE(16),0x4e4f534a);
assert.ok(20+glb.readUInt32LE(12)<=glb.length);
const document=JSON.parse(glb.subarray(20,20+glb.readUInt32LE(12)));
const metadata=document.extras.ontokin;
const artifactHash=provenance.glb.sha256;
const programRevision=oracle.program_revision;
assert.equal(exportReport.schema_version,'ontokin.glb-report/0.2');
assert.equal(exportReport.target_contract,'ontokin.glb/0.2');
assert.equal(exportReport.validation.status,'passed');
assert.equal(exportReport.program_revision,programRevision);
assert.equal(exportReport.artifact.sha256,artifactHash);
assert.equal(exportReport.artifact.byte_length,glb.length);
assert.equal(reference.schema_version,'ontokin.viewer-reference/0.2');
assert.equal(reference.program_revision,programRevision);
assert.equal(reference.artifact_sha256,artifactHash);
assert.equal(workflow.schema_version,'ontokin.program-agent-workflow/0.1');
assert.equal(workflow.status,'passed');
assert.equal(workflow.accepted_program_revision,programRevision);
assert.notEqual(workflow.initial_program_revision,programRevision);
assert.notEqual(workflow.rejected_program_revision,programRevision);
assert.equal(workflow.artifact_sha256,artifactHash);
assert.equal(metadata.target_contract,'ontokin.glb/0.2');
assert.equal(metadata.profile,'construction-0.1');
assert.equal(metadata.program.revision,programRevision);
assert.deepEqual(metadata.program.manifest,reference.source_manifest);
assert.deepEqual(exportReport.program.manifest,reference.source_manifest);
assert.deepEqual(workflow.source_manifest,reference.source_manifest);
assert.deepEqual(reference.tolerances,exportReport.tolerances);
assert.equal(bundle.schema_version,'ontokin.bundle/0.1');
assert.equal(bundle.entry.source,input.entry_source.toString('utf8'));
assert.equal(bundle.modules.length,1);
assert.equal(bundle.modules[0].source,input.library_source.toString('utf8'));
for (const unit of reference.source_manifest.units) {
  assert.equal(unit.source_revision,unit.source_id==='entry'?provenance.entry_source.sha256:provenance.library_source.sha256);
}
assert.equal(reference.independent_oracle.sha256,provenance.oracle.sha256);

const tolerances={position_m:0.001,rotation_rad:0.001,time_seconds:0.000001};
for (const [name,maximum] of Object.entries(tolerances)) {
  const declared=reference.tolerances[name];
  assert.ok(Number.isFinite(declared)&&declared>0&&declared<=maximum,`Invalid or relaxed ${name} tolerance`);
  tolerances[name]=declared;
}
function compareVector(actual,expected,tolerance,label) {
  assert.equal(actual.length,expected.length,`${label}: component count`);
  assert.ok([...actual,...expected].every(Number.isFinite),`${label}: finite components`);
  const error=Math.max(...actual.map((value,index)=>Math.abs(value-expected[index])));
  assert.ok(error<=tolerance,`${label}: ${actual} differs from ${expected} by ${error} (limit ${tolerance})`);
  return error;
}
function rotationError(actual,expectedWxyz) {
  assert.equal(actual.length,4); assert.equal(expectedWxyz.length,4);
  assert.ok([...actual,...expectedWxyz].every(Number.isFinite));
  const expected=[expectedWxyz[1],expectedWxyz[2],expectedWxyz[3],expectedWxyz[0]];
  const an=Math.hypot(...actual), en=Math.hypot(...expected);
  assert.ok(an>0&&en>0);
  const a=actual.map(x=>x/an), e=expected.map(x=>x/en);
  const minus=Math.hypot(...a.map((x,i)=>x-e[i]));
  const plus=Math.hypot(...a.map((x,i)=>x+e[i]));
  return 4*Math.atan2(Math.min(minus,plus),Math.max(minus,plus));
}
const metadataObjects=document.nodes.filter(node=>node.extras?.ontokin?.kind==='object');
assert.equal(metadataObjects.length,18);
assert.equal(oracle.objects.length,18);
for (const expected of oracle.objects) {
  const matches=metadataObjects.filter(node=>node.extras.ontokin.path===expected.path);
  assert.equal(matches.length,1,expected.path);
  assert.deepEqual(matches[0].extras.ontokin.element_id,expected.element_id);
}
const tooling=JSON.parse(await readFile(path.join(root,'tools/package.json')));
const playwrightVersion=JSON.parse(await readFile(require.resolve('playwright/package.json'))).version;
assert.equal(playwrightVersion,tooling.devDependencies.playwright);
await mkdir(outputDir,{recursive:true});
const checks=[
  'Exact entry/library bytes, program manifest, independent oracle, workflow, inspection reference, export report and GLB identities agree.',
  'All 18 imported GLB object identities match the predetermined keyed Rack oracle; collections add no objects.',
];
const report={
  schema_version:'ontokin.visual-validation/0.2',status:'running',scenario:'construction-program-custom-import',
  generated_at_utc:new Date().toISOString(),program_revision:programRevision,source_manifest:reference.source_manifest,
  artifact_sha256:artifactHash,provenance,agent_implementation:workflow.implementation,
  exporter:exportReport.exporter,exporter_source_code_sha256:exportReport.source_code_sha256,
  renderer:`Three.js ${tooling.devDependencies.three} / WebGL2`,playwright:playwrightVersion,
  environment:{platform:process.platform,architecture:process.arch,node:process.version,
    rendering:'Headless Chromium with ANGLE SwiftShader software rendering'},
  delivery:'Existing offline viewer custom Open GLB input, exact program-agent artifact bytes',
  tolerances,checks,samples:[],captures:[],page_errors:[],console_errors:[],network_requests:[],failed_requests:[],
  limits:[
    'Seven sampled times cover 126 browser world poses. They do not certify every possible program or continuous-time error.',
    'The custom-import UI receives only the GLB. This external harness separately verifies its source and numerical sidecars.',
    'Decoded mesh bounds are independently checked by verify_gltf.mjs; a screenshot alone does not establish geometry accuracy.',
    'No Blender import, live physics, agent productivity improvement, or general rendering-quality certification is claimed.',
  ],
};
let browser;
try {
  browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  report.browser=await browser.version();
  const page=await browser.newPage({viewport:{width:1440,height:1060},deviceScaleFactor:1,reducedMotion:'reduce'});
  page.on('pageerror',error=>report.page_errors.push(error.message));
  page.on('console',message=>{if(message.type()==='error')report.console_errors.push(message.text());});
  page.on('request',request=>{if(/^https?:/.test(request.url()))report.network_requests.push(request.url());});
  page.on('requestfailed',request=>report.failed_requests.push({url:request.url(),error:request.failure()?.errorText}));
  await page.route(/^https?:\/\//,route=>route.abort());
  await page.goto(pathToFileURL(files.viewer_html).href);
  await page.waitForFunction(()=>window.ontokinViewer?.ready);
  await page.locator('#local-file').setInputFiles(files.glb);
  await page.waitForFunction(()=>window.ontokinViewer.ready&&window.ontokinViewer.state.demo===null);
  assert.equal(await page.locator('#scene-title').textContent(),'keyed-rack.glb');
  assert.equal(await page.locator('#error').isVisible(),false);
  await page.click('#fit');
  checks.push('The existing offline viewer loads the agent-retrieved construction GLB through its custom input.');
  assert.equal(reference.samples.length,7);
  for (const sample of reference.samples) {
    const seconds=Number(sample.time_seconds);
    const oracleSamples=oracle.samples.filter(item=>Number(item.seconds)===seconds);
    assert.equal(oracleSamples.length,1);
    const expectedObjects=Object.fromEntries(oracleSamples[0].objects.map(item=>[item.path,item]));
    await page.locator('#timeline').fill(String(seconds));
    const state=await page.evaluate(()=>window.ontokinViewer.state);
    assert.ok(Math.abs(state.time-seconds)<=tolerances.time_seconds);
    assert.equal(state.demo,null); assert.equal(state.playing,false);
    assert.equal(await page.locator('#time').textContent(),seconds.toFixed(3));
    assert.deepEqual(Object.keys(state.objects).sort(),Object.keys(sample.objects).sort());
    assert.deepEqual(Object.keys(state.objects).sort(),Object.keys(expectedObjects).sort());
    const observations={};
    for (const [name,expected] of Object.entries(sample.objects)) {
      const actual=state.objects[name], independent=expectedObjects[name];
      const positionError=compareVector(actual.position_m,expected.position_m,tolerances.position_m,`${name} at ${seconds}s`);
      const oraclePositionError=compareVector(actual.position_m,independent.position_m,tolerances.position_m,`${name} oracle at ${seconds}s`);
      const orientationError=rotationError(actual.orientation_xyzw,expected.orientation_wxyz);
      const oracleOrientationError=rotationError(actual.orientation_xyzw,independent.rotation_wxyz);
      assert.ok(orientationError<=tolerances.rotation_rad,`${name} inspection rotation at ${seconds}s`);
      assert.ok(oracleOrientationError<=tolerances.rotation_rad,`${name} oracle rotation at ${seconds}s`);
      observations[name]={...actual,expected_position_m:expected.position_m,expected_orientation_wxyz:expected.orientation_wxyz,
        position_error_m:positionError,rotation_error_rad:orientationError,
        oracle_position_error_m:oraclePositionError,oracle_rotation_error_rad:oracleOrientationError};
    }
    report.samples.push({time_seconds:seconds,displayed_time_seconds:state.time,objects:observations});
  }
  report.pose_comparisons=report.samples.reduce((sum,sample)=>sum+Object.keys(sample.objects).length,0);
  assert.equal(report.pose_comparisons,126);
  checks.push('All 126 decoded browser world poses match both program-bound inspection and the predetermined independent position/rotation formulas.');
  await page.locator('#timeline').fill('0.5');
  await page.click('#play');
  await page.waitForFunction(()=>window.ontokinViewer.state.playing&&window.ontokinViewer.state.time>0.5);
  await page.click('#play');
  const paused=await page.evaluate(()=>window.ontokinViewer.state);
  assert.equal(paused.playing,false); assert.ok(paused.time>0.5&&paused.time<2);
  const later=await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(window.ontokinViewer.state)))));
  assert.equal(later.time,paused.time); assert.deepEqual(later.objects,paused.objects);
  report.playback={started_at_seconds:0.5,paused_at_seconds:paused.time,stable_across_rendered_frames:true};
  checks.push('Play advances the imported clip and Pause holds time and all world poses across rendered frames.');
  await page.locator('#timeline').fill('1.5');
  await page.selectOption('#object-select','second');
  for (const [axis,value] of Object.entries({x:'1.000',y:'0.000',z:'0.000'})) assert.equal(await page.locator('#position-'+axis).textContent(),value);
  assert.match(await page.locator('#object-status').textContent(),/OntoKin object/);
  checks.push('Selecting the unchanged five-finger assembly shows its decoded world position (1, 0, 0) metres.');
  const unclaimed={
    'asset-badge':'Local GLB · numerical status unknown','load-status':'Three.js loaded · no conformance report',
    'source-code':'The editable source is not embedded in this imported GLB.',
    'export-report':'No export report was supplied. Loading a file does not establish numerical conformance.',
    'position-tolerance':'Unknown','rotation-tolerance':'Unknown','time-tolerance':'Unknown',
    'evidence-note':'This file has not been compared with an OntoKin source program.','event-label':'Local GLB playback',
  };
  report.local_import_ui={};
  for (const [id,expected] of Object.entries(unclaimed)) {
    report.local_import_ui[id]=await page.locator('#'+id).textContent();
    assert.equal(report.local_import_ui[id],expected,id);
  }
  assert.equal(await page.locator('#download-source').isDisabled(),true);
  assert.deepEqual(await page.locator('.demo-tab').evaluateAll(buttons=>buttons.map(button=>button.getAttribute('aria-pressed'))),['false','false']);
  checks.push('Custom import preserves the honest unknown source/conformance UI and never inherits built-in demonstration evidence.');
  report.webgl=await page.evaluate(()=>{
    const gl=document.querySelector('#viewport canvas').getContext('webgl2');
    if(!gl)return null; const debug=gl.getExtension('WEBGL_debug_renderer_info');
    return {version:gl.getParameter(gl.VERSION),vendor:gl.getParameter(gl.VENDOR),renderer:gl.getParameter(gl.RENDERER),
      unmasked_renderer:debug?gl.getParameter(debug.UNMASKED_RENDERER_WEBGL):null};
  });
  assert.ok(report.webgl);
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  const capture=path.join(outputDir,'keyed-rack.png');
  await page.screenshot({path:capture,fullPage:true});
  report.captures.push({file:'keyed-rack.png',sha256:sha256(await readFile(capture)),time_seconds:1.5,
    selected_object:'second',viewport:{width:1440,height:1060},program_revision:programRevision,artifact_sha256:artifactHash});
  for(const key of ['page_errors','console_errors','network_requests','failed_requests'])assert.deepEqual(report[key],[],key);
  checks.push('A real WebGL2 frame is captured with no page errors, console errors, HTTP(S) requests or failed resource requests.');
  report.status='passed';
} catch(error) {
  report.status='failed'; report.failure={name:error.name,message:error.message}; throw error;
} finally {
  if(browser)await browser.close();
  await writeFile(path.join(outputDir,'viewer-results.json'),JSON.stringify(report,null,2)+'\n');
}
console.log(JSON.stringify({status:report.status,checks:checks.length,samples:report.samples.length,
  pose_comparisons:report.pose_comparisons,screenshots:report.captures.length,browser:report.browser,
  program_revision:programRevision,artifact_sha256:artifactHash,output_dir:outputDir},null,2));
