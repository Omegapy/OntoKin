"""Source-owned finite torque operands and immutable interval lowering."""
from fractions import Fraction

from .diagnostics import OntoKinError
from .profile_capabilities import TORQUE_PROFILE
from .validator import Context
from .values import ALIASES, TIME, Type, quantity_type


AXES = ("world_x", "world_y", "world_z")


def source_error(compiler, event, sequence_index, code, phase, message, reason, *, related=()):
    raise OntoKinError(code, message, event, phase=phase,
                       related=list(related),
                       details={"torque_key": event.key,
                                "target_path": compiler.render_path(event.path),
                                "sequence_index": sequence_index,
                                "torque_reason": reason})


def check_torque_structure(compiler):
    """Charge one source stage per statement before checking its bounded shape."""
    if compiler.model.profile != TORQUE_PROFILE:
        return
    ledger = compiler.budget.execution_budget
    keys = {}
    for block in compiler.program.scene.members:
        if block.kind != "event_block":
            continue
        for sequence_index, event in enumerate(block.events):
            if event.kind != "torque":
                continue
            previous = ledger.stage
            try:
                ledger.stage = "torque_source"
                compiler.budget.tick(event)
                compiler.key(event, event.key)
                compiler.expect(compiler.path_value(event.path, Context(scene=True, abstract=True), event),
                                Type("Ref", name="Object"), event)
                if event.key in keys:
                    source_error(compiler, event, sequence_index, "OKL-E-NAME", "compile",
                                 "Torque interval keys must be unique within the entry scene.", "duplicate_key",
                                 related=(keys[event.key],))
                keys[event.key] = event
            finally:
                ledger.stage = previous


def torque_values(compiler, event, context, sequence_index):
    target = compiler.expect(compiler.path_value(event.path, context, event),
                             Type("Ref", name="Object"), event)
    # Each child is evaluated and admitted before the next child is entered.
    # Child evaluation errors retain their own original diagnostic and span.
    operand = compiler.expression(event.operand, context)
    if operand.type != quantity_type(ALIASES["Torque"]):
        source_error(compiler, event, sequence_index, "OKL-E-TYPE", "type",
                     "A torque interval requires a scalar Torque value.", "operand_type")
    duration = compiler.expression(event.duration, context)
    if duration.type != quantity_type(TIME):
        source_error(compiler, event, sequence_index, "OKL-E-TYPE", "type",
                     "A torque interval requires a Time duration.", "duration_type")
    if event.axis not in AXES:
        source_error(compiler, event, sequence_index, "OKL-E-FRAME", "compile",
                     "A torque axis must be world_x, world_y or world_z.", "axis_name")
    if duration.known and duration.value <= 0:
        source_error(compiler, event, sequence_index, "OKL-E-EVENT-ORDER", "compile",
                     "A torque interval requires a strictly positive duration.", "duration_nonpositive")
    return target, operand, duration


def lower_torque(compiler, event, sequence_index):
    from .model import TorquePayload
    target, operand, duration = torque_values(compiler, event, Context(scene=True), sequence_index)

    def location(node):
        source = compiler.source_for(node)
        return {"source_id": node.source_id, "source_revision": source.revision,
                "start_byte": node.start, "end_byte": node.end}

    return target.value, TorquePayload(
        key=event.key, axis=event.axis, torque_n_m=operand.value,
        duration=Fraction.from_float(duration.value), sequence_index=sequence_index,
        source=location(event), operand_source=location(event.operand),
        duration_source=location(event.duration))


