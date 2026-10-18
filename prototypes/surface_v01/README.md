# Surface 0.1 prototype (not an installed language profile)

This directory contains a bounded, independent geometry kernel and tests for the adopted [OK-LANG-003](../../docs/language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md) contract.

It is deliberately **outside** the published `ontokin` Python package. The released 0.4.0 compiler and its independently identified external construction evidence remain byte-for-byte unchanged while the new source grammar, typed values, GLB/0.3 serializer and agent/0.3 inspection contract are still being implemented. This separation is a version/provenance boundary, not evidence that the new surface language already executes.

Run the geometry/corpus/GLB tests with `python -m unittest discover -s tests -p 'test_surface_*.py' -v` from the repository root. Run `python -m tools.build_surface_prototype --output-dir /tmp/ontokin-surface-prototype` to create an actual region-material GLB, then run `node tools/verify_surface_prototype.mjs /tmp/ontokin-surface-prototype/offset-taper.glb` (after `npm ci --prefix tools --ignore-scripts`) for Khronos format and Three.js decoding checks. The profile is not ready for release until M01-M12 have been exercised through actual `.ok` compilation, source-driven local placement/material groups, artifact decode, and browser checks.
