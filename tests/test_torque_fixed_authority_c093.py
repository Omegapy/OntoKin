"""C093 fixed-catalog specialization equivalence and executable ownership."""
import dis
from itertools import chain, repeat
from operator import is_
from types import FunctionType
import unittest
from unittest.mock import patch

from ontokin import torque_canonical_spin as canonical
from ontokin import torque_runtime as runtime


def record(function):
    return (function, function.__code__, function.__defaults__, function.__kwdefaults__,
            function.__closure__, function.__globals__, function.__builtins__,
            None if function.__kwdefaults__ is None else tuple(function.__kwdefaults__.items()))


def original_functions(compiled):
    functions, attributes, keywords = compiled[:3]
    if not all(map(is_, chain.from_iterable(map(canonical._FUNCTION_ATTRIBUTES, functions)), attributes)):
        return False
    for owner, length, expected in keywords:
        if len(owner) != length or not all(map(is_, chain.from_iterable(dict.items(owner)), expected)):
            return False
    return True


def original_bindings(compiled, getter=dict.get, contains=dict.__contains__):
    owners, names, expected, absent_owners, absent_names, missing = compiled[:6]
    return (not any(map(contains, absent_owners, absent_names))
            and all(map(is_, map(getter, owners, names, repeat(missing)), expected)))


