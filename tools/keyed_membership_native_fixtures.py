"""Independent safe construction of the frozen native adversary descriptions.

No production operation is imported here. The caller supplies the already
selected runtime classes after execution is authorized. Foreign hooks are traps
whose invocation is evidence of an admission bug, never an expected answer.
"""
from __future__ import annotations


class ForeignMethodCalled(AssertionError):
    pass


class TrapState:
    def __init__(self):
        self.calls = []

    def trip(self, method):
        self.calls.append(method)
        raise ForeignMethodCalled("Foreign method was called during bounded native admission: " + method)


def trap_types(state):
    class Foreign:
        def __eq__(self, other): return state.trip("foreign.__eq__")
        def __hash__(self): return state.trip("foreign.__hash__")
        def __str__(self): return state.trip("foreign.__str__")
        def __repr__(self): return state.trip("foreign.__repr__")
        def __len__(self): return state.trip("foreign.__len__")
        def __iter__(self): return state.trip("foreign.__iter__")

    class StringSubclass(str):
        def __eq__(self, other): return state.trip("str_subclass.__eq__")
        def __hash__(self): return state.trip("str_subclass.__hash__")
        def __str__(self): return state.trip("str_subclass.__str__")
        def __len__(self): return state.trip("str_subclass.__len__")

    class IntSubclass(int):
        def __eq__(self, other): return state.trip("int_subclass.__eq__")
        def __lt__(self, other): return state.trip("int_subclass.__lt__")
        def __gt__(self, other): return state.trip("int_subclass.__gt__")
        def __hash__(self): return state.trip("int_subclass.__hash__")

    class TupleSubclass(tuple):
        def __iter__(self): return state.trip("tuple_subclass.__iter__")
        def __len__(self): return state.trip("tuple_subclass.__len__")
        def __getitem__(self, key): return state.trip("tuple_subclass.__getitem__")

    return Foreign, StringSubclass, IntSubclass, TupleSubclass


