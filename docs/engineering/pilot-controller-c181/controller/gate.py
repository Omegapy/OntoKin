"""Serial Linux controller gate. Only the trusted operator process owns this object."""
import hashlib
import json
import math
import os
import signal
import subprocess
import time
import uuid
from datetime import UTC, datetime


class Stopped(Exception):
    """This run cannot dispatch any more model or tool operations."""


def count(value):
    if type(value) is not int or value < 0:
        raise ValueError("token count must be a nonnegative integer")
    return value


def normalize(usage):
    cached = count(usage["cachedInput"])
    output = count(usage["output"])
    if ("fullInput" in usage) == ("uncachedInput" in usage):
        raise ValueError("supply exactly one input accounting convention")
    if "fullInput" in usage:
        full = count(usage["fullInput"])
        if cached > full:
            raise ValueError("cached input exceeds full input")
    else:
        full = count(usage["uncachedInput"]) + cached
    if full == 0:
        raise ValueError("empty model input for a nonempty probe")
    return {"fullInput": full, "cachedInput": cached, "uncachedInput": full - cached,
            "output": output, "charged": full + output}


class Gate:
    def __init__(self, seconds, tokens, trace, run, on_stop=None, audit_model_stderr=False):
        if not math.isfinite(seconds) or seconds <= 0 or count(tokens) < 1:
            raise ValueError("positive finite time and token budgets required")
        self.started = time.monotonic()
        self.deadline = self.started + seconds
        self.limit = tokens
        self.charged = 0
        self.stopped = None
        self.on_stop = on_stop
        self.audit_model_stderr = audit_model_stderr
        self.trace = trace
        self.run = run
        self.log("opened", seconds=seconds, tokens=tokens)

    def log(self, event, **fields):
        entry = dict(utc=datetime.now(UTC).isoformat(), elapsed=time.monotonic() - self.started,
                     run=self.run, event=event, **fields)
        self.trace.write(json.dumps(entry, allow_nan=False) + "\n")
        self.trace.flush()
        os.fsync(self.trace.fileno())

    def stop(self, reason):
        if self.stopped:
            return
        self.stopped = reason
        self.log("stopped", reason=self.stopped, knownCharged=self.charged)

        if self.on_stop:
            try:
                self.log("teardown", outcome=self.on_stop())
            except Exception as exc:
                self.log("teardownFailed", exception=type(exc).__name__)
                raise Stopped("worker teardown unverified") from exc

    def invoke(self, kind, argv, request=b""):
        if not self.stopped and time.monotonic() >= self.deadline:
            self.stop("deadline")
        if self.stopped:
            self.log("refused", kind=kind, reason=self.stopped)
            raise Stopped(self.stopped)
        self.log("dispatch", kind=kind, argv=list(map(str, argv)),
                 inputSha256=hashlib.sha256(request).hexdigest())
        if time.monotonic() >= self.deadline:
            self.stop("deadline")
            self.log("refused", kind=kind, reason=self.stopped)
            raise Stopped(self.stopped)
        try:
            proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, start_new_session=True)
        except OSError as exc:
            self.log("launchError", kind=kind, errno=exc.errno)
            self.stop("launch failed")
            raise Stopped(self.stopped) from exc
        try:
            out, err = proc.communicate(request, timeout=max(0, self.deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait(timeout=3)
            for stream in (proc.stdin, proc.stdout, proc.stderr):
                stream.close()
            self.log("deadlineDuringOperation", kind=kind, exit=proc.returncode,
                     outputsDiscarded=True, incompleteModelUsage=(kind == "model"))
            self.stop("deadline")
            raise Stopped(self.stopped) from None
        self.log("returned", kind=kind, exit=proc.returncode, stdoutBytes=len(out),
                 stdoutSha256=hashlib.sha256(out).hexdigest(), stderrBytes=len(err),
                 stderrSha256=hashlib.sha256(err).hexdigest())
        if kind == "model" and self.audit_model_stderr and err:
            self.log("modelStderr", stderr=err[:8192].decode("utf-8", "replace"),
                     truncated=len(err) > 8192)
        if time.monotonic() >= self.deadline or proc.returncode:
            self.stop("deadline" if time.monotonic() >= self.deadline else "child failed")
            raise Stopped(self.stopped)
        return out

    def tool(self, argv):
        return self.invoke("tool", argv)

    def infer(self, client, prompt, snapshot, max_output):
        request_id = uuid.uuid4().hex
        req = dict(requestId=request_id, prompt=prompt, snapshot=snapshot,
                   remainingTokens=self.limit - self.charged, maxOutput=count(max_output))
        out = self.invoke("model", client, json.dumps(req).encode())
        try:
            r = json.loads(out)
            if r["requestId"] != request_id or r["snapshot"] != snapshot:
                raise ValueError("request ID or model identity mismatch")
            if r.get("status") == "no_capacity":
                required, context = count(r["requiredInput"]), count(r["context"])
                if not required or not context:
                    raise ValueError("invalid pre-inference capacity report")
                if required + 1 > req["remainingTokens"]:
                    reason = "remaining token allowance insufficient"
                elif required + 1 > context:
                    reason = "context window exhausted"
                else:
                    raise ValueError("unsupported capacity refusal")
                self.log("capacityRefusal", receipt=r, remainingTokens=req["remainingTokens"],
                         knownCharged=self.charged)
                self.stop(reason)
                raise Stopped(self.stopped)
            if type(r["text"]) is not str or type(r["source"]) is not str or not r["source"]:
                raise ValueError("missing reply or source")
            usage = normalize(r["usage"])
        except (KeyError, TypeError, ValueError) as exc:
            self.log("rejectedReceipt", problem=str(exc))
            self.stop("unusable receipt")
            raise Stopped(self.stopped) from exc
        self.charged += usage["charged"]
        self.log("usage", request=req, receipt=r, normalized=usage, cumulative=self.charged)
        if self.charged > self.limit or usage["output"] > req["maxOutput"]:
            self.stop("client exceeded budget")
            raise Stopped(self.stopped)
        if time.monotonic() >= self.deadline:
            self.stop("deadline")
            raise Stopped(self.stopped)
        if self.charged == self.limit:
            self.stop("token budget exhausted")
        return r, usage
