# Independent C080 fixture authoring

These files were authored after the published texture/asset decision and before runtime implementation. The generator uses Python's standard library only. It does not import OntoKin, read product outputs, triangulate production meshes or execute product tests.

PNG inputs start from literal pixels or the stated pixel formulas. The writer applies each standard filter in the forward direction and builds chunk lengths, CRCs and a complete zlib stream. Exact decoded-pixel and per-row hashes, asymmetric texel probes and known glyphs are predetermined. Malformed files change one identified layer where practical. The encoded-limit file deliberately contains empty DEFLATE blocks, not a decompression bomb; its output is one four-byte scanline.

UV expectations interpret authored binary64 inputs with Fraction. The complete affine sum is rounded once to binary64, then packed to binary32. The decimal cancellation witness distinguishes exact complete evaluation from intermediate binary64 subtraction. Probe records explicitly distinguish authored region corners from general analytic probes; a probe is never proof of emitted triangulation.

Program revisions are calculated directly from the adopted canonical source/asset manifest and domain prefix. They do not invoke a product bundle loader. Existing source SHA256 values retain their original meaning. Exact geometry/motion preservation is a required comparison against a corresponding source-only .12 control, not an assumed property of screenshots.

No verification pass is reported by this freeze. Stage labels locate expected refusal authority: transport before candidate revision, represented closure/image/constructor admission, constructed referenced UV bounds, current request authorization, or supplied artifact validation. An implementation must not replace a required geometry/image refusal with unrelated resource exhaustion. Maximum decoded cases explicitly request higher limits with independent host policy; the ordinary-budget maximum image intentionally fails by its channel-byte debit lower bound.

An isolated aggregate-one-over image case satisfying every count and individual bound is impossible because both aggregate ceilings equal four times their individual maxima. Exact aggregate cases and separate count/individual failures cover those boundaries without inventing a witness.

All old fixtures remain unchanged. New work must preserve this freeze and failed runs; fix implementation defects or publish a separate reviewed contract/fixture revision instead of changing frozen answers.

The first unpublished preparation is retained as commit e1ce1c14d4029c5c529af3fe56b655bda92d91f1. Static review found its missing-padding payload replaced padding with A, which remained canonical base64 and reached the wrong-digest refusal instead. Before freeze publication, this preparation removes the required padding only and adds explicit envelope, asset-slice, successful attachment add/remove and metadata-cursor probes. No runtime result drove the correction.
