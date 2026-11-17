# Independent C256 reader review

**Approved for the selected finite geometry and sampled-transform component** at commit `97e8942071502044cb3baedac71622c151e52283`, tree `db5b4a557c119dfdde4f2b690f5750c4274a366a`. Reader SHA-256: `5993d1a9ca1cbccd4518ed6f113238d18f6b71ba02befd59900b93fe47ef6e6a`.

## Verified evidence

The reviewer independently decoded both original GLBs using standard-library bytes, struct and math without importing the candidate, OntoKin parser/model/exporter or C255 oracle. All 18 source occurrence identities and separate definition identities match the pinned raw declarations. Actual POSITION/index arrays and 126 poses per artifact match the C253 source equations within unchanged delivery tolerances. Maximum observed errors are 4.77e-8 m position, 3.65e-8 rad orientation and 2.39e-8 m mesh coordinate/radius.

The final candidate passes **95 independent controls**. These include complete baseline arrays and origin resolution; 58 invalid or unsupported structural mutations; malformed shape and identity cases; actual changed POSITION, translation, quaternion and time bytes; metadata-only changes; quaternion sign equivalence; relocated/strided vertices; coordinated source-map corruption; wrong source closure; strict historical binding; and import independence. Every reported buffer offset, element width/stride, content hash, channel, sample index, stored time and raw sample was independently resolved against actual baseline artifact bytes. Matrix consistency uses an independent quaternion-vector rotation, not the candidate helper.

The reviewer also ran all **29 authored reader methods**, the unchanged **31 C255 methods**, and C253's unchanged **14-file, three-case manifest check**. All pass on hosted Linux CPython 3.12.14. CANDIDATE-INPUTS.json binds 27 exact files, the source revision and commands. No full aggregate or local-driver pass is claimed. The reviewed commit adds only CONTRACT.md, reader.py and test_reader.py under C256 relative to the observed baseline.

## Preserved correction

The initial independent run passed 89 of 93 controls and exposed four uncaught AttributeError paths for malformed asset, root metadata, node metadata and source-manifest lists. The author corrected the public refusal boundary and added regressions. All four now refuse explicitly. `attempt-01.json`, its log and all four exact corrupt GLB inputs remain preserved. The intermediate 95-control pass and final rerun after bounded-input corrections remain separate receipts; no failed observation was overwritten.

## Claim boundary

The three APIs separate untrusted artifact labels, exact-source identity association and exact historical endpoint admission. None fabricates complete semantics, accepted history, rebuild evidence or trial success. Geometry and transforms come from binary accessors; changing declared metadata dimensions alone does not change measurements. The computed matrix is explicitly derived from sampled TRS, rather than claimed as a stored matrix.

This review does not qualify ownership/follows/hinges/actions/physical parameters, native routes, model trials, source rebuild, rejected-edit atomicity, unseen evaluation families or all-time motion. All original held qualification failures and release gates remain. There are no unresolved code findings within the selected boundary.

Final shared documentation still requires review and preservation checks. Actual published-main identity/checks, final ZIP verification, fresh full offline restore and confirmed saved delivery remain separate required closure gates. This approval does not claim any of those operations already succeeded.
