# Independent C271 P07 design review

## Verdict

**ACCEPT_P07_DESIGN_ONLY.** Candidate `review-candidate-002` is concrete and compatible enough for the next bounded host-inspection implementation phase. No mandatory finding remains open. This accepts a design and staged plan, not an implemented inspector, eligible host or executed qualification.

The exact accepted candidate is `audit/host-design/review-candidate-002/MANIFEST.json`, SHA-256 `ad48e321ee9163f9f87c675c291f566e28b961b55696976f738b04e165845f2a`. Its nine payloads total **202,038 bytes**. The initial candidate remains unchanged at manifest SHA-256 `509d97fc3c85c82e210ee2fa084cc772ca8deaddffcffecb1340ce24753ddbb5`.

Reviewer: `/root/intake_review`, independently assigned by `/root`. The review began after the confirmed P07 early recovery recorded in `audit/delivery/EARLY-RECOVERY-RECEIPT.json`. Governing instructions were carried forward and their unchanged bytes checked. The full P05 contract/adoption and P06 schema/operations were read; relevant provider, JavaScript probe, supervisor, preparer and driver code was inspected as source. No project module was imported and no project checker/test, runtime preparer, Node, ldd, full routine, native/model trial or hosted CI was run.

## Finding and resolution

Candidate-001 had one mandatory finding, **P07-R01**. Its new sidecar restricted `actual_direct_starts` to zero or one, although interruption between `Popen` and the durable start callback can leave the true count unknown. An intent without a recorded start is not evidence that no child ran. This mattered because a false zero could conceal a started but unresolved attempt.

Candidate-002 separates the exact actual count (`0`, `1`, or `null`) from the observed lower bound and adds `PROVEN_ZERO`, `OBSERVED_ONE` and `UNKNOWN` states. Zero requires a completed refusal before entering the launch boundary; one requires retained actual PID/start or final process evidence. An interrupted window keeps the exact count null, aggregate unknown counts remain null, and success or automatic retry is forbidden. The design, human/machine plans, compatibility record and HI14/HI18/HI19 controls all carry this correction. The initial candidate and author response remain retained. Affected re-review passed.

`REVIEW-001.json` preserves the original mandatory finding. `REVIEW-002.json` records its resolution and final scope-only verdict. Preliminary criteria in `PRELIMINARY-REVIEW-NOTES.md` are explicitly separate from both verdicts.

## Evidence supporting acceptance

Thirteen independent static check groups passed. Both immutable candidate manifests match their exact inventories, payload sizes and hashes. All **34 source references** match the current inspected bytes, file modes and immutable Git blobs at their declared revisions. The technical baseline is `3d9d5eacaff25244916f99912ef92947e1582592`; the P07 requirement reference uses the Director's documentation checkpoint `f980ad31eb2af9d7e8b1b233b84e21ee662730fd`.

The machine plan's eleven copied P06 structure definitions match the adopted schema exactly. Plan descriptors match the final control matrix and source-binding bytes. All **21 P05 control rows** preserve their adopted requirements, mutations, expected outcomes and counts. All **three deferred P06 host rows** preserve their frozen expectations and `NOT_RUN_GATE_H` status. The matrix contains 44 distinct IDs, including twenty new authoring controls; none is claimed as executed.

All **seven original method IDs** and **nine method/helper AST bodies** remain exact. The scientific JavaScript suffix is byte-identical to the historical probe. The design preserves all **24 retained dependency identities**, the selected runtime/archive pins and original source/CPU resource limits. These checks establish source preservation only. They do not establish JavaScript syntax, runtime behavior, numerical correctness or host qualification.

Full machine-readable evidence is in `STATIC-CHECKS.json`, with the independent standard-library checker in `review_static.py`. `READ-SET.json` and `P06-CONSUMER-MATRIX.json` identify inspected sources and consumer constraints. A bounded read of the frozen P05 dependency-map member supported the module-loader control-flow claim; no predecessor restoration or historical behavioral audit was repeated.

## Operational assessment

The pre-HOST inspection plan avoids the existing provider's circular bootstrap: P06 validation already requires successful HOST observations. An independent reviewer instead accepts exact static plan bytes, and a separately selected invocation supplies their digest. Host observations cannot approve their own inputs or the later P06 configuration.

The proposed module and focused test live under the existing source inventories. Its rooted import of the already bound `rename_without_replacement` helper is concrete and does not invoke that tool's CLI. Existing P05/P06 consumers, schemas and protected source need no edit for this design.

The design preserves the exact successful P06 HOST, inspection, process and cleanup shapes. Failures, no-start refusals, unknown counts, provenance and publication history are separate records. It chooses the stricter intersection of Python and JavaScript consumer requirements, including real platform/boot and package identities, exact role/alias/file sets, fixed command vectors and complete ldd-output parsing.

The actual inspector and dynamic-loader inputs must be independently selected before execution. The finite static resolution map covers the admitted interpreter/script/library/search/alias/absence inputs and refuses unsupported semantics. Two supervised preparation launches are distinguished from ldd descendants and later checker starts. The unchanged supervisor's 5,000-ms total inspection clock contains the 2,000-ms cleanup reserve; it is not extended to seven seconds. The design acknowledges its host/kernel trust boundary and does not claim to authenticate an entire operating system or defeat every concurrent mutation.

Evidence publication has an explicit no-replace and durability sequence. A missing or lost raw supervisor final record cannot be synthesized into success. Unauthenticated plans cannot authorize filesystem output destinations; the separately selected outer harness retains such refusals. Actual inability to preserve failure evidence remains failed/unknown.

H01/H02 future negative controls reach specific source guards with the intended external comparator relationships. Their lack of reader imports is explicitly a source-backed execution-path inference requiring actual refusal evidence and the bound loader, not a claim of OS-wide import tracing. H03 still requires the three actual CPU outcomes and four original mocked coordinator outcomes, including the intended negative discrepancy and independent numerical audit.

## Remaining gates and limits

The future runtime fields are intentionally unavailable in this **nonexecutable design freeze**. Actual implementation/source identities, host/loader resolution, installations, receipts, configuration digest, fixtures and observational collectors must be supplied and independently reviewed at the declared later checkpoints. Their absence does not authorize fallback behavior.

The staged plan keeps HI, H0, H1, H2, H3, Gate R, R04 and R05 separate. Gate R still requires actual complete discovery, every selected driver stage, per-method outcome reconciliation and independent R03 acceptance; aggregate footer counts cannot substitute. The proposed outer timeout needs its own later justification and does not change source/CPU limits.

The Director's next action in this phase is canonical P07 finalization, reviewable publication and verified saved partial delivery, then stop. The first remaining technical gate belongs to a fresh phase: implement only the accepted inspector module and focused controls, bind the exact candidate and obtain independent implementation review, stopping before runtime preparation or Node/ldd.

C271 remains open. This reviewer performed no integration, publication or save. No active worker, child process, uncertain write or audit operation remains. Availability is limited to a separately assigned affected re-review or final package review.
