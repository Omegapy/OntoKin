# P21 wheel byte review — corrected inventory scope

Verdict: **REMEDIATION_INPUTS_AVAILABLE**. No remaining wheel-provenance or payload-verification gap was found.

The exact P21 ZIP is 9,327,161 bytes with SHA-256 `ba03995347ed65a5a37b4283211841daf4da74fe4a04dbe0617f9e833e9bb64f`. It contains 318 safe, unique members and 317 manifest payloads. All payload sizes/hashes pass. The preserved historical inventory also contains 317 payload rows and intentionally excludes the manifest itself.

All seven wheel payloads match their P20 preparation result, historical P21 inventory, P20 installation report, and frozen source lock. Their combined size is 7,769,774 bytes. Both outer-archive and wheel ZIP CRC/path checks pass. Stable Library identity and version 0 agree with the descriptor.

The initial report is preserved unchanged: one inventory assertion incorrectly expected 318 historical rows. The observed difference is exactly MANIFEST-SHA256.json. This corrected report reuses 657 passing checks only after verifying unchanged archive/inventory identities and adds four passing correction checks. No artifact bytes or expectations for the wheels changed.

Remediation inputs are available for separately reviewed preparation. H0 remains unaccepted. No code or wheel was extracted, imported, installed, or run; no Git or Library mutation occurred. Exact descriptors and readset remain in WHEEL-PROVENANCE.json and this report.
