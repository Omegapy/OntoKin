# Adoption of the C091 grouped expression span correction

Adopt only the exact replacement in AMENDMENT.json, SHA-256 `a372bb209dc37e840b2896138bfa8d1af21ab70991dac3c02638d76b1b07b922`, after exact published byte/mode readback. The independent review, SHA-256 `7b3fb707d8a012027c7b5a18fbdf1807d2432991812fef2b071f6ed3747bdea4`, passed 19 binding and untouched-source checks. The earlier proposed labels in the retained preparation files are historical.

The correction preserves the inherited parenthesized expression span for n28. It changes only `expected.primary_source` from bytes `[863,873)` and text `2[N*m] / 0` to `[862,874)` and `(2[N*m] / 0)`. Every other expected value, diagnostic, source identity, budget, tolerance and frozen file remains unchanged. Both exact predecessor reproductions and the original failed comparison remain available.

The later PUBLICATION.json identifies the actual remote commit/tree and exact readback. A local prepared record is not that readback. No change to the frozen file itself is authorized.
