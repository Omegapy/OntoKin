"""Finalize design/control prose after withdrawal of the extra document cap."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
C = ROOT / "candidate004"


def replace_once(text, old, new):
    assert text.count(old) == 1, old[:100]
    return text.replace(old, new)


def read(name):
    return json.loads((C / name).read_text())


def write(name, value):
    (C / name).write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n")


decision = (C / "DECISION.md").read_text()
decision = replace_once(decision, "one token-bearing subject; 4 MiB variant document; 4,096 unique needed names;", "one token-bearing subject; 4,096 unique needed names;")
old_paragraph = next(p for p in decision.split("\n\n") if p.startswith("The new profile's private variant-byte reader"))
decision = replace_once(decision, old_paragraph,
    "The variant document reuses the existing `_document` reader with `maximum=LIMITS['document_bytes']`, the unchanged 16 MiB allowance, the existing loader error category, and the existing `check` callback. That path already bounds bytes before decoding, checks descriptor and file identity, rejects duplicate JSON keys, and requires exact canonical serialization. The new variant-object shape is checked after that unchanged reader. No separate byte cap, private byte-reader seam, limit constant or decoding relaxation is proposed. The 4 MiB proposal was withdrawn after the user questioned its need: no measured or source-derived requirement justified a second size policy. Semantic suffix/name/path/product ceilings remain separate checks on interpretation. The preserved source controls `case_HI03` D/E/F cover decoder rejection, G covers 16 MiB plus one byte, and H covers mid-read identity drift; they remain part of the complete inherited future run, not tests executed in P11. [L01, L15]")
decision = replace_once(decision,
    "Candidate003 corrects the independent review's boundary-isolation and missing-ancestor findings, adds focused document/component/encoding controls, and preserves every prior expected record. `REVISION-003.json` binds its exact delta from candidate002. `MATERIALIZATION.md` specifies faithful restoration of recorded inert file modes after Git transport; it grants no operational executable or host authority.",
    "Candidate004 corrects the independent review's boundary-isolation and missing-ancestor findings, adds focused component/encoding controls, and preserves every prior expected record. The complete 99-case candidate003 attempt and its two withdrawn document-reader controls remain bound by `../ATTEMPT003-RETENTION.json`. `REVISION-004.json` records the final 97-case delta from the independently reviewed candidate002. `MATERIALIZATION.md` specifies faithful restoration of recorded inert file modes after Git transport; it grants no operational executable or host authority.")
(C / "DECISION.md").write_text(decision)

contract = (C / "CONTROL-CONTRACT.md").read_text()
contract = replace_once(contract, "The 99 cases", "The 97 cases")
contract = replace_once(contract, "eight auxiliary-vector byte strings, two exact variant-reader byte inputs and 99 JSON contexts", "eight auxiliary-vector byte strings and 97 JSON contexts")
route = next(line for line in contract.splitlines(keepends=True) if line.startswith("| `bounded_variant_read`"))
contract = replace_once(contract, route, "")
contract = replace_once(contract, "The legacy and bounded-reader contexts have separate explicitly nonoperational schema names.", "The legacy contexts have a separate explicitly nonoperational schema name.")
contract = replace_once(contract, "`build_controls_attempt003.py`", "`build_controls_attempt004.py`")
contract = replace_once(contract,
    "The private variant-byte reader applies its fixed ceiling before any decoding or shape interpretation.",
    "The variant document uses the inherited `_document` reader and `LIMITS['document_bytes']` 16 MiB cap before canonical decoding and its new closed shape; no additional byte limit or private reader seam is introduced.")
contract = replace_once(contract,
    " One separate reader positive covers exactly 4 MiB of bytes without accepting a variant object.", "")
contract = replace_once(contract, "Candidate003 uses the short synthetic basename", "Candidate004 retains candidate003's correction: the short synthetic basename")
contract = replace_once(contract, "The 77 refusal primitives", "The 76 refusal primitives")
old_reader_paragraph = next(p for p in contract.split("\n\n") if p.startswith("P08 and N74 bind exact regular-file bytes"))
contract = replace_once(contract, old_reader_paragraph,
    "The final corpus deliberately has no P08 or N74. Those identifiers belong to candidate003's withdrawn 4 MiB reader proposal. Its exact bytes, expectations, scripts and successful author-integrity report remain in the retained attempt; they are not adopted controls. The variant document instead uses the unchanged 16 MiB `_document`/`LIMITS['document_bytes']` path. Source review must verify that reuse and preserve its callback, predecode byte/identity, descriptor, duplicate-key, canonical JSON and subsequent closed-shape checks. Existing `case_HI03` D/E/F/G/H supplies the relevant inherited decoder/overlimit/drift controls, alongside the complete retained test inventory. No new byte-policy control or caller-replaceable reader limit is needed.")
old_static_paragraph = next(p for p in contract.split("\n\n") if p.startswith("`validate_artifacts_attempt003.py`"))
contract = replace_once(contract, old_static_paragraph,
    "`validate_artifacts_attempt004.py` checks exact path/size/mode/hash inventory, complete case/oracle coverage, inert files, fixed construction bytes, raw metadata expectations, positive declared lengths/cardinalities, isolated boundary measurements and complete logical ancestor guards. It does not implement the origin policy or call production code. Candidate004 passed 1,149 such checks over 131 fixture files. That count is not a product-test count. Candidate001's failed positive-length check, candidate002's incomplete controls and candidate003's withdrawn size-policy attempt remain recoverable. All 93 prior expectation records are unchanged; four newly authored entries and the exact file delta are identified in `REVISION-004.json`.")
(C / "CONTROL-CONTRACT.md").write_text(contract)

(C / "README.md").write_text("""# P11 decision and control candidate

