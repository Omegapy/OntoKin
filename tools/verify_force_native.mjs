// Independently decode source-built GLB/0.5 geometry, exact histories and motion.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import validator from 'gltf-validator';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {root,sha256,quat,comparePose,rotationError,vectorError,readAccessor,verifyGeometry} from './verify_surface_native.mjs';

export {root,sha256,comparePose,vectorError};
const json=bytes=>JSON.parse(bytes.toString('utf8'));
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'
  ?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const stable=v=>JSON.stringify(canonical(v));
const acceptanceBytes=await readFile(path.join(root,'docs/language-design/force-v0.1/acceptance.json'));
const acceptance=json(acceptanceBytes),cases=new Map(acceptance.source_cases.map(c=>[c.id,c]));
const fixtureInputs=Object.fromEntries(await Promise.all(['acceptance.json','reviewed-acceptance.json','source-errata.json','ADOPTION.md'].map(async name=>
  [name,sha256(await readFile(path.join(root,'docs/language-design/force-v0.1',name)))])));
const sourceErrata=json(await readFile(path.join(root,'docs/language-design/force-v0.1/source-errata.json'))),adoptedCases=new Map([...cases].map(([name,c])=>[name,structuredClone(c)]));
for(const correction of sourceErrata.sample_corrections) {
  const row=adoptedCases.get(correction.id).expected_samples.find(r=>['time','side','target'].every(key=>stable(r[key])===stable(correction[key])));assert.ok(row);
  for(const [key,value] of Object.entries(correction.old))assert.deepEqual(row[key],value,'Adopted source erratum precondition changed');
  Object.assign(row,structuredClone(correction.new));
}
const sourceBase=await readFile(path.join(root,'docs/language-design/force-v0.1/sources/p01-single-interval.ok'),'utf8');
assert.equal(sha256(Buffer.from(sourceBase)),cases.get('P01').source_sha256);
export const deliveryCases=[...Array.from({length:17},(_,i)=>'P'+String(i+1).padStart(2,'0')),'P19','P21','P22',
  'held-out-oblique','held-out-spin','held-out-prefix'];
const failureCases=['P18','P20','P21-full-horizon','float32-boundary-collapse','position-key-budget'];
export const agentDeliveryCases=['P01','P07','P10','P11','P12','P13','P21'];

export async function loadWorkflow(directory,{agentWorkflow=false,agentAudit}={}) {
  const bytes=await readFile(path.join(directory,'workflow.json')),workflow=json(bytes);
  assert.equal(workflow.target_contract,'ontokin.glb/0.5');
  if(!agentWorkflow) {
    assert.equal(agentAudit,undefined,'An Agent audit requires the explicit Agent workflow mode');
    assert.equal(workflow.schema_version,'ontokin.force-destination-workflow/0.1');assert.equal(workflow.status,'built');
    assert.equal(workflow.acceptance_manifest_sha256,sha256(acceptanceBytes));assert.deepEqual(workflow.fixture_inputs,fixtureInputs);
    assert.deepEqual(workflow.git_identity_after,workflow.git_identity);
    assert.equal(workflow.builder_sha256,sha256(await readFile(path.join(root,'tools/build_force_demo.py'))));
    assert.equal(workflow.oracle_sha256,sha256(await readFile(path.join(root,'tools/force_oracles.py'))));
    assert.deepEqual(workflow.fixtures.map(f=>f.fixture),workflow.selected_fixtures);
    assert.equal(new Set(workflow.selected_fixtures).size,workflow.selected_fixtures.length);
    for(const item of workflow.fixtures)assert.equal(item.directory,item.fixture);
    return {bytes,workflow,fixtures:workflow.fixtures,gitIdentity:workflow.git_identity,
      builderHash:workflow.builder_sha256,oracleHash:workflow.oracle_sha256,fixtureInputs:workflow.fixture_inputs,
      sourceKind:'source_export',agentAuditHash:null};
  }
  assert.ok(agentAudit,'Agent workflow mode requires its separately executed --agent-audit FILE');
  assert.equal(workflow.schema_version,'ontokin.force-delivery-workflow/0.1');assert.equal(workflow.status,'recorded');
  assert.equal(workflow.protocol,'ontokin.agent/0.5');assert.deepEqual(workflow.source_fixtures,agentDeliveryCases);
  assert.deepEqual(workflow.deliveries.map(d=>d.case_id),agentDeliveryCases);assert.equal(workflow.delivery_count,agentDeliveryCases.length);
  assert.deepEqual(workflow.fixture_inputs,fixtureInputs);
  const builderHash=sha256(await readFile(path.join(root,'tools/build_force_delivery_demo.py'))),
    oracleHash=sha256(await readFile(path.join(root,'tools/force_oracles.py')));
  assert.equal(workflow.writer_sha256,builderHash);
  assert.deepEqual(workflow.helper_inputs,{'tools/build_force_agent_demo.py':sha256(await readFile(path.join(root,'tools/build_force_agent_demo.py'))),
    'tools/force_oracles.py':oracleHash});
  assert.deepEqual(workflow.source_revision_after,workflow.source_revision,'Source changed during Agent recording');
  assert.equal(workflow.source_revision.worktree_clean,true);
  for(const key of ['commit','tree'])assert.match(workflow.source_revision[key],/^[0-9a-f]{40}$/);
  const auditBytes=await readFile(agentAudit),audit=json(auditBytes);
  assert.equal(audit.schema_version,'ontokin.force-delivery-audit/0.1');assert.equal(audit.status,'passed');
  assert.equal(audit.workflow_sha256,sha256(bytes));assert.deepEqual(audit.implementation,workflow.implementation);
  assert.deepEqual(audit.fixture_inputs,workflow.fixture_inputs);
  assert.equal(audit.verifier_sha256,sha256(await readFile(path.join(root,'tools/verify_force_delivery_workflow.py'))));
  assert.deepEqual(audit.deliveries.map(d=>d.case_id),agentDeliveryCases);
  const fixtures=[];
  for(const item of workflow.deliveries) {
    const prefix='cases/'+item.case_id;
    for(const [name,record] of Object.entries(item.files)) {
      assert.equal(path.basename(name),name);assert.equal(record.path,prefix+'/'+name);
      assert.equal(record.sha256,sha256(await readFile(path.join(directory,record.path))));
    }
    assert.equal(item.files['scene.glb'].sha256,item.sha256);
    const audited=audit.deliveries.find(d=>d.case_id===item.case_id);
    assert.equal(audited.sha256,item.sha256);assert.equal(audited.bytes,item.total_bytes);
    assert.equal(audited.artifact_chunks,item.artifact_roles.length);assert.equal(audited.source_samples,item.reference_roles.length);
    fixtures.push({fixture:item.case_id,directory:prefix,program_revision:item.program_revision,
      artifact_sha256:item.sha256,glb_bytes:item.total_bytes,end_seconds:item.options.end,
      fixed_samples:item.reference_roles.length});
  }
  return {bytes,workflow,fixtures,gitIdentity:{head:workflow.source_revision.commit,tree:workflow.source_revision.tree,worktree_changes:[]},
    builderHash,oracleHash,fixtureInputs,sourceKind:'agent_retrieved_artifact',agentAuditHash:sha256(auditBytes)};
}

