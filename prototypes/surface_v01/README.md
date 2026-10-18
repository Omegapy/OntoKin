# Surface 0.1 prototype (not an installed language profile)

This directory contains a bounded, independent geometry kernel and tests for the adopted [OK-LANG-003](../../docs/language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md) contract.

It is deliberately **outside** the published `ontokin` Python package. The released 0.4.0 compiler and its independently identified external construction evidence remain byte-for-byte unchanged while the new source grammar, typed values, GLB/0.3 serializer and agent/0.3 inspection contract are still being implemented. This separation is a version/provenance boundary, not evidence that the new surface language already executes.

Run the geometry tests with `python -m unittest tests.test_surface_geometry -v` from the repository root. The profile is not ready for release until M01-M12 have been exercised through actual `.ok` compilation, source-driven local placement/material groups, artifact decode, and browser checks.
