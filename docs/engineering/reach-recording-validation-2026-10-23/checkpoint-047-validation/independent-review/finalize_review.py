#!/usr/bin/env python3
"""Write the independent review, exact output manifest, and last window-closure record."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
B=Path('/workspace/scratch/f34f66f87e3e');O=B/'c047-final-review'
def j(name):return json.loads((O/name).read_text())
def d(path):
    data=path.read_bytes();return {'path':str(path.relative_to(O)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
r=j('result.json');c=j('command.json');s=j('source-bindings.json')
assert r['status']=='passed' and r['checks_passed']==r['checks_total']==62 and c['exit_code']==0
assert j('owned-ref-at-close.json')['object']['sha']==r['core_commit']
assert (O/'inputs-before.json').read_bytes()==(O/'inputs-after.json').read_bytes()
review='''INDEPENDENT C047 PUBLISHED-CORE REVIEW

Disposition: passed for the exact published core and bounded claims reviewed below.
There are no unresolved findings concerning this core's publication identity,
source preservation, evidence package, or current source/cache-lifetime claim.
This review does not cover a later containing validation-appendix commit.

CORE AND ACTUAL REVIEW EXECUTION

Published core: 7d2c118f5cc5ca141f2092b68d02b23fd933b571
Published tree: 219ceb20170a5dc3393bc9e7383b374193ce6c02
Executed pair parent: 48b5d381a0f86d9706a109b78e2ce52eb0d287f0
Executed pair parent tree: 33ac0caa77528432d18132a1e606d1e4fbd7ab80
Review window: Issue #26 comment 6428329816, active after 21:59:10Z on
2026-10-26, expiry 22:19:09Z. The root and the other reviewers remained paused.

The new independent audit passed 62 aggregate metadata/source/data checks.
Its actual process ran 22:05:23.292668Z through 22:05:28.812527Z, exited 0,
and produced an empty stderr. CPython 3.12.14 and the precise executable,
platform, process duration, script hashes, and raw stream hashes are retained
in command.json. All 3,048 declared inputs, totaling 711,675,411 bytes,
were byte-identical before and after. The input manifests include every
current tracked source file, retained original evidence and review files,
publication and validation records, fresh remote metadata, and audit code.
These 62 checks are metadata assertions and source-review support, not new
runtime tests. No product module or archived review script was imported or
run. No product request, original pair, test suite, or archive extraction was
executed in this window. Only this final-review directory was written.

PUBLICATION AND COMPLETE SOURCE PRESERVATION

Fresh independent GitHub reads of the owned ref, commit, and untruncated
recursive tree identify the core above. Another fresh ref read at closure
still identifies the same core. The actual 314-byte raw commit object hashes
to that commit and names exactly the C046 parent and current tree; no
synthetic commit is substituted. Local HEAD, the index, complete tree, and
working tree are unchanged and clean.

All 2,596 tracked files and 524,662,681 bytes match the fresh remote blob
identities, file modes, and lengths. The full tree was independently rebuilt
from the file identities and matches 219ceb20170a5dc3393bc9e7383b374193ce6c02.
Every one of the 2,556 parent files is preserved with its exact blob, mode,
and size. The only 40 additions total 15,983,134 bytes, all beneath the
checkpoint documentation/evidence directory, and match the publication plan.
All 65 ontokin Python runtime modules match the held C035 tree
87c949b238055af1ce368c694e1d5683c8aeacde. No runtime change is present.

The root's retained immutable GitHub byte-readback record covers all 40
additions and agrees with their independently checked local hashes and
fresh remote Git blob identities. This reviewer freshly fetched Git metadata;
the separate full remote-byte downloads were performed by the root and are
bound here through their exact receipts and the published immutable tree.
The root's earlier normalized-text/JSON readback preparation failure remains
disclosed and retained; it does not invalidate the later successful readback.

ARCHIVE, REVIEWS, AND ACTUAL VALIDATION

All 18 archive parts match the checkpoint's exact hashes and sizes. Their
joined ZIP is 15,483,218 bytes with SHA256
ee15945c4377c6dc86b22587fe239d4846bdeacda08cefd882ae773736681137.
The archive contains exactly 414 unique safe members totaling 167,310,502
uncompressed bytes. Every member was read with its ZIP CRC checked, and its
mode, length, SHA256, and exact bytes were compared to the published member
manifest and the retained original file. Nothing was extracted. There are
no missing, duplicate, unexpected, changed, or corrupt members. All 14
direct lifetime-review copies agree with both archive and original bytes.
Every review-index entry is bound by its exact member hash. The member
manifest SHA256 is bff175cc43e11ccfedba16db7a51f6ee3ab237fc145bb3116da54ddc64b80351.
The packaging and prior extraction receipts describe these same bytes.

The root's actual 53-check core metadata validation passed inside its declared
window and retains an exact complete 2,596-file before/after inventory equal
to the files checked here. Its unchanged documentation checker exited 0;
raw stdout and stderr match the command receipt. The actual result verifies
29 sources, 233 sections, 208 documents, 1,671 local links, and 92 anchors,
with no failures. This audit verified those execution records and source
bindings rather than executing the documentation checker again.

ORIGINAL FAILED-PAIR EVIDENCE BINDING

The earlier independent pair audit's exact 61,593-assertion result remains
unchanged, SHA256 65517f6fe4a5ea7f45a1da4bb12dcb8c7035e68261c7856984142ed913666aab.
Its original script, raw successful streams, command receipt, stable
2,901-input inventories, and preserved failed first attempt are all bound.
The original pair's complete evidence is byte-identical in the archive and
the retained directories. Those 61,593 assertions were not repeated here.

Both actual commands completed with the expected product exit 1 under the
original C046 commit/tree, inside the original pair window. The two complete
work maps, diagnostics, options, program identities, and underlying 27
file/function/line traceback frames were already compared in that bound
review. Only the two specifically approved wrapper frames at the exact
external driver path were removed from that comparison. Shared operations
remain 100,001 and reach operations 95,767 across 288 work categories.

The unchanged capture records 154 key calls: 153 provisional returns and the
current exception at key 153. All 311 ordered snapshots, the full key ledger,
failure locals, and unvalidated GLB are still bound by exact hashes and bytes.
The bound earlier audit includes all per-key and outer identity checks,
snapshot membership and JSON bounds, clock/cursor/failure-prefix consistency,
and empty observation errors. The new audit independently rechecked the
complete key prefix, original options and program identity, fixed native
domain, coefficient births, surviving centered cursors, and current failure.
The GLB remains unvalidated reader input, not an accepted product artifact.

Measured request times remain 2.175590550999914 seconds for stock and
5.610394618997816 seconds for capture. Whole-process times remain
4.428695784998126 and 16.815537924001546 seconds. Capture pre-imports and
observation work differ. These measurements are neither an elapsed-neutrality
result nor a benchmark. The 30,000 ms elapsed allowance was unchanged; this
pair refused at the shared operation limit. No general observation-neutrality
claim follows from matching this one refusal route.

INDEPENDENT REVIEW OF THE BOUNDED CACHE-LIFETIME REASONING

The source-bound interval starts at current key 0 entry and ends at key 153's
exception snapshot before outer source-batch cleanup. The earlier C046
interval is not substituted. The new source-bindings.json identifies 34
reviewed function bodies across six unchanged source files, with their line
bounds and exact file/body hashes. Human control-flow review supplements
the compact text/AST assertions; those assertions are not a formal verifier.

Reader mutations are closed by the native arithmetic lookup/remember and
Cartesian path, centered guard lookup/remember, pending-cursor publication,
operand-domain clear, batch discard, and C035 product publication. Existing
lookup promotion deletes then reinserts without an intervening callback;
replacement preserves size; a new insertion grows below capacity and replaces
one entry at capacity. C035 _ProductSession.publish requires that the exact
previous object is still resident after its checked work before assigning the
expanded value. It therefore preserves size and order and cannot restore an
evicted slot. Its close operation restores the session observer and closes
the session; it does not delete reader-cache entries.

The only size-reducing paths relevant to this native reader are an operand
domain clear and effectful batch discard. All 311 snapshots and current
failure locals preserve bits=128, scale=2^128, cache operand limit=32768 and
work operand limit=32768. The original native ConstructionBudget callback,
source guards, wrapper authority checks, and absence of custom/reentrant or
trace/profile paths support a fixed domain within each key, not merely at
its boundaries. Source review found no intervening native domain mutation.

Key 0 starts with no registered plan or batch-owned cursor. Its exit contains
one complete eight-node, six-target plan whose centered_recipe_fields value
is exactly False. _phase_poses returns before centered evaluate when the
recipe is not a tuple; ordinary fallback can register that rejected recipe
but cannot construct a native centered cursor. There is only one centered
attempt in _key_comparisons. This rules out an earlier effectful centered
discard in key 0. Each later key exit retains owned centered cursors with
the observed continuing histories. A centered rejection's discard removes
all still-owned resident values, and the subsequent ordinary fallback cannot
recreate a centered cursor or centered stationary value. The ordinary
completed-request ledger cleanup leaves unchanged still-resident older
owned values owned. The surviving cursor histories therefore exclude an
effectful discard in those keys. Inter-key certificate work does not provide
a centered discard/recreation route. The captured consecutive index sequence
excludes a replay/restart of this interval. Outer __exit__ cleanup is later
than the retained failure snapshot and is expressly outside the proof.

With those reducing paths excluded, completed reader mutations are
nondecreasing until capacity 256, then size-preserving at 256. A capacity
eviction would consequently force the final pre-cleanup size to be 256.
The observed final size is 165, following 112 at key 0 entry. Thus no capacity
eviction occurred within this bounded interval. This reasoning uses source
control flow plus retained data; the boundary sizes alone are insufficient.
The failed coefficient key is absent initially and in every one of the 311
snapshots. With no removal route in the interval, it was not previously
completed/published and then evicted there. Protecting an allegedly evicted
instance of that failed key is unsupported for this interval.

Seven coefficient keys are present initially. Exactly five new keys appear:
(exponent=129, degree=7) and (129,8) at key 1 exit, time 2/87;
(129,13) and (129,17) at key 66 exit, time 44/29;
(129,16) at key 88 exit, time 179/89.
Each uses the unchanged operand-limit component 32768. No coefficient key
disappears at a retained boundary; the final set contains 12 keys. This is
a source/data key census and does not infer exact lookup-hit counts or
numerical coefficient payload equality from object IDs or bit widths.

The current failure remains key 153, clock 244/89, previous clock 243/89,
rig.arm.forearm.frame. Its previous centered cursor has 64 steps; advance
is false and the new local steps variable is 0. The miss is exactly
('series_coefficients',32768,129,14), cached=None. Construction has reached
index 7, odd 15, with seven completed coefficient elements. The leading
_series_integer tick refuses before the pending common/factorials[15]
division executes. The upper replacement is pending, the forearm replacement
has not completed, and published entry/exit cursors remain equal. This is
current evidence, not a borrowed historical failure or inferred successful
tail. No solver or helper was invoked to produce this review.

SCOPE AND OPEN GATES

The core correctly retains the original 24/28 source-suite result, four
unresolved cases including L03, held C035 including its adverse prior timing,
zero newly passed product requests, and no accepted artifact or selected
runtime candidate. The full R01-R12/Q01-Q22, complete source/agent artifact,
rate/native/browser/visual/hostile/inherited, Python 3.11/3.12/3.13, formal
closure, and resulting-main gates remain open as described in the core.
This review does not authorize a changed coefficient algorithm, an increased
capacity or retirement bound, a fixture-specific exception, a new product
replay, an elapsed benefit, numerical acceptance, or release acceptance.
The final appendix is absent from the audited tree and must bind this review
to the containing publication separately.

INDEPENDENCE AND PRESERVED AUDIT FAILURES

This reviewer earlier acquired/hash-verified the C046 source and independently
audited the original C047 pair. It did not author the capture driver, pair
runner, lifetime review, published prose, or core publication. This final
audit is new code and a new control-flow/data/publication review. The earlier
pair audit's off-by-one second-phase clock formula failure remains retained
in its own evidence and has not been erased or reclassified as product work.

Two unsuccessful attempts of this final audit are also retained in full:
attempt-001 resolved audit.stdout against the workspace instead of the prior
audit directory and stopped with FileNotFoundError before its final inventory.
attempt-002 requested the nonexistent ReachExecutionWork.checkpoint symbol;
its other 61 checks passed, and all 3,048 inputs were stable. The corrected
inventory binds actual charge and tick functions. Both failures were reviewer
code/schema assumptions, not source/product/evidence failures. Their exact
scripts, process receipts, raw streams, and available input/results are in
attempt-001 and attempt-002. The final successful attempt has empty stderr,
all checks passed, and complete stable input inventories.

KEY OUTPUT BINDINGS

'''
for name in ['audit_core.py','run_audit.py','result.json','command.json','audit.stdout','audit.stderr','inputs-before.json','inputs-after.json','source-bindings.json','core-file-bindings.json','owned-ref.json','owned-ref-at-close.json','remote-core-commit.json','remote-core-tree.json','window.json']:
    row=d(O/name);review+=row['path']+' | '+str(row['bytes'])+' bytes | SHA256 '+row['sha256']+'\n'
(O/'review.txt').write_text(review)
rows=[d(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name not in ['manifest.json','window-closure.json']]
manifest={'schema':'ontokin.c047-independent-final-review-manifest/0.1','core_commit':r['core_commit'],'core_tree':r['core_tree'],'created_utc':datetime.now(timezone.utc).isoformat(),'files':rows,'file_count':len(rows),'bytes':sum(x['bytes'] for x in rows),'excluded':['manifest.json (self)','window-closure.json (written last)'],'retained_failed_attempts':['attempt-001','attempt-002'],'final_appendix_covered':False}
(O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
summary={'status':'passed','checks':62,'review':d(O/'review.txt'),'result':d(O/'result.json'),'manifest':d(O/'manifest.json'),'manifest_files':len(rows),'manifest_bytes':sum(x['bytes'] for x in rows),'input_files':r['input_files'],'inputs_stable':r['inputs_stable']}
closure={'schema':'ontokin.c047-independent-final-review-window-closure/0.1','window_comment_id':6428329816,'closed_utc':datetime.now(timezone.utc).isoformat(),'expires_utc':'2026-10-26T22:19:09Z','status':'complete; paused after this final writer exits','core_commit':r['core_commit'],'core_tree':r['core_tree'],'result':summary['result'],'review':summary['review'],'manifest':summary['manifest'],'next_action':'Root may resume only after reviewer reports this process has exited; reviewer will issue no further commands or writes without a new explicit window.'}
(O/'window-closure.json').write_text(json.dumps(closure,indent=2)+'\n')
summary['closure']=closure['closed_utc'];summary['closure_record']=d(O/'window-closure.json')
print(json.dumps(summary,indent=2))
