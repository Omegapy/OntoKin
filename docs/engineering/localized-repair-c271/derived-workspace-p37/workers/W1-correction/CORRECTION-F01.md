# W1: correction of DECISION-001 for finding F-01 (control author W2)

Requested by the Director after S4. Recorded at 2026-11-28T01:07:38Z. Only `DECISION-001.md` changed. The code, the
tests, the interface note and W2's files are untouched. Nothing was run; no Git start.

- Before: `f0af6f395d83f96cdd217a11b1e43609474143120939be332cf5aa6f05688121`
- After: `7a1626cb7916d744c7e91f6c82f6ce84d72a9c4e84d44bfa8004fdcdd21815fe`
- Cited: control P37-C24 of `derived-workspace-p37/CONTROLS-FROZEN.json`
  (`7c5f86ca92d8e6452b73e89ce9c97475533f6a7bed23a1a7a8266fb26c534a8a` when read), with expected
  refusal `CH-SOURCE`, `Complete CPU source inventory differs`.

## Changed text

1. Section 2, the bullet "Not missing source". These sentences were removed: "All of it lies inside the
   copied set: its trees and files lie under `ontokin`, `tests`, `prototypes`, `tools` and `docs`,
   plus `pyproject.toml`. Its absence therefore refuses twice: through that binding, and through rule
   B's condition 4." The bullet now says that:
   - a missing file of the source set always refuses through the binding;
   - rule B's condition 4 would refuse as well only when the file lies inside the copied set;
   - a file of the source set outside the copied set (`ontokin/.env`) refuses through the binding
     alone (P37-C24);
   - the check fails closed either way, and the Director found all 644 files of HOST's source inventory
     at gate MR's commit inside the copied set.
2. Section 6, the sub-bullet on names that `ignored()` matches. "so admitted as ` D` only" became "so
   rule B admits its line as ` D` only". One sentence was added: such a file that also belongs to the
   0.2.0 source set still refuses, through the source set's binding alone (P37-C24; section 2).

"Decision in brief" repeats no such claim and is unchanged.

## Starts

`python3 -I -S -B` twice, to read CONTROLS-FROZEN.json; once, to check the corrected file's whitespace
and encoding. Shell utilities: ls, grep, sed, shasum, date and cat.
