# Fresh numerical reconstruction review

This directory records newly executed checks of the `recovery14` numerical proposal. The missing earlier work and its original certificate hash are identified in [reconstruction.json](reconstruction.json). These files do not recover or relabel the earlier execution.

The [current check report](check-report.json) verifies [numeric-admission.md](../numeric-admission.md), the [outward interval checker](../interval_oracle.py), the [independent corpus verifier](../verify_rounding.py), and the [deterministic certificate](../rounding-certificates.json) by exact input hashes. It records CPython 3.12.14 on the observed Linux environment and the pre-commit checkout head. The input manifest, rather than that baseline Git head alone, identifies the actual newly written proposal bytes.

## Observed result

All **54** original primary-action target coordinates match the unchanged prescribed binary64 bits. Five fixed numeric classification cases, 17 mathematical probes, nine resource/cancellation-counter probes and 25 one-ULP wrong-cell mutations passed. All 27 original selected pairs resolve at 96 fractional bits. Maximum measured original-case counters are 366 series recurrence steps, 1,803 interval operations and 114 exact proof helper operations; those maxima need not occur in the same case.

The separate smallest-subnormal-target probe resolves after the full five-pass schedule at 1,536 bits. It consumed 4,996 recurrence steps, 21,593 interval operations and 412 exact helper operations. This is fresh mathematical preparation for that identified input. It establishes no actual source/runtime, transaction, Agent or recorded-delivery result.

The certificate contains exact enclosures, canonical input bit patterns, rounding-cell midpoints/tie rules, target bits, residual-squared bounds and measured counters for every original case. Its verifier reproduces the complete file byte-for-byte and checks cell inclusion through a separate adjacent-binary64 calculation. The preserved Decimal oracle remains an independently authored expectation source; it is not imported by the interval checker or verifier.

## Preserved preliminary result

[preliminary-001/check-report.json](preliminary-001/check-report.json), [its certificate](preliminary-001/rounding-certificates.json) and [its verifier text](preliminary-001/verify_rounding.py.txt) retain the earlier successful preparation within this reconstruction. The current verifier derives its reported precision set directly from observed certificates. That reporting correction changes file identities; the preliminary report remains tied to its original inputs. No expected target or numerical method changed.

## Remaining gates

Independent review of this reconstructed proof, integrated proposal navigation, adoption, actual runtime accounting and cooperative interruption, source lifecycle/rollback, complete Agent workflows, destination/browser evidence and full compatibility/release execution remain separate gates. The current report does not substitute for any of them. The exact recovered D25 prose has a separate provenance qualification owned by the integrator; its pre-rollback references must not be read as a claim that this new certificate is the missing historical certificate.

## Independent quantization review

[quantization-peer-review.json](quantization-peer-review.json) records the separate review of the reconstructed continuous recording bound, exact binary32 clock conversion and nonbinary Q16 phase handling. It identifies the exact five reviewed input files by size and SHA-256. The reviewed quantization document is 17,761 bytes with SHA-256 `ee8b60cf240615966f6c4f9724ec45fc7c90964ce7c6ff873b65e8b779520184`; its pure checker is 10,322 bytes with SHA-256 `80cc872c641a37e9f8773dabcbf4cb0af29974a3eabe099df27dc17e6425f2dd`.

The [independent peer checker](verify_quantization_peer.py) uses integer exponent/significand rounding to compare 3,052 fixed exact rational inputs against the author's binary32 bit-code search. Every case matched, and the author's 30 pure contract checks passed. The review also checks the continuous bound's mathematical argument, exact ideal derivative rates, complete touched-phase coverage and the uniform positional allowance for non-rigid matrix/vertex arithmetic. No blocking contract finding remains for these exact inputs. This is not evidence that an actual source or destination numerical kernel meets the bounds.

After integration, reproduce the fixed checks from the repository root with:

```sh
python3 docs/language-design/planar-reach-v0.1/numeric-review/verify_quantization_peer.py
```

For a separate proposal checkout, pass `--proposal-root` with that checkout's `docs/language-design/planar-reach-v0.1` directory. The checker refuses changed input hashes; another contract revision requires a fresh review. `--output` writes only a new report path and refuses to overwrite existing evidence.
