"""Normalized, renderer-independent records shared by validation and evaluation.

Numbers are canonical SI binary64 constants. Scheduling uses the exact rational
value of each elaborated binary64 time. Paths are revision-local source lookup
paths; ``element_id`` contains the stable occurrence keys exposed to callers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any


Vec = tuple[float, float, float]
Quat = tuple[float, float, float, float]


@dataclass(frozen=True)
class Pose:
    frame: str = "world"
    position: Vec = (0.0, 0.0, 0.0)
    rotation: Quat = (1.0, 0.0, 0.0, 0.0)


@dataclass
class ObjectModel:
    path: str
    name: str
    class_name: str
    element_id: tuple[str, ...]
    owner: str | None = None
    placement: Pose = field(default_factory=Pose)
    velocity: Vec = (0.0, 0.0, 0.0)
    omega: Vec = (0.0, 0.0, 0.0)
    motion: str = "prescribed"
    collision: str = "disabled"
    geometry: dict[str, Any] = field(default_factory=lambda: {"kind": "empty"})
    appearance: tuple[float, float, float, float] = (0.5, 0.5, 0.5, 1.0)
    physical: dict[str, Any] = field(default_factory=lambda: {"kind": "no_body"})
    role: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    placement_authored: bool = False
    span: Any = None

    @property
    def mass(self) -> float:
        return self.physical.get("mass", 0.0)

    @property
    def radius(self) -> float | None:
        return self.physical.get("radius")

    @property
    def inertia(self) -> float | None:
        return self.physical.get("inertia")


@dataclass
class SiteModel:
    path: str
    element_id: tuple[str, ...]
    owner: str
    pose: Pose
    interface: str = "rigid.origin"
    size: float = 0.0
    span: Any = None


@dataclass
class JointModel:
    path: str
    name: str
    element_id: tuple[str, ...]
    kind: str
    parent: str
    child: str
    axis: Vec | None = None
    limits: tuple[float, float] | None = None
    initial: float | None = None
    span: Any = None


@dataclass
class FollowModel:
    path: str
    name: str
    element_id: tuple[str, ...]
    parent: str
    child: str
    offset: Pose
    span: Any = None


@dataclass
class ActionModel:
    path: str
    name: str
    element_id: tuple[str, ...]
    kind: str
    target: str
    duration: Fraction
    vector: Vec | None = None
    goal: float | None = None
    span: Any = None


@dataclass
class ImpulsePayload:
    """Elaborated source constants; application pose remains runtime state."""

    impulse_world_n_s: Vec
    point_self_m: Vec
    sequence_index: int
    source: dict[str, Any]


@dataclass
class Event:
    kind: str
    target: str
    span: Any = None
    impulse: ImpulsePayload | None = None


@dataclass
class EventBlock:
    time: Fraction
    events: list[Event]
    span: Any = None


@dataclass
class SceneModel:
    module_name: str
    module_key: str
    scene_name: str
    scene_key: str
    profile: str = "core-0.1"
    duration: Fraction = Fraction(0)
    gravity: Vec = (0.0, 0.0, 0.0)
    objects: dict[str, ObjectModel] = field(default_factory=dict)
    sites: dict[str, SiteModel] = field(default_factory=dict)
    joints: dict[str, JointModel] = field(default_factory=dict)
    follows: dict[str, FollowModel] = field(default_factory=dict)
    actions: dict[str, ActionModel] = field(default_factory=dict)
    events: list[EventBlock] = field(default_factory=list)
    diagnostics: list[Any] = field(default_factory=list)
    requested_capabilities: tuple[str, ...] = ()
    span: Any = None
    # These fields are populated only by the explicitly versioned construction
    # compiler. Per-file hashes retain their original Source.revision meaning.
    program_revision: str | None = None
    source_manifest: dict[str, Any] | None = None
    source_provenance: dict[str, Any] = field(default_factory=dict)
    occurrence_provenance: dict[str, Any] = field(default_factory=dict)
    collection_provenance: dict[str, Any] = field(default_factory=dict)

    def frame_owner(self, frame: str) -> str | None:
        """Return the instance containing an instance/site frame, or world."""
        if frame == "world":
            return None
        stem = frame.removesuffix(".frame")
        if stem in self.objects:
            return stem
        if stem in self.sites:
            return self.sites[stem].owner
        raise KeyError(frame)

    def owned_mass(self, path: str) -> float:
        return sum(obj.mass for obj in self.objects.values()
                   if obj.path == path or obj.path.startswith(path + "."))