const gcd=(a,b)=>{a=a<0n?-a:a;while(b){[a,b]=[b,a%b];}return a;};
function rational(n,d=1n) {if(d<0n){n=-n;d=-d;}assert.notEqual(d,0n);const k=gcd(n,d);return {n:n/k,d:d/k};}
function decimal(text) {
  const m=String(text).match(/^([+-]?)(\d+)(?:\.(\d+))?(?:[eE]([+-]?\d+))?$/);assert.ok(m,'Invalid exact clock '+text);
  const scale=(m[3]?.length??0)-Number(m[4]??0);let n=BigInt(m[2]+(m[3]??''));if(m[1]==='-')n=-n;
  return scale>=0?rational(n,10n**BigInt(scale)):rational(n*10n**BigInt(-scale));
}
function binary(number) {
  assert.ok(Number.isFinite(number));if(number===0)return rational(0n);
  const bytes=new ArrayBuffer(8),view=new DataView(bytes);view.setFloat64(0,number,false);
  const bits=view.getBigUint64(0,false),exponent=Number((bits>>52n)&2047n);
  let n=(bits&((1n<<52n)-1n))+(exponent?1n<<52n:0n);if(bits>>63n)n=-n;
  const power=exponent?exponent-1075:-1074;
  return power>=0?rational(n<<BigInt(power)):rational(n,1n<<BigInt(-power));
}
const add=(a,b)=>rational(a.n*b.d+b.n*a.d,a.d*b.d);
const sub=(a,b)=>rational(a.n*b.d-b.n*a.d,a.d*b.d);
const mul=(a,b)=>rational(a.n*b.n,a.d*b.d);
const div=(a,b)=>rational(a.n*b.d,a.d*b.n);
const compare=(a,b)=>a.n*b.d<b.n*a.d?-1:a.n*b.d>b.n*a.d?1:0;
function number(r) {
  // Round the complete rational once, including huge cancelling operands.
  // Converting numerator and denominator separately can overflow or double
  // round a source acceleration before the final binary64 quotient exists.
  if(r.n===0n)return 0;
  const negative=r.n<0n,n=negative?-r.n:r.n,d=r.d;
  let exponent=n.toString(2).length-d.toString(2).length;
  if(exponent>=0?n<(d<<BigInt(exponent)):(n<<BigInt(-exponent))<d)exponent--;
  exponent=Math.max(exponent,-1022);
  const shift=52-exponent,a=shift>=0?n<<BigInt(shift):n,b=shift>=0?d:d<<BigInt(-shift);
  let quotient=a/b;const remainder=a%b;
  if(2n*remainder>b||(2n*remainder===b&&quotient%2n!==0n))quotient++;
  const result=Number(quotient)*2**(exponent-52);
  return negative?-result:result;
}
function text(r) {
  let denominator=r.d,a=0,b=0;while(denominator%2n===0n){denominator/=2n;a++;}while(denominator%5n===0n){denominator/=5n;b++;}
  assert.equal(denominator,1n,'Source clocks retain exact finite decimal expansions');
  const places=Math.max(a,b),negative=r.n<0n,n=(negative?-r.n:r.n)*2n**BigInt(places-a)*5n**BigInt(places-b);
  if(!places)return (negative?'-':'')+String(n);
  const digits=String(n).padStart(places+1,'0');return ((negative?'-':'')+digits.slice(0,-places)+'.'+digits.slice(-places)).replace(/0+$/,'').replace(/\.$/,'');
}
const clock=n=>text(binary(n));
const force=(key,start,duration,vector,target='ball',sequence=0)=>({key,target,start_seconds:clock(start),
  duration_seconds:clock(duration),end_seconds:text(add(binary(start),binary(duration))),vector_n:vector,sequence_index:sequence});
const impulse=(time,vector,point=[0,0,0],target='ball',sequence=0)=>({time_seconds:clock(time),vector_n_s:vector,point_self_m:point,target,sequence_index:sequence});

// Independently stated fixture operands. This registry is checked against actual
// retained .ok bytes, not against the Python-generated oracle or export report.
function specification(name) {
  const s={fixture:name,mass_kg:2,radius_m:.5,position_m:[0,0,0],velocity_m_per_s:[0,0,0],gravity_m_per_s2:[0,0,0],
    forces:[],impulses:[],end_seconds:'3',fps:12};
  if(name==='P01')s.forces=[force('push',1,1,[4,0,0])];
  else if(name==='P02')Object.assign(s,{end_seconds:'4',forces:[force('a',0,2,[4,0,0]),force('b',1,2,[-2,0,0])]});
  else if(name==='P03')s.forces=[force('a',0,2,[4,0,0]),force('b',0,2,[-4,0,0],'ball',1)];
  else if(name==='P04')s.forces=[force('a',0,1,[4,0,0]),force('b',1,1,[4,0,0])];
  else if(name==='P05')Object.assign(s,{velocity_m_per_s:[3,0,0],forces:[force('push',1,1,[0,0,0])]});
  else if(name==='P06')Object.assign(s,{gravity_m_per_s2:[0,-10,0],forces:[force('push',1,1,[0,20,0])]});
  else if(name==='P07')Object.assign(s,{forces:[force('a',0,2,[4,0,0])],impulses:[impulse(1,[0,2,0],[.5,0,0])]});
  else if(name==='P08')Object.assign(s,{forces:[force('a',0,1,[4,0,0])],impulses:[impulse(1,[2,0,0])]});
  else if(name==='P09')Object.assign(s,{gravity_m_per_s2:[0,-10,0],forces:[force('push',1,1,[2,20,0],'ball',1)],release_seconds:'1',fps:60});
  else if(['P10','P11','P12','P13'].includes(name))Object.assign(s,{mass_kg:name==='P11'?4:2,generated:true,
    forces:[force('push',1,name==='P13'?.5:1,[name==='P12'?8:4,0,0],'rack.props["first"]'),force('sibling',1,1,[4,0,0],'rack.props["second"]',1)]});
  else if(name==='P14')Object.assign(s,{end_seconds:'2',forces:[force('push',0,1,[4,0,0])]});
  else if(name==='P15')Object.assign(s,{end_seconds:'2',forces:[force('push',2,1,[4,0,0])]});
  else if(name==='P16')Object.assign(s,{end_seconds:'1',forces:[force('push',.1,.2,[4,0,0])]});
  else if(name==='P17')Object.assign(s,{end_seconds:'2',forces:[force('push',1,5,[4,0,0])]});
  else if(name==='P19')Object.assign(s,{end_seconds:'2',mass_kg:1e308,
    forces:[force('a',0,1,[1e308,0,0]),force('b',0,1,[1e308,0,0],'ball',1),force('c',0,1,[-1e308,0,0],'ball',2)]});
  else if(name==='P21')Object.assign(s,{end_seconds:'1',mass_kg:.5,forces:[force('early',0,1,[1,0,0]),force('late',2,1,[1e308,0,0])]});
  else if(name==='P22')Object.assign(s,{end_seconds:'2.5',mass_kg:3.5,velocity_m_per_s:[.2,-.1,.3],forces:[force('push',.5,1.25,[1,3,-2])]});
  else if(name==='held-out-oblique')Object.assign(s,{end_seconds:'2.5',mass_kg:5,radius_m:.75,position_m:[1,-.5,2],
    velocity_m_per_s:[-.4,.2,.1],gravity_m_per_s2:[.3,-.7,.2],forces:[force('slant',.375,1.125,[3,-4,2]),force('cross',1.125,.75,[-1,2,3])]});
  else if(name==='held-out-spin')Object.assign(s,{end_seconds:'2.25',gravity_m_per_s2:[0,-2,0],
    forces:[force('drive',0,.75,[12,2,0]),force('brake',.75,1.25,[-8,0,0])],impulses:[impulse(.25,[0,16,0],[.5,0,0])]});
  else {assert.equal(name,'held-out-prefix');Object.assign(s,{end_seconds:'1',declared_duration_seconds:'4',mass_kg:3,
    forces:[force('still-active',.125,2,[3,-6,1])],impulses:[impulse(3,[0,1e308,0],[.5,0,0])]});}
  return s;
}

export function expectedPose(object,time) {
  const m=object.motion,t=Number(time),position=[0,0,0];let angle=0;
  if(m.kind==='fixed')return {position_m:position,orientation_xyzw:[0,0,0,1]};
  if(m.kind==='release_carrier')return {position_m:[Math.min(t,1),0,0],orientation_xyzw:[0,0,Math.sin(-1+Math.min(t,1)),Math.cos(-1+Math.min(t,1))]};
  if(m.release_seconds!==undefined) {
    if(t<1){angle=-2+2*t;return {position_m:[t+.5*Math.cos(angle),.5*Math.sin(angle),0],orientation_xyzw:[0,0,Math.sin(angle/2),Math.cos(angle/2)]};}
    const dt=t-1;position.splice(0,3,1.5+dt,dt-5*dt*dt,0);angle=2*dt;
  } else for(let axis=0;axis<3;axis++)position[axis]=m.position_m[axis]+m.velocity_m_per_s[axis]*t+.5*m.gravity_m_per_s2[axis]*t*t;
  for(const f of m.forces) {
    if(f.target!==object.path||t<=Number(f.start_seconds))continue;
    const elapsed=t-Number(f.start_seconds),duration=Number(f.duration_seconds);
    const integral=elapsed<=duration?.5*elapsed*elapsed:duration*(elapsed-.5*duration);
    for(let axis=0;axis<3;axis++)position[axis]+=number(div(binary(f.vector_n[axis]),binary(m.mass_kg)))*integral;
  }
  for(const event of m.impulses) {
    if(event.target!==object.path||t<=Number(event.time_seconds))continue;
    const dt=t-Number(event.time_seconds),[x,y,z]=event.point_self_m,[jx,jy,jz]=event.vector_n_s;
    for(let axis=0;axis<3;axis++)position[axis]+=event.vector_n_s[axis]/m.mass_kg*dt;
    assert.equal(y*jz-z*jy,0);assert.equal(z*jx-x*jz,0);
    angle+=(x*jy-y*jx)/(.4*m.mass_kg*m.radius_m**2)*dt;
  }
  return {position_m:position,orientation_xyzw:[0,0,Math.sin(angle/2),Math.cos(angle/2)]};
}

