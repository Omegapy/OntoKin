"""Typed pure planar reach descriptions and finite structural support checks.

This module never solves an inverse problem or reads a run. Only constructed
named actions participate in the chain/action inventory. Source aliases retain
one description identity while every named action gets its own lifecycle.
"""
from __future__ import annotations

import math
from dataclasses import replace
from fractions import Fraction
from typing import Any

from .diagnostics import OntoKinError
from .model import ReachPayload, ReachSourceLocation
from .values import LENGTH, TIME, Type, Value, quantity_type


PROFILE = "planar-reach-0.1"
BRANCHES = frozenset({"elbow_positive", "elbow_negative"})
NAMES = BRANCHES | {"ReachBranch", "reach_planar"}
PI64 = float.fromhex("0x1.921fb54442d18p+1")
IDENTITY = (1.0, 0.0, 0.0, 0.0)
ZERO = (0.0, 0.0, 0.0)


def reach_error(code: str, message: str, node: Any = None, *,
                phase: str | None = None, details: dict | None = None,
                time: Fraction | None = None, side: str = "after",
                element_id=None, related=(), blocks=None) -> OntoKinError:
    category = ("unsupported" if code in {"reach_chain", "reach_domain"} else
                "resource_limit" if code == "reach_resource" else
                "numerical_failure" if code == "reach_numeric" else "invalid")
    envelope = ("OKL-E-TYPE" if code == "reach_type" else
                "OKL-E-RESOURCE" if code == "reach_resource" else
                "OKL-E-NUMERIC" if code == "reach_numeric" else "OKL-E-REACH")
    default_phase = ("type" if code == "reach_type" else
                     "elaboration" if code == "reach_frame" else
                     "support" if code in {"reach_chain", "reach_domain", "reach_resource"} else "admission")
    return OntoKinError(envelope, message, node, category=category,
                       phase=phase or default_phase, time=time, side=side,
                       element_id=None if element_id is None else list(element_id),
                       related=list(related), blocks=blocks, rule_ids=["REA-001"],
                       details={"reach_code": code, **(details or {})},
                       repair="Use the supported planar chain, typed operands and current two-coordinate authority.")


def declaring(compiler, node) -> bool:
    return compiler.linked.modules[node.source_id].ast.profile == PROFILE


def source_location(compiler, node) -> ReachSourceLocation:
    source = compiler.source_for(node)
    return ReachSourceLocation(node.source_id, source.revision, node.start, node.end)


def reach_builtin(compiler, args, node, context) -> Value:
    if not declaring(compiler, node):
        raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED",
                           "reach_planar is defined only in a planar-reach-0.1 declaring unit.",
                           node, category="unsupported", phase="support")
    if len(args) != 6:
        raise reach_error("reach_type", "reach_planar requires six positional operands.", node)
    types = (Type("JointRef"), Type("JointRef"), Type("SiteRef"),
             Type("Point3", element=quantity_type(LENGTH)), quantity_type(TIME), Type("ReachBranch"))
    typed = []
    for index, (value, expected) in enumerate(zip(args, types)):
        compiler.budget.tick(node.args[index])
        try:
            typed.append(compiler.expect(value, expected, node.args[index]))
        except OntoKinError as error:
            if error is compiler.budget.callback_error:
                raise
            if error.code not in {"OKL-E-TYPE", "OKL-E-UNIT"}:
                raise
            raise reach_error("reach_type", str(error), node.args[index],
                              details={"operand_index": index, "expected_type": str(expected),
                                       "actual_type": str(value.type)}) from error
    if context.abstract or any(not value.known for value in typed):
        return Value(Type("Action"))
    shoulder, elbow, tip, target, duration, branch = typed
    if branch.value not in BRANCHES:
        raise reach_error("reach_type", "ReachBranch requires one of its two opaque enum values.", node.args[5])
    point = tuple(component.value for component in target.value)
    if not all(math.isfinite(value) for value in point):
        raise reach_error("reach_domain", "A reach target must have finite canonical components.", node.args[3])
    if point[2] != 0:
        raise reach_error("reach_frame", "A planar reach target must have exact local z = 0.", node.args[3],
                          details={"target_m": list(point)})
    clock = Fraction(duration.value)
    if not Fraction(1, 1024) <= clock <= 60 or any(abs(value) > 8 for value in point[:2]):
        raise reach_error("reach_domain", "Reach target or duration is outside the supported closed range.", node,
                          details={"target_m": list(point), "duration_seconds": str(duration.value)})
    payload = ReachPayload(shoulder.value, elbow.value, tip.value,
                           target.frame, point, branch.value)
    return Value(Type("Action"), {"kind": "reach_planar", "target": shoulder.value,
                                  "duration": clock, "reach": payload})


def bind_description(compiler, path: str, value: Value) -> None:
    action = compiler.model.actions[path]
    if action.kind != "reach_planar":
        return
    # Keep the backing value alive as well as its id: object-id reuse must not
    # merge a later independent action description with a preceding one.
    descriptions = compiler._reach_descriptions
    key = id(value.value)
    if key not in descriptions:
        descriptions[key] = (value.value, action.element_id, source_location(compiler, action.span))
    _, identity, source = descriptions[key]
    action.reach = replace(action.reach, description_identity=identity, source_location=source)


