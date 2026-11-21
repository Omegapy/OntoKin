"""Update only the mutable candidate003 records before independent freeze."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
CANDIDATE = ROOT / "candidate003"


def read(name):
    return json.loads((CANDIDATE / name).read_text())


def write(name, value):
    (CANDIDATE / name).write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n")


review = read("REVIEW-REQUEST.json")
review["candidate"] = "candidate003"
review["acceptance"].extend([
    "Byte/component boundary pairs isolate the unreduced expression and contain every logical ancestor guard.",
    "ASCII admission belongs only to new origin/variant fields; legacy path character semantics remain unchanged.",
    "The 4 MiB control reaches the actual new-profile fixed-cap byte reader before decode; no test-provided maximum masks a missing production cap.",
    "All 93 prior expectations are preserved; six explicit new records cover document/component/encoding review findings.",
    "Git transport is followed only by exact private inert-file materialization, never operational pin or executable-mode substitution."
])
review["previous_candidate_manifest_sha256"] = "563e84cc83f31a202cc0eead9102b66b08050ea011dfbbf4ed6fc19db318c8f4"
review["focused_delta"] = "REVISION-003.json"
write("REVIEW-REQUEST.json", review)

surface = read("FUTURE-SURFACE.json")
surface["surface"].insert(3, {
    "path": "prototypes/static_tray_v01/current_host_inspection_v01.py",
    "symbols": ["new private fixed-cap origin-variant byte reader", "new variant-document admission caller", "_decode"],
    "change": "New-profile variant admission must call a private reader with its own fixed 4 MiB maximum before existing canonical JSON decoding and closed shape checks. No adapter-supplied maximum or new decoding relaxation.",
    "checks": "P08/N74 consume exact frozen byte inputs at that actual reader seam; independently verify caller/constant linkage. Scalar success is raw-byte acceptance only. Preserve _decode canonical serialization, duplicate-key refusal and descriptor equality."
})
for row in surface["surface"]:
    if "new private guarded-origin rule" in row["symbols"]:
        row["change"] += " New path fields are ASCII-only; count leading root and unreduced parent components explicitly."
        row["checks"] += "; P09/N75 isolated component limit and full ancestor guards; N76/N77 coherent non-ASCII refusals"
    if "_validate" in row["symbols"]:
        row["change"] = row["change"].replace("before Git/commands/STATIC_READY", "before _load_helpers, Git/commands/STATIC_READY on the new profile")
surface["preservation_matrix"].append({
    "id": "K08", "obligation": "Legacy _absolute character/count behavior and exact canonical JSON/document guards",
    "evidence": "L01 _absolute, _canonical, _decode and _document; candidate003 DECISION sections 4 and 6",
    "future_check": "Keep old path acceptance unchanged; apply ASCII only on new origin/variant branch; check actual production variant-reader cap linkage and unchanged subsequent decoding/closed shape."
})
write("FUTURE-SURFACE.json", surface)

errors = read("AUTHORING-ERRORS.json")
errors["attempts"].extend([
    {"id": "candidate002-independent-review", "outcome": "Five mandatory design/control findings; no product execution",
     "findings": ["N69 had multiple overlong paths and P07/N69 used a basename masking the raw-expression guard.",
                  "P07/N69 lacked 63 logical ancestor guards and retained an extraneous ancestor.",
                  "New byte wording needed explicit relation to legacy character-count paths.",
                  "4 MiB variant-reader and 128-component ceilings lacked focused controls.",
                  "Git file mode transport needed an explicit faithful private materialization rule."],
     "disposition": "Preserve candidate002 and all 14 exact support files. Candidate003 repairs contexts, clarifies ASCII-only new paths, adds six controls, and freezes materialization. All 93 old expected records remain unchanged."},
    {"id": "variant-padding-proposal-rejected-before-write",
     "outcome": "An initial communicated proposal to pad a full variant document with whitespace was rejected during source inspection before any such fixture was written.",
     "cause": "Existing _decode requires exact canonical serialization, so whitespace padding would fail later decoding.",
     "disposition": "Freeze exact canonical JSON scalar bytes at the actual new fixed-cap reader seam only. They never claim variant schema or profile acceptance. Existing canonical guard remains unchanged."},
    {"id": "prepare003", "command": "python3 -I -S -B session_evidence/loader_design/prepare_attempt003.py",
     "outcome": "exit 0; verified all 139 old payload files and 14 old supports before preparing new scripts",
     "stdout": "../prepare003.stdout.txt", "stderr": "../prepare003.stderr.txt"},
    {"id": "build003", "command": "python3 -I -S -B session_evidence/loader_design/build_controls_attempt003.py session_evidence/loader_design/candidate003",
     "outcome": "exit 0; 99 cases, 135 fixture files, 26 ELF images",
     "stdout": "../build003.stdout.txt", "stderr": "../build003.stderr.txt"},
    {"id": "static003", "command": "python3 -I -S -B session_evidence/loader_design/validate_artifacts_attempt003.py session_evidence/loader_design/candidate003",
     "outcome": "exit 0; 1176 static fixture integrity/layout checks, no failures",
     "stdout": "../static003.stdout.json", "stderr": "../static003.stderr.txt",
     "scope": "No product code, policy implementation, production parser, target execution or host observation."},
    {"id": "patch003-failed001", "outcome": "apply_patch rejected a duplicate Delete/Add operation for README before mutation",
     "evidence": "../patch003-failed001.json", "disposition": "Retained failure record; applied separate valid updates to mutable candidate003 only."}
])
write("AUTHORING-ERRORS.json", errors)
print(json.dumps({"candidate": "candidate003", "records_updated": ["REVIEW-REQUEST.json", "FUTURE-SURFACE.json", "AUTHORING-ERRORS.json"],
    "prior_candidate_changed": False, "product_execution": False}, sort_keys=True))
