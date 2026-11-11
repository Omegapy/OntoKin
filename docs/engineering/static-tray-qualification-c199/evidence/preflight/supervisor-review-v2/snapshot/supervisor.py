"""Bounded Linux process groups for the explicitly selected static-tray profile.

This module owns the one monotonic clock and capped pipe capture.  Both the
native stages and the separately labelled lifecycle controls use this path.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import stat
import subprocess
import time


LIMITS = {"transaction_ms": 65000, "construction_ms": 30000,
          "receiving_ms": 30000, "promotion_ms": 3000, "cleanup_ms": 2000,
          "poll_ms": 50, "terminate_grace_ms": 500,
          "output_bytes": 64 * 1024 * 1024, "glb_bytes": 8 * 1024 * 1024,
          "log_bytes": 4 * 1024 * 1024, "result_bytes": 4 * 1024 * 1024}


def json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Stop(Exception):
    def __init__(self, code, reason, state="REJECTED"):
        self.code, self.reason, self.state = code, reason, state
        super().__init__(reason)

    def as_dict(self):
        return {"code": self.code, "reason": self.reason, "state": self.state}


class Clock:
    def __init__(self, *, total_ms=65000, cancel_file=None):
        if not 0 < total_ms <= LIMITS["transaction_ms"]:
            raise ValueError("Invalid bounded host allowance")
        self.started = time.monotonic()
        self.end = self.started + total_ms / 1000
        self.cancel_file = Path(cancel_file) if cancel_file else None
        self.cancel_observed = None
        self.requested_ms = total_ms

    def check(self, stage_end=None):
        now = time.monotonic()
        if self.cancel_file and self.cancel_file.exists():
            if self.cancel_observed is None:
                self.cancel_observed = now
            raise Stop("OTRAY-E-CANCELLED", "Cancellation observed", "CANCELLED")
        if now >= min(self.end, stage_end if stage_end is not None else self.end):
            raise Stop("OTRAY-E-RESOURCE", "Monotonic stage or transaction deadline", "TIMEOUT")

    def stage(self, milliseconds):
        self.check()
        now = time.monotonic()
        if self.end - now < milliseconds / 1000:
            raise Stop("OTRAY-E-RESOURCE", "Remaining transaction allowance cannot cover stage", "TIMEOUT")
        return now + milliseconds / 1000

    def elapsed_ms(self):
        return (time.monotonic() - self.started) * 1000


def inventory(directory, *, enforce_caps=True):
    """Inspect actual regular files; never follow a staged symlink or alias."""
    directory = Path(directory)
    rows, total = {}, 0
    for path in sorted(directory.rglob("*")):
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            raise Stop("OTRAY-E-BINDING", "A staged path is a symlink")
        if stat.S_ISDIR(info.st_mode):
            continue
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise Stop("OTRAY-E-BINDING", "Staged file is not a private regular file")
        total += info.st_size
        if enforce_caps and (total > LIMITS["output_bytes"] or
                (path.suffix == ".glb" and info.st_size > LIMITS["glb_bytes"]) or
                (path.suffix == ".json" and info.st_size > LIMITS["result_bytes"])):
            raise Stop("OTRAY-E-RESOURCE", "Staged output byte ceiling exceeded")
        rows[path.relative_to(directory).as_posix()] = {
            "size_bytes": info.st_size, "mode": stat.S_IMODE(info.st_mode)}
    return rows


def group_exists(pid):
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False


def _reap(pid):
    while True:
        try:
            child, _ = os.waitpid(-pid, os.WNOHANG)
        except ChildProcessError:
            return
        if child == 0:
            return


def terminate_group(process, clock):
    """Graceful group stop followed by a mandatory kill and bounded reaping."""
    started = time.monotonic()
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    grace = min(started + LIMITS["terminate_grace_ms"] / 1000, clock.end)
    while time.monotonic() < grace:
        process.poll()
        if process.returncode is not None:
            _reap(process.pid)
        if not group_exists(process.pid):
            break
        time.sleep(0.01)
    if group_exists(process.pid):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    deadline = min(started + LIMITS["cleanup_ms"] / 1000, clock.end)
    while time.monotonic() < deadline:
        process.poll()
        if process.returncode is not None:
            _reap(process.pid)
        if not group_exists(process.pid):
            process.wait(timeout=max(0.001, deadline - time.monotonic()))
            return {"passed": True, "elapsed_ms": (time.monotonic()-started)*1000,
                    "process_group_absent": True, "reaped": True}
        time.sleep(0.01)
    # Never leave an owned process running even after a scheduler overrun.
    # Such an overrun is retained as a failed cleanup/transaction, not success.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.poll()
    if process.returncode is not None:
        _reap(process.pid)
    raise Stop("OTRAY-E-BACKEND", "Owned process group cleanup exceeded stage or transaction ceiling")


def run_process(argv, *, stage, label, clock, stage_end, env=None,
                on_started=None, cancel_after_ms=None):
    """One directly launched child, no retry and no inherited working directory."""
    stage = Path(stage).resolve()
    if not stage.is_dir() or not isinstance(argv, list) or not argv:
        raise ValueError("A private stage and explicit argv are required")
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:
        raise Stop("OTRAY-E-BACKEND", "Cannot establish Linux descendant reaping")
    clock.check(stage_end)
    if clock.end-time.monotonic() <= LIMITS["cleanup_ms"]/1000:
        raise Stop("OTRAY-E-RESOURCE", "Insufficient transaction allowance for child and cleanup", "TIMEOUT")
    active_end = min(stage_end, clock.end-LIMITS["cleanup_ms"]/1000)
    record = {"argv": argv, "cwd": str(stage), "environment": env,
              "label": label, "start_monotonic": time.monotonic(),
              "pid": None, "process_group": None, "returncode": None,
              "observed_log_bytes": 0, "retained_log_bytes": 0,
              "cleanup": None, "handles_closed": False, "error": None}
    process, streams, selector, failure = None, {}, selectors.DefaultSelector(), None
    try:
        process = subprocess.Popen(argv, cwd=stage, env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        record["pid"] = record["process_group"] = process.pid
        for pipe, suffix in ((process.stdout, "stdout.log"), (process.stderr, "stderr.log")):
            os.set_blocking(pipe.fileno(), False)
            output = (stage / (label + "." + suffix)).open("xb")
            streams[pipe.fileno()] = (pipe, output)
            selector.register(pipe, selectors.EVENT_READ)
        if on_started:
            on_started(record.copy())
        while selector.get_map() or process.poll() is None:
            if cancel_after_ms is not None and (time.monotonic()-record["start_monotonic"])*1000 >= cancel_after_ms:
                clock.cancel_observed = time.monotonic()
                raise Stop("OTRAY-E-CANCELLED", "Controlled cancellation after child start", "CANCELLED")
            clock.check(active_end)
            inventory(stage)
            remaining = active_end-time.monotonic()
            for key, _ in selector.select(max(0, min(LIMITS["poll_ms"]/1000, remaining))):
                data = os.read(key.fd, 65536)
                if not data:
                    selector.unregister(key.fileobj)
                    continue
                previous = record["observed_log_bytes"]
                record["observed_log_bytes"] += len(data)
                retained = data[:max(0, LIMITS["log_bytes"]-previous)]
                streams[key.fd][1].write(retained)
                streams[key.fd][1].flush()
                record["retained_log_bytes"] += len(retained)
                if record["observed_log_bytes"] > LIMITS["log_bytes"]:
                    raise Stop("OTRAY-E-RESOURCE", "Captured output exceeded the fixed log ceiling")
        process.wait()
        if group_exists(process.pid):
            raise Stop("OTRAY-E-BACKEND", "Child exited while an owned descendant remained")
        clock.check(stage_end)
        inventory(stage)
        if process.returncode != 0:
            raise Stop("OTRAY-E-BACKEND", "Child exited with status " + str(process.returncode))
        record["cleanup"] = {"passed": True, "process_group_absent": True,
                             "reaped": True, "elapsed_ms": 0}
    except BaseException as exc:
        failure = exc if isinstance(exc, Stop) else Stop("OTRAY-E-BACKEND", type(exc).__name__ + ": " + str(exc))
        record["error"] = failure.as_dict()
        if process is not None:
            try:
                record["cleanup"] = terminate_group(process, clock)
            except Stop as cleanup_error:
                failure = cleanup_error
                record["cleanup"] = {"passed": False, "reason": cleanup_error.reason}
                record["error"] = failure.as_dict()
    finally:
        selector.close()
        for pipe, output in streams.values():
            pipe.close()
            output.close()
        record["handles_closed"] = True
        record["returncode"] = process.returncode if process else None
        record["end_monotonic"] = time.monotonic()
        if clock.cancel_observed is not None:
            record["cancellation_completion_ms"] = (time.monotonic()-clock.cancel_observed)*1000
            if record["cancellation_completion_ms"] > LIMITS["cleanup_ms"]:
                failure = Stop("OTRAY-E-BACKEND", "Cancellation cleanup ceiling exceeded")
                record["error"] = failure.as_dict()
        (stage / (label + ".process.json")).write_bytes(json_bytes(record))
    if failure:
        failure.process_record = record
        raise failure
    return record
