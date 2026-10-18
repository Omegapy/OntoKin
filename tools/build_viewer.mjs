// Rebuild the checked-in offline viewer after editing examples/visual/viewer.js.
import {build} from 'esbuild';
import {copyFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const directory = path.resolve(here, '../examples/visual');
await build({entryPoints: [path.join(directory, 'viewer.js')], outfile: path.join(directory, 'viewer.bundle.js'),
  bundle: true, minify: true, format: 'iife', target: ['es2020'], legalComments: 'inline',
  nodePaths: [path.join(here, 'node_modules')]});
await copyFile(path.join(here, 'node_modules/three/LICENSE'), path.join(directory, 'THREE-LICENSE.txt'));
console.log('Built the offline Three.js viewer.');