const sections=[{key:'foot',station_m:0,center_xy_m:[0,0],radii_xy_m:[.5,.35],region:'clay'},
  {key:'neck',station_m:1,center_xy_m:[.15,0],radii_xy_m:[.3,.2],region:'paint'},
  {key:'tip',station_m:1.5,center_xy_m:[.15,0],radii_xy_m:[.2,.1],region:'paint'}];
const materials={clay:{rgba:[.6,.3,.2,1],metallic:0,roughness:.8},paint:{rgba:[.1,.4,.8,1],metallic:.2,roughness:.4}};
function checkOracle(oracle) {
  assert.ok(deliveryCases.includes(oracle.fixture));const spec=specification(oracle.fixture);
  assert.deepEqual(oracle.specification,spec);assert.equal(oracle.end_seconds,spec.end_seconds);
  const paths=spec.generated?['rack.props["first"]','rack.props["second"]']:['ball'];
  const empty=spec.generated?['rack']:oracle.fixture==='P09'?['carrier']:[];
  assert.deepEqual(oracle.shapes.map(s=>s.path),paths);assert.deepEqual(oracle.empty_objects.map(s=>s.path),empty);
  for(const object of [...oracle.shapes,...oracle.empty_objects]) {
    const motion={...spec,kind:'force_pulses'};
    if(object.path==='rack.props["second"]')Object.assign(motion,{mass_kg:4,position_m:[3,0,0]});
    if(object.path==='rack')motion.kind='fixed';if(object.path==='carrier')motion.kind='release_carrier';
    assert.deepEqual(object.motion,motion,'Independent fixture operands differ');
    const keys=object.path.startsWith('rack.props')?['rack','props',object.path.includes('"first"')?'first':'second']:[object.path];
    assert.deepEqual(object.element_id,['force-demo','demo',...keys]);
    if(object.sections) {
      assert.deepEqual(object.sections,sections);assert.deepEqual(object.materials,materials);
      assert.equal(object.facets,16);assert.equal(object.caps,'flat');assert.equal(object.physical_kind,'sphere_body');
      assert.equal(object.body_mass_kg,motion.mass_kg);assert.equal(object.body_radius_m,motion.radius_m);
      assert.deepEqual(object.local_position_m,[0,0,.1]);assert.deepEqual(object.local_rotation_wxyz,[1,0,0,0]);
      assert.deepEqual(object.expected,{triangles:96,vertices:288,triangles_per_region:{clay:48,paint:48}});
    }
  }
}

function heldOutSource(spec) {
  const units=(v,u)=>v.map(n=>`${n}[${u}]`).join(', '),events=new Map();
  const put=(time,sequence,line)=>events.set(time,[...events.get(time)??[],[sequence,line]]);
  for(const f of spec.forces)put(f.start_seconds,f.sequence_index,`force ${f.target} @ "${f.key}" using vector(world, ${units(f.vector_n,'N')}) for ${Number(f.duration_seconds)}[s];`);
  for(const i of spec.impulses)put(i.time_seconds,i.sequence_index,`impulse ${i.target} using vector(world, ${units(i.vector_n_s,'N*s')}) at point(${i.target}.frame, ${units(i.point_self_m,'m')});`);
  const blocks=[...events].sort((a,b)=>compare(decimal(a[0]),decimal(b[0]))).map(([time,items])=>
    `at ${Number(time)}[s] sequence { ${items.sort((a,b)=>a[0]-b[0]).map(x=>x[1]).join(' ')} }`).join(' ');
  return sourceBase.slice(0,sourceBase.indexOf('scene Demo'))+`scene Demo @ "demo" {
    duration = ${spec.declared_duration_seconds??spec.end_seconds}[s]; gravity = vector(world, ${units(spec.gravity_m_per_s2,'m/s^2')});
    object ball @ "ball": bodies.SphereProp { body_mass = ${spec.mass_kg}[kg]; body_radius = ${spec.radius_m}[m];
    placement = pose(world, vec3(${units(spec.position_m,'m')}), quat(1,0,0,0)); velocity = vector(world, ${units(spec.velocity_m_per_s,'m/s')}); }
    ${blocks} }`;
}
function sourceTokens(source) {
  // This bounded authored corpus has no comments. Preserve string contents
  // and token boundaries: stripping whitespace would equate an invalid
  // stable key "de mo" with "demo", or split identifiers with real names.
  const tokens=source.match(/"(?:[^"\\]|\\.)*"|[A-Za-z_][A-Za-z0-9_]*|(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?|[^\s]/g)??[];
  return stable(tokens.map(token=>/^\d/.test(token)?['number',Number(token)]:['token',token]));
}
function parseStatements(payload,revision) {
  const source=payload.entry.source,records={forces:[],impulses:[]};
  const numberPattern='([-+]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[eE][-+]?\\d+)?)';
  const forcePattern=new RegExp('^force (.+?) @ "([^"]+)" using vector\\(world,\\s*'+numberPattern+'\\[N\\],\\s*'+numberPattern+'\\[N\\],\\s*'+numberPattern+'\\[N\\]\\) for '+numberPattern+'\\[s\\];$');
  const impulsePattern=new RegExp('^impulse (.+?) using vector\\(world,\\s*'+numberPattern+'\\[N\\*s\\],\\s*'+numberPattern+'\\[N\\*s\\],\\s*'+numberPattern+'\\[N\\*s\\]\\) at point\\((.+?)\\.frame,\\s*'+numberPattern+'\\[m\\],\\s*'+numberPattern+'\\[m\\],\\s*'+numberPattern+'\\[m\\]\\);$');
  for(const block of source.matchAll(/at\s+([-+\d.eE]+)\[s\]\s+sequence\s*\{([^}]*)\}/g)) {
    const start=block.index+block[0].indexOf('{')+1;let cursor=0,sequence=0;
    for(const part of block[2].split(';').slice(0,-1)) {
      const statement=part.trim()+';',index=start+cursor+part.indexOf(part.trim());cursor+=part.length+1;
      const location={source_id:'entry',source_revision:sha256(Buffer.from(source)),start_byte:Buffer.byteLength(source.slice(0,index)),end_byte:Buffer.byteLength(source.slice(0,index+statement.length))};
      const f=statement.match(forcePattern),i=statement.match(impulsePattern);
      if(f)records.forces.push({...force(f[2],Number(block[1]),Number(f[6]),f.slice(3,6).map(Number),f[1],sequence),source_location:location});
      if(i){assert.equal(i[1],i[5]);records.impulses.push({...impulse(Number(block[1]),i.slice(2,5).map(Number),i.slice(6,9).map(Number),i[1],sequence),source_location:location});}
      if(statement.startsWith('force '))assert.ok(f,'The bounded fixture source force parser rejected a statement');
      if(statement.startsWith('impulse '))assert.ok(i,'The bounded fixture source impulse parser rejected a statement');
      sequence++;
    }
  }
  return records;
}

function exactBoundaries(spec) {
  const end=decimal(spec.end_seconds),values=new Map([['0',decimal('0')],[spec.end_seconds,end]]);
  for(const f of spec.forces)for(const key of ['start_seconds','end_seconds'])if(compare(decimal(f[key]),end)<=0)values.set(f[key],decimal(f[key]));
  for(const i of spec.impulses)if(compare(decimal(i.time_seconds),end)<=0)values.set(i.time_seconds,decimal(i.time_seconds));
  if(spec.release_seconds)values.set(spec.release_seconds,decimal(spec.release_seconds));
  return [...values.values()].sort(compare).map(text);
}
function requiredSamples(spec,fixture) {
  const samples=new Map(),put=(time,side)=>samples.set(text(time)+'|'+side,[time,side]);
  for(const time of exactBoundaries(spec))for(const side of ['before','after'])put(decimal(time),side);
  for(const row of fixture?.expected_samples??[])put(rational(BigInt(row.time.numerator),BigInt(row.time.denominator)),row.side);
  for(let i=0;i<=16;i++)put(mul(decimal(spec.end_seconds),rational(BigInt(i),16n)),'after');
  return [...samples.values()].sort((a,b)=>compare(a[0],b[0])||(a[1]==='after'?1:-1)).map(([time,side])=>[text(time),side]);
}

