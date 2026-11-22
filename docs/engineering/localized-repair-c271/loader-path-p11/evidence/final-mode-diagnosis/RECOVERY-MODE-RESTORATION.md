# Supplemental private recovery procedure

This procedure restores recorded evidence metadata. It does not change the frozen
ZIP, original evidence, Git checkout, operational runtimes, fixture bytes or control
expectations. Do not execute any restored file.

1. **Authenticate the input.** Check the final ZIP against the separately recorded
   size **5,606,509** and SHA-256
   `4eddd353047fb8d6aa316544c8b54d655eb53a1613f9c522bbed0edc1ab1249e`.
   Verify ZIP integrity, unique safe relative member names, and the complete
   `MANIFEST-SHA256.json` inventory. Verify `CHECKPOINT.json` and
   `SOURCE-MANIFEST.json` against source commit
   `e7508fb23c64563549631a1be46a3523593e2d9f`, tree
   `06c7db644326a5e03bffe8ad53ea4fa0004e7065`. Read
   `RECOVERY-FILE-MAP.json` only after its manifest size/hash passes.
2. **Create a separate private destination.** Exclusively create a fresh owned
   root with mode `0700`, outside the Git checkout, original evidence and runtime
   paths. Refuse an existing destination. Validate each `relative_path` and
   `payload_path`; reject absolute paths, traversal, duplicate destinations,
   symlinks, hardlinks and special files. Treat `original_path` as historical
   evidence only; never write to it.
3. **Restore every embedded recovery row.** For each row with `payload_path`, read
   that exact ZIP member and verify the row's size and SHA-256. Under the new root,
   create private directories and the row's `relative_path` as a new ordinary file,
   without following links or overwriting. Write only those verified bytes. Apply
   the row's authenticated `source_mode` to this new file. Accept ordinary recorded
   modes only; reject special-file or set-id modes. Do not substitute the ZIP's
   `0644` transport attribute for the recorded original mode.
4. **Verify the restored result.** Re-read every new file and require exact size,
   SHA-256, regular-file type, single-link status and the recorded mode. For this
   archive, the check must cover all **813 embedded rows**, including all **532**
   rows recorded as `0600` but transported as `0644`. Any mismatch refuses
   consumption; preserve the failed observation without rewriting expectations.
5. **Handle external rows explicitly.** The remaining rows have exact dependency
   locators instead of embedded bytes. To restore them, authenticate the named
   archive/receipt, retrieve the exact referenced member/blob, verify the row's
   size/hash, then apply the same private-copy and mode procedure. Otherwise mark
   those rows as externally recoverable and not materialized; do not claim they
   were restored by the embedded-row check.
6. **Keep a separate restoration receipt.** Record the ZIP and source identities,
   recovery-map identity, fresh destination, covered row counts, resulting mode/hash
   checks, exclusions and outcome outside the frozen package. Preserve the initial
   FP12 failure and distinguish this restoration result from ZIP transport-mode
   equality, product execution, H0/H1 or whole-project acceptance.
