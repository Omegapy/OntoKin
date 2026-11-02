# Independent raw-download helper review 01

**Approved after the identified corrections. No open blocking findings remain for the scoped coordinator helper.**

The exact reviewed downloader SHA-256 is `057cf60ff2d4ee04a1f86b912b3746ba7cc769d8364c3893a9ec18072fcd1c7d`. The directory-capture helper SHA-256 is `7774f95f82f64d99d977ddacdc7deadd7a29f756cdc6a63e1a14a898a17e9f81`. The reviewed plan SHA-256 is `17874d8e7067f66b9430c2523b97d2584cb0c9db60f9c0875eba56a6c6648716`, pinning commit `754f72106279abc6c867ab180300f2ba382a3f2d` and tree `693ad3ad6cf176b6b645d2edda3468673d5cae52`.

## Checks completed

The focused local/mock harness passed **41 checks**, with **zero real network requests**. It covered exact host/ref/path admission, request and observation identity mismatch, fragment/userinfo rejection, redirects, byte/hash/length/header failures, bounded reads, actual HTTP 403 evidence, no-overwrite behavior, corrupted existing payloads through both helper and main, and synthetic-query redaction.

The reviewer also ran the actual read-only preparation against **533 unique planned blobs in 42 directory observations**, totaling **19,062,747 expected bytes**. Every private returned raw URL matched its pinned repository/ref/path and planned blob metadata. Private URL queries were neither printed nor copied into review artifacts. Exact public redacted observations and code/plan snapshots are retained under `raw-download-review01-inputs/`.

## Corrections confirmed

1. **Existing receipts now receive verification.** Initially main filtered them out before calling the branch that verifies saved payloads. It now verifies every existing receipt/payload before selecting pending work. A corrupted saved payload makes main refuse without fetching anything.
2. **Failures retain actual HTTP status.** Status and redacted response URL are captured before validation, and HTTPError preserves its safe numeric status. Wrong Content-Length and HTTP 403 mocks confirm the evidence survives. Exception messages remain generic.
3. **Directory-capture errors suppress raw exception text.** A rejected tool call now produces a fixed message rather than String(reason), preventing URL-bearing exceptions from leaking private query data.
4. **Final execution identity is captured at module load.** Each new receipt and batch summary uses that captured source hash. An earlier coordinator batch that overlapped a file edit requires its separately retained start-version/disposition; the final review does not retrospectively label that earlier code as this version.

## Scope and remaining responsibility

The helper uses only URLs returned by the captured GitHub listings. It performs no token or global credential discovery. It requires HTTPS and the exact raw GitHub authority and pinned repository/ref/path, rejects every redirect, bounds each read by expected length plus one byte, and verifies both SHA-256 and the native Git blob SHA-1 before exclusive creation of the payload and passing receipt. Existing files are never overwritten. Failed requests retain distinct failed receipts with redacted URLs.

This approval covers the helper and actual plan preparation, not completion of all remote downloads. The coordinator's actual HTTP receipts and separate final readback verifier must establish complete publication bytes, tree membership and native modes. No candidate, repository, runtime or remote reference was modified by this reviewer.

Detailed identities and the focused check receipts are in `raw-download-review01.json`, `raw-download-check01.json` and `raw-download-actual-plan-check01.json`. The inspected intermediate downloader and initial directory-capture source are preserved separately.