export async function loadCase(directory) {
  const names={bundle:'program.bundle.json',manifest:'source-manifest.json',glb:'scene.glb',export:'scene.export.json',reference:'scene.reference.json',oracle:'oracle.json'};
  const inputs=Object.fromEntries(await Promise.all(Object.entries(names).map(async ([key,file])=>[key,await readFile(path.join(directory,file))])));
  const provenance=Object.fromEntries(Object.entries(names).map(([key,file])=>[key,{file,sha256:sha256(inputs[key]),byte_length:inputs[key].length}]));
  const payload=json(inputs.bundle),exportReport=json(inputs.export),reference=json(inputs.reference),oracle=json(inputs.oracle),fixture=cases.get(oracle.fixture);
  assert.equal(payload.schema_version,'ontokin.bundle/0.1');assert.equal(oracle.schema_version,'ontokin.force-fixture-oracle/0.1');
  assert.equal(oracle.acceptance_manifest_sha256,sha256(acceptanceBytes));checkOracle(oracle);
  assert.equal(oracle.frozen_fixture,Boolean(fixture));assert.deepEqual(oracle.frozen_expected,fixture?.expected_samples??[]);
  assert.deepEqual(oracle.fixture_inputs,fixtureInputs);assert.deepEqual(oracle.adopted_expected,adoptedCases.get(oracle.fixture)?.expected_samples??[]);
  assert.deepEqual(oracle.adopted_sample_corrections,sourceErrata.sample_corrections.filter(c=>c.id===oracle.fixture));
  const units=[{source_id:'entry',package_id:null,version:null,filename:payload.entry.filename,source_revision:sha256(Buffer.from(payload.entry.source))},
    ...payload.modules.map(m=>({source_id:`package:${m.package_id}@${m.version}`,package_id:m.package_id,version:m.version,filename:m.filename,source_revision:sha256(Buffer.from(m.source))}))]
    .sort((a,b)=>a.source_id<b.source_id?-1:a.source_id>b.source_id?1:0);
  if(fixture)assert.deepEqual(units,fixture.source_units,'Every source byte belongs to the frozen closure');
  else {
    assert.deepEqual(units.filter(u=>u.source_id!=='entry'),cases.get('P01').source_units.filter(u=>u.source_id!=='entry'));
    assert.equal(sourceTokens(payload.entry.source),sourceTokens(heldOutSource(oracle.specification)),'Held-out source differs from its independent authored parameters');
  }
  const manifest={schema_version:'ontokin.bundle/0.1',entry_source_id:'entry',units};
  assert.deepEqual(json(inputs.manifest),manifest,'Retained source manifest is exact');
  const revision=sha256(Buffer.concat([Buffer.from('ontokin.bundle/0.1\0'),Buffer.from(stable(manifest))]));
  assert.equal(oracle.program_revision,revision);if(fixture)assert.equal(revision,fixture.program_revision);
  for(const [index,unit] of [payload.entry,...payload.modules].entries()) {
    assert.equal(path.basename(unit.filename),unit.filename);const raw=await readFile(path.join(directory,unit.filename));assert.equal(raw.toString('utf8'),unit.source);
    provenance['source_'+index]={file:unit.filename,sha256:sha256(raw),byte_length:raw.length};
  }
  const sourceStatements=parseStatements(payload,revision);
  for(const key of ['forces','impulses'])assert.deepEqual(sourceStatements[key].map(({source_location,...record})=>record),oracle.specification[key],'Actual source operands differ from independent expectations');
  if(fixture)assert.deepEqual(sourceStatements.forces.map(f=>({...f.source_location,text:Buffer.from(payload.entry.source).subarray(f.source_location.start_byte,f.source_location.end_byte).toString('utf8')})),fixture.force_statements);
  const bytes=inputs.glb;assert.ok(bytes.length<=64*1024*1024);assert.equal(bytes.readUInt32LE(0),0x46546c67);assert.equal(bytes.readUInt32LE(4),2);
  assert.equal(bytes.readUInt32LE(8),bytes.length);assert.equal(bytes.readUInt32LE(16),0x4e4f534a);
  const length=bytes.readUInt32LE(12),document=json(bytes.subarray(20,20+length)),offset=20+length;
  assert.equal(bytes.readUInt32LE(offset+4),0x004e4942);assert.equal(offset+8+bytes.readUInt32LE(offset),bytes.length);
  const binaryData=bytes.subarray(offset+8),metadata=document.extras.ontokin;
  assert.equal(exportReport.schema_version,'ontokin.glb-report/0.5');assert.equal(exportReport.target_contract,'ontokin.glb/0.5');
  assert.equal(exportReport.validation.status,'passed');assert.equal(metadata.target_contract,'ontokin.glb/0.5');assert.equal(metadata.schema_version,'0.5');
  assert.equal(metadata.profile,'force-0.1');assert.equal(metadata.program.revision,revision);assert.equal(exportReport.program_revision,revision);
  assert.deepEqual(metadata.program.manifest,manifest);assert.deepEqual(exportReport.program.manifest,manifest);
  assert.equal(reference.schema_version,'ontokin.force-native-reference/0.1');assert.equal(reference.program_revision,revision);assert.deepEqual(reference.source_manifest,manifest);
  assert.equal(reference.artifact_sha256,provenance.glb.sha256);assert.equal(exportReport.artifact.sha256,provenance.glb.sha256);assert.equal(exportReport.artifact.byte_length,bytes.length);
  assert.deepEqual(reference.tolerances,exportReport.tolerances);
  const tolerances={position_m:.001,rotation_rad:.001,time_seconds:.000001};
  for(const [key,bound] of Object.entries(tolerances)){const actual=reference.tolerances[key];assert.ok(Number.isFinite(actual)&&actual>0&&actual<=bound);tolerances[key]=actual;}
  assert.deepEqual(reference.samples.map(s=>[s.time_seconds,s.side]),requiredSamples(oracle.specification,fixture),'All predetermined exact sample sides are required');
  return {directory,bytes,document,binary:binaryData,metadata,exportReport,reference,oracle,manifest,revision,payload,
    provenance,tolerances,artifactHash:provenance.glb.sha256,fixture,sourceStatements};
}

const occurred=(clock,time,side)=>compare(decimal(clock),decimal(time))<(side==='after'?1:0);
const sortedKeys=object=>Object.keys(object).sort();
const sourceObjects=state=>[...state.oracle.shapes,...state.oracle.empty_objects];
const targetRecord=(state,object,f)=>({force_key:f.key,force_element_id:['force-demo','demo','force',f.key],
  target_path:object.path,target_element_id:object.element_id,program_revision:state.revision,
  source_location:f.source_location,sequence_index:f.sequence_index,force_world_n:f.vector_n,
  activation_time_seconds:f.start_seconds,duration_seconds:f.duration_seconds,completion_time_seconds:f.end_seconds});

function expectedForce(state,object,time,side) {
  const records=state.sourceStatements.forces.filter(f=>f.target===object.path);
  const started=records.filter(f=>occurred(f.start_seconds,time,side)),completed=records.filter(f=>occurred(f.end_seconds,time,side));
  const active=started.filter(f=>!occurred(f.end_seconds,time,side)).sort((a,b)=>a.key<b.key?-1:1);
  const events=[...started.map(f=>({clock:f.start_seconds,kind:'started',f})),...completed.map(f=>({clock:f.end_seconds,kind:'completed',f}))];
  events.sort((a,b)=>compare(decimal(a.clock),decimal(b.clock))||(a.kind!==b.kind?(a.kind==='completed'?-1:1):
    a.kind==='completed'?(a.f.key<b.f.key?-1:1):a.f.sequence_index-b.f.sequence_index));
  const latest=events.at(-1)?.clock??null;
  const net=[0,1,2].map(axis=>number(active.reduce((sum,f)=>add(sum,binary(f.vector_n[axis])),rational(0n))));
  const free=Boolean(object.sections)&&(!object.motion.release_seconds||occurred(object.motion.release_seconds,time,side));
  const acceleration=free?net.map((n,axis)=>number(add(binary(object.motion.gravity_m_per_s2[axis]),div(binary(n),binary(object.body_mass_kg))))):null;
  return {active:active.map(f=>targetRecord(state,object,f)),net_force_world_n:net,acceleration_world_m_per_s2:acceleration,
    started_count:started.length,completed_count:completed.length,last_change_time_seconds:latest,
    last_changes:events.filter(e=>e.clock===latest).map(e=>({kind:e.kind,...targetRecord(state,object,e.f)}))};
}

