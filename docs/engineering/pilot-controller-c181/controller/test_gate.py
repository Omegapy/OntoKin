import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

from gate import Gate, Stopped, normalize
from preflight import probe


class Accounting(unittest.TestCase):
    def test_inclusive_equals_disjoint(self):
        u = normalize(dict(fullInput=10, cachedInput=2, output=3))
        self.assertEqual(u, normalize(dict(uncachedInput=8, cachedInput=2, output=3)))
        self.assertEqual(u["charged"], 13)

    def test_malformed_usage(self):
        for usage in [dict(fullInput=1,cachedInput=2,output=1),
                      dict(fullInput=1,cachedInput=0,output=True),
                      dict(fullInput=1,uncachedInput=1,cachedInput=0,output=1),
                      dict(fullInput=-1,cachedInput=0,output=1),
                      dict(fullInput=1,output=0),dict(fullInput=0,cachedInput=0,output=1)]:
            with self.subTest(usage=usage), self.assertRaises((KeyError, ValueError)):
                normalize(usage)

    def test_fixture_aggregate_and_deadline(self):
        with tempfile.TemporaryDirectory() as td:
            backend = Path(td) / "fixture.py"
            backend.write_text("import json,sys\nr=json.load(sys.stdin)\n"
                              "print(json.dumps(dict(requestId=r['requestId'],snapshot=r['snapshot'],"
                              "text='X',source='FIXTURE ONLY',usage=dict(fullInput=5,cachedInput=2,output=1))))\n")
            d = Path(td) / "results"
            result = probe(d, [sys.executable,"-I",str(backend)], "fixture", 5)
            self.assertTrue(result["wallPassed"] and result["tokenPassed"])
            self.assertFalse(result["admitted"])
            events = [json.loads(line) for line in (d/"events.jsonl").read_text().splitlines()]
            self.assertEqual(sum(e["event"]=="refused" for e in events), 4)
            self.assertEqual(result["charged"], 12)

    def test_failed_or_overrun_receipts_stop_model_and_tool(self):
        with tempfile.TemporaryDirectory() as td:
            for n, expr in enumerate(["{}", "dict(requestId='bad',snapshot='x',text='y',source='fixture',"
                "usage=dict(fullInput=2,cachedInput=0,output=1))",
                "dict(requestId=r['requestId'],snapshot='x',text='y',source='fixture',"
                "usage=dict(fullInput=12,cachedInput=0,output=1))"]):
                with self.subTest(expr=expr), (Path(td)/str(n)).open("w") as trace:
                    gate = Gate(3, 12, trace, "negative control")
                    client=[sys.executable,"-I","-c","import json,sys;r=json.load(sys.stdin);print(json.dumps("+expr+"))"]
                    with self.assertRaises(Stopped):
                        gate.infer(client, "benign", "x", 1)
                    for kind in ("model","tool"):
                        with self.assertRaises(Stopped):
                            gate.invoke(kind, ["/missing/after/stop"])
                    self.assertNotEqual(gate.stopped, "launch failed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