class FixedAuthorityC093Tests(unittest.TestCase):
    def test_original_function_slots_and_in_place_keyword_values_remain_live(self):
        token = object()
        def function(value=token, *, first=token, second=None):
            return value
        def changed(value=None, *, first=None, second=None):
            raise AssertionError('A source function body must not execute in admission')
        compiled = canonical._compile_functions((record(function),))
        self.assertIsNotNone(compiled[3])
        original_code, original_defaults = function.__code__, function.__defaults__
        original_keywords = function.__kwdefaults__
        for field, value in (('__code__', changed.__code__), ('__defaults__', (object(),)),
                             ('__kwdefaults__', dict(original_keywords))):
            with self.subTest(field=field):
                saved = getattr(function, field)
                setattr(function, field, value)
                try:
                    self.assertFalse(original_functions(compiled))
                    self.assertFalse(canonical._functions_current(compiled))
                finally:
                    setattr(function, field, saved)
        foreign = []
        class ForeignEquality:
            def __eq__(self, other):
                foreign.append(other)
                raise AssertionError('Foreign value equality executed')
        original_keywords['first'] = ForeignEquality()
        try:
            self.assertFalse(original_functions(compiled))
            self.assertFalse(canonical._functions_current(compiled))
            self.assertEqual(foreign, [])
        finally:
            original_keywords['first'] = token
        self.assertIs(function.__code__, original_code)
        self.assertIs(function.__defaults__, original_defaults)
        self.assertTrue(canonical._functions_current(compiled))

    def test_keyword_length_key_identity_and_iteration_order_are_preserved(self):
        token = object()
        def function(*, first=token, second=None):
            return first
        compiled = canonical._compile_functions((record(function),))
        mapping = function.__kwdefaults__
        saved = tuple(mapping.items())
        replacements = (
            saved[:1],
            tuple(reversed(saved)),
            ((b'first'.decode(), saved[0][1]), saved[1]),
        )
        self.assertIsNot(replacements[2][0][0], saved[0][0])
        for entries in replacements:
            with self.subTest(entries=len(entries)):
                mapping.clear()
                mapping.update(entries)
                try:
                    self.assertFalse(original_functions(compiled))
                    self.assertFalse(canonical._functions_current(compiled))
                finally:
                    mapping.clear()
                    mapping.update(saved)
        self.assertTrue(canonical._functions_current(compiled))

    def test_generated_executable_slots_are_sealed_before_foreign_code(self):
        def native():
            return None
        compiled = canonical._compile_functions((record(native),))
        generated = compiled[3][0]
        saved = (generated.__code__, generated.__defaults__, generated.__kwdefaults__)
        calls = []
        sentinel = RuntimeError('C093 foreign generated body')
        def foreign():
            calls.append('executed')
            raise sentinel
        def changed(getter, contains):
            return _c093_foreign_callback()
        code = changed.__code__.replace(co_freevars=generated.__code__.co_freevars)
        namespace = generated.__globals__
        self.assertNotIn('_c093_foreign_callback', namespace)
        namespace['_c093_foreign_callback'] = foreign
        try:
            # Prove the replacement is an executable foreign-body control.
            activation = FunctionType(code, namespace, closure=generated.__closure__)
            with self.assertRaises(RuntimeError) as control:
                activation(dict.get, dict.__contains__)
            self.assertIs(control.exception, sentinel)
            self.assertEqual(calls, ['executed'])
            calls.clear()
            for field, value in (('__code__', code), ('__defaults__', (object(),)),
                                 ('__kwdefaults__', {'unused': object()})):
                with self.subTest(field=field):
                    previous = getattr(generated, field)
                    setattr(generated, field, value)
                    try:
                        self.assertFalse(canonical._functions_current(compiled))
                        self.assertEqual(calls, [])
                    finally:
                        setattr(generated, field, previous)
        finally:
            generated.__code__, generated.__defaults__, generated.__kwdefaults__ = saved
            del namespace['_c093_foreign_callback']
        self.assertTrue(canonical._functions_current(compiled))

    def test_binding_generators_preserve_orders_and_actual_passed_callables(self):
        token, missing = object(), object()
        owner = {'present': token}
        rows = ((owner, 'present', token), (owner, 'absent', missing))
        compiled = canonical._compile_bindings(rows)
        log = []
        def getter(mapping, name, fallback):
            log.append(('get', name))
            return dict.get(mapping, name, fallback)
        def contains(mapping, name):
            log.append(('contains', name))
            return dict.__contains__(mapping, name)
        self.assertTrue(canonical._bindings_current(compiled, getter, contains))
        self.assertEqual(log, [('contains', 'absent'), ('get', 'present')])
        log.clear()
        self.assertTrue(original_bindings(compiled, getter, contains))
        self.assertEqual(log, [('contains', 'absent'), ('get', 'present')])
        entry = canonical.compile_point_entry(((), (), rows))
        log.clear()
        self.assertTrue(entry[2][0](getter, contains))
        self.assertEqual(log, [('get', 'present'), ('contains', 'absent')])
        owner['absent'] = missing
        try:
            log.clear()
            self.assertFalse(canonical._bindings_current(compiled, getter, contains))
            self.assertEqual(log, [('contains', 'absent')])
            log.clear()
            self.assertFalse(entry[2][0](getter, contains))
            self.assertEqual(log, [('get', 'present'), ('contains', 'absent')])
        finally:
            del owner['absent']
        # A different supplied getter must not silently use a captured one.
        self.assertFalse(canonical._bindings_current(compiled, lambda *args: missing, contains))

    def test_present_removal_and_absent_sentinel_plant_cannot_impersonate_ownership(self):
        token = object()
        owner = {'present': token}
        compiled = canonical._compile_bindings(((owner, 'present', token),
                                                (owner, 'absent', canonical._MISSING)))
        self.assertTrue(canonical._bindings_current(compiled))
        del owner['present']
        self.assertFalse(canonical._bindings_current(compiled))
        owner['present'] = token
        for value in (canonical._MISSING, compiled[5]):
            owner['absent'] = value
            try:
                self.assertFalse(original_bindings(compiled))
                self.assertFalse(canonical._bindings_current(compiled))
            finally:
                del owner['absent']

    def test_all_ten_actual_generated_predicates_have_no_namespace_resolution(self):
        receipts = [canonical._AUTHORITY[5][0][3], canonical._POINT_AUTHORITY[5][0][3],
                    canonical._RUNTIME_BINDING[5][0][3], canonical._AUTHORITY[5][2][6],
                    canonical._POINT_AUTHORITY[5][2][6], canonical._RUNTIME_BINDING[5][1][6],
                    canonical._RUNTIME_BINDING[5][3][6], *runtime._CANONICAL_POINT_ENTRY[11]]
        self.assertEqual(len(receipts), 10)
        forbidden = {'LOAD_GLOBAL', 'LOAD_NAME', 'IMPORT_NAME', 'IMPORT_FROM', 'IMPORT_STAR',
                     'STORE_GLOBAL', 'STORE_NAME', 'DELETE_GLOBAL', 'DELETE_NAME'}
        for receipt in receipts:
            with self.subTest(bytecode_bytes=len(receipt[1].co_code)):
                function = receipt[0]
                self.assertIsNone(function.__defaults__)
                self.assertIsNone(function.__kwdefaults__)
                self.assertFalse(forbidden.intersection(i.opname for i in dis.get_instructions(function)))
                self.assertFalse(any(type(value) is type(function.__code__)
                                     for value in function.__code__.co_consts))
                self.assertLessEqual(len(receipt[-1].encode('ascii')), canonical._PREDICATE_TEXT_BYTES)

    def test_comparison_and_text_caps_keep_the_original_generic_result(self):
        def native():
            return None
        records = (record(native),) * (canonical._PREDICATE_COMPARISONS // 3 + 1)
        functions = canonical._compile_functions(records)
        self.assertIsNone(functions[3])
        self.assertTrue(canonical._functions_current(functions))
        original = native.__defaults__
        native.__defaults__ = ()
        try:
            self.assertFalse(original_functions(functions))
            self.assertFalse(canonical._functions_current(functions))
        finally:
            native.__defaults__ = original
        owner, token = {}, object()
        owner['name'] = token
        bindings = canonical._compile_bindings(((owner, 'name', token),)
                                               * (canonical._PREDICATE_COMPARISONS + 1))
        self.assertIsNone(bindings[6])
        self.assertTrue(canonical._bindings_current(bindings))
        owner['name'] = object()
        self.assertFalse(original_bindings(bindings))
        self.assertFalse(canonical._bindings_current(bindings))
        with patch.object(canonical, '_PREDICATE_TEXT_BYTES', 1):
            short = canonical._compile_functions((record(native),))
        self.assertIsNone(short[3])
        self.assertTrue(original_functions(short))
        self.assertTrue(canonical._functions_current(short))


if __name__ == '__main__':
    unittest.main()