function expectedVelocity(object,time,side) {
  const m=object.motion,t=Number(time),zero=[0,0,0];let velocity,omega=0;
  if(m.kind==='fixed')return {velocity:zero,omega:zero};
  if(m.kind==='release_carrier') {
    const moving=occurred('0',time,side)&&!occurred('1',time,side);
    return {velocity:moving?[1,0,0]:zero,omega:moving?[0,0,2]:zero};
  }
  if(m.release_seconds&&!occurred(m.release_seconds,time,side)) {
    if(!occurred('0',time,side))return {velocity:zero,omega:zero};
    const angle=-2+2*t;return {velocity:[1-Math.sin(angle),Math.cos(angle),0],omega:[0,0,2]};
  }
  if(m.release_seconds){velocity=[1,1-10*(t-1),0];omega=2;}
  else velocity=m.velocity_m_per_s.map((v,i)=>v+m.gravity_m_per_s2[i]*t);
  for(const f of m.forces) {
    if(f.target!==object.path||!occurred(f.start_seconds,time,side))continue;
    const width=Math.min(t-Number(f.start_seconds),Number(f.duration_seconds));
    for(let i=0;i<3;i++)velocity[i]+=number(div(binary(f.vector_n[i]),binary(m.mass_kg)))*width;
  }
  for(const event of m.impulses) {
    if(event.target!==object.path||!occurred(event.time_seconds,time,side))continue;
    for(let i=0;i<3;i++)velocity[i]+=event.vector_n_s[i]/m.mass_kg;
    omega+=(event.point_self_m[0]*event.vector_n_s[1]-event.point_self_m[1]*event.vector_n_s[0])/(.4*m.mass_kg*m.radius_m**2);
  }
  return {velocity,omega:[0,0,omega]};
}

function expectedAuthority(state,object,time,side) {
  const m=object.motion;
  if(m.kind==='fixed')return {kind:'prescribed',translation_action:null,orientation_action:null};
  if(m.kind==='release_carrier') {
    const moving=occurred('0',time,side)&&!occurred('1',time,side);
    return {kind:'prescribed',translation_action:moving?'carry':null,orientation_action:moving?'turn':null};
  }
  if(m.release_seconds&&!occurred(m.release_seconds,time,side))return {kind:'joint',relation:'hold'};
  const origin=m.release_seconds??'0';let anchor=origin;
  for(const boundary of exactBoundaries(m)) {
    if(compare(decimal(boundary),decimal(origin))<0||!occurred(boundary,time,side))continue;
    const before=expectedForce(state,object,boundary,'before').acceleration_world_m_per_s2;
    const after=expectedForce(state,object,boundary,'after').acceleration_world_m_per_s2;
    if(stable(before)!==stable(after)||m.impulses.some(i=>i.target===object.path&&i.time_seconds===boundary))anchor=boundary;
  }
  return {kind:'free_sphere',since_seconds:origin,trajectory_anchor_seconds:anchor};
}

function verifyImpulse(state,object,time,side,actual) {
  assert.deepEqual(sortedKeys(actual),['applied_count','last_application_time_seconds','last_applications'].sort());
  const applied=state.sourceStatements.impulses.filter(i=>i.target===object.path&&occurred(i.time_seconds,time,side));
  const latest=applied.at(-1)?.time_seconds??null,last=applied.filter(i=>i.time_seconds===latest);
  assert.equal(actual.applied_count,applied.length);assert.equal(actual.last_application_time_seconds,latest);
  assert.equal(actual.last_applications.length,last.length);
  for(const [index,item] of last.entries()) {
    const record=actual.last_applications[index],pose=expectedPose(object,item.time_seconds);
    const lever=new THREE.Vector3(...item.point_self_m).applyQuaternion(new THREE.Quaternion(...pose.orientation_xyzw));
    const angular=lever.clone().cross(new THREE.Vector3(...item.vector_n_s)),before=expectedVelocity(object,item.time_seconds,'before');
    const wanted={sequence_index:item.sequence_index,source_location:item.source_location,target_element_id:object.element_id,target_path:object.path,
      impulse_world_n_s:item.vector_n_s,application_point_self_m:item.point_self_m,lever_arm_world_m:lever.toArray(),
      application_point_world_m:lever.clone().add(new THREE.Vector3(...pose.position_m)).toArray(),angular_impulse_world_n_m_s:angular.toArray(),
      linear_velocity_before_world_m_per_s:before.velocity,angular_velocity_before_world_rad_per_s:before.omega,
      linear_velocity_after_world_m_per_s:before.velocity.map((v,i)=>v+item.vector_n_s[i]/object.body_mass_kg),
      angular_velocity_after_world_rad_per_s:before.omega.map((v,i)=>v+angular.getComponent(i)/(.4*object.body_mass_kg*object.body_radius_m**2))};
    assert.deepEqual(sortedKeys(record),sortedKeys(wanted),'Complete impulse application fields');
    for(const [key,value] of Object.entries(wanted)) {
      if(Array.isArray(value)&&value.every(v=>typeof v==='number'))vectorError(record[key],value,1e-9,'Independent '+key);
      else assert.deepEqual(record[key],value,'Independent '+key);
    }
  }
  return last.length;
}

export function verifyInfluences(state) {
  const objects=sourceObjects(state),paths=objects.map(o=>o.path).sort();let forceComparisons=0,impulseComparisons=0;
  for(const sample of state.reference.samples) {
    assert.deepEqual(sortedKeys(sample.objects),paths,'Every source carrier requires a complete sample');
    for(const object of objects) {
      const actual=sample.objects[object.path],label=state.oracle.fixture+' '+object.path+' '+sample.time_seconds+' '+sample.side;
      assert.deepEqual(actual.element_id,object.element_id);assert.equal(actual.own_mass_kg,object.body_mass_kg??0);
      assert.deepEqual(actual.forces,expectedForce(state,object,sample.time_seconds,sample.side),label+' complete force projection');
      assert.deepEqual(actual.pose_authority,expectedAuthority(state,object,sample.time_seconds,sample.side),label+' motion authority/anchor');
      const velocity=expectedVelocity(object,sample.time_seconds,sample.side);
      vectorError(actual.velocity_m_per_s,velocity.velocity,1e-9,label+' independent velocity');
      vectorError(actual.angular_velocity_rad_per_s,velocity.omega,1e-9,label+' independent angular velocity');
      comparePose({position_m:actual.position_m,orientation_xyzw:quat(actual.orientation_wxyz).toArray()},
        expectedPose(object,sample.time_seconds),{position_m:1e-9,rotation_rad:1e-7},label+' independent reference pose');
      impulseComparisons+=verifyImpulse(state,object,sample.time_seconds,sample.side,actual.impulses);forceComparisons++;
    }
  }
  for(const expected of state.oracle.adopted_expected) {
    const time=text(rational(BigInt(expected.time.numerator),BigInt(expected.time.denominator)));
    const actual=state.reference.samples.find(s=>s.time_seconds===time&&s.side===expected.side).objects[expected.target];
    for(const [key,wanted] of [['position_m','position_m'],['velocity_m_per_s','velocity_m_s'],['angular_velocity_rad_per_s','omega_world_rad_s']])
      vectorError(actual[key],expected[wanted],1e-9,'Adopted frozen '+key);
    const componentError=Math.min(...[-1,1].map(sign=>Math.max(...actual.orientation_wxyz.map((v,i)=>Math.abs(v-sign*expected.orientation_wxyz[i])))));
    assert.ok(componentError<=1e-9,'Adopted frozen quaternion components');
    const forces=actual.forces;assert.deepEqual(forces.active.map(f=>f.force_key),expected.active_keys);
    assert.deepEqual(Object.fromEntries(forces.active.map(f=>[f.force_key,f.completion_time_seconds])),Object.fromEntries(Object.entries(expected.active_ends)
      .map(([key,value])=>[key,text(rational(BigInt(value.numerator),BigInt(value.denominator)))])));
    for(const key of ['started_count','completed_count'])assert.equal(forces[key],expected[key]);
    vectorError(forces.net_force_world_n,expected.net_force_world_n,1e-9,'Adopted frozen net force');
    if(expected.acceleration_world_m_s2===null)assert.equal(forces.acceleration_world_m_per_s2,null);
    else vectorError(forces.acceleration_world_m_per_s2,expected.acceleration_world_m_s2,1e-9,'Adopted frozen acceleration');
    const exact=value=>value===null?null:text(rational(BigInt(value.numerator),BigInt(value.denominator)));
    assert.equal(forces.last_change_time_seconds,exact(expected.last_boundary));
    assert.deepEqual(forces.last_changes.map(f=>({key:f.force_key,kind:f.kind})),expected.last_changes);
    assert.equal(actual.pose_authority.since_seconds??null,exact(expected.dynamic_since));
    assert.equal(actual.pose_authority.trajectory_anchor_seconds??null,exact(expected.anchor_time));
  }
  const records=state.metadata.boundary_states,boundaries=exactBoundaries(state.oracle.specification);
  assert.deepEqual(records.map(r=>r.source_seconds),boundaries,'Every exact source boundary, including the valid prefix endpoint, is retained');
  assert.deepEqual(state.exportReport.sampling.boundary_times_seconds,boundaries);
  assert.equal(state.exportReport.sampling.end_seconds,state.oracle.end_seconds);
  for(const record of records) {
    const sample=state.reference.samples.find(s=>s.time_seconds===record.source_seconds&&s.side==='after');assert.ok(sample);
    for(const [field,source] of [['force_states_after','forces'],['impulse_states_after','impulses'],['pose_authorities_after','pose_authority']]) {
      assert.deepEqual(sortedKeys(record[field]),paths,'Every boundary includes all carriers in '+field);
      for(const object of objects)assert.deepEqual(record[field][object.path],sample.objects[object.path][source],field+' independently checked source state');
    }
  }
  const profile=state.metadata.force_profile;
  assert.equal(profile.name,'force-0.1');assert.equal(profile.continuous_external_torques,'absent');assert.equal(profile.contacts,'disabled');
  assert.equal(profile.source_impulses,'instantaneous_world_momentum_at_target_self_point');
  assert.equal(profile.continuous_external_forces,'canonical_active_source_force_sum_plus_uniform_gravity');
  assert.ok(profile.source_forces.includes('world')&&(/center_of_mass|com/.test(profile.source_forces)),'COM-only world force disclosure');
  assert.ok(profile.destination_behavior.includes('recorded'),'Force delivery must disclose recorded playback');
  return {status:'passed',boundary_count:records.length,complete_source_force_projections:forceComparisons,
    retained_impulse_application_comparisons:impulseComparisons,exact_force_clocks_and_source_spans_checked:true,all_carriers_required:true};
}

