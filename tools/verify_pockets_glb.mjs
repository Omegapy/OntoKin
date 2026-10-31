#!/usr/bin/env node
// Independent Khronos/Three.js decoding and actual browser playback for C079.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import validator from 'gltf-validator';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {AnimationMixer,LoopOnce,Vector3,Quaternion,Matrix4,REVISION} from 'three';
import {build} from 'esbuild';
import {chromium} from 'playwright';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const sha=data=>createHash('sha256').update(data).digest('hex');
function near(a,b,t=1e-5){assert.equal(a.length,b.length);for(let i=0;i<a.length;i++)assert.ok(Number.isFinite(a[i])&&Math.abs(a[i]-b[i])<=t,`${a} vs ${b}`);}
function rotationNear(actual, expected) {
  assert.equal(actual.length, 4); assert.equal(expected.length, 4);
  assert.ok([...actual, ...expected].every(Number.isFinite));
  near([Math.hypot(...actual), Math.hypot(...expected)], [1, 1], 1e-5);
  const a = new Quaternion(...actual).normalize(), b = new Quaternion(...expected).normalize();
  assert.ok(a.angleTo(b) <= .001, 'Recorded orientation exceeds the unchanged .001-radian tolerance');
}
function compare(objects,expected,t){
  assert.deepEqual(Object.keys(objects).sort(),Object.keys(expected.nodes).sort());
  return Object.entries(expected.nodes).map(([name,n])=>{const p=n.origin.map((x,i)=>x+t*n.velocity[i]);near(objects[name].position,p,.001);rotationNear(objects[name].rotation,n.rotation_xyzw??[0,0,0,1]);near(objects[name].scale,[1,1,1],1e-6);return {path:name,time_seconds:t,position:objects[name].position,rotation:objects[name].rotation,scale:objects[name].scale};});
}
const browserSource=`
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const bytes=Uint8Array.from(atob(globalThis.BYTES),c=>c.charCodeAt(0));
const gltf=await new GLTFLoader().parseAsync(bytes.buffer,'');
const scene=new THREE.Scene();scene.background=new THREE.Color(0xe7edf2);scene.add(gltf.scene);scene.add(new THREE.AmbientLight(0xffffff,1.5));
for(const [x,y,z,power] of [[6,8,10,2.5],[-4,3,-8,1.8]]){const l=new THREE.DirectionalLight(0xffffff,power);l.position.set(x,y,z);scene.add(l);}
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(1);renderer.setSize(1100,720);renderer.outputColorSpace=THREE.SRGBColorSpace;document.querySelector('#view').append(renderer.domElement);
const camera=new THREE.PerspectiveCamera(35,1100/720,.001,10000),mixer=new THREE.AnimationMixer(gltf.scene),action=mixer.clipAction(gltf.animations[0]);
function seek(t){action.reset().setLoop(THREE.LoopOnce,1).play();action.clampWhenFinished=true;mixer.setTime(t);gltf.scene.updateMatrixWorld(true);}
const bounds=new THREE.Box3();for(const t of [0,.5,1]){seek(t);bounds.union(new THREE.Box3().setFromObject(gltf.scene));}
const center=bounds.getCenter(new THREE.Vector3()),radius=Math.max(.1,bounds.getSize(new THREE.Vector3()).length()/2),distance=radius/Math.sin(35*Math.PI/360)*1.25;
function observe(t,view='front'){
 seek(t);const direction=view==='oblique'?new THREE.Vector3(.7,-.6,1):view==='underside'?new THREE.Vector3(0,0,-1):new THREE.Vector3(0,0,1);direction.normalize();camera.position.copy(center).addScaledVector(direction,distance);camera.near=Math.max(.001,distance-radius*1.6);camera.far=distance+radius*3+1;camera.lookAt(center);camera.updateProjectionMatrix();camera.updateMatrixWorld(true);renderer.render(scene,camera);
 document.querySelector('#clock').textContent=t+' s | '+view;const objects={};let maxNdc=0,triangles=0;
 gltf.scene.traverse(n=>{if(n.userData.ontokin?.kind==='object')objects[n.userData.ontokin.path]={position:n.getWorldPosition(new THREE.Vector3()).toArray(),rotation:n.getWorldQuaternion(new THREE.Quaternion()).toArray(),scale:n.getWorldScale(new THREE.Vector3()).toArray()};if(n.isMesh){triangles+=(n.geometry.index?.count??n.geometry.attributes.position.count)/3;n.geometry.computeBoundingBox();const b=n.geometry.boundingBox;for(const x of [b.min.x,b.max.x])for(const y of [b.min.y,b.max.y])for(const z of [b.min.z,b.max.z]){const p=new THREE.Vector3(x,y,z).applyMatrix4(n.matrixWorld).project(camera);maxNdc=Math.max(maxNdc,Math.abs(p.x),Math.abs(p.y));}}});return {objects,maxNdc,triangles,renderCalls:renderer.info.render.calls};
}
globalThis.pocketsObserver={observe};observe(0);globalThis.READY=true;
`;
async function browserCheck(bytes,expected,output){
 const bundled=await build({stdin:{contents:browserSource,resolveDir:path.join(ROOT,'tools'),sourcefile:'pockets-observer.mjs'},bundle:true,write:false,format:'esm',platform:'browser',target:'es2022'});
 const script=bundled.outputFiles[0].contents;
 const html='<!doctype html><meta charset="utf-8"><title>OntoKin blind polygon pockets</title><style>body{margin:0;background:#e7edf2;color:#20313f;font:18px system-ui}header{padding:16px 24px;display:flex;justify-content:space-between}canvas{display:block}</style><header><strong>OntoKin | '+expected.case_id+'</strong><span id="clock"></span></header><div id="view"></div><script>globalThis.BYTES='+JSON.stringify(bytes.toString('base64'))+'</script><script type="module" src="/observer.js"></script>';
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const report={version:browser.version(),observations:[],captures:[],page_errors:[],failed_requests:[],visual_review:'pending_actual_image_inspection',observer_sha256:sha(script)};
 try{
  const page=await browser.newPage({viewport:{width:1100,height:780},deviceScaleFactor:1});page.on('pageerror',e=>report.page_errors.push(String(e)));page.on('requestfailed',r=>report.failed_requests.push(r.url()));
  await page.route('**/*',route=>{const u=route.request().url();if(u==='https://ontokin-pockets.invalid/')return route.fulfill({contentType:'text/html',body:html});if(u==='https://ontokin-pockets.invalid/observer.js')return route.fulfill({contentType:'text/javascript',body:Buffer.from(script)});return route.abort();});
  await page.goto('https://ontokin-pockets.invalid/');await page.waitForFunction(()=>globalThis.READY===true);
  const triangles=Object.values(expected.nodes).reduce((n,x)=>n+(x.geometry?.triangle_count??0),0);
  for(const t of [0,.25,.5,.75,1]){const obs=await page.evaluate(t=>globalThis.pocketsObserver.observe(t),t);assert.ok(obs.maxNdc<=1&&obs.renderCalls>0);assert.equal(obs.triangles,triangles);report.observations.push(...compare(obs.objects,expected,t));}
  for(const view of (expected.case_id==='rectangular-pocket'?['front','oblique','underside']:['front','oblique'])){const t=expected.case_id==='agent-repaired'?1:.5;const obs=await page.evaluate(({t,view})=>globalThis.pocketsObserver.observe(t,view),{t,view});assert.ok(obs.maxNdc<=1);const filename=view+'.png';await page.screenshot({path:path.join(output,filename)});report.captures.push({path:filename,time_seconds:t,view,max_abs_ndc_xy:obs.maxNdc,sha256:sha(await readFile(path.join(output,filename)))});}
  assert.deepEqual(report.page_errors,[]);assert.deepEqual(report.failed_requests,[]);report.status='passed';
 }finally{await browser.close();}
 return report;
}

