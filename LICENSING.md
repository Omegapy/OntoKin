# OntoKin licensing and attribution

Copyright 2026 Alexander Samuel Ricciardi
Project: https://github.com/Omegapy/OntoKin

## License coverage

| Material | License | Governing terms |
| --- | --- | --- |
| Original OntoKin source code, scripts, executable tests, build/configuration files and code examples (including `.ok` programs and executable examples within documentation) | Apache License, Version 2.0 (SPDX: `Apache-2.0`) | [LICENSE](LICENSE); [LICENSE-CODE](LICENSE-CODE) retains the existing complete copy and copyright preamble |
| Original explanatory documentation, specifications, plans, essays, and non-code templates | Creative Commons Attribution 4.0 International (`CC-BY-4.0`) | [LICENSE-DOCS](LICENSE-DOCS) |
| Third-party software, copied upstream sources and externally supplied fixtures | The original license indicated with that material | Preserve the applicable source and attribution notices |

This scope applies only to content that its respective copyright holder is authorized to license, and is subject to any more specific notice associated with a component. A code block in documentation does not become CC BY 4.0 merely because the surrounding explanation is.

## Copyright and attribution

The original OntoKin software was developed by **Alexander Samuel Ricciardi**, whose GitHub account is **Omegapy**. The applicable copyright and attribution notices are retained in [NOTICE](NOTICE).

Apache-2.0 permits commercial use, redistribution and modification under its terms. Redistributors must preserve applicable copyright and attribution notices and, where applicable, the contents of the NOTICE file, according to Section 4. The license does **not** require an on-screen credit for every product that uses OntoKin. The NOTICE file adds attribution information, not new license restrictions.

The `[yyyy]` and `[name of copyright owner]` fields appearing in the *appendix of the standard Apache License text* are instructional examples that must remain unchanged; they are not missing values in OntoKin's own notices.

## Known third-party exceptions

- `examples/visual/viewer.bundle.js` incorporates **three.js**, licensed under the MIT License; the bundled copyright and license are recorded in [examples/visual/THREE-LICENSE.txt](examples/visual/THREE-LICENSE.txt).
- [examples/splat-composite/fixtures/external/LICENSE-lux.txt](examples/splat-composite/fixtures/external/LICENSE-lux.txt) records the MIT License and copyright of **rudybear** for the corresponding external fixture material.
- The retained Blender upstream reference in `docs/engineering/normal-codec-c213/upstream/` includes GPL licensing information, with `COPYING` and `GPL-license.txt`. It is not relicensed as Apache-2.0 by this repository's top-level license.

These examples do not constitute an exhaustive inventory of third-party material. When using any copied or externally supplied material, inspect its own provenance and license.

## New original files

For a newly authored first-party source file, an optional short file header is:

```text
Copyright 2026 Alexander Samuel Ricciardi
SPDX-License-Identifier: Apache-2.0
```

Adapt it to the file's comment syntax. Do not add this ownership declaration to third-party files or material whose copyright belongs to another contributor.

The complete Apache-2.0 terms reside at [LICENSE](LICENSE). The CC BY 4.0 terms remain at [LICENSE-DOCS](LICENSE-DOCS). Neither license text has been modified to add attribution requirements.
