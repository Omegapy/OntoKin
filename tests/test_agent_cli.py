"""Real process/JSONL checks for the durable agent transport."""

from __future__ import annotations

import json
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import time
import unittest

from test_agent import PROJECT, ROOT, RESPONSE_SCHEMA, VALID_SOURCE, request, schema_errors


class AgentCLITests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ontokin-agent-cli-")
        self.directory = Path(self.temporary.name)
        self.store = self.directory / "state"
        self.serial = 0

    def tearDown(self):
        self.temporary.cleanup()

    def command(self):
        return [sys.executable, "-m", "ontokin", "agent", "--store", str(self.store)]

    def run_request(self, submitted, *, wait=True):
        self.serial += 1
        path = self.directory / f"request-{self.serial}.json"
        path.write_text(json.dumps(submitted, ensure_ascii=False), encoding="utf-8")
        command = self.command() + ["--request", str(path)] + (["--wait"] if wait else [])
        process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=20)
        try:
            response = json.loads(process.stdout)
        except json.JSONDecodeError:
            self.fail(f"CLI did not return one JSON value: {process.stdout!r}; stderr={process.stderr!r}")
        self.assertEqual(schema_errors(response, RESPONSE_SCHEMA), [], response)
        return response, process

    def create_request(self, identity="create"):
        return request("create", identity, filename="service.ok", source=VALID_SOURCE,
                       expected_revision=None, requested_level="represented", budgets={})

    def test_receipt_survives_exit_and_same_request_completes_once(self):
        submitted = self.create_request()
        receipt, process = self.run_request(submitted, wait=False)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(receipt["status"], "queued")
        completed, process = self.run_request(submitted)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(completed["status"], "succeeded", completed)
        repeated, process = self.run_request(dict(reversed(list(submitted.items()))))
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(repeated, completed)
        evaluation, process = self.run_request(request("evaluate", "evaluate", source_revision=completed["source_revision"],
                                                       run_id=None, until_seconds="0.5", budgets={}))
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(evaluation["status"], "succeeded", evaluation)
        self.assertTrue(evaluation["run_id"])

    def test_jsonl_returns_one_receipt_per_line_and_status_does_not_repeat_work(self):
        process = subprocess.Popen(self.command(), cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, bufsize=1)
        exchanges = 0

        def exchange(submitted):
            nonlocal exchanges
            process.stdin.write(json.dumps(submitted, ensure_ascii=False) + "\n")
            process.stdin.flush()
            self.assertTrue(select.select([process.stdout], [], [], 10)[0], "No immediate JSONL response")
            line = process.stdout.readline()
            self.assertTrue(line, "Service ended before returning a response")
            response = json.loads(line)
            self.assertEqual(schema_errors(response, RESPONSE_SCHEMA), [], response)
            self.assertEqual(response["request_id"], submitted["request_id"])
            exchanges += 1
            return response

        try:
            submitted = self.create_request()
            receipt = exchange(submitted)
            self.assertEqual(receipt["status"], "queued")
            deadline = time.monotonic() + 10
            target = None
            index = 0
            while time.monotonic() < deadline:
                status = exchange(request("status", f"status-{index}", target_request_id=submitted["request_id"]))
                self.assertEqual(status["status"], "succeeded")
                target = status["result"]["target"]
                if target["status"] not in ("queued", "running"):
                    break
                index += 1
                time.sleep(0.01)
            self.assertIsNotNone(target)
            self.assertEqual(target["status"], "succeeded", target)
            replay = exchange(submitted)
            self.assertEqual(replay, target)
            process.stdin.close()
            process.wait(timeout=10)
            self.assertEqual(process.returncode, 0, process.stderr.read())
            self.assertEqual(process.stdout.read(), "", "Worker emitted an unsolicited extra response")
            self.assertGreaterEqual(exchanges, 3)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None and not stream.closed:
                    stream.close()

    def test_invalid_json_is_reported_without_ending_the_jsonl_stream(self):
        discover = request("discover", "discover", profile="core-0.1", limit=5)
        data = '{"broken":\n' + json.dumps(discover) + "\n"
        process = subprocess.run(self.command(), input=data, cwd=ROOT, capture_output=True,
                                 text=True, timeout=15)
        lines = process.stdout.splitlines()
        self.assertEqual(len(lines), 2, (process.stdout, process.stderr))
        invalid, continued = [json.loads(line) for line in lines]
        self.assertEqual(schema_errors(invalid, RESPONSE_SCHEMA), [], invalid)
        self.assertEqual(invalid["status"], "rejected")
        self.assertIsNotNone(invalid["protocol_error"])
        self.assertIsNone(invalid["source_revision"])
        self.assertEqual(invalid["diagnostics"], [])
        self.assertEqual(schema_errors(continued, RESPONSE_SCHEMA), [], continued)
        self.assertEqual(continued["request_id"], "discover")
        self.assertIn(continued["status"], ("queued", "running", "succeeded"))

    def test_unknown_request_fields_are_rejected_before_acceptance(self):
        malformed = {**self.create_request("malformed"), "execute_python": "unexpected"}
        rejected, _ = self.run_request(malformed)
        self.assertEqual(rejected["status"], "rejected")
        self.assertIsNotNone(rejected["protocol_error"])
        self.assertEqual(rejected["diagnostics"], [])
        self.assertIsNone(rejected["accepted_revision"])
        successful, process = self.run_request(self.create_request("corrected"))
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(successful["status"], "succeeded", successful)

    def test_queued_work_can_be_cancelled_from_a_reconnected_process(self):
        submitted = self.create_request()
        receipt, _ = self.run_request(submitted, wait=False)
        self.assertEqual(receipt["status"], "queued")
        cancelled, process = self.run_request(request("cancel", "cancel", target_request_id=submitted["request_id"]))
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(cancelled["status"], "succeeded")
        self.assertEqual(cancelled["result"]["target_status"], "cancelled")
        retry, _ = self.run_request(submitted)
        self.assertEqual(retry["status"], "cancelled")
        created, process = self.run_request(self.create_request("deliberate-new-create"))
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(created["status"], "succeeded", created)

    def test_transport_rejects_ambiguous_invalid_and_deep_bytes_then_continues(self):
        duplicate = b'{"schema_version":"ontokin.agent/0.1","project_id":"p","request_id":"duplicate","operation":"status","operation":"cancel","target_request_id":"unknown"}'
        nested = b'[' * 1500 + b'0' + b']' * 1500
        non_utf8 = b'{"source":"\xff"}'
        surrogate = b'{"schema_version":"ontokin.agent/0.1","project_id":"\\ud800","request_id":"surrogate","operation":"status","target_request_id":"unknown"}'
        huge_number = b'{"value":' + b'9' * 5000 + b'}'
        malformed = [duplicate, nested, non_utf8, surrogate, huge_number]
        valid = json.dumps(request("status", "continued", target_request_id="unknown")).encode("utf-8")
        process = subprocess.run(self.command(), input=b"\n".join(malformed + [valid]) + b"\n", cwd=ROOT,
                                 capture_output=True, timeout=15)
        self.assertEqual(process.returncode, 0, process.stderr.decode("utf-8", errors="replace"))
        lines = process.stdout.decode("utf-8").splitlines()
        self.assertEqual(len(lines), len(malformed) + 1, lines)
        for raw in lines[:-1]:
            response = json.loads(raw)
            self.assertEqual(schema_errors(response, RESPONSE_SCHEMA), [], response)
            self.assertEqual(response["status"], "rejected")
            self.assertIsNotNone(response["protocol_error"])
            self.assertEqual(response["diagnostics"], [])
            self.assertIsNone(response["accepted_revision"])
        continued = json.loads(lines[-1])
        self.assertEqual(schema_errors(continued, RESPONSE_SCHEMA), [], continued)
        self.assertEqual(continued["request_id"], "continued")
        self.assertEqual(continued["status"], "succeeded")
        self.assertEqual(continued["result"]["target_status"], "unknown_outcome")


if __name__ == "__main__":
    unittest.main()
