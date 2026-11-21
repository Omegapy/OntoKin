"""Retain the withdrawn size-policy attempt and prepare the bounded final revision."""
from pathlib import Path
import hashlib
import json
import shutil
import stat

ROOT = Path(__file__).resolve().parent
WITHDRAWN = ROOT / "candidate003"
NEW = ROOT / "candidate004"


def descriptor(path):
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(), "mode": oct(stat.S_IMODE(path.stat().st_mode))}


def replace_once(text, before, after):
    assert text.count(before) == 1, before[:100]
    return text.replace(before, after)


retention = {
    "schema": "ontokin.c271.p11-withdrawn-attempt-retention/1",
    "attempt": "candidate003", "state": "withdrawn_before_independent_freeze",
    "reason": "The user questioned the new document-size policy. No measured or source-derived need justified a separate 4 MiB maximum. The Director and independent reviewer selected reuse of the existing _document/LIMITS document_bytes 16 MiB behavior.",
    "preserved_payload": [descriptor(path) for path in sorted(WITHDRAWN.rglob("*")) if path.is_file()],
    "preserved_support": [descriptor(path) for path in sorted(ROOT.iterdir()) if path.is_file() and "003" in path.name],
    "executed_author_tools": ["prepare_attempt003.py", "build_controls_attempt003.py", "validate_artifacts_attempt003.py"],
    "unexecuted_author_tools": ["document_attempt003.py", "freeze_attempt003.py"],
    "limits": "Some copied records in this unfinished attempt still name candidate002, and no candidate003 candidate manifest or independent acceptance exists. This external retention manifest binds the exact unfinished bytes without rewriting them.",
    "frozen_for_history_only": True, "product_execution": False,
    "superseding_candidate": "candidate004", "withdrawn_controls": ["P08_variant_reader_4mib", "N74_variant_reader_over_bound"]
}
with (ROOT / "ATTEMPT003-RETENTION.json").open("x") as stream:
    stream.write(json.dumps(retention, sort_keys=True, indent=2, ensure_ascii=True) + "\n")

builder = (ROOT / "build_controls_attempt003.py").read_text()
start = builder.index("# Exact document byte boundaries")
end = builder.index("component_parent =", start)
builder = builder[:start] + builder[end:]
builder = replace_once(builder, '    "variant_document_read_fixtures": variant_read_specs,\n', "")
with (ROOT / "build_controls_attempt004.py").open("x") as stream:
    stream.write(builder)

validator = (ROOT / "validate_artifacts_attempt003.py").read_text()
validator = replace_once(validator,
    '("metadata", "refusal", "rule_acceptance", "propagated_callback", "bounded_read")',
    '("metadata", "refusal", "rule_acceptance", "propagated_callback")')
start = validator.index('for name, spec in construction["variant_document_read_fixtures"].items():')
end = validator.index('nonascii_origin =', start)
validator = validator[:start] + validator[end:]
with (ROOT / "validate_artifacts_attempt004.py").open("x") as stream:
    stream.write(validator)

NEW.mkdir()
for path in sorted(WITHDRAWN.iterdir()):
    if path.is_file() and path.name not in {"CANDIDATE-MANIFEST.json", "EXPECTATIONS.json", "CONSTRUCTION.json", "FIXTURE-MANIFEST.json"}:
        shutil.copy2(path, NEW / path.name)
print(json.dumps({"prepared": NEW.name, "retained_attempt003_payloads": len(retention["preserved_payload"]),
    "retained_attempt003_supports": len(retention["preserved_support"]), "new_size_policy": False,
    "new_reader_seam": False, "product_execution": False}, sort_keys=True))