function sourceAngularBound(state) {
  let bound=0;
  for(const object of sourceObjects(state))for(const time of exactBoundaries(state.oracle.specification))for(const side of ['before','after']) {
    if(time===state.oracle.end_seconds&&side==='after')continue;
    bound=Math.max(bound,Math.hypot(...expectedVelocity(object,time,side).omega));
  }
  return bound;
}

export function assertClock(state,document=state.document,binaryData=state.binary) {
  assert.equal(document.animations.length,1);const animation=document.animations[0];
  assert.ok(animation.samplers.length);const first=readAccessor(document,binaryData,animation.samplers[0].input).flat();
  assert.equal(first[0],0);assert.equal(first.at(-1),Math.fround(Number(state.oracle.end_seconds)));
  for(const sampler of animation.samplers) {
    assert.equal(sampler.interpolation,'LINEAR');assert.deepEqual(readAccessor(document,binaryData,sampler.input).flat(),first);
  }
  const boundaries=exactBoundaries(state.oracle.specification),bound=sourceAngularBound(state);
  assert.equal(new Set(boundaries.map(t=>Math.fround(Number(t)))).size,boundaries.length,'Distinct source boundaries cannot alias in binary32');
  for(const boundary of boundaries) {
    const exported=Math.fround(Number(boundary));assert.ok(first.includes(exported),'Exact source boundary missing from decoded clock '+boundary);
    assert.ok(Math.abs(number(sub(binary(exported),decimal(boundary))))<=state.tolerances.time_seconds);
  }
  let maxChord=0,maxStep=0,maxAngularStep=0;
  for(let i=1;i<first.length;i++) {
    const width=first[i]-first[i-1];assert.ok(Number.isFinite(width)&&width>0,'Destination clock strictly increases');maxStep=Math.max(maxStep,width);
    const middle=String(first[i-1]+width/2);
    const intervalAngularBound=Math.max(...sourceObjects(state).map(object=>Math.hypot(...expectedVelocity(object,middle,'after').omega)));
    const angularStep=width*intervalAngularBound;maxAngularStep=Math.max(maxAngularStep,angularStep);
    assert.ok(angularStep<=Math.PI/4,'Authored spin aliases beyond the declared pi/4 interval bound');
    for(const object of state.oracle.shapes) {
      const acceleration=expectedForce(state,object,middle,'after').acceleration_world_m_per_s2;
      if(acceleration===null)continue;
      const chord=Math.hypot(...acceleration)*width*width/8;maxChord=Math.max(maxChord,chord);
      assert.ok(chord<=state.tolerances.position_m*.25*(1+1e-6),'Constant-acceleration chord exceeds the quarter-position-tolerance allocation');
    }
  }
  assert.ok(state.exportReport.sampling.angular_speed_bound_rad_per_s>=bound,'Reported spin bound must cover the independently derived prefix');
  return {times:first,summary:{key_count:first.length,independent_angular_speed_bound_rad_per_s:bound,
    maximum_interval_seconds:maxStep,maximum_analytic_acceleration_chord_m:maxChord,source_boundaries_retained:true,
    maximum_angular_step_rad:maxAngularStep,angular_bound_policy:'source_interval_local_pi_over_four',
    future_events_excluded_from_bound:true}};
}

function rejectMutations(state) {
  const results=[];
  const reject=(name,mutate)=>{
    const altered={...state,metadata:structuredClone(state.metadata),reference:structuredClone(state.reference)};mutate(altered);
    assert.throws(()=>verifyInfluences(altered));results.push({mutation:name,status:'rejected',validation_layer:'semantic_checks_after_provenance'});
  };
  reject('omitted_empty_or_physical_carrier',s=>{delete s.metadata.boundary_states[0].force_states_after[sourceObjects(state)[0].path];});
  reject('truncated_force_history_in_reference_and_metadata',s=>{
    const row=s.reference.samples.find(r=>Object.values(r.objects).some(o=>o.forces.active.length));assert.ok(row);
    const object=Object.values(row.objects).find(o=>o.forces.active.length);object.forces.active=[];
    const boundary=s.metadata.boundary_states.find(r=>r.source_seconds===row.time_seconds);
    if(boundary)for(const [name,o] of Object.entries(row.objects))boundary.force_states_after[name]=structuredClone(o.forces);
  });
  reject('false_source_span_in_reference_and_metadata',s=>{
    for(const row of s.reference.samples)for(const object of Object.values(row.objects))
      for(const record of [...object.forces.active,...object.forces.last_changes])record.source_location.start_byte++;
    for(const row of s.metadata.boundary_states)for(const object of Object.values(row.force_states_after))
      for(const record of [...object.active,...object.last_changes])record.source_location.start_byte++;
  });
  reject('false_net_force_in_reference_and_metadata',s=>{
    for(const row of s.reference.samples)for(const object of Object.values(row.objects))object.forces.net_force_world_n[0]=12345;
    for(const row of s.metadata.boundary_states)for(const object of Object.values(row.force_states_after))object.net_force_world_n[0]=12345;
  });
  if(['P01','held-out-spin'].includes(state.oracle.fixture)) {
    const document=structuredClone(state.document),binaryData=Buffer.from(state.binary),coarse=exactBoundaries(state.oracle.specification).map(t=>Math.fround(Number(t)));
    for(const index of new Set(document.animations[0].samplers.map(s=>s.input))) {
      const accessor=document.accessors[index],view=document.bufferViews[accessor.bufferView];assert.ok(accessor.count>coarse.length);
      const offset=(view.byteOffset??0)+(accessor.byteOffset??0),stride=view.byteStride??4;
      coarse.forEach((t,i)=>binaryData.writeFloatLE(t,offset+i*stride));accessor.count=coarse.length;
    }
    assert.throws(()=>assertClock(state,document,binaryData),/spin aliases|chord exceeds/);
    results.push({mutation:'only_boundary_clock_keys',status:'rejected',actual_binary_clock_coarsened:true});
  }
  if(!state.fixture) {
    const original=sourceTokens(heldOutSource(state.oracle.specification));
    for(const [name,mutated] of [
      ['whitespace_inside_stable_key',state.payload.entry.source.replace(/scene\s+Demo\s+@\s*"demo"/,'scene Demo @ "de mo"')],
      ['split_object_identifier',state.payload.entry.source.replace(/object\s+ball\b/,'object ba ll')]]) {
      assert.notEqual(mutated,state.payload.entry.source);assert.notEqual(sourceTokens(mutated),original,'Invalid source token changes cannot disappear');
      results.push({mutation:name,status:'rejected',validation_layer:'independent_authored_source_tokens'});
    }
  }
  return results;
}

