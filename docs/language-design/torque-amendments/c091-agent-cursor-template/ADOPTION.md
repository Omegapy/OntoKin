# Adoption of the C091 Agent cursor template correction

Adopt only the two exact replacements in AMENDMENT.json, SHA-256 `6f765c0c9bbe8992c92c7e91c0ea3ba23c43a91f3ee7c1b436592c1aefa4aab9`, after exact published byte/mode readback. The independent review, SHA-256 `ab4769102ed682b7f16877726b5d0edd17f37a7c9d3a1ed9e6c6dd824293405a`, passed 16 checks and independently replayed all 170 exact C090 package files. Proposed preparation labels remain historical.

Both A04 cursor references change from `A04.page.result.next_cursor` to `A04.page.next_cursor`. The existing top-level response envelope and pagination behavior are preserved. No original frozen file, other expectation, source, budget, tolerance or runtime semantic changes. The original failed workflow remains failed and is identified separately.

PUBLICATION.json will identify the actual remote commit/tree and exact readback. A local prepared record is not that readback.
