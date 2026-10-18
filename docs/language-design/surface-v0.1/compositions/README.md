# Native source composition companions

These additional `.ok` fixtures exercise the adopted M05 composition and M09
rotation/release requirements. They reuse the **unchanged** pinned
`../01-surface-parts.ok` bytes. They do not replace the frozen Studio source or
change `../acceptance.json`.

`expected.json` fixes source identities, scalar geometry definitions, keyed
part counts, material values and independent motion formulas before the new
workflow is executed. It contains no derived triangles or runtime observations.

- `ordinary.ok` declares two ordinary parts using the imported Shell directly.
  Explicit follows place them on a translating empty carrier; ownership alone
  does not provide a motion relationship.
- `generated-one.ok`, `generated-three.ok` and `generated-seven.ok` reuse a
  subclass of that same Shell. One declaration generates **1, 3 and 7** parts.
  The surviving `a`, `d` and `g` keys keep their independently fixed dimensions.
  The subclass adds an explicit mounting follow while inheriting the native
  loft, its default palette and its local visual offset.
- `rotated-release.ok` reuses the frozen rings and palette on two native visual
  objects with explicit sphere physical proxies. A carrier translated at
  `(1, 0, 0) m/s` has a constant 90 degree Z rotation. The local visual transform
  is `(0.2, -0.1, 0.3) m` and a 90 degree X rotation. The falling proxy releases
  at 1 s using incoming velocity; its center is
  `(t, 2.5 - 5*max(0, t-1)^2, 0) m`. The held sibling remains at
  `(t+2, 2.5, 0) m`. Both carrier orientations remain the authored Z rotation.

Run `python3 tools/build_surface_agent_demo.py --output-dir /tmp/ontokin-surface-agent-demo`
from the repository root. The tool sends actual Agent/0.3 JSON operations,
retains each request/response and source snapshot, and reconstructs GLBs only
from the service's bounded artifact chunks. Independent destination/browser
tools validate those exact bytes separately. A successful corpus build alone
does not complete M01–M12, the full native surface release or GOAL.