class NativeFactory:
    def __init__(self, Type, Value, KeyedValue, UNKNOWN):
        self.Type, self.Value, self.KeyedValue, self.UNKNOWN = Type, Value, KeyedValue, UNKNOWN

    def descriptor(self, record):
        child = record.get("element")
        return self.Type(record["kind"],
                         dimension=None if record.get("dimension") is None else tuple(record["dimension"]),
                         element=None if child is None else self.descriptor(child),
                         name=record.get("name"))

    def malformed_type(self, defect, state):
        T = self.Type
        Foreign, StringSubclass, IntSubclass, TupleSubclass = trap_types(state)
        class TypeSubclass(T):
            pass
        if defect in ("not_type", "leaf_type_not_type"): return Foreign()
        if defect == "type_subclass": return TypeSubclass("Int")
        if defect in ("kind_nonstring", "kind_foreign_eq_hash"): return T(Foreign())
        if defect == "kind_string_subclass": return T(StringSubclass("Int"))
        if defect == "kind_33_chars": return T("x" * 33)
        if defect == "unknown_kind": return T("ForeignLeaf")
        if defect == "simple_dimension_non_none": return T("Int", dimension=(1, 0, 0, 0))
        if defect == "simple_element_non_none": return T("Int", element=T("Real"))
        if defect == "simple_name_non_none": return T("Int", name="extra")
        if defect == "none_equal_object": return T("Int", name=Foreign())
        if defect == "quantity_dim_list": return T("Quantity", dimension=[1, 0, 0, 0])
        if defect == "quantity_dim_tuple_subclass": return T("Quantity", dimension=TupleSubclass((1, 0, 0, 0)))
        if defect == "quantity_dim_arity3": return T("Quantity", dimension=(1, 0, 0))
        if defect == "quantity_dim_bool": return T("Quantity", dimension=(True, 0, 0, 0))
        if defect == "quantity_dim_int_subclass": return T("Quantity", dimension=(IntSubclass(1), 0, 0, 0))
        if defect == "quantity_dim_plus17": return T("Quantity", dimension=(17, 0, 0, 0))
        if defect == "quantity_dim_minus17": return T("Quantity", dimension=(-17, 0, 0, 0))
        if defect == "quantity_dim_all_zero": return T("Quantity", dimension=(0, 0, 0, 0))
        if defect == "quantity_element_non_none": return T("Quantity", dimension=(1, 0, 0, 0), element=T("Real"))
        if defect == "quantity_name_non_none": return T("Quantity", dimension=(1, 0, 0, 0), name="extra")
        if defect == "dimension_foreign_eq_hash": return T("Quantity", dimension=Foreign())
        if defect == "vec_child_non_type": return T("Vec3", element=Foreign())
        if defect == "vec_child_type_subclass": return T("Vec3", element=TypeSubclass("Real"))
        if defect == "vec_child_bool_kind": return T("Vec3", element=T("Bool"))
        if defect == "vec_child_vec3": return T("Vec3", element=T("Vec3", element=T("Real")))
        if defect == "vec_dimension_non_none": return T("Vec3", element=T("Real"), dimension=(1, 0, 0, 0))
        if defect == "vec_name_non_none": return T("Vec3", element=T("Real"), name="extra")
        if defect == "point3_child_real": return T("Point3", element=T("Real"))
        if defect == "point3_child_wrong_dimension": return T("Point3", element=T("Quantity", dimension=(0, 0, 1, 0)))
        if defect == "point3_child_non_type": return T("Point3", element=Foreign())
        if defect == "ref_empty_name": return T("Ref", name="")
        if defect == "ref_279_name": return T("Ref", name="C" * 279)
        if defect == "ref_name_subclass": return T("Ref", name=StringSubclass("C"))
        if defect == "ref_name_foreign_eq": return T("Ref", name=Foreign())
        if defect == "ref_dimension_non_none": return T("Ref", name="C", dimension=(1, 0, 0, 0))
        if defect == "ref_element_non_none": return T("Ref", name="C", element=T("Int"))
        if defect == "cyclic_element":
            value = T("Vec3")
            object.__setattr__(value, "element", value)
            return value
        if defect == "deep_chain_10000":
            value = T("Real")
            for _ in range(10000):
                value = T("Vec3", element=value)
            return value
        raise ValueError("Unimplemented frozen native Type defect: " + defect)

    def build(self, case):
        """Return (raw collection, query, resolved expected leaf Type, traps)."""
        T, V, K = self.Type, self.Value, self.KeyedValue
        state = TrapState()
        Foreign, StringSubclass, _, _ = trap_types(state)
        expected = T("Int")
        keys = list(case.get("base_keys", case.get("keys", ["a"])))
        entries = tuple((key, V(T("Int"), 1)) for key in keys)
        query = case.get("query", "a")
        if "descriptor" in case:
            expected = self.descriptor(case["descriptor"])
            entries = tuple((key, V(self.descriptor(case["descriptor"]), Foreign())) for key in keys)
            return K(entries), query, expected, state
        defect = case.get("defect")
        if defect is None:
            return K(entries), query, expected, state
        where = case.get("metadata_location")
        if where is not None:
            if defect == "leaf_not_value":
                return K((("a", Foreign()),)), query, expected, state
            bad = self.malformed_type(defect, state)
            if where == "collection":
                expected = bad
            else:
                entries = (("a", V(bad, 1)),)
            return K(entries), query, expected, state
        if defect == "different_valid_type":
            expected = self.descriptor(case["expected_descriptor"])
            entries = (("a", V(self.descriptor(case["leaf_descriptor"]), 1)),)
        elif defect == "entries_list":
            return K(list(entries)), query, expected, state
        elif defect == "keyed_subclass":
            class KeyedSubclass(K):
                pass
            return KeyedSubclass(entries), query, expected, state
        elif defect == "entry_list": entries = (["a", V(T("Int"), 1)],)
        elif defect == "entry_arity_one": entries = (("a",),)
        elif defect == "key_int": entries = ((1, V(T("Int"), 1)),)
        elif defect == "key_str_subclass": entries = ((StringSubclass("a"), V(T("Int"), 1)),)
        elif defect == "key_empty": entries = (("", V(T("Int"), 1)),)
        elif defect == "value_subclass":
            class ValueSubclass(V):
                pass
            entries = (("a", ValueSubclass(T("Int"), 1)),)
        elif defect == "different_value_type": entries = (("a", V(T("Bool"), True)),)
        elif defect == "unknown_value_payload": entries = (("a", V(T("Int"), self.UNKNOWN)),)
        elif defect == "duplicate_second_key": entries = (("a", V(T("Int"), 1)), ("a", V(T("Int"), 2)))
        elif defect == "descending_second_key": entries = (("b", V(T("Int"), 1)), ("a", V(T("Int"), 2)))
        elif defect == "257_entries": entries = tuple((f"k{i:03d}", V(T("Int"), i)) for i in range(257))
        elif defect == "query_native_int": query = 1
        elif defect == "query_str_subclass": query = StringSubclass("a")
        elif defect == "leaf_not_value": entries = (("a", Foreign()),)
        elif defect == "leaf_type_not_type": entries = (("a", V(Foreign(), 1)),)
        elif defect == "second_leaf_not_value": entries = (("a", V(T("Int"), 1)), ("b", Foreign()))
        elif defect == "second_leaf_unknown": entries = (("a", V(T("Int"), 1)), ("b", V(T("Int"), self.UNKNOWN)))
        else:
            raise ValueError("Unimplemented frozen native fixture: " + str(defect))
        return K(entries), query, expected, state

    def callback(self, case, collection, expected, state):
        """Use real frozen dataclass fields; never mutate a global Type singleton."""
        changed = []
        target = case["mutation_before_stage"]
        first_leaf = collection.entries[0][1]
        if expected is first_leaf.type:
            raise AssertionError("Captured-Type fixture must use distinct fresh Type objects.")
        def mutation(stage):
            if changed or stage != target:
                return
            if case["id"] == "capture-entry-tuple":
                object.__setattr__(collection, "entries", (("z", self.Value(self.Type("Int"), 1)),))
            elif case["id"] == "capture-expected-descriptor":
                object.__setattr__(expected, "kind", "Bool")
            elif case["id"] == "no-payload-reread":
                object.__setattr__(first_leaf, "value", self.UNKNOWN)
            else:
                raise ValueError("Unknown captured-state fixture")
            changed.append({"stage": stage, "case": case["id"]})
        return mutation, changed