Read `DECISION.md`, then `CONTROL-CONTRACT.md`, `SOURCES.json` and `FUTURE-SURFACE.json`. `FIXTURE-MANIFEST.json` binds the portable inputs; `EXPECTATIONS.json` is the independently authored future oracle; `CONSTRUCTION.json` explains their bytes. `PROTECTED-SOURCES.json` identifies the legacy source boundary. `REVISION-004.json` gives the exact delta from candidate002. `MATERIALIZATION.md` explains faithful inert-file mode restoration after Git transport.

This is candidate004 of one bounded design phase. It proposes an opt-in, nonselecting interpretation of the exact selected direct Python's `$ORIGIN/../lib`. No production code, tests, adopted contracts, pins or historical artifacts changed. No product parser, product test, host observation, Node/ldd, runtime preparation or implementation ran. The real H0 prerequisite remains unaccepted.

Synthetic positive controls exercise private rule seams. They cannot satisfy the real selected image's fixed operational hash. The path-boundary pairs use a deliberately synthetic base-only variant model, a short invented basename and complete logical ancestors. Actual loader variant completeness remains an unresolved future H0 input.

The user questioned the proposed separate document-size limit. The final decision reuses the existing 16 MiB document reader, canonical JSON, identity and callback checks. It adds no byte-size policy or private byte-reader seam. The withdrawn 99-case candidate003, including its two 4 MiB reader controls and exact logs, remains preserved by `../ATTEMPT003-RETENTION.json`. Earlier candidates and all supporting identities remain intact.

The author static result `../static004.stdout.json` reports 1,149 passed integrity/layout checks over 97 cases, 26 ELF images and 131 fixture files. All 93 prior expected records remain unchanged; four new records cover the component and encoding findings. These are not product-test results. Independent review of this frozen candidate is a separate gate; this README makes no review/adoption claim.

The new constructor/checker and distinct attempt004 support files are bound by `CANDIDATE-MANIFEST.json`, together with the prior frozen support identities and the withdrawn-attempt retention record. The Director owns repository publication, canonical adoption and verified final delivery.

