# Keyed construction operations

[User guides](README.md) · [Project overview](../../README.md) · [Current status](../../STATUS.md)

Run command examples from the repository root with Python 3.11 or later. Each named profile keeps its own contract and evidence; the examples do not select a new default or establish a comparative authoring advantage.

## Select sparse per-key component overrides

Explicit source `0.21` / `keyed-membership-0.1` supports bounded, read-only keyed membership:

```ontokin
if has_key(overrides, key) then overrides[key] else defaults[key]
```

A pinned component library can select an optional override while preserving each occurrence's complete catalog, independently identifiable parts, appearance and recorded motion. The operation accepts an existing immutable keyed value and an exact String query, admits the complete input, and checks canonical keys under the current request's execution budget. Both results preserve actual dependencies and inherited provenance. Generated keyed views retain their existing access and taint restrictions. Invalid queries and unguarded missing lookups remain explicit errors.

```bash
python3 -m ontokin export examples/keyed-membership/agent/base.files.json --bundle --target ontokin.glb/0.21 --output /tmp/ontokin-sparse-panels.glb
python3 -m ontokin agent --protocol ontokin.agent/0.21 --store /tmp/ontokin-keyed-membership-agent
```

The [adopted decision](../../docs/language-design/keyed-membership-v0.1/ADOPTION.md), [language guide](../../docs/language-design/keyed-membership-v0.1/README.md), [Agent/0.21 guide](../../docs/language-design/agent-v0.21/README.md) and [C088 engineering record](../../docs/engineering/keyed-membership-2026-11-02-c088/README.md) identify the contract, independent inputs, actual checks and integration. An existing typed reduction/conditional helper remains a valid alternative for authored keyed leaves. This experimental convenience introduces no physical authority or measured authoring-benefit claim; complete feature release and full-product acceptance remain open.

## Give reusable part groups computed namespaces

Explicit source `0.20` / `string-concat-0.1` supports pure immutable String concatenation:

```ontokin
rekey_keyed<Length>(widths, (old_key, width) -> prefix + old_key)
```

A pinned library can receive different prefixes for independent occurrences while preserving each original payload and source dependency. Both operands evaluate once, in order. Results preserve exact Unicode text and are bounded to 65,536 UTF-8 bytes each and 4,194,304 cumulative logical result bytes per request. The existing admitted execution budget governs scanning, allocation and publication. Rekey retains its separate 1–64-character ASCII stable-key rule and collision refusal. Earlier declaring versions and ordinary defaults retain their meanings.

```bash
python3 -m ontokin export examples/string-concat/agent/panel-task.files.json --bundle --target ontokin.glb/0.20 --output /tmp/ontokin-namespaced-panels.glb
python3 -m ontokin agent --protocol ontokin.agent/0.20 --store /tmp/ontokin-string-concat-agent
```

The [adopted decision](../../docs/language-design/string-concat-v0.1/ADOPTION.md), [frozen corpus guide](../../docs/language-design/string-concat-v0.1/CORPUS.md), [Agent/0.20 guide](../../docs/language-design/agent-v0.20/README.md) and [C087 engineering record](../../docs/engineering/string-concat-2026-11-01-c087/README.md) distinguish meaning, executed checks and integration. The representative workflow changes one occurrence's prefix or member set while preserving its sibling, pinned library, image and unrelated recorded motion. Complete experimental-feature release and full-product acceptance remain open.

## Pair named attributes with exact key agreement

Explicit source `0.18` / `keyed-zip-0.1` combines corresponding entries from two immutable keyed values:

```ontokin
zip_keyed<Length, Length, Area>(widths, heights,
    (key, width, height) -> width * height)
```

Both inputs must have exactly the same complete key set. The operation admits the left input once, then the right, refuses the first missing partner in canonical ASCII order, and runs the pure body once per matched key. Input and result types are exact; at most 256 entries are allowed. Inspection retains both original contributors, aggregate dependencies, and detached paired provenance through later construction.

```bash
python3 -m ontokin export examples/keyed-zip/panel-task.files.json --bundle --target ontokin.glb/0.18 --output /tmp/ontokin-paired-panels.glb
python3 -m ontokin agent --protocol ontokin.agent/0.18 --store /tmp/ontokin-keyed-zip-agent
```

The [versioned decision](../../docs/language-design/keyed-zip-v0.1/ADOPTION.md), [independent frozen examples](../../examples/keyed-zip/README.md), [Agent/0.18 guide](../../docs/language-design/agent-v0.18/README.md), and [C085 engineering record](../../docs/engineering/keyed-zip-2026-11-01-c085/README.md) distinguish the contract, actual execution, and integration. Separate keyed dimension and material libraries support an atomic repair of one textured occurrence while preserving its sibling and unrelated motion. Ordinary budgets and earlier defaults remain unchanged. This selected experimental capability adds no physical or motion authority; complete feature release and full-product acceptance remain open.

