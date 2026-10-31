# C080 input erratum 001: two invalid positive controls

The published original input freeze remains commit
`4e5da7152e775b065299f2000ca80d51301bcd21`, tree
`34cac914450fb5c7d2a5264d00e632f00f35e561`. None of its 314 files changes.
Its first actual execution at implementation commit
`c83cfcffc86af4cdcaa67ab7be9d49592cfd0de7` refused two inputs that had been
predetermined as valid. Those original expectations remain failed observations.
The correction directory retains both original receipts and the complete first
producer summary verbatim, including the unrelated implementation/harness
failures observed in that run.

## Separate corrected inputs

| Original case | Actual first refusal | Exact correction |
| --- | --- | --- |
| T035 `inherited-loft` | `OKL-E-SURFACE-FACETS`: the inherited loft requires at least 8 facets and a count divisible by four. | Change only the facets literal `4` to `8` in separately copied textured source and its separately copied untextured .12 control. |
| T102 `older-user-function-png-asset` | `OKL-E-SYNTAX`: `digest` is a reserved token, so it cannot name a parameter. | Rename that parameter to `digest_text` in a separately copied .12 module, then update the exact module hash in separately copied .13 entry and .12 control. |

Neither correction changes an existing parser, inherited source semantics,
texture declaration rules, material behavior, budget, geometric tolerance, or
acceptance criterion. The ordinary user-defined function remains named
`png_asset`, its unqualified call remains in the .12 module, and its qualified
call remains in the .13 caller. That control still has an empty asset set.

The eight-facet loft has 18 logical ring/cap-center positions and 32 triangles.
For radius and height both one meter, its regular-octagon volume is
`2*sqrt(2)` cubic meters and its area is
`4*sqrt(2)+16*sin(pi/8)` square meters. These are analytic source-derived facts.
The corrected expected file includes independently computed source corner UV
probes using exact rational evaluation of the binary64 source coordinates and
mapping, followed by binary64 and binary32 rounding. No produced mesh supplies
those expectations. The original generic affine probe points and four-facet
source remain visible in the immutable original input.

## Corpus version 2 and evidence policy

`examples/textured-surfaces-corrections/active-corpus.json` names all 102 active
cases explicitly: 100 cases reference the original freeze unchanged, and the
two corrected cases reference separate expected files with old/new program
identities and original refusal receipts. The source/image identity algorithm
is unchanged. The label PNG copied for the loft remains byte-for-byte equal to
its original pinned image.

`author_corrections.py` uses Python's standard library only. It copies evidence,
performs the two constrained edits, derives new exact source/import/manifest
pins and analytic expectations, and writes `correction-freeze.json`. The latter
inventories every correction input and provenance file except itself and binds
this document. Root publication of the correction's exact bytes and commit,
following independent static review, must precede corrected runtime execution.

Tools must select corpus version 2 explicitly and record both the original
freeze and correction freeze identities. They may not silently reinterpret the
old expected-valid inputs as accepted, hide the first refusals, or modify the
original freeze to make a later result appear to have passed earlier.
