# Saved publication readback verifier: critical review

The authored verifier is `c090-tools/verify_published_readback.py`, SHA-256 `dc4476fb3c5e89b95649715e7c5a2c82aa8d36d967ec0949b5e2447bd3ff94cf`. This is a self-review of the new local evidence verifier, plus five focused synthetic integration controls. It is not evidence that a remote publication already occurred.

## What must agree

The verifier reads the publication description and immutable local parent/base/target objects. It rehashes native objects, derives the complete changed-path set itself and rejects deletions. Every publication identity, text/binary element, mode, byte length, SHA-1 and SHA-256 must match the independently derived native blob. Identical contents at different paths share one required blob response while retaining separate path/mode proofs.

The saved commit response must carry the expected commit SHA, exactly one parent equal to the prepared parent and the prepared target tree. For each saved tree observation, the declared prefix must identify that exact local target directory. The returned SHA must agree, `truncated` must be false, and the full response must equal the native immediate or recursive entry set selected by the observation. A false truncation flag cannot excuse an omitted entry. Returned file entries map back to full exact paths, and every changed path must be covered with its native mode and blob SHA.

The blob response set must equal the unique changed native blob set, with no omissions, duplicates or extras. GitHub CR/LF base64 line wrapping is explicitly permitted; other outside-alphabet characters are rejected. The compact encoding is decoded with validation and compared with canonical re-encoding, preserving padding and discarded-bit checks. The verifier compares decoded length, native Git blob hash, SHA-256 and exact bytes with local source. A digest-shaped string alone never establishes byte equality.

Input JSON rejects duplicate keys and nonfinite constants. File identities include path, length, mode and SHA-256, and every evidence file is reread before success. Output must be a fresh ordinary path outside the repository and is created exclusively. A verification failure produces a separate failed receipt with its actual reason and the inputs read so far; it cannot claim complete coverage.

## Focused validation

Five synthetic controls passed their expected outcomes. The valid fixture contains six changed paths and five unique blobs, including repeated multibyte text with CRLF, NUL/invalid-UTF-8 binary data, an empty blob, executable mode and a mode-only changed file. API-shaped base64 includes line wrapping. The hostile controls independently corrupt decoded blob content, omit a tree entry while retaining `truncated=false`, duplicate a blob response and replace the commit parent. Each produces an explicit failed receipt and nonzero exit. Exact generated response inputs, receipts, commands, logs and helper snapshot remain under `integration-readback-review01-inputs`.

The tests create and dispose of their own synthetic Git repositories. They do not modify project source, contact a service, execute OntoKin, rerun frozen preflight or update a project ref. No broad optional regression campaign was run for this helper.

## Scope boundaries

The verifier establishes consistency of caller-supplied saved API responses with the prepared immutable local tree. The caller must preserve the actual API retrieval provenance and perform expected-head publication/ref checks. The program makes no network request and cannot authenticate the origin of a locally supplied response by itself.

The commit API response is checked for its expected SHA, parent and tree fields. The verifier does not reconstruct a complete serialized commit object from that API JSON. The later native package audit must verify the actual native commit/object graph and sealed recovery. Whole working-tree permissions, old-source preservation and index stability remain the separately verified preservation helper's responsibilities. Runtime, controlled destination playback and release acceptance remain false in these receipts.
