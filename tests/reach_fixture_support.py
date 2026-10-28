"""Small evidence checks that do not require the reach evaluator or service."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ontokin.bundle import ProgramBundle


def source_unit_identity(program: ProgramBundle, returned: dict) -> dict:
    """Check returned bytes and labels against the immutable source unit.

    ProgramBundle.sources exposes detached diagnostic Source objects. Package
    pins belong to SourceUnit, obtained from ProgramBundle.units, instead.
    The returned identity uses verified labels, not unverified response fields.
    """
    units = {unit.source_id: unit for unit in program.units}
    source_id = returned["source_id"]
    if source_id not in units:
        raise AssertionError(f"Returned source unit is absent from the bundle: {source_id!r}")
    stored = units[source_id]
    if returned["source"].encode("utf-8") != stored.raw:
        raise AssertionError(f"Returned source bytes differ for {source_id!r}")
    if returned["source_revision"] != stored.revision:
        raise AssertionError(f"Returned source revision differs for {source_id!r}")
    if returned["filename"] != stored.filename:
        raise AssertionError(f"Returned source filename differs for {source_id!r}")
    return {
        "source_id": stored.source_id,
        "source_revision": stored.revision,
        "filename": stored.filename,
        "package_id": stored.package_id,
        "version": stored.version,
    }
