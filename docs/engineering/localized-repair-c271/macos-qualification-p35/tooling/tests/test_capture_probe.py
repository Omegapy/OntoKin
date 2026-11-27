"""Focused tests of capture_probe.py (FC-P3, FC-P6 and FC-K5) and of the procedure's text.

The recorded processes are this test's own children: this interpreter with -B, waiting on its stdin in
a new session, and /usr/bin/true. The started records are written by this test as the runner writes
them, with the supervisor's record under /process. Children of the test process: those, and the
interpreter with -I -S -B for each probe start."""
from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import unittest
from unittest import mock

import mh_support as S

WAIT_ON_STDIN = "import sys; sys.stdin.read()"
IGNORE_SIGTERM = "import signal, sys; signal.signal(signal.SIGTERM, signal.SIG_IGN); sys.stdin.read()"


class CaptureWorld:
    def __init__(self, test):
        self.test, self.base = test, S.resolved_temp(test)
        self.children = []
        test.addCleanup(self.cleanup)

    def cleanup(self):
        for child in self.children:
            if child.poll() is None:
                child.kill()
            child.wait()
            for stream in (child.stdin,):
                if stream is not None:
                    stream.close()

    def child(self, code=WAIT_ON_STDIN):
        child = S.start_child([S.PYTHON, "-B", "-c", code], stdin=subprocess.PIPE, start_new_session=True)
        self.children.append(child)
        return child

    def record(self, name, data):
        path = self.base + "/" + name
        S.write(path, data)
        return path

    def started(self, name, child, argv0, code=WAIT_ON_STDIN):
        process = {"argv": [argv0, "-B", "-c", code], "pid": child.pid, "process_group": child.pid,
                   "label": "synthetic"}
        return self.record(name, json.dumps({"schema": "synthetic", "state": "STARTED", "process": process}).encode())

    def pair(self, *, argv0=None, intent_after_start=False, code=WAIT_ON_STDIN):
        """An intent record, one start, and its started record, in the order the runner writes them."""
        if not intent_after_start:
            intent = self.record("intent-%d.json" % len(os.listdir(self.base)), b'{"state": "INTENT"}')
            time.sleep(0.02)
        child = self.child(code)
        time.sleep(0.2)
        if intent_after_start:
            intent = self.record("intent-%d.json" % len(os.listdir(self.base)), b'{"state": "INTENT"}')
            time.sleep(0.02)
        started = self.started("started-%d.json" % len(os.listdir(self.base)), child,
                               S.process_image() if argv0 is None else argv0, code)
        return child, intent, started

    def run(self, *args, reap=()):
        """One probe start; children that end meanwhile are reaped, so that their group can become absent."""
        output = self.base + "/capture-%d.json" % len(os.listdir(self.base))
        tool = S.start_tool("capture_probe.py", *args, "--output", output, flags=("-I", "-S", "-B"),
                            env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"})
        deadline = time.monotonic() + 60
        while tool.poll() is None:
            for child in reap:
                child.poll()
            self.test.assertLess(time.monotonic(), deadline, "the probe did not end")
            time.sleep(0.005)
        _, stderr = tool.communicate()
        return tool.returncode, stderr, S.read_json(output)


class ProbeTests(unittest.TestCase):
    def test_a_present_process_with_an_established_identity(self):
        world = CaptureWorld(self)
        child, intent, started = world.pair()
        code, stderr, record = world.run("probe", "--pair", intent, started)
        self.assertEqual(code, 0, stderr.decode()[-3000:])
        target = record["targets"][0]
        self.assertEqual(target["state"], "present, identity established")
        self.assertEqual((target["kill"], target["killpg"]), ("success", "success"))
        self.assertEqual(target["identity"], dict(target["identity"], start_within_window=True,
                                                  image_equals_argv0=True, group_equals_recorded=True,
                                                  established=True))
        self.assertEqual(target["bsdinfo"]["pgid"], child.pid)
        self.assertEqual(target["image"], S.process_image())
        self.assertIn(child.pid, target["group_members"])
        self.assertIn("FC-P5", target["limit"])
        self.assertEqual(record["process_events"], [])
        self.assertIsNone(child.poll(), "a probe sends no signal")
        self.assertEqual(record["boot_before"], record["boot_after"])

    def test_an_image_that_is_not_the_recorded_argv0_does_not_establish_identity(self):
        world = CaptureWorld(self)
        child, intent, started = world.pair(argv0=S.PYTHON)
        code, _, record = world.run("probe", "--pair", intent, started)
        self.assertEqual(code, 0)
        target = record["targets"][0]
        self.assertEqual(target["state"], "present, identity not established")
        self.assertFalse(target["identity"]["image_equals_argv0"])
        self.assertTrue(target["identity"]["start_within_window"])

    def test_a_start_outside_the_window_does_not_establish_identity(self):
        world = CaptureWorld(self)
        child, intent, started = world.pair(intent_after_start=True)
        code, _, record = world.run("probe", "--pair", intent, started)
        self.assertEqual(code, 0)
        target = record["targets"][0]
        self.assertEqual(target["state"], "present, identity not established")
        self.assertFalse(target["identity"]["start_within_window"])
        self.assertTrue(target["identity"]["image_equals_argv0"])

    def test_absence_is_established_by_esrch_and_a_malformed_record_is_unknown(self):
        world = CaptureWorld(self)
        intent = world.record("intent.json", b"{}")
        gone = S.start_child(["/usr/bin/true"], start_new_session=True)
        gone.wait()
        started = world.started("started.json", gone, "/usr/bin/true")
        malformed = world.record("malformed.json", b'{"process": {"pid": 1}}')
        code, _, record = world.run("probe", "--pair", intent, started, "--pair", intent, malformed)
        self.assertEqual(code, 0)
        absent, unknown = record["targets"]
        self.assertEqual((absent["state"], absent["kill"], absent["killpg"]), ("absent", "ESRCH", "ESRCH"))
        self.assertEqual(unknown["state"], "unknown")
        self.assertEqual(unknown["pair"]["refusal"]["rule"], "RECORD")


class StopTests(unittest.TestCase):
    def test_an_established_identity_is_ended_through_its_group(self):
        world = CaptureWorld(self)
        child, intent, started = world.pair()
        code, stderr, record = world.run("stop", "--pair", intent, started, reap=[child])
        self.assertEqual(code, 0, stderr.decode()[-3000:])
        stop = record["stop"]
        self.assertEqual(stop["probe"]["state"], "present, identity established")
        self.assertEqual([send["signal"] for send in stop["sends"]], ["SIGTERM"])
        self.assertEqual(stop["sends"][0]["group"], child.pid)
        self.assertEqual((stop["state"], stop["result"]), ("absent", "absent after SIGTERM"))
        self.assertEqual(stop["probes"][-1]["killpg"], "ESRCH")
        child.wait()
        self.assertEqual(child.returncode, -signal.SIGTERM)

    def test_sigkill_follows_only_continuous_presence_and_a_second_established_identity(self):
        world = CaptureWorld(self)
        child, intent, started = world.pair(code=IGNORE_SIGTERM)
        code, stderr, record = world.run("stop", "--pair", intent, started, reap=[child])
        self.assertEqual(code, 0, stderr.decode()[-3000:])
        stop = record["stop"]
        self.assertEqual([send["signal"] for send in stop["sends"]], ["SIGTERM", "SIGKILL"])
        self.assertEqual(stop["probe_before_sigkill"]["state"], "present, identity established")
        self.assertTrue(all(row["killpg"] in ("success", "EPERM") for row in stop["probes"]
                            if row["phase"] == "after SIGTERM"))
        self.assertGreaterEqual(stop["sends"][1]["monotonic"] - stop["sends"][0]["monotonic"], 2.0)
        self.assertEqual((stop["state"], stop["result"]), ("absent", "absent after SIGKILL"))
        child.wait()
        self.assertEqual(child.returncode, -signal.SIGKILL)

    def test_nothing_is_sent_when_identity_is_not_established(self):
        """TR-05: a present process whose identity is not established is recorded, and never signalled."""
        world = CaptureWorld(self)
        child, intent, started = world.pair(argv0=S.PYTHON)
        code, _, record = world.run("stop", "--pair", intent, started, reap=[child])
        self.assertEqual(code, 0)
        stop = record["stop"]
        self.assertEqual(stop["sends"], [])
        self.assertEqual(stop["state"], "present, identity not established")
        self.assertEqual(stop["result"], "no signal sent: present, identity not established")
        self.assertIsNone(child.poll(), "the process was signalled")


class ListingTests(unittest.TestCase):
    def test_the_readback_listing_never_follows_a_link(self):
        world = CaptureWorld(self)
        attempt = world.base + "/attempt"
        S.write(attempt + "/command/started.json", b'{"state": "STARTED"}')
        outside = S.write(world.base + "/outside.txt", b"never read through the link")
        os.symlink(outside, attempt + "/HOST.json")
        code, _, record = world.run("listing", "--dir", attempt, "--path", attempt + "/HOST.json",
                                    "--path", attempt + "/completion.json")
        self.assertEqual(code, 0)
        entries = record["directories"][attempt]["entries"]
        self.assertEqual(entries["HOST.json"], {"state": "present", "kind": "symlink", "target": outside,
                                                "mode": entries["HOST.json"]["mode"],
                                                "size_bytes": entries["HOST.json"]["size_bytes"]})
        self.assertEqual(entries["command"]["kind"], "directory")
        self.assertEqual(entries["command/started.json"]["sha256"], S.sha256_bytes(b'{"state": "STARTED"}'))
        self.assertEqual(record["paths"][attempt + "/completion.json"], {"state": "absent"})
        self.assertEqual(record["paths"][attempt + "/HOST.json"]["kind"], "symlink")
        self.assertEqual(record["digests_computed_by"], "this capture_probe.py listing process")

    def test_a_start_without_dash_b_refuses(self):
        """TR-17, in this process with sys.flags as a start without -B shows them; nothing is started."""
        tool = S.load_module("mh_capture_under_test", str(S.TOOLING / "capture_probe.py"))
        world = CaptureWorld(self)
        output = world.base + "/listing-without-b.json"
        with mock.patch.object(sys, "flags", S.FlagsWithoutB()), contextlib.redirect_stderr(io.StringIO()):
            code = tool.main(["listing", "--dir", world.base, "--output", output])
        self.assertEqual(code, 2)
        self.assertEqual(S.read_json(output)["refusal"]["rule"], "PYTHON")


class ProcedureTextTests(unittest.TestCase):
    """TR-05 and TR-16: the bound procedure establishes identity before any signal and names its tool."""

    def section(self, text, name):
        match = re.search(r"- \*\*" + re.escape(name) + r"\..*?(?=\n- \*\*FC-|\n## )", text, re.S)
        self.assertIsNotNone(match, name)
        return " ".join(match.group(0).split())

    def test_identity_comes_before_any_signal_and_the_probes_are_code(self):
        text = (S.TOOLING / "FAILURE-CAPTURE.md").read_text(encoding="utf-8")
        p3, p6, k5 = (self.section(text, name) for name in ("FC-P3", "FC-P6", "FC-K5"))
        self.assertIn("capture_probe.py probe", p3)
        self.assertIn("PROC_PIDTBSDINFO", p3)
        self.assertIn("proc_pidpath", p3)
        self.assertIn("capture_probe.py stop", p6)
        self.assertIn("Only a process whose identity is established is ended", p6)
        self.assertIn("nothing is sent to it, and its outcome stays unknown", p6)
        self.assertIn("capture_probe.py listing", k5)


if __name__ == "__main__":
    unittest.main()
