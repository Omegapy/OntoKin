const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const [moduleDir, kitPath, listPath, destination] = process.argv.slice(2);
const validator = require(path.resolve(moduleDir));
async function main() {
  const root = path.resolve(kitPath);
  const files = JSON.parse(fs.readFileSync(listPath, 'utf8'));
  const receipts = {};
  for (const name of files) {
    const bytes = fs.readFileSync(path.join(root, name));
    const report = await validator.validateBytes(new Uint8Array(bytes), {uri:name, writeTimestamp:false});
    receipts[name] = {sha256:crypto.createHash('sha256').update(bytes).digest('hex'), report};
    if (report.issues.numErrors || report.issues.numWarnings) process.exitCode = 1;
  }
  fs.writeFileSync(destination, JSON.stringify(receipts, null, 2) + '\n');
  console.log(JSON.stringify({files:files.length, issues:Object.fromEntries(Object.entries(receipts).map(([k,v])=>[k,v.report.issues]))}));
}
main().catch(error=>{console.error(error);process.exitCode=1});
