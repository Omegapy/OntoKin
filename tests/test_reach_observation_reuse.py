"""Shared physical operands never merge distinct source action observations."""
from __future__ import annotations

import copy
from fractions import Fraction as Q
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.bundle import load_file_manifest
from ontokin.construction import compile_construction
from ontokin.json_limits import measure_json
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.reach_runtime import ReachSimulator


DATA=Path(__file__).resolve().parents[1]/"docs/language-design/planar-reach-v0.1"


def simulator(name, *, capacity=None):
    directory=DATA/"draft2-supplements" if name.startswith("L") else DATA
    compiler=compile_construction(load_file_manifest(directory/(name.lower()+".files.json")))
    work=compiler.reach_work if capacity is None else ReachExecutionWork(max_cache_entries=capacity)
    return ReachSimulator(compiler.model,work=work)


class ReachObservationReuseTests(unittest.TestCase):
    def observed(self, name, time, side, *, reuse):
        sim=simulator(name)
        original=sim._current
        def current(path, time, side, state, *, observation_cache=None):
            return original(path,time,side,state,observation_cache=observation_cache if reuse else None)
        before=sim.work.operations
        with patch.object(sim,"_current",current):
            result=sim.advance(time,side)
        return result,sim.work.operations-before

    def test_128_distinct_actions_keep_complete_values_and_occurrence_counts(self):
        cached,cost=self.observed("P24",Q(1,4),"after",reuse=True)
        uncached,old_cost=self.observed("P24",Q(1,4),"after",reuse=False)
        self.assertEqual(cached,uncached)
        self.assertEqual(measure_json(cached),measure_json(uncached))
        self.assertEqual(len(cached["reaches"]),128)
        self.assertEqual(len({tuple(record["element_id"]) for record in cached["reaches"].values()}),128)
        self.assertLess(cost,old_cost)
        running=cached["reaches"]["reach"]["current"]["value"]
        pending=cached["reaches"]["pending_001"]["current"]["value"]
        self.assertEqual(running["lifecycle"],"running")
        self.assertEqual(pending["lifecycle"],"pending")
        self.assertEqual(len(running["claimed_joint_ids"]),2)
        self.assertEqual(pending["claimed_joint_ids"],[])
        self.assertIsNone(pending["resolved_joint_targets_rad"])
        self.assertEqual(running["tip_pose_base"],pending["tip_pose_base"])
        self.assertIsNot(running["tip_pose_base"],pending["tip_pose_base"])
        self.assertIsNot(running["tip_pose_base"]["position_m"],pending["tip_pose_base"]["position_m"])
        before=copy.deepcopy(pending["tip_pose_base"])
        running["tip_pose_base"]["position_m"][0]=999
        self.assertEqual(pending["tip_pose_base"],before)

    def test_snapshot_boundaries_targets_and_new_claim_owners_are_separate(self):
        for time,side in ((Q(0),"before"),(Q(0),"after"),(Q(3,4),"after")):
            with self.subTest(time=time,side=side):
                cached,_=self.observed("L02",time,side,reuse=True)
                uncached,_=self.observed("L02",time,side,reuse=False)
                self.assertEqual(cached,uncached)
                values=[record["current"]["value"] for record in cached["reaches"].values()]
                self.assertEqual(len(values),2)
                self.assertNotEqual(values[0]["current_world_target_m"],values[1]["current_world_target_m"])
                for value in values:
                    self.assertEqual(value["observation"]["side"],side)
                if time==Q(3,4):
                    self.assertEqual({value["lifecycle"] for value in values},{"stopped","running"})

    def test_snapshot_cache_capacity_and_cancellation_remain_bounded(self):
        sim=simulator("L02",capacity=1)
        original=sim._current
        caches=[]
        def current(path,time,side,state,*,observation_cache=None):
            result=original(path,time,side,state,observation_cache=observation_cache)
            caches.append(observation_cache)
            self.assertLessEqual(len(observation_cache),1)
            return result
        with patch.object(sim,"_current",current):
            first=sim._reach_map(Q(0),"before",sim.state)
            second=sim._reach_map(Q(0),"after",sim.state)
        self.assertEqual(len(first),2)
        self.assertEqual(len(second),2)
        self.assertIs(caches[0],caches[1])
        self.assertIs(caches[2],caches[3])
        self.assertIsNot(caches[0],caches[2])
        before=copy.deepcopy(sim.state)
        start=sim.work.counts.get("source_physical_observation_lookup",0)
        marker=RuntimeError("cancel repeated physical observation")
        def check():
            if sim.work.counts.get("source_physical_observation_lookup",0)>=start+2: raise marker
        sim.work.external_check=check
        with self.assertRaises(RuntimeError) as raised: sim._reach_map(Q(0),"before",sim.state)
        self.assertIs(raised.exception,marker)
        self.assertIs(sim.work.callback_error,marker)
        self.assertEqual(sim.state,before)


if __name__=="__main__": unittest.main()
