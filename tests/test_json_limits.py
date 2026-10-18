"""Bounded JSON must measure the same built-in values that it serializes."""
import json
import random
import unittest
from unittest.mock import patch

from ontokin.json_limits import JSONLimitError, bounded_dumps, measure_json


class JSONLimitsTests(unittest.TestCase):
    def assert_rejected_before_encoding(self, value):
        with patch('ontokin.json_limits.json.dumps',
                   side_effect=AssertionError('encoding happened before rejection')):
            with self.assertRaisesRegex(ValueError, 'Unsupported JSON value type:'):
                bounded_dumps(value)

    def test_dictionary_cannot_hide_values_from_the_byte_guard(self):
        class HiddenValues(dict):
            def values(self):
                return iter(())

        self.assert_rejected_before_encoding(HiddenValues(payload='x' * 256))

    def test_dictionary_cannot_substitute_items_during_encoding(self):
        class ChangedItems(dict):
            def items(self):
                raise AssertionError('custom items method must not run')

        self.assert_rejected_before_encoding(ChangedItems(payload='x'))

    def test_dictionary_length_hook_is_not_called(self):
        class HookedDict(dict):
            def __len__(self):
                raise AssertionError('custom length method must not run')

        self.assert_rejected_before_encoding(HookedDict(payload='x'))

    def test_dictionary_iteration_hook_is_not_called(self):
        class HookedDict(dict):
            def __iter__(self):
                raise AssertionError('custom iteration method must not run')

        self.assert_rejected_before_encoding(HookedDict(payload='x'))

    def test_list_length_hook_is_not_called(self):
        class HookedList(list):
            def __len__(self):
                raise AssertionError('custom length method must not run')

        self.assert_rejected_before_encoding(HookedList([1, 2, 3]))

    def test_list_iteration_hook_is_not_called(self):
        class HookedList(list):
            def __iter__(self):
                raise AssertionError('custom iteration method must not run')

        self.assert_rejected_before_encoding(HookedList([1, 2, 3]))

    def test_tuple_length_hook_is_not_called(self):
        class HookedTuple(tuple):
            def __len__(self):
                raise AssertionError('custom length method must not run')

        self.assert_rejected_before_encoding(HookedTuple((1, 2, 3)))

    def test_tuple_iteration_hook_is_not_called(self):
        class HookedTuple(tuple):
            def __iter__(self):
                raise AssertionError('custom iteration method must not run')

        self.assert_rejected_before_encoding(HookedTuple((1, 2, 3)))

    def test_nested_custom_containers_are_also_rejected(self):
        class CustomDict(dict):
            pass

        class CustomList(list):
            pass

        class CustomTuple(tuple):
            pass

        for value in (CustomDict(a=1), CustomList([1]), CustomTuple((1,))):
            with self.subTest(kind=type(value).__name__):
                self.assert_rejected_before_encoding({'outer': [value]})

    def test_container_type_equality_hook_is_not_called(self):
        class HookedType(type):
            def __eq__(cls, other):
                raise AssertionError('custom type equality must not run')

        class CustomList(list, metaclass=HookedType):
            pass

        self.assert_rejected_before_encoding(CustomList([1, 2, 3]))

    def test_builtin_scalars_and_containers_keep_exact_utf8_sizes(self):
        values = [None, True, False, 0, -17, 1.25, -0.0, 1e-100,
                  '', 'plain', 'é中😀', '\\"\b\f\n\r\t\u0000\u001f',
                  {}, [], (), {'é': ['x', {}, [], (False, None)]},
                  {'b': 1, 'a': 2}, {'payload': 'x' * 256}]
        for value in values:
            with self.subTest(value=value):
                expected = json.dumps(value, sort_keys=True, ensure_ascii=False,
                                      separators=(',', ':'), allow_nan=False)
                self.assertEqual(bounded_dumps(value), expected)
                self.assertEqual(measure_json(value)['bytes'],
                                 len(expected.encode('utf-8')))

    def test_all_control_character_and_unicode_sizes_match_encoding(self):
        text = ''.join(chr(n) for n in range(128)) + 'é中😀\u2028\u2029'
        expected = json.dumps(text, ensure_ascii=False, separators=(',', ':'))
        self.assertEqual(measure_json(text)['bytes'], len(expected.encode('utf-8')))
        self.assertEqual(bounded_dumps(text), expected)

    def test_exact_byte_boundary_is_accepted_and_one_byte_less_is_rejected(self):
        value = {'payload': ['é😀', 17, None]}
        expected = bounded_dumps(value)
        size = len(expected.encode('utf-8'))
        self.assertEqual(bounded_dumps(value, max_bytes=size), expected)
        with self.assertRaises(JSONLimitError) as caught:
            bounded_dumps(value, max_bytes=size - 1)
        self.assertEqual(caught.exception.details['budget'], 'encoded_json_bytes')
        self.assertEqual(caught.exception.details['limit'], size - 1)

    def test_shared_values_count_each_logical_occurrence(self):
        shared = ['x'] * 10
        value = [shared] * 10
        self.assertEqual(measure_json(value, max_entries=111)['entries'], 111)
        with self.assertRaises(JSONLimitError) as caught:
            measure_json(value, max_entries=110)
        self.assertEqual(caught.exception.details,
                         {'budget': 'logical_json_entries', 'limit': 110,
                          'consumed': 111})

    def test_depth_boundary_is_preserved(self):
        value = {'a': [(None,)]}
        self.assertEqual(measure_json(value, max_depth=3)['entries'], 4)
        with self.assertRaises(JSONLimitError) as caught:
            measure_json(value, max_depth=2)
        self.assertEqual(caught.exception.details,
                         {'budget': 'json_depth', 'limit': 2, 'consumed': 3})

    def test_cycles_are_rejected_but_noncyclic_shared_containers_are_valid(self):
        sequence = []
        sequence.append(sequence)
        mapping = {}
        mapping['self'] = mapping
        bridge = []
        tuple_cycle = (bridge,)
        bridge.append(tuple_cycle)
        for value in (sequence, mapping, tuple_cycle):
            with self.subTest(kind=type(value).__name__), self.assertRaisesRegex(
                    ValueError, 'cyclic'):
                measure_json(value)
        shared = {'a': []}
        self.assertEqual(bounded_dumps([shared, shared]), '[{"a":[]},{"a":[]}]')

    def test_oversized_shared_values_are_rejected_before_encoding(self):
        value = {'data': ['x' * 100000] * 50}
        with patch('ontokin.json_limits.json.dumps',
                   side_effect=AssertionError('unbounded encoding attempted')):
            with self.assertRaises(JSONLimitError):
                bounded_dumps(value)

    def test_nonfinite_numbers_and_surrogate_strings_remain_invalid(self):
        for value in (float('inf'), float('-inf'), float('nan'), '\ud800',
                      '\udfff', {'\ud800': 0}):
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):
                measure_json(value)

    def test_nonstring_keys_and_scalar_subclasses_remain_invalid(self):
        class CustomString(str):
            pass

        class CustomInt(int):
            pass

        for value in ({1: 'x'}, {CustomString('x'): 1}, CustomString('x'),
                      CustomInt(3), set(), object()):
            with self.subTest(kind=type(value).__name__), self.assertRaises(ValueError):
                measure_json(value)

    def test_cancellation_exception_is_not_swallowed(self):
        class Cancelled(Exception):
            pass

        def cancel():
            raise Cancelled()

        with self.assertRaises(Cancelled):
            measure_json(['x'] * 200, check=cancel)

    def test_deterministic_builtin_corpus_matches_encoder(self):
        rng = random.Random(20261018)
        atoms = [None, True, False, 0, -1, 2**63, 0.25, -0.0,
                 '', 'x', 'é中😀', '\\"\n\u0000']

        def make_value(depth):
            if depth == 0 or rng.randrange(4) == 0:
                return rng.choice(atoms)
            count = rng.randrange(5)
            kind = rng.randrange(3)
            if kind == 0:
                return [make_value(depth - 1) for _ in range(count)]
            if kind == 1:
                return tuple(make_value(depth - 1) for _ in range(count))
            return {f'key-{i}': make_value(depth - 1) for i in range(count)}

        for case in range(300):
            value = make_value(4)
            with self.subTest(case=case):
                expected = json.dumps(value, sort_keys=True, ensure_ascii=False,
                                      separators=(',', ':'), allow_nan=False)
                size = len(expected.encode('utf-8'))
                self.assertEqual(measure_json(value)['bytes'], size)
                self.assertEqual(bounded_dumps(value, max_bytes=size), expected)
                with self.assertRaises(JSONLimitError):
                    bounded_dumps(value, max_bytes=size - 1)


if __name__ == '__main__':
    unittest.main()
