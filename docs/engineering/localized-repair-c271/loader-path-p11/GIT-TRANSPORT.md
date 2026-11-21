# Lossless Git transport for raw evidence

Three raw evidence paths use the envelopes listed in `GIT-TRANSPORT.json`. Two are identical unified diffs; the third is the preserved failed whitespace-check output. The ordinary whitespace gate remains enabled. The original raw bytes, hashes and permissions remain unchanged in the handoff recovery inventory.

Before validating a private materialized candidate from Git, read this mapping from the exact reviewed Git revision. Verify each envelope's SHA-256, require the exact closed envelope schema and base64 encoding, decode it strictly, and verify the decoded size and SHA-256. For the candidate diff, independently compare that identity with the adopted candidate manifest. Verify the independent review's corresponding diff identity as well.

Create the listed relative destination only inside a fresh owned private evidence tree. Reject absolute paths, empty/parent components, symlink traversal, hardlinks, special files and existing destinations. Write the decoded bytes as a regular nonexecutable file with the recorded mode, then verify them again. Keep the original repository and frozen scratch copies unchanged. Record materialization outside the frozen payload.

After this transport step, apply `design/candidate004/MATERIALIZATION.md` to the complete candidate and its explicit sibling support files. No expectation is regenerated, no runtime is modified, and no Git whitespace option or attribute is weakened. The mapping supplies exact evidence bytes; it does not grant execution authority.
