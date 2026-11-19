# Independent review of the optional startup packet

No remaining correctness blocker found in executed scope. The Director deferred this experimental helper from the active workflow; this review does not recommend deployment or claim token savings.

## Candidate and scope

- Reviewer: `/root/compress_workflow`; author: `/root/compress_goals`.
- Tool SHA-256: `a5eccf81f399176bf7c237982bdaa33537e54e784f6fdbe5bb933b17321acde8`.
- Test SHA-256: `75c09cdb935ac05a202e223639d6962e90a920363ca45a3ffc7e8a1df0996d5f`.
- Exercised source revision: `7ff41e071fb694dadf1ba256b13168e1a4083926`.
- Full tool and test source inspected; final tool/test hashes rechecked unchanged.
- Required claims: R06 and the optional-reader paragraph in START.

## Independent checks

10/10 independent check groups passed. Exact inputs, observed rejection messages, source identities and reproducible check program are in [PACKET-REVIEW.json](PACKET-REVIEW.json).

- Real pinned cohort, exact byte reconstruction and expansion: passed.
- Synthetic exact-text and deterministic glossary control: passed.
- Omitted/added/reordered cohort, same-length tamper, stale expected ref and missing Git file: passed.
- Explicit omit-entry assertion and live-versus-local evidence limits: passed.
- Malformed definitions, aliases, headers, lengths, UTF-8, truncation and trailing bytes: passed.
- Malformed metadata types, duplicate keys, excessive depth and integer length: passed.
- Unsafe and README paths plus source alias collisions: passed.
- Oversized expansion is rejected before substitution: passed.
- Bounded regular-file input, FIFO/device rejection, README CLI exclusion and exclusive output: passed.
- Tool source access remains local and read-only: passed.

## Findings and corrections

- **PACKET-F01**: Expansion was materialized before the decoded-length limit check. Preflight expanded UTF-8 size before substitution. Status: resolved; independent guard trap confirmed substitution is not reached for oversized input.
- **PACKET-F02**: Malformed selector types and deep/overlong-integer JSON could bypass normalized PacketError rejection. Explicit selector type check, 64-level JSON preflight and ValueError/RecursionError wrapping. Status: resolved; independent malformed-input cases passed.
- **PACKET-F03**: stat size followed by read_bytes did not bound device/FIFO or growing-file reads. No unbounded device read was executed. Nonblocking descriptor open, regular-file fstat check and read(MAX_PACKET + 1). Status: resolved; independent device/FIFO/size controls passed.

The author retained an earlier failed deep-JSON test in [implementation evidence](PACKET-IMPLEMENTATION.md). Its final 23-test result is author evidence; the independent groups above were executed separately.

## Meaning and limits

The helper reconstructs the selected local Git blobs and checks metadata, ordered cohort and every source byte. Its rejection paths prescribe direct reads. It does not observe live GitHub head, prove that an omitted entry was already read, or replace nested/scope-specific instructions.

The report counts the whole packet, including glossary and framing. Whole-startup token comparisons must also count the already-read entry. No tokenizer was run by this reviewer. The Director deferred active integration on reported savings below 3%.

No Git refs, index, remote state, procedure documents or source/test files were changed by this review.