Stop after independent design/control review and saved partial handoff. Implementation, actual-host variant/closure reconstruction and H0 acceptance require later separately selected phases.
""")

review = read("REVIEW-REQUEST.json")
review["candidate"] = "candidate004"
review["acceptance"].extend([
    "Byte/component boundary pairs isolate the unreduced expression and contain every logical ancestor guard.",
    "ASCII admission belongs only to new origin/variant fields; legacy path character semantics remain unchanged.",
    "The variant document reuses existing _document/LIMITS document_bytes 16 MiB behavior, including all identity/callback/canonical/closed-shape safeguards; no new byte reader or size policy.",
    "All 93 prior expectations are preserved; four explicit new records cover component/encoding findings. The withdrawn two document-size controls remain historical only.",
    "Git transport is followed only by exact private inert-file materialization, never operational pin or executable-mode substitution."
])
review["previous_candidate_manifest_sha256"] = "563e84cc83f31a202cc0eead9102b66b08050ea011dfbbf4ed6fc19db318c8f4"
review["focused_delta"] = "REVISION-004.json"
write("REVIEW-REQUEST.json", review)

sources = read("SOURCES.json")
for row in sources["local"]:
    if row["id"] == "L01":
        row["anchors"].extend(["_absolute", "_read_file", "_canonical", "_decode", "_document", "LIMITS document_bytes"])
    if row["id"] == "L15":
        row["anchors"].append("case_HI03 variants D/E/F/G/H: decoder, 16 MiB+1 input and mid-read identity drift")
sources["inherited_document_bound"] = {"source": "L01", "tests": "L15 case_HI03 D/E/F/G/H",
    "reader": "_document -> _read_file -> descriptor equality -> _decode", "maximum_bytes": 16777216,
    "new_byte_policy": False, "production_execution_in_p11": False}
write("SOURCES.json", sources)

surface = read("FUTURE-SURFACE.json")
surface["surface"].insert(3, {
    "path": "prototypes/static_tray_v01/current_host_inspection_v01.py",
    "symbols": ["new variant-document admission caller", "existing _document", "existing _read_file", "existing _decode", "existing LIMITS['document_bytes']"],
    "change": "Read the new bound variant document through the existing _document function with its unchanged 16 MiB document cap and callbacks, then validate the new closed variant object. No new byte-reader helper, maximum, or decoder behavior.",
    "checks": "Static caller/source review and inherited case_HI03 D/E/F/G/H preserve byte bounds, identity, descriptor equality, duplicate-key/canonical JSON and shape rejection. No new size-policy control is adopted."
})
for row in surface["surface"]:
    if "new private guarded-origin rule" in row["symbols"]:
        row["change"] += " New path fields are ASCII-only; count leading root and unreduced parent components explicitly."
        row["checks"] += "; P09/N75 isolated component limit and complete ancestor guards; N76/N77 coherent non-ASCII refusals"
    if "_validate" in row["symbols"]:
        row["change"] = row["change"].replace("before Git/commands/STATIC_READY", "before _load_helpers, Git/commands/STATIC_READY on the new profile")
surface["preservation_matrix"].append({
    "id": "K08", "obligation": "Legacy _absolute character/count behavior and existing document/canonical JSON guards",
    "evidence": "L01 _absolute, LIMITS document_bytes, _read_file, _canonical, _decode and _document; L15 case_HI03 D/E/F/G/H",
    "future_check": "Keep old path behavior unchanged; apply ASCII only on new origin/variant fields; reuse existing 16 MiB reader and unchanged callback/identity/descriptor/canonical checks before new closed shape."
})
write("FUTURE-SURFACE.json", surface)

errors = read("AUTHORING-ERRORS.json")
errors["attempts"].extend([
    {"id": "candidate002-independent-review", "outcome": "Five mandatory design/control findings; no product execution",
     "findings": ["N69 multiple overlong paths and synthetic basename masked raw-expression byte bound.",
                  "P07/N69 lacked 63 logical ancestor guards and included an extraneous ancestor.",
                  "New byte wording needed an explicit relation to legacy character counts.",
                  "Document and 128-component ceilings lacked focused controls.",
                  "Git mode transport required a faithful private materialization procedure."],
     "disposition": "All candidate002 payload/support bytes retained. Final candidate004 resolves path/component/encoding/materialization findings. The unnecessary new document cap is withdrawn in favor of inherited behavior."},
    {"id": "variant-padding-proposal-rejected-before-write", "outcome": "A communicated whitespace-padding idea was rejected by source inspection before such bytes were written.",
     "cause": "_decode requires exact canonical serialization.",
     "disposition": "Candidate003 instead constructed canonical scalar bytes at a proposed reader-only seam; that entire extra size policy was subsequently withdrawn."},
    {"id": "candidate003-author-tools", "outcome": "prepare/build/static exited 0; 99 cases, 135 fixture files, 26 ELF images, 1176 static checks",
     "evidence": "../ATTEMPT003-RETENTION.json", "production_execution": False,
     "unexecuted_tools": ["document_attempt003.py", "freeze_attempt003.py"]},
    {"id": "patch003-failed001", "outcome": "apply_patch rejected duplicate Delete/Add operations for README before mutation",
     "evidence": "../patch003-failed001.json", "disposition": "Preserved failure record; valid separate updates affected candidate003 prose before retention only."},
    {"id": "user-document-limit-question", "outcome": "The user asked why a new document-size limit was needed. No concrete measured or source-derived need supported 4 MiB rather than the existing 16 MiB bound.",
     "decision_by": "/root with independent reviewer support", "disposition": "Withdraw new 4 MiB policy, separate bounded_variant_read seam and P08/N74 from adopted candidate. Preserve exact candidate003 and supports; reuse existing document reader and inherited controls."},
    {"id": "prepare004", "command": "python3 -I -S -B session_evidence/loader_design/prepare_attempt004.py",
     "outcome": "exit 0; retained 148 unfinished candidate003 payloads and 12 supports before creating candidate004",
     "stdout": "../prepare004.stdout.txt", "stderr": "../prepare004.stderr.txt"},
    {"id": "build004", "command": "python3 -I -S -B session_evidence/loader_design/build_controls_attempt004.py session_evidence/loader_design/candidate004",
     "outcome": "exit 0; 97 cases, 131 fixture files, 26 ELF images",
     "stdout": "../build004.stdout.txt", "stderr": "../build004.stderr.txt"},
    {"id": "static004", "command": "python3 -I -S -B session_evidence/loader_design/validate_artifacts_attempt004.py session_evidence/loader_design/candidate004",
     "outcome": "exit 0; 1149 fixture integrity/layout checks; no product execution",
     "stdout": "../static004.stdout.json", "stderr": "../static004.stderr.txt"}
])
write("AUTHORING-ERRORS.json", errors)
print(json.dumps({"candidate": "candidate004", "new_size_policy": False, "new_reader_seam": False,
    "case_count": 97, "previous_93_expectations_unchanged": True, "product_execution": False}, sort_keys=True))
