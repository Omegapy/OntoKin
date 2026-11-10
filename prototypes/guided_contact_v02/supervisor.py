"""Finite process-group supervision, capped streams and descendant reaping."""
import ctypes
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time

from .common import Failure, canonical_bytes


def staged_size(stage):
    return sum(path.stat().st_size for path in stage.rglob("*") if path.is_file())


def check_sizes(stage, budget, limits):
    result = stage / "native-result.json"
    if result.exists():
        budget.native_result_bytes = result.stat().st_size
        if budget.native_result_bytes > limits["native_result_bytes"]:
            raise Failure("E_RESOURCE_LIMIT", "Native result byte ceiling exceeded", budget.anchor)
    budget.staged_output_bytes = staged_size(stage)
    if budget.staged_output_bytes > limits["staged_output_bytes"]:
        raise Failure("E_RESOURCE_LIMIT", "Staged output byte ceiling exceeded", budget.anchor)


def _group_exists(pid):
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False


def _reap_descendants(pid):
    while True:
        try:
            waited, _ = os.waitpid(-pid, os.WNOHANG)
        except ChildProcessError:
            return
        if waited == 0:
            return


def stop_group(process, grace_ms):
    """Stop the owned session and reap adopted descendants, including zombies."""
    start = time.monotonic()
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    grace_end = start + grace_ms / 1000
    while time.monotonic() < grace_end:
        process.poll()
        if process.returncode is not None:
            _reap_descendants(process.pid)
        if not _group_exists(process.pid):
            break
        time.sleep(min(0.01, max(0, grace_end - time.monotonic())))
    if _group_exists(process.pid):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=1)
    end = start + 1.8
    while time.monotonic() < end:
        _reap_descendants(process.pid)
        if not _group_exists(process.pid):
            return
        time.sleep(0.01)
    raise RuntimeError("Owned native process group could not be fully reaped")


def supervise(argv, stage, budget, backend, backend_span, hooks=None):
    """Actual supervisor seam used by production and trusted failure probes."""
    hooks = hooks or {}
    stage = Path(stage)
    limits = backend["limits"]
    # Linux subreaper makes grandchildren ours when the worker leader exits.
    # This is process-local and lets the bounded supervisor reap the entire group.
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:  # PR_SET_CHILD_SUBREAPER
        raise Failure("E_NATIVE_FAILURE", "Cannot establish native descendant reaping", backend_span)
    if "worker_command" in hooks:
        argv = hooks["worker_command"](list(argv), stage)
    if not isinstance(argv, list) or not argv or any(not isinstance(value, str) for value in argv):
        raise Failure("E_NATIVE_FAILURE", "Invalid trusted worker command", backend_span)
    budget.check()
    record = {"argv": argv, "started_unix_ns": time.time_ns(), "pid": None, "process_group": None,
              "returncode": None, "stop_reason": None, "trusted_test_hooks": sorted(hooks),
              "poll_ms": limits["supervisor_poll_ms"], "terminate_grace_ms": limits["terminate_grace_ms"]}
    started = time.monotonic()
    process = None
    selector = selectors.DefaultSelector()
    streams = {}
    try:
        process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True)
        record["pid"] = record["process_group"] = process.pid
        for pipe, filename in ((process.stdout, "native.stdout.txt"), (process.stderr, "native.stderr.txt")):
            os.set_blocking(pipe.fileno(), False)
            streams[pipe.fileno()] = (pipe, (stage / filename).open("wb"))
            selector.register(pipe, selectors.EVENT_READ)
        if "worker_started" in hooks:
            hooks["worker_started"](process, stage)
        while selector.get_map() or process.poll() is None:
            budget.check()
            check_sizes(stage, budget, limits)
            remaining = max(0, (budget.max_elapsed_ms - budget.elapsed_ms) / 1000)
            for key, _ in selector.select(min(limits["supervisor_poll_ms"] / 1000, remaining)):
                data = os.read(key.fd, 65536)
                if not data:
                    selector.unregister(key.fileobj)
                    continue
                old = budget.native_log_bytes
                budget.native_log_bytes += len(data)
                streams[key.fd][1].write(data[:max(0, limits["native_log_bytes"] - old)])
                streams[key.fd][1].flush()
                if budget.native_log_bytes > limits["native_log_bytes"]:
                    raise Failure("E_RESOURCE_LIMIT", "Native stdout/stderr byte ceiling exceeded", budget.anchor)
        process.wait()
        if _group_exists(process.pid):
            raise Failure("E_NATIVE_FAILURE", "Native worker left a live descendant", backend_span)
        budget.check()
        check_sizes(stage, budget, limits)
        if process.returncode:
            raise Failure("E_NATIVE_FAILURE", f"Native worker exited {process.returncode}", backend_span)
    except BaseException as exc:
        record["stop_reason"] = exc.code if isinstance(exc, Failure) else type(exc).__name__
        if process is not None:
            stop_group(process, limits["terminate_grace_ms"])
        if budget.cancellation_requested_ns is not None:
            budget.cancellation_completion_ms = max(0, (time.time_ns() - budget.cancellation_requested_ns) / 1e6)
        if isinstance(exc, Failure):
            raise
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise Failure("E_CANCELLED", "Host interruption stopped the native group", budget.anchor) from exc
        raise Failure("E_NATIVE_FAILURE", str(exc), backend_span) from exc
    finally:
        selector.close()
        for pipe, stream in streams.values():
            pipe.close()
            stream.close()
        budget.native_elapsed_ms += (time.monotonic() - started) * 1000
        record["finished_unix_ns"] = time.time_ns()
        record["returncode"] = process.returncode if process else None
        record["native_log_bytes_observed"] = budget.native_log_bytes
        record["cancellation_completion_ms"] = budget.cancellation_completion_ms
        (stage / "native-command.json").write_bytes(canonical_bytes(record))
    return record