def source_intervals(compiler, path, budget):
    """Project complete occurrence histories from the accepted source model."""
    from .evaluator import MAX_OUTPUT_RECORDS
    from .execution_budget import SharedExecutionBudget
    import math
    from .model import Event, EventBlock, ObjectModel, SceneModel
    from .reach_numeric import MAX_OPERAND_BITS, ReachExecutionWork
    from .syntax import Node
    from .torque_runtime import _active, _native_work_callback, _record, _source_snapshot
    def invalid_context():
        raise OntoKinError("OKL-E-RESOURCE", "Torque source projection requires its original admitted context.",
            category="resource_limit", phase="support", details={
                "budget_reason": "execution_context_required", "target_contract": "ontokin.glb/0.22"})
    model = compiler.model
    ledger = getattr(budget, "execution_budget", None)
    work = compiler.reach_work
    if type(ledger) is not SharedExecutionBudget or type(work) is not ReachExecutionWork or type(model) is not SceneModel:
        invalid_context()
    bundle = compiler.bundle
    entry = bundle.entry
    identity = (model.program_revision, model.module_key, model.scene_key)
    source_identity = (bundle.program_revision, entry.revision, ledger.admitted_entry_revision, model.profile)
    receipt = None
    owner_receipt = None
    work_counter_receipt = None
    source_guard_active = False
    original_context_guard = ledger._torque_context_guard
    def context(*, numerical_increment=False):
        if (type(ledger) is not SharedExecutionBudget or ledger.resolved is None
                or type(work) is not ReachExecutionWork or type(model) is not SceneModel
                or compiler.model is not model or compiler.bundle is not bundle
                or bundle.entry is not entry
                or compiler.reach_work is not work or budget.execution_budget is not ledger
                or compiler.budget.execution_budget is not ledger
                or work.execution_budget is not ledger
                or not _native_work_callback(work, ledger)
                or source_guard_active and work._source_after_charge is not after_numeric_charge
                or type(ledger.started) not in (int, float) or not math.isfinite(ledger.started)
                or type(work.started) not in (int, float) or not math.isfinite(work.started)
                or any(type(value) is not int or value <= 0 for value in (
                    work.max_operand_bits, work.max_cache_entries, work.max_operations, work.max_elapsed_ms))
                or type(ledger._limits) is not dict or len(ledger._limits) != 2
                or any(type(key) is not str or type(value) is not int or value <= 0
                       for key, value in ledger._limits.items())
                or any(type(value) is not str for value in (*identity, *source_identity))
                or any(actual is not expected for actual, expected in zip(
                    (model.program_revision, model.module_key, model.scene_key), identity))
                or any(actual is not expected for actual, expected in zip(
                    (bundle.program_revision, entry.revision, ledger.admitted_entry_revision, model.profile), source_identity))
                or source_identity[2] != source_identity[1]
                or identity[0] != source_identity[0] or source_identity[3] != TORQUE_PROFILE
                or receipt is not None and (
                    ledger.check is not receipt[0] or ledger._clock is not receipt[1]
                    or ledger.started is not receipt[2] or ledger.resolved is not receipt[3]
                    or ledger._limits is not receipt[4]
                    or any(key is not old_key or value is not old_value
                           for (key, value), (old_key, old_value) in zip(ledger._limits.items(), receipt[5]))
                    or any(actual is not expected for actual, expected in zip(
                        (work.started, work.max_operand_bits, work.max_cache_entries,
                         work.max_operations, work.max_elapsed_ms), receipt[6:])))):
            invalid_context()
        if owner_receipt is not None:
            objects, entries, owner, element_id = owner_receipt
            if (model.objects is not objects or type(objects) is not dict or len(objects) != len(entries)
                    or any(key is not old_key or value is not old_value
                           for (key, value), (old_key, old_value) in zip(objects.items(), entries))
                    or type(owner) is not ObjectModel or owner.element_id is not element_id):
                invalid_context()
        if (type(work.operations) is not int or work.operations < 0 or work.operations.bit_length() > 53
                or type(work.counts) is not dict or len(work.counts) > 256
                or any(type(key) is not str or type(value) is not int or value < 0 or value.bit_length() > 53
                       for key, value in work.counts.items())):
            invalid_context()
        if work_counter_receipt is not None:
            operations, counts_owner, items = work_counter_receipt
            if (work.counts is not counts_owner or not numerical_increment and (
                    work.operations is not operations or len(work.counts) != len(items)
                    or any(key is not old_key or value is not old_value
                           for (key, value), (old_key, old_value) in zip(work.counts.items(), items)))):
                invalid_context()
    context()
    if original_context_guard is not None:
        original_context_guard()
        context()
    receipt = (ledger.check, ledger._clock, ledger.started, ledger.resolved, ledger._limits, tuple(ledger._limits.items()),
               work.started, work.max_operand_bits, work.max_cache_entries,
               work.max_operations, work.max_elapsed_ms)
    work_counter_receipt = (work.operations, work.counts, tuple(work.counts.items()))
    if (type(model.objects) is not dict or type(path) is not str
            or any(type(key) is not str for key in model.objects) or path not in model.objects):
        raise ValueError("A torque source projection requires a resolved occurrence.")
    objects = model.objects
    owner = model.objects[path]
    if (type(owner) is not ObjectModel or type(owner.element_id) is not tuple
            or any(type(value) is not str for value in owner.element_id)):
        raise ValueError("A torque source occurrence has an invalid native identity.")
    element_id = owner.element_id
    owner_receipt = (objects, tuple(objects.items()), owner, element_id)
    # Capture native immutable fields before the first original callback.
    # Two whole-source comparisons and one local comparison per emitted row
    # keep validation linear; no callback can substitute a new source history.
    if type(model.events) is not list or len(model.events) > MAX_OUTPUT_RECORDS:
        raise ValueError("A torque source history has an invalid native shape.")
    def clock_token(value, *, duration=False):
        if type(value) is not Fraction:
            raise ValueError("A torque source clock has an invalid native shape.")
        numerator, denominator = value.numerator, value.denominator
        if (type(numerator) is not int or type(denominator) is not int
                or max(numerator.bit_length(), denominator.bit_length()) > MAX_OPERAND_BITS
                or denominator <= 0 or numerator < 0 or duration and numerator == 0):
            raise ValueError("A torque source clock exceeds its native exact-clock domain.")
        return numerator, denominator
    def span_token(node):
        if node is None:
            return None
        if (type(node) is not Node or type(node.start) is not int or type(node.end) is not int
                or node.start < 0 or node.end < node.start or node.end.bit_length() > 53
                or node.source_id is not None and type(node.source_id) is not str):
            raise ValueError("A torque source span has an invalid native shape.")
        return node.source_id, node.start, node.end
    blocks, events, snapshots, count = [], [], {}, 0
    block_tokens, event_tokens = {}, {}
    for block in model.events:
        if type(block) is not EventBlock or type(block.events) is not list or type(block.time) is not Fraction:
            raise ValueError("A torque source block has an invalid native shape.")
        token = clock_token(block.time)
        block_tokens[id(block)] = (block.time, token, block.span, span_token(block.span), block.events)
        start = Fraction(*token)
        work.guard(block.time)
        count += len(block.events)
        if count > MAX_OUTPUT_RECORDS:
            raise ValueError("A torque source history exceeds its complete record bound.")
        members = []
        for event in block.events:
            if type(event) is not Event or type(event.kind) is not str:
                raise ValueError("A torque source event has an invalid native shape.")
            members.append((event, event.kind))
            if event.kind == "torque":
                snapshot = _source_snapshot(model, event)
                duration = clock_token(event.torque.duration, duration=True)
                event_tokens[id(event)] = (event.torque.duration, duration, event.span, span_token(event.span),
                                          event.torque.source, event.torque.operand_source, event.torque.duration_source)
                # A native Fraction's private integer slots are mutable. Keep
                # detached integer tokens and detached arithmetic operands,
                # never a second alias presented as an immutable snapshot.
                snapshot = (*snapshot[:4], Fraction(*duration), *snapshot[5:])
                snapshots[id(event)] = (event.torque, snapshot)
                if event.target == path:
                    events.append((block, start, event, snapshot))
        blocks.append((block, start, tuple(members)))
    def block_unchanged(block):
        clock, token, span, location, members = block_tokens[id(block)]
        return (block.time is clock and clock_token(block.time) == token
                and block.span is span and span_token(block.span) == location and block.events is members)
    def event_unchanged(event, snapshot):
        payload = snapshots[id(event)][0]
        duration, token, span, location, source, operand, duration_source = event_tokens[id(event)]
        return (event.torque is payload and event.torque.duration is duration
                and clock_token(event.torque.duration, duration=True) == token
                and event.span is span and span_token(event.span) == location
                and event.torque.source is source and event.torque.operand_source is operand
                and event.torque.duration_source is duration_source
                and _source_snapshot(model, event) == snapshot)
    def unchanged():
        context()
        if type(model.events) is not list or len(model.events) != len(blocks):
            raise ValueError("A torque source projection owner changed during its callback.")
        for actual, (block, start, members) in zip(model.events, blocks):
            if (actual is not block or not block_unchanged(block) or type(block.events) is not list
                    or len(block.events) != len(members)):
                raise ValueError("A torque source block changed during its callback.")
            for actual_event, (event, kind) in zip(block.events, members):
                if actual_event is not event or type(event.kind) is not str or event.kind is not kind:
                    raise ValueError("A torque source event changed during its callback.")
                if kind == "torque":
                    _, snapshot = snapshots[id(event)]
                    if not event_unchanged(event, snapshot):
                        raise ValueError("A torque source payload changed during its callback.")
    original_observer = work._source_after_charge
    numeric_receipt = None
    def source_context_guard():
        if ledger._torque_context_guard is not source_context_guard:
            invalid_context()
        context()
        # Parent guards bind their own hook identity. They perform callback-free
        # admission, so restoring that exact owner only during its check keeps
        # its authority intact without replacing the original host callback.
        if original_context_guard is not None:
            ledger._torque_context_guard = original_context_guard
            try:
                original_context_guard()
            finally:
                ledger._torque_context_guard = source_context_guard
        context()
    def after_numeric_charge():
        nonlocal work_counter_receipt
        if original_observer is not None:
            original_observer()
        context(numerical_increment=True)
        if numeric_receipt is None:
            invalid_context()
        operations, numeric_operations, counts, block, start, event, snapshot = numeric_receipt
        if (type(ledger.operations) is not int or ledger.operations != operations + 1
                or type(work.operations) is not int or work.operations != numeric_operations + 1
                or work.counts != {**counts, "exact_add": counts.get("exact_add", 0) + 1}
                or not block_unchanged(block) or not event_unchanged(event, snapshot)):
            invalid_context()
        # Only this proven original one-charge exact addition may advance the
        # numerical receipt. Structural callbacks cannot reset native integers
        # or replace/clear the already accumulated numerical category counts.
        work_counter_receipt = (work.operations, work.counts, tuple(work.counts.items()))
    def structural_tick():
        context()
        operations = ledger.operations
        if type(operations) is not int or operations < 0:
            invalid_context()
        ledger.tick()
        if type(ledger.operations) is not int or ledger.operations != operations + 1:
            invalid_context()
    previous = ledger.stage
    try:
        if ledger._torque_context_guard is not original_context_guard:
            invalid_context()
        work._source_after_charge = after_numeric_charge
        source_guard_active = True
        ledger._torque_context_guard = source_context_guard
        ledger.stage = "torque_projection"
        structural_tick()
        unchanged()
        rows = []
        for block, start, event, snapshot in events:
            structural_tick()
            context()
            if not block_unchanged(block) or not event_unchanged(event, snapshot):
                raise ValueError("A torque source interval changed during its callback.")
            if type(work.operations) is not int or type(work.counts) is not dict or len(work.counts) > 256:
                invalid_context()
            numeric_receipt = (ledger.operations, work.operations, dict(work.counts), block, start, event, snapshot)
            row = _record(model, _active(model, event, start, work=work, snapshot=snapshot))
            numeric_receipt = None
            if row["torque_n_m"] == 0:
                row["torque_n_m"] = 0.0
            rows.append(row)
        unchanged()
        source_context_guard()
        return rows
    finally:
        ledger._torque_context_guard = original_context_guard
        work._source_after_charge = original_observer
        ledger.stage = previous
