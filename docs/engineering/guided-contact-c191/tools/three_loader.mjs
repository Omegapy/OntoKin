import {pathToFileURL} from 'node:url';
import {resolve as resolvePath, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolvePath(dirname(fileURLToPath(import.meta.url)),'../indexer-view/three');
export async function resolve(specifier,context,nextResolve) {
  const names={'three':'build/three.webgpu.js','three/webgpu':'build/three.webgpu.js','three/tsl':'build/three.tsl.js'};
  if(names[specifier])return {url:pathToFileURL(resolvePath(root,names[specifier])).href,shortCircuit:true};
  return nextResolve(specifier,context);
}
