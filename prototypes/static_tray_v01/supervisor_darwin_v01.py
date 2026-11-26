"""Bounded Darwin arm64 process groups for the 0.2.0 current-host readback contract.

Contract ``ontokin.current-host-readback/0.2.0``, profile ``darwin-arm64-v1``, section 5
(S4).  ``run_process`` is the original ``supervisor.run_process`` with one change: the Linux
precondition ``prctl(PR_SET_CHILD_SUBREAPER)`` is replaced by the Darwin precondition, which
requires ``sys.platform == "darwin"``, ``os.uname().machine == "arm64"`` and
``sysctl.proc_translated`` equal to 0, read through ``sysctlbyname`` from libSystem.  A failed
or unreadable precondition raises the original kind of ``Stop`` before any process start.

Every other name comes unchanged from ``supervisor.py``, which stays byte-identical and remains
the Linux contract's supervisor.  Darwin has no child subreaper: orphaned descendants are
re-parented to launchd, not to this supervisor.  The receipt fields keep their text, with the
narrowed meaning that contract section 5 states.
"""
from __future__ import annotations

import ctypes
import os
from pathlib import Path
import selectors
import subprocess
import sys
import time

from prototypes.static_tray_v01.supervisor import (
    Clock, LIMITS, Stop, group_exists, inventory, json_bytes, terminate_group)


LIBSYSTEM = "/usr/lib/libSystem.B.dylib"


def _libsystem():
    """libSystem through dlopen; current macOS serves it from the dyld shared cache."""
    return ctypes.CDLL(LIBSYSTEM)


def proc_translated():
    """``sysctl.proc_translated`` through ``sysctlbyname``: 0 native, 1 translated, None unreadable."""
    try:
        sysctlbyname = _libsystem().sysctlbyname
    except (OSError, AttributeError):
        return None
    sysctlbyname.argtypes = (ctypes.c_char_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t),
                             ctypes.c_void_p, ctypes.c_size_t)
    sysctlbyname.restype = ctypes.c_int
    value = ctypes.c_int(-1)
    size = ctypes.c_size_t(ctypes.sizeof(value))
    try:
        status = sysctlbyname(b"sysctl.proc_translated", ctypes.byref(value), ctypes.byref(size), None, 0)
    except ctypes.ArgumentError:
        return None
    if status != 0 or size.value != ctypes.sizeof(value):
        return None
    return value.value


def darwin_precondition():
    """None when this process runs natively on Darwin arm64; otherwise the first unmet condition."""
    if sys.platform != "darwin":
        return "sys.platform is not darwin"
    if os.uname().machine != "arm64":
        return "os.uname().machine is not arm64"
    translated = proc_translated()
    if translated is None:
        return "sysctl.proc_translated is unreadable"
    if translated != 0:
        return "sysctl.proc_translated is not 0"
    return None


def run_process(argv, *, stage, label, clock, stage_end, env=None,
                on_started=None, cancel_after_ms=None):
    """One directly launched child, no retry and no inherited working directory."""
    stage = Path(stage).resolve()
    if not stage.is_dir() or not isinstance(argv, list) or not argv:
        raise ValueError("A private stage and explicit argv are required")
    unmet = darwin_precondition()
    if unmet is not None:
        raise Stop("OTRAY-E-BACKEND", "Cannot establish the Darwin arm64 native precondition: " + unmet)
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
        # Count a start immediately after Popen, even if pipe/log setup fails.
        if on_started:
            on_started(record.copy())
        for pipe, suffix in ((process.stdout, "stdout.log"), (process.stderr, "stderr.log")):
            os.set_blocking(pipe.fileno(), False)
            output = (stage / (label + "." + suffix)).open("xb")
            streams[pipe.fileno()] = (pipe, output)
            selector.register(pipe, selectors.EVENT_READ)
        while selector.get_map() or process.poll() is None:
            poll_started = time.monotonic()
            if cancel_after_ms is not None and (time.monotonic()-record["start_monotonic"])*1000 >= cancel_after_ms:
                clock.cancel_observed = time.monotonic()
                raise Stop("OTRAY-E-CANCELLED", "Controlled cancellation after child start", "CANCELLED")
            clock.check(active_end)
            inventory(stage, clock=clock, stage_end=active_end)
            remaining = active_end-time.monotonic()
            poll_remaining = LIMITS["poll_ms"]/1000-(time.monotonic()-poll_started)
            for key, _ in selector.select(max(0, min(poll_remaining, remaining))):
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
        if process:
            for pipe in (process.stdout, process.stderr):
                if pipe is not None and not pipe.closed:
                    pipe.close()
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
