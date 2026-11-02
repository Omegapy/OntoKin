"""JSONL transport and one-request frontend for the local agent service."""

from __future__ import annotations

import json
import sqlite3
import sys
import threading

from .agent import AgentService
from .agent_protocol import MAX_REQUEST_BYTES, ProtocolError, envelope


def _decode(raw: bytes, *, max_request_bytes=MAX_REQUEST_BYTES):
    if len(raw) > max_request_bytes:
        raise ProtocolError("OKA-E-RESOURCE", f"A JSON request exceeds the {max_request_bytes // (1024 * 1024)} MiB transport limit.")
    try:
        def pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    raise ValueError("duplicate JSON member")
                result[key] = value
            return result
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite JSON number")))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ProtocolError("OKA-E-JSON", "The request is not one valid UTF-8 JSON value with unique object members.") from exc


def _error(error: ProtocolError, envelope_fn=envelope):
    response = envelope_fn({}, "rejected")
    response["protocol_error"] = error.to_dict()
    return response


def _emit(response):
    print(json.dumps(response, ensure_ascii=False, separators=(",", ":"), allow_nan=False), flush=True)


def run(args, *, host_policy=None) -> int:
    service_type, envelope_fn = AgentService, envelope
    service_options = {}
    selected_protocol = getattr(args, "protocol", "ontokin.agent/0.1")
    if selected_protocol in ("ontokin.agent/0.2", "ontokin.agent/0.3", "ontokin.agent/0.4", "ontokin.agent/0.5", "ontokin.agent/0.6"):
        from .program_agent import ProgramAgentService
        from .program_protocol import bind
        service_type, envelope_fn = ProgramAgentService, bind(selected_protocol).envelope
        service_options = {"protocol": selected_protocol}
    elif selected_protocol == "ontokin.agent/0.7":
        from .budget_agent import BudgetAgentService
        from .budget_protocol import BudgetProtocol
        service_type, envelope_fn = BudgetAgentService, BudgetProtocol.envelope
        service_options = {"protocol": selected_protocol, "host_policy": host_policy}
    elif selected_protocol == "ontokin.agent/0.8":
        from .extrusion_agent import ExtrusionAgentService
        from .extrusion_protocol import ExtrusionProtocol
        service_type, envelope_fn = ExtrusionAgentService, ExtrusionProtocol.envelope
        service_options = {"protocol": selected_protocol, "host_policy": host_policy}
    elif selected_protocol == "ontokin.agent/0.9":
        from .holes_agent import HolesAgentService
        from .holes_protocol import HolesProtocol
        service_type, envelope_fn = HolesAgentService, HolesProtocol.envelope
        service_options = {"protocol": selected_protocol, "host_policy": host_policy}
    elif selected_protocol == "ontokin.agent/0.10":
        from .ring_loft_agent import RingLoftAgentService
        from .ring_loft_protocol import RingLoftProtocol
        service_type, envelope_fn = RingLoftAgentService, RingLoftProtocol.envelope
        service_options = {"protocol": selected_protocol, "host_policy": host_policy}
    elif selected_protocol == "ontokin.agent/0.11":
        from .framed_loft_agent import FramedLoftAgentService
        from .framed_loft_protocol import FramedLoftProtocol
        service_type, envelope_fn = FramedLoftAgentService, FramedLoftProtocol.envelope
        service_options = {"protocol": selected_protocol, "host_policy": host_policy}
    elif selected_protocol == "ontokin.agent/0.12":
        from .pockets_agent import PocketsAgentService
        from .pockets_protocol import PocketsProtocol
        service_type, envelope_fn = PocketsAgentService, PocketsProtocol.envelope
        service_options = {"protocol": selected_protocol, "host_policy": host_policy}
    elif selected_protocol == "ontokin.agent/0.20":
        from .string_concat_agent import StringConcatAgentService
        from .string_concat_protocol import StringConcatProtocol
        service_type, envelope_fn = StringConcatAgentService, StringConcatProtocol.envelope
        service_options = {"protocol": selected_protocol, "host_policy": host_policy}
    elif selected_protocol == "ontokin.agent/0.19":
        from .keyed_rekey_agent import KeyedRekeyAgentService
        from .keyed_rekey_protocol import KeyedRekeyProtocol
        service_type, envelope_fn = KeyedRekeyAgentService, KeyedRekeyProtocol.envelope
        service_options = {"protocol": selected_protocol, "host_policy": host_policy}
    elif selected_protocol == "ontokin.agent/0.18":
        from .keyed_zip_agent import KeyedZipAgentService
        from .keyed_zip_protocol import KeyedZipProtocol
        service_type, envelope_fn = KeyedZipAgentService, KeyedZipProtocol.envelope
        service_options = {"protocol": selected_protocol, "host_policy": host_policy}
    elif selected_protocol == "ontokin.agent/0.17":
        from .keyed_merge_agent import KeyedMergeAgentService
        from .keyed_merge_protocol import KeyedMergeProtocol
        service_type, envelope_fn = KeyedMergeAgentService, KeyedMergeProtocol.envelope
        service_options = {"protocol": selected_protocol, "host_policy": host_policy}
    elif selected_protocol == "ontokin.agent/0.16":
        from .keyed_filter_agent import KeyedFilterAgentService
        from .keyed_filter_protocol import KeyedFilterProtocol
        service_type, envelope_fn = KeyedFilterAgentService, KeyedFilterProtocol.envelope
        service_options = {"protocol": selected_protocol, "host_policy": host_policy}
    elif selected_protocol == "ontokin.agent/0.15":
        from .keyed_reduction_agent import KeyedReductionAgentService
        from .keyed_reduction_protocol import KeyedReductionProtocol
        service_type, envelope_fn = KeyedReductionAgentService, KeyedReductionProtocol.envelope
        service_options = {"protocol": selected_protocol, "host_policy": host_policy}
    elif selected_protocol == "ontokin.agent/0.14":
        from .keyed_transform_agent import KeyedTransformAgentService
        from .keyed_transform_protocol import KeyedTransformProtocol
        service_type, envelope_fn = KeyedTransformAgentService, KeyedTransformProtocol.envelope
        service_options = {"protocol": selected_protocol, "host_policy": host_policy}
    elif selected_protocol == "ontokin.agent/0.13":
        from .texture_agent import TextureAgentService
        from .texture_protocol import TextureProtocol
        service_type, envelope_fn = TextureAgentService, TextureProtocol.envelope
        service_options = {"protocol": selected_protocol, "host_policy": host_policy}
    max_request_bytes = 8 * 1024 * 1024 if selected_protocol in ("ontokin.agent/0.13", "ontokin.agent/0.14", "ontokin.agent/0.15", "ontokin.agent/0.16", "ontokin.agent/0.17", "ontokin.agent/0.18", "ontokin.agent/0.19", "ontokin.agent/0.20") else MAX_REQUEST_BYTES
    def error_response(error):
        return _error(error, envelope_fn)
    try:
        service = service_type(args.store, **service_options)
    except (OSError, sqlite3.Error, ProtocolError) as exc:
        error = exc if isinstance(exc, ProtocolError) else ProtocolError("OKA-E-STORE", "The local store could not be opened.", reason=str(exc))
        _emit(error_response(error))
        return 1
    if args.request is not None:
        try:
            with args.request.open("rb") as stream:
                request = _decode(stream.read(max_request_bytes + 1), max_request_bytes=max_request_bytes)
            response = service.handle(request, wait=args.wait)
        except (OSError, ProtocolError) as exc:
            error = exc if isinstance(exc, ProtocolError) else ProtocolError("OKA-E-IO", "The request file could not be read.", reason=str(exc))
            response = error_response(error)
        finally:
            service.close()
        _emit(response)
        return 1 if response["status"] in {"rejected", "failed", "unknown_outcome"} else 0

    wake, finished = threading.Event(), threading.Event()

    def worker():
        while True:
            if service.work_next():
                continue
            if finished.is_set():
                return
            wake.wait(.05)
            wake.clear()

    thread = None
    if not args.wait:
        thread = threading.Thread(target=worker, name="ontokin-agent-worker", daemon=True)
        thread.start()
    try:
        while True:
            raw = sys.stdin.buffer.readline(max_request_bytes + 1)
            if not raw:
                break
            if len(raw) > max_request_bytes:
                # Drain this one oversized line in bounded chunks; the next request remains usable.
                while raw and not raw.endswith(b"\n"):
                    raw = sys.stdin.buffer.readline(max_request_bytes + 1)
                response = error_response(ProtocolError("OKA-E-RESOURCE", f"A JSONL request exceeds the {max_request_bytes // (1024 * 1024)} MiB transport limit."))
            else:
                try:
                    request = _decode(raw, max_request_bytes=max_request_bytes)
                    response = service.handle(request, wait=args.wait)
                except ProtocolError as exc:
                    response = error_response(exc)
            _emit(response)
            wake.set()
        finished.set()
        wake.set()
        if thread is not None:
            thread.join()
        return 0
    except KeyboardInterrupt:
        return 130
    finally:
        finished.set()
        wake.set()
        service.close()
