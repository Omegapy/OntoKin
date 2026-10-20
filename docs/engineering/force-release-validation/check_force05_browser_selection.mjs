import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import vm from 'node:vm';
import {createHash} from 'node:crypto';
import {deliveryCases,agentDeliveryCases} from './OntoKin/tools/verify_force_native.mjs';

const source=await readFile(new URL('./OntoKin/tools/verify_force_viewer.mjs',import.meta.url),'utf8');
const start=source.indexOf('const args=process.argv.slice(2),fixtureNames=[];');
const end=source.indexOf('await mkdir(outputDir,{recursive:true});');
assert.ok(start>=0&&end>start);
const program=source.slice(start,end)+'\nJSON.stringify({fixtures:fixtureNames,complete:completeBrowserCorpus});';
const required=['P02','P07','P09','P10','P11','P12','P13','held-out-oblique','held-out-spin'];
function select(names,agent=false){
 const argv=['node','selection-check','--demo-dir','/unopened-input','--output-dir','/unwritten-output'];
 if(agent)argv.push('--agent-workflow');
 if(names)for(const n of names)argv.push('--fixture',n);
 return JSON.parse(vm.runInNewContext(program,{process:{argv},assert,path,deliveryCases,agentDeliveryCases}));
}
const checks=[];
for(const [id,names,agent,expected] of [
 ['default-source-required-nine',null,false,true],
 ['explicit-source-required-nine',required,false,true],
 ['source-partial-eight',required.slice(0,-1),false,false],
 ['same-count-wrong-source-case',['P01',...required.slice(1)],false,false],
 ['default-agent-required-seven',null,true,true],
 ['agent-partial-six',agentDeliveryCases.slice(0,-1),true,false],
 ['all-source-exports-are-a-different-selection',deliveryCases,false,false],
]){
 const result=select(names,agent);assert.equal(result.complete,expected,id);
 if(id==='default-source-required-nine')assert.deepEqual(result.fixtures,required);
 if(id==='default-agent-required-seven')assert.deepEqual(result.fixtures,agentDeliveryCases);
 checks.push({id,status:'passed',selected_fixtures:result.fixtures,complete_browser_corpus:result.complete});
}
for(const [id,names] of [['duplicate-source-case',['P02','P02']],['unknown-source-case',['unknown']]]){
 assert.throws(()=>select(names));checks.push({id,status:'passed',rejected:true});
}
const result={schema_version:'ontokin.browser-selection-preflight/0.1',status:'passed',
 generated_at_utc:new Date().toISOString(),node:process.version,
 verifier_sha256:'sha256:'+createHash('sha256').update(source).digest('hex'),
 scope:'Executes the actual browser verifier argument/selection prefix in a VM; no Agent store, GLB load or browser is opened.',
 release_certified:false,checks};
await writeFile(new URL('./force05-browser-selection-preflight.json',import.meta.url),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(result));