## Combine named part groups with explicit collision refusal

Explicit source `0.17` / `keyed-merge-0.1` combines two immutable keyed values with the same exact element type:

```ontokin
merge_keyed<Length>(standard_widths, optional_widths)
```

The operation evaluates and fully admits the left input once, then the right input once. It refuses the lowest shared ASCII key even when its values are equal. A disjoint result keeps original keys and detached typed values in canonical order, with at most 256 entries. Both inputs' actual dependencies and source origins remain available through later construction and inspection.

```bash
python3 -m ontokin export examples/keyed-merge/panel-task.files.json --bundle --target ontokin.glb/0.17 --output /tmp/ontokin-merged-panels.glb
python3 -m ontokin agent --protocol ontokin.agent/0.17 --store /tmp/ontokin-keyed-merge-agent
```

The [versioned decision](../../docs/language-design/keyed-merge-v0.1/ADOPTION.md), [frozen examples](../../examples/keyed-merge/README.md), [Agent/0.17 guide](../../docs/language-design/agent-v0.17/README.md) and [C084 engineering record](../../docs/engineering/keyed-merge-2026-11-01-c084/README.md) separate semantics, actual verification and integration. The representative repair adds and then removes an optional vent in one occurrence while preserving its standard panels, sibling, pinned image and unrelated recorded motion. This explicit experimental capability keeps ordinary 100,000-operation / 30,000-ms defaults and adds no physical or motion authority. Complete feature release and full-product acceptance remain open.

## Select optional keyed parts while preserving surviving identities

Explicit source `0.16` / `keyed-filter-0.1` adds a bounded pure selection:

```ontokin
filter_keyed<Length>(widths, (key, width) -> width >= 1.5[m])
```

The input is evaluated once. A strict Boolean predicate visits at most 256 entries in canonical ASCII key order, retaining original keys and detached values for survivors. Empty input still receives static predicate checking. Filtering composes with mapping and reduction to select optional parts while preserving exact source repair authority and every actual dependency, including when no entries survive.

```bash
python3 -m ontokin export examples/keyed-filter/panel-task.files.json --bundle --target ontokin.glb/0.16 --output /tmp/ontokin-filtered-panels.glb
python3 -m ontokin agent --protocol ontokin.agent/0.16 --store /tmp/ontokin-keyed-filter-agent
```

The [versioned decision](../../docs/language-design/keyed-filter-v0.1/ADOPTION.md), [frozen examples](../../examples/keyed-filter/README.md), [Agent/0.16 guide](../../docs/language-design/agent-v0.16/README.md) and [C083 engineering record](../../docs/engineering/keyed-filter-2026-10-31-c083/README.md) identify semantics, actual repair evidence and remaining gates. The representative repair removes one occurrence's left panel while preserving its right panel, sibling, pinned image and unrelated recorded motion. This experimental construction operation preserves ordinary defaults of 100,000 operations / 30,000 ms and adds no physical or motion authority. Complete feature release and full-product acceptance remain open.

## Compute reusable construction parameters from keyed values

Explicit source `0.15` / `keyed-reduction-0.1` adds a bounded pure aggregate with an explicit typed seed:

```ontokin
reduce_keyed<Length>(dimensions, 0[m], (total, key, value) -> total + value)
```

The input is admitted once, then the seed is evaluated once. A pure body processes at most 256 entries sequentially in canonical ASCII key order, preserving every intermediate type, unit, frame, domain and resource check. Empty input returns a detached seed after static body checking. This composes with `map_keyed` to derive reusable dimensions, offsets and other admitted construction values.

```bash
python3 -m ontokin export examples/keyed-reduction/panel-task.files.json --bundle --target ontokin.glb/0.15 --output /tmp/ontokin-keyed-panels.glb
python3 -m ontokin agent --protocol ontokin.agent/0.15 --store /tmp/ontokin-keyed-reduction-agent
```

The [versioned decision](../../docs/language-design/keyed-reduction-v0.1/ADOPTION.md), [frozen examples](../../examples/keyed-reduction/README.md) and [Agent/0.15 guide](../../docs/language-design/agent-v0.15/README.md) define the contract. Inspection preserves detached reduction provenance for exact source repair. The [C082 engineering record](../../docs/engineering/keyed-reduction-2026-10-31-c082/README.md) separates actual source, Agent, delivered-stream and native-view evidence from complete release acceptance. Ordinary defaults remain 100,000 operations / 30,000 ms; larger requests require current host authority. Older bindings and defaults retain their meanings. This experimental construction operation adds no physical or motion authority.
