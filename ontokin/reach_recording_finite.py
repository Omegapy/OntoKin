"""A completed finiteness receipt for one retained complete source graph.

No pose or public component is computed here. The ordinary boundary walk
admits each pose first; this receipt only avoids repeating that same complete
proof when the retained graph and every exact operand remain unchanged.
"""
from __future__ import annotations

from fractions import Fraction

from .reach_numeric import MAX_OPERAND_BITS
from .reach_pose import PoseValue, RotationValue, _PoseFinitenessProof


_MAX_FRAMES = 4096
_FRAMES_PER_CHECK = 8  # At most 120 fixed-size rational fingerprints per block.


def _pose_fingerprint(pose, ops, *, capture=False):
    """Read current immutable operands, without arithmetic or callbacks.

    Shared mutable proof families and incomplete/foreign memos keep their
    ordinary field path. Integer pairs also detect hostile replacement of a
    private Fraction or RotationValue after the original completed proof.
    """
    try:
        if (type(pose) is not PoseValue or pose._ops is not ops
                or type(pose._projection) is not dict
                or pose._finite_family is not None
                or type(pose.rotation) is not RotationValue
                or pose.rotation.frozen_projection is not None):
            return None
        proof = pose._finite_proof
        fields = (pose.exact_position, pose.rotation, pose.exact_velocity, pose.exact_omega)
        if (type(proof) is not _PoseFinitenessProof or proof.owner is not ops
                or type(proof.cap) is not int or proof.cap != MAX_OPERAND_BITS
                or type(proof.fields) is not tuple or len(proof.fields) != 4
                or any(current is not saved for current, saved in zip(fields, proof.fields))):
            return None
        vectors = (pose.exact_position, pose.rotation.components,
                   pose.exact_velocity, pose.exact_omega)
        if any(type(vector) is not tuple or len(vector) != size
               for vector, size in zip(vectors, (3, 4, 3, 3))):
            return None
        values = (*(value for vector in vectors for value in vector),
                  pose.rotation.error_rad, pose.position_error_m)
        result = []
        for value in values:
            if type(value) is not Fraction:
                return None
            numerator, denominator = value.numerator, value.denominator
            if (type(numerator) is not int or type(denominator) is not int
                    or denominator <= 0
                    or capture and max(abs(numerator).bit_length(), denominator.bit_length()) > 512):
                return None
            result.append((numerator, denominator))
        return tuple(result)
    except AttributeError:
        # Malformed private records cannot authorize the optional shortcut.
        return None


class _RecordingGraphFiniteness:
    """One bounded proof attached to the existing retained graph, never a cache."""

    def __init__(self, owner, poses, frames):
        self.owner = owner
        self.work = owner.work
        self.ops = owner.pose_ops
        self.state = owner.state
        self.check = owner.check
        self.external_check = owner.work.external_check
        self.poses = poses
        self.frames = frames
        self.pose_count = len(poses)
        self.rows = []
        self.valid = True
        self.active = False

    @classmethod
    def begin(cls, owner, poses, frames):
        if (type(poses) is not dict or type(frames) is not dict
                or not 1 <= len(frames) <= _MAX_FRAMES
                or type(owner.work.max_operand_bits) is not int
                or owner.work.max_operand_bits != MAX_OPERAND_BITS):
            return None
        return cls(owner, poses, frames)

    def _context(self, poses, frames):
        owner = self.owner
        return (self.valid and owner.work is self.work and owner.pose_ops is self.ops
            and self.ops.work is self.work and owner.state is self.state
            and owner.check is self.check and self.work.external_check is self.external_check
            and type(self.work.max_operand_bits) is int
            and self.work.max_operand_bits == MAX_OPERAND_BITS
            and poses is self.poses and frames is self.frames
            and type(poses) is dict and type(frames) is dict
            and type(self.rows) in (list, tuple) and 1 <= len(self.rows) <= _MAX_FRAMES
            and len(poses) == self.pose_count and len(frames) == len(self.rows))

    def append(self, path, pose):
        """Capture the fixed-size operands inside the already charged walk."""
        if not self.valid:
            return
        if type(path) is not str or len(self.rows) >= _MAX_FRAMES:
            self.valid = False
            return
        fingerprint = _pose_fingerprint(pose, self.ops, capture=True)
        if fingerprint is None:
            self.valid = False
            return
        alias = path.endswith(".frame") and self.poses.get(path[:-6]) is pose
        self.rows.append((path, pose, alias, fingerprint))

    def _same(self, poses, frames):
        if not self._context(poses, frames):
            return False
        for (path, pose), row in zip(frames.items(), self.rows):
            if type(row) is not tuple or len(row) != 4:
                return False
            saved_path, saved_pose, alias, fingerprint = row
            if (type(path) is not str or path != saved_path or pose is not saved_pose
                    or (path.endswith(".frame") and poses.get(path[:-6]) is pose) != alias
                    or _pose_fingerprint(pose, self.ops) != fingerprint):
                return False
        return True

    def complete(self):
        # Later row callbacks may have changed an earlier pose. The final read
        # is callback-free and publishes no partial or stale graph receipt.
        if self._same(self.poses, self.frames):
            self.rows = tuple(self.rows)
            return self
        return None

    def matches(self, owner, poses, frames):
        if (owner is not self.owner or self.active or not self._context(poses, frames)):
            return False
        self.active = True
        try:
            # The old numerical proof is reused, not repeated with fewer
            # charges. Only its bounded structural admission is performed.
            # Check the live domain after every callback; a transient narrowed
            # domain leaves this shortcut before another admission callback.
            for _ in range(0, len(self.rows), _FRAMES_PER_CHECK):
                self.work.charge("recording_graph_finiteness_guard")
                if (not self._context(poses, frames)
                        or owner._recording_graph_finiteness is not self):
                    return False
            # Source fields, map order, ownership and all exact operands are
            # read after the final callback. No numerical result is published.
            return self._same(poses, frames)
        finally:
            self.active = False
