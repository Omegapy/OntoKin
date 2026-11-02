# Optional keyed component configuration

These examples select source `0.21` / `keyed-membership-0.1`. `has_key(collection, query)` allows a reusable component to test a sparse override before using the existing keyed lookup. Read the [language guide](../../docs/language-design/keyed-membership-v0.1/README.md), [adoption](../../docs/language-design/keyed-membership-v0.1/ADOPTION.md) and [Agent guide](../../docs/language-design/agent-v0.21/README.md) for the exact boundaries.

The [base program](agent/base.files.json) has two independent occurrences of one pinned three-panel library. The first overrides its left panel width; the sibling overrides its right panel width. The [inserted](agent/inserted.files.json), [updated](agent/updated.files.json), [removed](agent/removed.files.json) and [restored](agent/restored.files.json) programs demonstrate changes to the first occurrence. The [reordered](agent/reordered.files.json) source preserves canonical results, and [unused override](agent/unused-override.files.json) demonstrates that an unused override does not generate a new panel. The [invalid selected width](agent/invalid-selected.files.json) is an intentional geometry refusal. The [empty collection](empty.files.json) example returns false for a valid absent key.

The `reduction-*` and `literal-*` programs explicitly retain source `.20`; they provide independently authored equivalent controls with their own pinned library variants. They are not automatically migrated to `.21`.

Export the base program through its explicit recorded destination:

```bash
python3 -m ontokin export examples/keyed-membership/agent/base.files.json --bundle --target ontokin.glb/0.21 --output /tmp/keyed-membership.glb
```

Serve the corresponding local Agent contract:

```bash
python3 -m ontokin agent --protocol ontokin.agent/0.21 --store /tmp/keyed-membership-agent
```

The [source-copy inventory](EXACT-FROZEN-SOURCE-COPIES.json) ties every executable example byte to the independently published acceptance inputs. Expected results, stage schedules, protocol requests, complete artifact comparisons and hostile-reader requirements remain in the [frozen packet](../../docs/language-design/keyed-membership-v0.1/freeze/README.md). Passing one example alone does not establish those larger scopes.
