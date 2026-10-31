# Explicit C080 corrected input corpus

Read `docs/language-design/textured-surfaces-v0.1/INPUT-ERRATA-001.md` for the
two independently diagnosed fixture defects and the narrow corrections.

The immutable original corpus stays in `examples/textured-surfaces`. This
directory is a separately versioned input supplement: `active-corpus.json`
selects 100 exact original cases and two explicitly corrected cases. Its
`first-failure` directory retains original observed refusals and the first full
producer summary unchanged. A corrected pass never converts an original
failure into a historical pass.

`correction-freeze.json` pins all supplement files except itself. Its own hash
and published Git identity must be recorded by the caller before the first
corrected runtime execution. The authoring script uses no product code and
must not be rerun after this correction freeze has been published.