export async function verifyCase(directory) {
  const state=await loadCase(directory),format=await validator.validateBytes(new Uint8Array(state.bytes),{uri:'scene.glb',maxIssues:1000});
  assert.equal(format.issues.numErrors,0,JSON.stringify(format.issues.messages));assert.equal(format.issues.numWarnings,0,JSON.stringify(format.issues.messages));
  const gltf=await new GLTFLoader().parseAsync(state.bytes.buffer.slice(state.bytes.byteOffset,state.bytes.byteOffset+state.bytes.byteLength),'');
  const expectedObjects=sourceObjects(state);assert.equal(state.document.nodes.length,expectedObjects.length,'One source carrier per declared object');
  const objects=new Map();
  for(const object of expectedObjects) {
    const index=state.document.nodes.findIndex(n=>n.extras?.ontokin?.path===object.path);assert.ok(index>=0);
    const node=await gltf.parser.getDependency('node',index);objects.set(object.path,node);
    assert.deepEqual(state.document.nodes[index].extras.ontokin.element_id,object.element_id);
    assert.ok(!state.document.nodes[index].children?.length,'Baked world carriers have no second motion hierarchy');
    if(!object.sections)assert.ok(!('mesh' in state.document.nodes[index]),'Empty carriers retain no authored mesh');
  }
  const clockResult=assertClock(state),influences=verifyInfluences(state),geometry=state.oracle.shapes.map(s=>verifyGeometry(state,s));
  for(const shape of state.oracle.shapes) {
    const physical=state.document.nodes.find(n=>n.extras.ontokin.path===shape.path).extras.ontokin.physical;
    assert.equal(physical.mass,shape.body_mass_kg);assert.equal(physical.radius,shape.body_radius_m);
    assert.ok(Math.abs(physical.inertia/(.4*shape.body_mass_kg*shape.body_radius_m**2)-1)<1e-12);
  }
  const decodedMaterials=[];
  for(const shape of state.oracle.shapes) {
    const meshes=[];objects.get(shape.path).traverse(n=>{if(n.isMesh)meshes.push(n);});
    assert.equal(meshes.length,Object.keys(shape.materials).length);
    for(const mesh of meshes) {
      const region=mesh.userData.ontokin?.region_key??mesh.material.userData.ontokin?.source_region_key;assert.ok(region in shape.materials);
      const material=shape.materials[region];vectorError([...mesh.material.color.toArray(),mesh.material.opacity],material.rgba,1e-12,'Three.js linear PBR');
      assert.equal(mesh.material.metalness,material.metallic);assert.equal(mesh.material.roughness,material.roughness);
      decodedMaterials.push({path:shape.path,region,triangles:mesh.geometry.index.count/3,rgba:[...mesh.material.color.toArray(),mesh.material.opacity],metallic:mesh.material.metalness,roughness:mesh.material.roughness});
    }
  }
  assert.equal(gltf.animations.length,1);const mixer=new THREE.AnimationMixer(gltf.scene),action=mixer.clipAction(gltf.animations[0]);
  action.setLoop(THREE.LoopOnce,1);action.clampWhenFinished=true;action.play();
  const readPose=(object,time,label,reference)=>{
    const node=objects.get(object.path),actual={position_m:node.getWorldPosition(new THREE.Vector3()).toArray(),orientation_xyzw:node.getWorldQuaternion(new THREE.Quaternion()).toArray()};
    const independent=comparePose(actual,expectedPose(object,time),state.tolerances,label),result={...actual,independent};
    if(reference)result.evaluator=comparePose(actual,{position_m:reference.position_m,orientation_xyzw:quat(reference.orientation_wxyz).toArray()},state.tolerances,label+' evaluator');
    return result;
  };
  const seek=time=>{action.reset().play();mixer.setTime(time);gltf.scene.updateMatrixWorld(true);};
  const samples=[];
  for(const sample of state.reference.samples) {
    const time=Number(sample.time_seconds);seek(time);const poses={};
    for(const object of expectedObjects) {
      const actual=readPose(object,time,object.path+' source request at '+time,sample.objects[object.path]),landmarks=[];
      const pose=expectedPose(object,time),node=objects.get(object.path);
      node.traverse(mesh=>{if(mesh.isMesh)for(const index of [mesh.geometry.index.getX(0),mesh.geometry.index.getX(mesh.geometry.index.count-1)]) {
        const local=new THREE.Vector3().fromBufferAttribute(mesh.geometry.attributes.position,index),world=local.clone().applyMatrix4(mesh.matrixWorld);
        const wanted=local.clone().applyQuaternion(new THREE.Quaternion(...pose.orientation_xyzw)).add(new THREE.Vector3(...pose.position_m));
        const error=vectorError(world.toArray(),wanted.toArray(),state.tolerances.position_m,'Decoded world surface probe');
        landmarks.push({local_m:local.toArray(),world_m:world.toArray(),error_m:error});
      }});
      poses[object.path]={...actual,landmarks};
    }
    samples.push({time_seconds:sample.time_seconds,side:sample.side,objects:poses});
  }
  const decodedTimes=new Set(clockResult.times);
  for(let i=1;i<clockResult.times.length;i++)for(const fraction of [.25,.5,.75])decodedTimes.add(clockResult.times[i-1]+fraction*(clockResult.times[i]-clockResult.times[i-1]));
  const end=Number(state.oracle.end_seconds);
  // Prime-denominator probes are held out from both source reference and baked
  // clock schedules, including cancellation and non-axis force fixtures.
  for(let i=0;i<=257;i++)decodedTimes.add(end*i/257);
  const decodedSamples=[];
  for(const time of [...decodedTimes].sort((a,b)=>a-b)) {
    seek(time);const poses={};for(const object of expectedObjects)poses[object.path]=readPose(object,time,object.path+' independent dense at '+time);
    decodedSamples.push({time_seconds:time,objects:poses});
  }
  return {fixture:state.oracle.fixture,status:'passed',case_ids:['F11'],program_revision:state.revision,artifact_sha256:state.artifactHash,
    provenance:state.provenance,exporter_source_code_sha256:state.exportReport.source_code_sha256,source_reference_implementation:state.reference.implementation,
    khronos:{version:validator.version(),errors:format.issues.numErrors,warnings:format.issues.numWarnings,infos:format.issues.numInfos,hints:format.issues.numHints,messages:format.issues.messages},
    force_boundaries:influences,clock:clockResult.summary,adversarial_checks:rejectMutations(state),geometry,
    three_js:{version:THREE.REVISION,materials:decodedMaterials,world_pose_comparisons:samples.length*expectedObjects.length,samples,
      dense_pose_comparisons:decodedSamples.length*expectedObjects.length,dense_samples:decodedSamples,
      held_out_schedule:{prime_denominator:257,includes_all_decoded_keys:true,interior_fractions:[.25,.5,.75]}}};
}

async function verifyFailure(demoDir,record) {
  assert.ok(failureCases.includes(record.fixture));assert.equal(record.status,'expected_delivery_failure');assert.equal(record.artifact_written,false);
  assert.ok(['OKL-E-RESOURCE','OKL-E-NUMERIC'].includes(record.code));
  const directory=path.join(demoDir,record.fixture),bytes=await readFile(path.join(directory,'delivery-failure.json'));
  assert.deepEqual(json(bytes),record);await assert.rejects(()=>readFile(path.join(directory,'scene.glb')),e=>e.code==='ENOENT');
  const payload=json(await readFile(path.join(directory,'program.bundle.json'))),sources=[payload.entry,...payload.modules];
  assert.equal(sources.length,record.source_units.length);
  for(const source of sources) {
    const unit=record.source_units.find(u=>u.file===source.filename);assert.ok(unit);
    const raw=await readFile(path.join(directory,source.filename));assert.equal(raw.toString('utf8'),source.source);assert.equal(sha256(raw),unit.source_revision);
  }
  const units=[{source_id:'entry',package_id:null,version:null,filename:payload.entry.filename,source_revision:sha256(Buffer.from(payload.entry.source))},
    ...payload.modules.map(m=>({source_id:`package:${m.package_id}@${m.version}`,package_id:m.package_id,version:m.version,
      filename:m.filename,source_revision:sha256(Buffer.from(m.source))}))].sort((a,b)=>a.source_id<b.source_id?-1:a.source_id>b.source_id?1:0);
  const manifest={schema_version:'ontokin.bundle/0.1',entry_source_id:'entry',units};
  assert.equal(record.program_revision,sha256(Buffer.concat([Buffer.from('ontokin.bundle/0.1\0'),Buffer.from(stable(manifest))])));
  const fixed=cases.get(record.fixture==='P21-full-horizon'?'P21':record.fixture==='position-key-budget'?'P01':record.fixture);
  if(fixed)assert.deepEqual(units,fixed.source_units,'Negative delivery source closure is independently pinned');
  else {
    assert.equal(record.fixture,'float32-boundary-collapse');
    assert.equal(payload.entry.source,sourceBase.replace('at 1[s]','at 0.5[s]').replace('for 1[s]','for 1e-9[s]'));
    assert.deepEqual(units.filter(u=>u.source_id!=='entry'),cases.get('P01').source_units.filter(u=>u.source_id!=='entry'));
  }
  if(record.fixture==='float32-boundary-collapse')assert.equal(record.details.export_code,'OKE-E-TIMES-COLLAPSED');
  if(record.fixture==='position-key-budget')assert.equal(record.details.export_code,'OKE-E-KEYFRAME-BUDGET');
  return {fixture:record.fixture,status:'passed',diagnostic_sha256:sha256(bytes),program_revision:record.program_revision,code:record.code,details:record.details,no_artifact:true};
}

