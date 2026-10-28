"""Prepare a new passive boundary driver; this script executes no product code."""
from pathlib import Path

root = Path('/workspace/scratch/fd65650eb54f/OntoKin/docs/engineering/reach-recording-validation-2026-10-23')
source = (root / 'checkpoint-033-capture.py').read_text()

def change(old, new):
    global source
    assert source.count(old) == 1, (old[:80], source.count(old))
    source = source.replace(old, new)

change('"""Capture original P11/L03 endpoint boundaries without replacing arithmetic.',
       '"""Prepared C046 driver for a later original-L03 passive boundary capture.\n\n+Not executed in C046. Source review and preparation do not establish neutrality.\n+This extends the two C033 wrappers; it installs no trace/profile/monitor hook.')
change('import sys\n', 'import sys\nimport subprocess\n')
change('choices=("P11", "L03")', 'choices=("L03",)')
change('    args = parser.parse_args(argv)', '''    parser.add_argument("--expected-source-commit", required=True)
    parser.add_argument("--expected-source-tree", required=True)
    args = parser.parse_args(argv)''')
change('    sys.path.insert(0, str(root))', '''    # Source identity checks happen before any OntoKin import or request.
    def git(*arguments):
        return subprocess.check_output(["git", *arguments], cwd=root, text=True).strip()
    assert git("rev-parse", "HEAD") == args.expected_source_commit
    assert git("rev-parse", "HEAD^{tree}") == args.expected_source_tree
    assert git("status", "--porcelain") == ""
    sys.path.insert(0, str(root))''')
change('center._CenteredNode: ("vector", "position_radius", "identity_offset", "coefficient_source", "seal"),',
       'center._CenteredNode: ("vector", "position_radius", "identity_offset", "coefficient_source", "product_pair", "product_owner", "seal"),')
change('    def source_state(reference, arithmetic):', '''    def ordered_cache_snapshot(source):
        """Detach keys and native metadata without source lookup/promotion.

        Value identities are run-local labels, never reusable numerical data.
        Exact coefficient keys and tuple shapes are observed; integer widths
        describe values but do not establish equality across different runs.
        """
        own = object.__getattribute__(source, "__dict__")
        cache = own["cache"]
        assert type(cache) is dict and len(cache) <= 256
        tally, rows = [0], []
        for ordinal, (key, value) in enumerate(dict.items(cache)):
            assert type(key) is tuple and key and type(key[0]) is str
            row = {"ordinal": ordinal, "key": frozen(key, tally=tally),
                   "value_object_id": id(value), "value_type_object_id": id(type(value))}
            if key[0] == "series_coefficients":
                assert len(key) == 4 and all(type(v) is int for v in key[1:])
                assert type(value) is tuple and len(value) == 3
                coefficients, denominator, lane = value
                assert type(coefficients) is tuple and len(coefficients) <= 65
                assert all(type(v) is int and abs(v).bit_length() <= 32768
                           for v in (*coefficients, denominator, lane))
                row["series_value"] = {"coefficient_count": len(coefficients),
                    "coefficient_bits": tuple(abs(v).bit_length() for v in coefficients),
                    "denominator_bits": abs(denominator).bit_length(),
                    "lane_bits": abs(lane).bit_length(),
                    "native_immutable_integer_tuple_shape": True}
            rows.append(row)
        assert all(type(own[name]) is int for name in ("bits", "scale", "_cache_operand_limit"))
        return {"cache_object_id": id(cache), "ordered_rows": rows,
                "source_domain": {name: own[name] for name in ("bits", "scale", "_cache_operand_limit")},
                "observation_kind": "boundary snapshot; no intra-key operation event is observed"}

    def source_state(reference, arithmetic):''')
change('                "source_cursors": cursors, "source_batch": batch_record}',
       '                "source_cursors": cursors, "source_batch": batch_record,\n                "source_cache_ordered_snapshot": ordered_cache_snapshot(source)}')
change('                           "registered_time": ratio(time), "node_paths": tuple(node.path for node in plan.nodes)}',
       '                           "registered_time": ratio(time), "node_paths": tuple(node.path for node in plan.nodes),\n                           "centered_recipe_fields": None if plan.centered is None else frozen(plan.centered)}')
old = '''            elif filename == rr.__file__ and function in ("exact", "_series_coefficients", "_series_integer"):
                names = ("a", "b", "kind") if function == "exact" else (
                    ("common", "odd", "index", "degree", "exponent", "denominator", "lane", "coefficient", "packed")
                    if function == "_series_coefficients" else ("a", "b", "kind"))
                selected = {name: frozen(local[name]) for name in names
                            if name in local and type(local[name]) in (str, int, float, Fraction, bool)}'''
new = '''            elif filename == rr.__file__:
                names = {
                    "exact": ("a", "b", "kind"),
                    "_series_integer": ("a", "b", "kind"),
                    "_series_coefficients": ("key", "cached", "common", "odd", "index", "degree", "exponent",
                        "denominator", "lane", "coefficient", "packed", "coefficients", "factorials"),
                    "_series_dyadic": ("middle", "squared", "exponent", "degree", "limit", "last", "width"),
                    "lookup": ("key", "value"),
                    "remember": ("key",),
                }.get(function, ())
                selected = {name: frozen(local[name]) for name in names if name in local}
                owner = local.get("self")
                if selected and type(owner) is rr._Arithmetic:
                    own = object.__getattribute__(owner, "__dict__")
                    selected["native_domain_fields"] = {name: frozen(own[name])
                        for name in ("bits", "scale", "_cache_operand_limit")}
                    selected["source_cache_ordered_snapshot"] = ordered_cache_snapshot(owner)'''
change(old, new)
source = source.replace('ontokin.source-endpoint-capture/0.1', 'ontokin.l03-boundary-capture/0.1')
source = source.replace('ontokin.source-endpoint-ledger/0.1', 'ontokin.l03-boundary-ledger/0.1')
source = source.replace('ontokin.source-endpoint-failure-locals/0.1', 'ontokin.l03-boundary-failure-locals/0.1')
change('        "reader_calls": retained["reader_calls"], "key_calls": retained["key_calls"],',
       '        "reader_calls": retained["reader_calls"], "key_calls": retained["key_calls"],\n        "expected_source_commit": args.expected_source_commit, "expected_source_tree": args.expected_source_tree,\n        "boundary_only": True, "intra_key_lookup_publication_eviction_events": None,\n        "elapsed_neutrality_claimed": False,')
(root / 'checkpoint-046-capture.py').write_text(source)
print('Prepared C046 capture source; no product imports or requests executed.')