def _chain(compiler, action) -> ReachPayload:
    model, payload = compiler.model, action.reach

    def fail(message, *, code="reach_chain", **details):
        raise reach_error(code, message, action.span, element_id=action.element_id, details=details)

    compiler.budget.tick(action.span)
    if payload.shoulder == payload.elbow:
        fail("The shoulder and elbow must be distinct hinge occurrences.")
    try:
        shoulder, elbow = (model.joints[path] for path in (payload.shoulder, payload.elbow))
        tip = model.sites[payload.tip]
        parent, upper_base, upper_end, forearm_base = (
            model.sites[path] for path in (shoulder.parent, shoulder.child, elbow.parent, elbow.child))
    except KeyError:
        fail("Reach operands must resolve to actual constructed joint and site occurrences.")
    if shoulder.kind != "hinge" or elbow.kind != "hinge":
        fail("Reach operands must be two prescribed hinges.")
    base, upper, forearm = parent.owner, upper_base.owner, forearm_base.owner
    if len({base, upper, forearm}) != 3 or upper_end.owner != upper or tip.owner != forearm:
        fail("The reach operands do not form the ordered base, upper-link and forearm chain.")
    if model.objects[upper].motion != "prescribed" or model.objects[forearm].motion != "prescribed":
        fail("Both reach links must have prescribed motion.")
    if shoulder.axis != (0.0, 0.0, 1.0) or elbow.axis != (0.0, 0.0, 1.0):
        fail("Both hinge axes must equal canonical positive local Z.")
    if any(site.pose.position != ZERO or site.pose.rotation != IDENTITY
           for site in (upper_base, forearm_base)):
        fail("Both hinge child sites must have identity local poses.")
    if any(site.pose.rotation != IDENTITY or site.pose.position[1:] != (0.0, 0.0)
           for site in (upper_end, tip)):
        fail("The elbow parent and tip must be unrotated positive local-X sites.")
    lengths = (upper_end.pose.position[0], tip.pose.position[0])
    if any(length <= 0 for length in lengths):
        fail("The elbow parent and tip must be positive local-X sites.")
    limits = (shoulder.limits, elbow.limits)
    if any(not 0.125 <= length <= 4.0 for length in lengths):
        fail("Each actual link length must lie in [0.125, 4] meters.", code="reach_domain", lengths_m=list(lengths))
    if any(not -PI64 <= value <= PI64 for joint in (shoulder, elbow)
           for value in (*joint.limits, joint.initial)):
        fail("Reach initial coordinates and closed limits must lie in [-Pi64, Pi64].", code="reach_domain")
    frame = shoulder.parent + ".frame"
    if payload.target_frame != frame:
        fail("The target must name the exact shoulder-parent site frame.", code="reach_frame",
             expected_frame=frame, actual_frame=payload.target_frame)

    # Existing relation validation has already established uniqueness and
    # acyclicity. Inspect actual incoming edges; ownership is not attachment.
    incoming = {model.sites[joint.child].owner: ("joint", joint)
                for joint in model.joints.values()}
    incoming.update({follow.child: ("follow", follow) for follow in model.follows.values()})
    current = base
    seen = set()
    while current is not None:
        compiler.budget.tick(action.span)
        if current in seen:
            fail("The reach base dependency chain is cyclic.")
        seen.add(current)
        if model.objects[current].motion not in {"static", "prescribed"}:
            fail("A reach base cannot depend on dynamic motion.")
        if current not in incoming:
            break
        kind, relation = incoming[current]
        if kind == "joint":
            if relation.kind != "fixed":
                fail("Only fixed transforms and massless following may precede a reach base.")
            current = model.sites[relation.parent].owner
        else:
            if model.objects[current].mass:
                fail("A reach base follow dependency must be massless.")
            current = model.frame_owner(relation.parent)
    return replace(payload, base_frame=frame, lengths_m=lengths, limits_rad=limits)


def bind_reaches(compiler) -> None:
    """Validate actual named bindings only, after the inherited pose graph."""
    reaches = [action for action in compiler.model.actions.values() if action.kind == "reach_planar"]
    if not reaches:
        return
    if len(reaches) > 128:
        raise reach_error("reach_resource", "The program exceeds 128 named reach actions.", reaches[128].span,
                          details={"budget": "named_reach_actions", "limit": 128, "consumed": len(reaches)})
    triples = set()
    for action in reaches:
        compiler.budget.tick(action.span)
        action.reach = _chain(compiler, action)
        payload = action.reach
        triples.add((tuple(compiler.model.joints[payload.shoulder].element_id),
                     tuple(compiler.model.joints[payload.elbow].element_id),
                     tuple(compiler.model.sites[payload.tip].element_id)))
        if len(triples) > 32:
            raise reach_error("reach_resource", "The program exceeds 32 distinct bound reach chains.", action.span,
                              element_id=action.element_id,
                              details={"budget": "structural_reach_chains", "limit": 32, "consumed": len(triples)})