async function main() {
  const args=process.argv.slice(2);let demoDir,output,agentAudit,agentWorkflow=false;
  for(let i=0;i<args.length;i++) {
    if(args[i]==='--help'){console.log('Usage: node tools/verify_force_native.mjs --demo-dir DIR --output FILE [--agent-workflow --agent-audit FILE]');return;}
    if(args[i]==='--agent-workflow'){assert.equal(agentWorkflow,false);agentWorkflow=true;continue;}
    const option=args[i];assert.ok(['--demo-dir','--output','--agent-audit'].includes(option));assert.ok(args[i+1]);
    const value=path.resolve(args[++i]);if(option==='--demo-dir')demoDir=value;else if(option==='--output')output=value;else agentAudit=value;
  }
  assert.ok(demoDir&&output);const loaded=await loadWorkflow(demoDir,{agentWorkflow,agentAudit});
  const {bytes:workflowBytes,workflow,fixtures}=loaded;
  if(!agentWorkflow) {
    assert.equal(workflow.complete_component_corpus,true);assert.deepEqual(fixtures.map(f=>f.fixture),deliveryCases);
    assert.deepEqual(workflow.delivery_failures.map(f=>f.fixture),failureCases);
  }
  const tooling=json(await readFile(path.join(root,'tools/package.json')));assert.equal(validator.version(),tooling.devDependencies['gltf-validator']);
  assert.equal(json(await readFile(path.join(root,'tools/node_modules/three/package.json'))).version,tooling.devDependencies.three);
  const results=[],report={schema_version:agentWorkflow?'ontokin.force-delivery-destination-validation/0.1':'ontokin.force-destination-validation/0.1',status:'running',generated_at_utc:new Date().toISOString(),
    implementation:workflow.implementation,git_identity:loaded.gitIdentity,workflow_sha256:sha256(workflowBytes),acceptance_manifest_sha256:sha256(acceptanceBytes),fixture_inputs:fixtureInputs,
    workflow_schema_version:workflow.schema_version,source_kind:loaded.sourceKind,agent_audit_sha256:loaded.agentAuditHash,
    verifier_sha256:sha256(await readFile(fileURLToPath(import.meta.url))),surface_verifier_sha256:sha256(await readFile(path.join(root,'tools/verify_surface_native.mjs'))),
    tooling_lock_sha256:sha256(await readFile(path.join(root,'tools/package-lock.json'))),
    environment:{node:process.version,platform:process.platform,architecture:process.arch,three:tooling.devDependencies.three,khronos_gltf_validator:validator.version()},
    fixtures:results,delivery_failures:[],source_repairs:[],limits:[
      agentWorkflow?'These are the exact GLBs reconstructed from the independently audited Agent artifact chunks; no second export was performed.':
        'This component validates the complete predetermined force destination corpus; Agent request/delivery/repair transport is recorded separately.',
      'Independent analytic motion, every actual binary32 key and three interval probes plus held-out dense samples cover these finite artifacts, not all programs or continuous times.',
      'GLB stores recorded transforms and metadata; live forces, torques, contacts, Blender, external engines and authoring-productivity benchmarks were not executed.',
      'Screenshots require separate identified human/agent visual review. Complete F01-F12, inherited regression, compatibility and provenance remain separate gates.']};
  try {
    for(const item of fixtures) {
      const result=await verifyCase(path.join(demoDir,item.directory));assert.equal(result.program_revision,item.program_revision);assert.equal(result.artifact_sha256,item.artifact_sha256);
      assert.equal('sha256:'+result.exporter_source_code_sha256,workflow.implementation.source_code_sha256);
      assert.deepEqual(result.source_reference_implementation,workflow.implementation);results.push(result);
    }
    if(!agentWorkflow)for(const item of workflow.delivery_failures)report.delivery_failures.push(await verifyFailure(demoDir,item));
    const baseline=results.find(r=>r.fixture==='P10'),sibling='rack.props["second"]',target='rack.props["first"]';
    const baselineState=await loadCase(path.join(demoDir,fixtures.find(f=>f.fixture==='P10').directory));
    for(const fixture of ['P11','P12','P13']) {
      const changed=results.find(r=>r.fixture===fixture);assert.notEqual(changed.program_revision,baseline.program_revision);
      const changedState=await loadCase(path.join(demoDir,fixtures.find(f=>f.fixture===fixture).directory));
      assert.deepEqual(changedState.payload.modules,baselineState.payload.modules,'A scoped physical edit changed its pinned libraries');
      for(const original of baseline.geometry) {
        const edited=changed.geometry.find(g=>g.path===original.path);assert.equal(edited.positions_sha256,original.positions_sha256);
        assert.equal(edited.topology_sha256,original.topology_sha256);assert.deepEqual(edited.regions,original.regions);
      }
      const comparisonBounds={position_m:baselineState.tolerances.position_m+changedState.tolerances.position_m,
        rotation_rad:baselineState.tolerances.rotation_rad+changedState.tolerances.rotation_rad};
      let common=0,maximumPositionDifference=0,maximumRotationDifference=0;
      for(const sample of baseline.three_js.samples) {
        const other=changed.three_js.samples.find(s=>s.time_seconds===sample.time_seconds&&s.side===sample.side);if(!other)continue;
        const originalSource=baselineState.reference.samples.find(s=>s.time_seconds===sample.time_seconds&&s.side===sample.side).objects[sibling];
        const editedSource=changedState.reference.samples.find(s=>s.time_seconds===sample.time_seconds&&s.side===sample.side).objects[sibling];
        for(const key of ['position_m','orientation_wxyz','velocity_m_per_s','angular_velocity_rad_per_s','own_mass_kg'])
          assert.deepEqual(editedSource[key],originalSource[key],'Scoped repair changed exact sibling source '+key);
        // Both decoded poses already passed their own unchanged source bound.
        // A target edit may refine the shared clock and alter interpolation
        // of the unchanged sibling; its cross-artifact bound is their sum.
        const difference=comparePose(other.objects[sibling],sample.objects[sibling],comparisonBounds,'Scoped repair recorded sibling');
        maximumPositionDifference=Math.max(maximumPositionDifference,difference.position_error_m);
        maximumRotationDifference=Math.max(maximumRotationDifference,difference.rotation_error_rad);common++;
      }
      assert.ok(common>=20);const at=result=>result.three_js.samples.find(s=>s.time_seconds==='3'&&s.side==='after').objects[target];
      const distance=new THREE.Vector3(...at(changed).position_m).distanceTo(new THREE.Vector3(...at(baseline).position_m));assert.ok(distance>.1);
      report.source_repairs.push({before_fixture:'P10',after_fixture:fixture,status:'passed',target_path:target,sibling_path:sibling,
        geometry_and_pbr_unchanged:true,pinned_libraries_unchanged:true,sibling_source_state_exactly_unchanged:true,
        sibling_pose_comparisons:common,target_final_translation_change_m:distance,
        sibling_recorded_maximum_position_difference_m:maximumPositionDifference,sibling_recorded_maximum_rotation_difference_rad:maximumRotationDifference,
        sibling_cross_artifact_bounds:comparisonBounds,baseline_key_count:baseline.clock.key_count,edited_key_count:changed.clock.key_count});
    }
    report.status='passed';
  } catch(error){report.status='failed';report.failure={name:error.name,message:error.message};throw error;}
  finally{await mkdir(path.dirname(output),{recursive:true});await writeFile(output,JSON.stringify(report)+'\n');}
  console.log(JSON.stringify({status:report.status,fixtures:results.length,expected_delivery_failures:report.delivery_failures.length,
    world_pose_comparisons:results.reduce((n,r)=>n+r.three_js.world_pose_comparisons,0),dense_pose_comparisons:results.reduce((n,r)=>n+r.three_js.dense_pose_comparisons,0),output},null,2));
}

if(process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url)await main();