function argumentsForRun(args) {
  if (args.length === 2 && !args[0].startsWith('--')) return args;
  const options = {};
  for (let i = 0; i < args.length; i += 2) {
    assert.ok(['--demo-dir', '--output-dir'].includes(args[i]) && args[i + 1]);
    assert.ok(options[args[i]] === undefined, 'An option cannot repeat');
    options[args[i]] = args[i + 1];
  }
  return [options['--demo-dir'], options['--output-dir']];
}

function frozenCorners(geometry) {
  assert.equal(geometry.source_positions.length, geometry.logical_vertex_count);
  const ids = geometry.source_positions.map(item => JSON.stringify(item.identity));
  assert.equal(new Set(ids).size, ids.length);
  // The source identities and independently placed positions were frozen before
  // implementation. Production geometry never supplies these expected values.
  return geometry.source_positions.map(item => {
    assert.equal(item.placed_position_m.length, 3);
    assert.ok(item.placed_position_m.every(Number.isFinite));
    return new Vector3(...item.placed_position_m);
  });
}

async function main() {
  const [inputDir, outputDir] = argumentsForRun(process.argv.slice(2));
  assert.ok(inputDir && outputDir, 'Use --demo-dir INPUT --output-dir OUTPUT');
  const input = path.resolve(inputDir), output = path.resolve(outputDir);
  assert.ok(output !== ROOT && !output.startsWith(ROOT + path.sep));
  await mkdir(output, {recursive: false});
  const report = {
    schema_version: 'ontokin.pockets-destination-check/0.1', status: 'running',
    started_utc: new Date().toISOString(),
    source_git: {
      commit: execFileSync('git', ['-C', ROOT, 'rev-parse', 'HEAD'], {encoding: 'utf8'}).trim(),
      tree: execFileSync('git', ['-C', ROOT, 'rev-parse', 'HEAD^{tree}'], {encoding: 'utf8'}).trim(),
      tracked_status: execFileSync('git', ['-C', ROOT, 'status', '--porcelain', '--untracked-files=no'], {encoding: 'utf8'}).trim(),
    },
    node: process.version, three_revision: REVISION,
    checker_sha256: sha(await readFile(fileURLToPath(import.meta.url))),
    artifacts: [], release_acceptance: false,
  };
  try {
    assert.equal(process.versions.node, '22.14.0');
    const pins = {three: '0.180.0', 'gltf-validator': '2.0.0-dev.3.10', playwright: '1.56.1', esbuild: '0.25.10'};
    for (const [name, version] of Object.entries(pins)) {
      assert.equal(JSON.parse(await readFile(path.join(ROOT, 'tools/node_modules', name, 'package.json'))).version, version);
    }
    report.dependencies = pins;
    const acceptance = JSON.parse(await readFile(path.join(input, 'summary.json')));
    assert.equal(acceptance.status, 'passed');
    const captureCases = new Set(['rectangular-pocket', 'concave-outer', 'concave-pocket',
      'unequal-depths', 'heldout-stepped-tray', 'maximum-pockets-and-vertices',
      'placed-rotated-pocket', 'generated', 'agent-repaired']);
    for (const item of acceptance.artifacts) {
      const data = await readFile(path.join(input, item.path));
      const expectedBytes = await readFile(path.join(input, item.name + '.expected.json'));
      const expected = JSON.parse(expectedBytes);
      assert.equal(sha(data), item.sha256);
      assert.equal(expected.program_revision, item.program_revision);
      const check = {name: item.name, sha256: sha(data), bytes: data.length,
        expected_sha256: sha(expectedBytes)};
      report.artifacts.push(check);
      const format = await validator.validateBytes(new Uint8Array(data), {uri: item.path, maxIssues: 200});
      check.khronos = {errors: format.issues.numErrors, warnings: format.issues.numWarnings, messages: format.issues.messages};
      assert.equal(format.issues.numErrors, 0);
      assert.equal(format.issues.numWarnings, 0);
      const gltf = await new GLTFLoader().parseAsync(data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength), '');
      const meta = gltf.parser.json.extras.ontokin;
      assert.equal(meta.target_contract, 'ontokin.glb/0.12');
      assert.equal(meta.profile, 'polygon-pockets-0.1');
      assert.equal(meta.schema_version, '0.12');
      assert.equal(meta.program.revision, expected.program_revision);
      const objects = new Map();
      gltf.scene.traverse(node => {
        if (node.userData.ontokin?.kind !== 'object') return;
        assert.ok(!objects.has(node.userData.ontokin.path), 'Duplicate carrier identity');
        objects.set(node.userData.ontokin.path, node);
      });
      assert.deepEqual([...objects.keys()].sort(), Object.keys(expected.nodes).sort());
      gltf.scene.updateMatrixWorld(true);
      check.geometry = [];
      for (const [name, wanted] of Object.entries(expected.nodes)) {
        const carrier = objects.get(name), regions = {};
        const inverse = new Matrix4().copy(carrier.matrixWorld).invert();
        const corners = wanted.geometry ? frozenCorners(wanted.geometry) : [];
        let triangleCount = 0, volume = 0, area = 0;
        const reference = corners[0] ?? new Vector3();
        carrier.traverse(node => {
          if (!node.isMesh) return;
          let owner = node;
          while (owner && owner.userData.ontokin?.kind !== 'object') owner = owner.parent;
          if (owner !== carrier) return;
          assert.ok(wanted.geometry, 'A geometry-free carrier cannot hide a mesh');
          assert.ok(!Array.isArray(node.material));
          const geometry = node.geometry, region = node.material.userData.ontokin.source_region_key;
          assert.ok(wanted.geometry.palette[region]);
          assert.ok(geometry.index && geometry.index.count % 3 === 0);
          regions[region] = (regions[region] ?? 0) + geometry.index.count / 3;
          triangleCount += geometry.index.count / 3;
          near([...node.material.color.toArray(), node.material.opacity], wanted.geometry.palette[region], 1e-6);
          near([node.material.metalness, node.material.roughness], [wanted.geometry.metallic, wanted.geometry.roughness], 1e-6);
          const matrix = new Matrix4().multiplyMatrices(inverse, node.matrixWorld);
          for (let i = 0; i < geometry.index.count; i += 3) {
            const points = [0, 1, 2].map(j => new Vector3().fromBufferAttribute(
              geometry.attributes.position, geometry.index.getX(i + j)).applyMatrix4(matrix));
            const ab = new Vector3().subVectors(points[1], points[0]);
            const ac = new Vector3().subVectors(points[2], points[0]);
            area += new Vector3().crossVectors(ab, ac).length() / 2;
            const shifted = points.map(point => new Vector3().subVectors(point, reference));
            volume += shifted[0].dot(new Vector3().crossVectors(shifted[1], shifted[2])) / 6;
          }
          for (let i = 0; i < geometry.attributes.position.count; i++) {
            const point = new Vector3().fromBufferAttribute(geometry.attributes.position, i).applyMatrix4(matrix);
            assert.ok(Math.min(...corners.map(corner => corner.distanceTo(point))) <= 1e-5, 'Decoded independently frozen pocket corner');
          }
        });
        assert.equal(triangleCount, wanted.geometry?.triangle_count ?? 0);
        if (wanted.geometry) {
          assert.deepEqual(regions, wanted.geometry.region_triangle_counts);
          assert.ok(volume > 0, 'Actual complete pocket mesh has positive signed volume');
          near([volume], [wanted.geometry.volume_m3], Math.max(1e-5, Math.abs(wanted.geometry.volume_m3) * 1e-5));
          near([area], [wanted.geometry.surface_area_m2], Math.max(1e-5, Math.abs(wanted.geometry.surface_area_m2) * 1e-5));
        }
        check.geometry.push({path: name, triangles: triangleCount, regions, volume_m3: volume, surface_area_m2: area,
          expectation: 'independently frozen pocket source positions'});
      }
      assert.equal(gltf.animations.length, 1);
      near([gltf.animations[0].duration], [1], 1e-6);
      const mixer = new AnimationMixer(gltf.scene), action = mixer.clipAction(gltf.animations[0]);
      check.native_observations = [];
      for (const t of [0, .25, .5, .75, 1]) {
        action.reset().setLoop(LoopOnce, 1).play();
        action.clampWhenFinished = true;
        mixer.setTime(t);
        gltf.scene.updateMatrixWorld(true);
        const observations = {};
        for (const [name, node] of objects) observations[name] = {
          position: node.getWorldPosition(new Vector3()).toArray(),
          rotation: node.getWorldQuaternion(new Quaternion()).toArray(),
          scale: node.getWorldScale(new Vector3()).toArray(),
        };
        check.native_observations.push(...compare(observations, expected, t));
      }
      if (captureCases.has(item.name)) {
        const directory = path.join(output, item.name);
        await mkdir(directory);
        check.browser = await browserCheck(data, expected, directory);
      }
      check.status = 'passed';
    }
    report.status = 'passed';
  } catch (error) {
    report.status = 'failed';
    report.failure = {type: error.name, message: error.message, stack: error.stack};
    process.exitCode = 1;
  }
  report.finished_utc = new Date().toISOString();
  await writeFile(path.join(output, 'summary.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({status: report.status, artifacts: report.artifacts.length, failure: report.failure}));
}

await main();
