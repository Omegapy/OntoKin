# Raw restoration output

`RESTORATION.stdout.transport.json` preserves the original `RESTORATION.stdout.json` bytes in base64, with their byte count, SHA-256 and original permission mode. Decode the data and verify these identities to recover the exact raw JSON output, including its final blank line. The original session evidence remains unchanged.

The first delivery-candidate whitespace check rejected that raw final blank line. Its failed result remains in `session_p12/checks/delivery-candidate`; the successful affected-check recheck is recorded separately. This is an evidence transport correction, not a product test or a change to the restoration result.
