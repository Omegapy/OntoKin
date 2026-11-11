"""C208 read-only historical input preservation; does not execute old cohorts."""
import argparse, datetime, hashlib, json, pathlib, subprocess
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--repo',type=pathlib.Path,required=True)
p.add_argument('--baseline',type=pathlib.Path,required=True)
p.add_argument('--out',type=pathlib.Path,required=True)
a=p.parse_args();repo=a.repo.resolve();base=a.baseline.resolve();a.out.mkdir(parents=True,exist_ok=True)
def git(root,*args):
    return subprocess.run(['git','--no-optional-locks','-C',str(root),*args],capture_output=True,text=True,check=True).stdout.strip()
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
receipt='docs/engineering/static-tray-admission-c201/evidence/transaction-c206/c206-validation/candidate-protected-inputs.json'
old=json.loads((base/receipt).read_bytes())
def compare(rows):
    results=[]
    for r in rows:
        f=repo/r['path'];actual=digest(f) if f.is_file() else None;size=f.stat().st_size if f.is_file() else None
        results.append({'path':r['path'],'expectedSha256':r['sha256'],'actualSha256':actual,
                        'expectedSizeBytes':r['size_bytes'],'actualSizeBytes':size,'match':actual==r['sha256'] and size==r['size_bytes']})
    return results
prefixes=['prototypes/static_tray_v01','tools/static_tray_reader_v01','fixtures/static_tray_v01',
          'docs/engineering/static-tray-mapping-c198','docs/engineering/static-tray-qualification-c199',
          'docs/engineering/static-tray-exporter-c200']
historical_paths=git(base,'ls-tree','-r','--name-only','HEAD','--',*prefixes).splitlines()
locked=compare(old['lockedInputs']);protocol=compare(old['protocolDocuments'])
historical=compare([{'path':f,'sha256':digest(base/f),'size_bytes':(base/f).stat().st_size} for f in historical_paths])
head=git(repo,'rev-parse','HEAD');basehead=git(base,'rev-parse','HEAD')
historical_diff=git(repo,'diff','--name-status',basehead,'--',*prefixes)
historical_untracked=git(repo,'ls-files','--others','--exclude-standard','--',*prefixes)
shared_diff=git(repo,'diff','--name-status',basehead,'--','ontokin','conformance','grammar','schemas','.github','tools')
record={'schema':'ontokin.c208.independent-preservation/0.1','observedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'commit':head,'tree':git(repo,'rev-parse','HEAD^{tree}'),'baselineCommit':basehead,'baselineTree':git(base,'rev-parse','HEAD^{tree}'),
 'inheritedBindingReceipt':receipt,'inheritedBindingReceiptSha256':digest(base/receipt),'lockedInputs':locked,'protocolDocuments':protocol,
 'historicalFiles':historical,'historicalDiff':historical_diff,'historicalUntracked':historical_untracked,'sharedRuntimeWorkflowDiff':shared_diff,
 'candidateDifference':git(repo,'diff','--name-status',basehead),'nativeStarts':0,'historicalCohortRuns':0}
record['passed']=all(v['match'] for v in locked+protocol+historical) and not historical_diff and not historical_untracked and not shared_diff and basehead=='60460e8eb7526f88c0cce9028ef077ca1c1d16d0'
(a.out/'PRESERVATION.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'commit':head,'lockedInputs':len(locked),'protocolDocuments':len(protocol),'historicalFiles':len(historical),'passed':record['passed']}))
raise SystemExit(0 if record['passed'] else 1)
