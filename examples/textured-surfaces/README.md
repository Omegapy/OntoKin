# Textured native surfaces: independent C080 inputs

The [adopted C080 decision](../../docs/language-design/textured-surfaces-v0.1/ADOPTION.md) selects source .13, bundle/files .2, Agent .13 and recorded GLB .13. This corpus freezes input and expected behavior before runtime implementation.

The source corpus has 102 cases: {'valid': 45, 'resource_rejected': 1, 'source_rejected': 56}. Separate transport cases, file-path cases, Agent workflows and hostile supplied-GLB controls remain separately counted. None is an executed pass.

Start with `rgb-panel.files.json`, `warning-panel.files.json` and `marked-tray.files.json`. Each manifest supplies exact source and image bytes under this folder. `expected.json` records source/asset revisions, mapping equations and probes, image pixels and hashes, geometry/motion invariants and finite limits. `workflow-controls.json` prescribes the actual Agent lifecycle and supplied-artifact adversaries.

The pinned library examples cover independent siblings, source-only mapping and image-selection repair, generated occurrences and rollback. The legacy-name control preserves an earlier user function called `png_asset`; textual name matching must not turn it into a .13 asset declaration.

`maximum-decoded-one` and `maximum-decoded-four` require explicit independent host ceilings of 2000000 operations / 80000 ms. Defaults elsewhere remain 100000 operations / 30000 ms. Asset limits and geometry/motion contracts remain separate from runtime grants.

See [AUTHORING.md](AUTHORING.md) for independent methods. `acceptance-freeze.json` binds the exact source/assets/expectations and the published decision. Full appearance/product release, Unreal import, live physics and inherited incomplete gates are not established here.
