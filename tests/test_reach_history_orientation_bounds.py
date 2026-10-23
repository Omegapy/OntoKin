"""Independent history orientation proofs preserve raw quaternion semantics."""
from copy import deepcopy
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import reach_conformance as reader
from ontokin.diagnostics import OntoKinError
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work
from ontokin.reach_reference import Interval


def cells(values, width=F(0)):
    return tuple(Interval(F(value)-width, F(value)+width) for value in values)


def compare(actual, expected, allowance, work=None, *, sufficient=True):
    arithmetic = reader._Bounds(work or Work())
    with patch.object(reader, '_history_orientation_sufficient',
                      wraps=reader._history_orientation_sufficient if sufficient else None,
                      **({} if sufficient else {'return_value':False})):
        reader._assert_projection(list(actual), expected, arithmetic=arithmetic,
                                  allowances={'rotation':allowance}, path=('orientation_wxyz',))
    return arithmetic.work


class HistoryOrientationBoundsTests(unittest.TestCase):
    def test_small_independent_error_avoids_norms_and_reduces_actual_work(self):
        source=cells((F(3,5),F(4,5),0,0),F(1,1<<80))
        actual=(.6,.8+2.**-45,0.,0.)
        work=Work()
        with patch.object(reader._Bounds,'difference',side_effect=AssertionError('unneeded norm')):
            compare(actual,source,F(1,10**12),work)
        ordinary=compare(actual,source,F(1,10**12),sufficient=False)
        self.assertLess(work.operations,ordinary.operations)
        self.assertEqual(work.max_operations,100000)
        self.assertLessEqual(len(work._cache),256)

    def test_antipodal_sign_and_raw_nonunit_values_preserve_existing_meaning(self):
        source=cells((F(3,5),F(4,5),0,0),F(1,1<<80))
        for actual in ((.6,.8+2.**-45,0.,0.),(-.6,-.8-2.**-45,0.,0.)):
            compare(actual,source,F(1,10**12))
        for sufficient in (True,False):
            with self.subTest(sufficient=sufficient),self.assertRaises(OntoKinError) as caught:
                compare((1.2,1.6,0.,0.),source,F(1,10**12),sufficient=sufficient)
            self.assertEqual(caught.exception.diagnostic.details['export_code'],'OKE-E-BOUNDARY-HISTORY')

    def test_insufficient_l1_bound_keeps_a_passing_euclidean_comparison(self):
        source=cells((1,0,0,0));actual=(1.0001,.0001,0.,0.)
        with patch.object(reader._Bounds,'difference',autospec=True,
                          side_effect=reader._Bounds.difference) as norm:
            compare(actual,source,F(15,100000))
        self.assertEqual(norm.call_count,2)
        compare(actual,source,F(15,100000),sufficient=False)

    def test_tighter_allowance_and_changed_history_cannot_borrow_a_pass(self):
        source=cells((F(3,5),F(4,5),0,0),F(1,1<<80));actual=(.6,.8+2.**-45,0.,0.)
        work=compare(actual,source,F(1,10**12))
        for raw,limit in ((actual,F(0)),((.6,.9,0.,0.),F(1,10**12)),(actual,F(-1))):
            with self.subTest(raw=raw,limit=limit),self.assertRaises(OntoKinError):
                compare(raw,source,limit,work)

    def test_narrow_initial_or_callback_domain_retains_original_root_failure(self):
        source=cells((1,0,0,0));actual=(1.,1/1024,0.,0.)
        for checkpoint in (None,'independent_history_orientation_domain','independent_quaternion_sign'):
            work=Work(max_operand_bits=128 if checkpoint is None else 32768)
            original=work.charge
            def charge(kind='checkpoint',amount=1):
                result=original(kind,amount)
                if kind==checkpoint: work.max_operand_bits=128
                return result
            with self.subTest(checkpoint=checkpoint),patch.object(work,'charge',charge),self.assertRaises(ReachAdmissionError) as caught:
                compare(actual,source,F(1,10),work)
            self.assertEqual(caught.exception.details['limit'],128)

    def test_cancellation_preserves_original_exception_and_cache(self):
        source=cells((1,0,0,0));work=Work();saved=deepcopy(work._cache)
        marker=RuntimeError('cancel history comparison');original=work.charge
        def charge(kind='checkpoint',amount=1):
            if kind=='independent_history_orientation_domain':
                def fail(): raise marker
                work.external_check=fail
            return original(kind,amount)
        with patch.object(work,'charge',charge),self.assertRaises(RuntimeError) as caught:
            compare((1.,.001,0.,0.),source,F(1,10),work)
        self.assertIs(caught.exception,marker);self.assertIs(work.callback_error,marker)
        self.assertEqual(work._cache,saved)

    def test_malformed_and_overwide_members_retain_rejection(self):
        source=cells((1,0,0,0))
        bad=((False,0.,0.,0.),(float('nan'),0.,0.,0.),(float('inf'),0.,0.,0.),(1<<32768,0,0,0))
        for actual in bad:
            with self.subTest(kind=type(actual[0]).__name__),self.assertRaises((OntoKinError,ReachAdmissionError)):
                compare(actual,source,F(1,10))
        reversed_cell=Interval(F(0),F(1))
        object.__setattr__(reversed_cell,'lo',F(1))
        object.__setattr__(reversed_cell,'hi',F(0))
        with self.assertRaises(OntoKinError):
            compare((1.,0.,0.,0.),(reversed_cell,*source[1:]),F(1,10))

    def test_ordinary_and_sufficient_outcomes_match_across_small_exact_cells(self):
        for sign in (-1,1):
            for delta in (0.,2.**-45,2.**-30,.001):
                for width in (F(0),F(1,1<<80),F(1,1<<30)):
                    source=cells((F(3,5),F(4,5),0,0),width)
                    actual=(sign*.6,sign*(.8+delta),0.,0.)
                    outcomes=[]
                    for sufficient in (False,True):
                        try: compare(actual,source,F(1,10**10),sufficient=sufficient);outcomes.append('passed')
                        except OntoKinError as e: outcomes.append(e.diagnostic.details.get('export_code',e.diagnostic.code))
                    self.assertEqual(outcomes[0],outcomes[1],(sign,delta,width))


if __name__=='__main__': unittest.main()
