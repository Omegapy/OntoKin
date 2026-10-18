"""Program context plus actual per-source UTF-8 diagnostic locations."""
from __future__ import annotations


def diagnostic_dict(diagnostic, program, run_id=None):
    sources = program.sources

    def location(node, element_id=None):
        source_id = getattr(node, "source_id", None)
        if source_id not in sources:
            return None
        source = sources[source_id]
        return {"source_id": source_id, "source_revision": source.revision,
                "file": source.filename, "start_byte": node.start, "end_byte": node.end,
                "element_id": element_id}

    # The baseline supplies severity/category/repair rules. All location and
    # revision fields are replaced from actual source origins below.
    result = diagnostic.to_dict(program.entry.to_source(), run_id)
    primary = location(diagnostic.node, diagnostic.element_id)
    result.update(schema_version="ontokin.diagnostic/0.2", program_revision=program.program_revision,
                  source_id=None if primary is None else primary["source_id"],
                  source_revision=None if primary is None else primary["source_revision"],
                  primary=primary, related=[x for node in diagnostic.related if (x := location(node)) is not None])
    if primary is None:
        result["location_status"] = "program_condition_without_source_span"
    return result
