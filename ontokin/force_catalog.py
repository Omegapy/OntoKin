"""Additive source-force discovery; older profile catalogs are never mutated."""
from __future__ import annotations

import copy

PROFILE = "force-0.1"
SPEC = "docs/language-design/OK-LANG-005-finite-center-of-mass-force-intervals.md"
AGENT = "docs/engineering/OK-AGENT-005-finite-force-program-workflows.md"
EXPORT = "docs/engineering/OK-ENG-007-native-force-glb-export.md"
FIXTURE = "docs/language-design/force-v0.1/"


def force_catalog(inherited: dict) -> dict:
    """Build static metadata without reading files or evaluating a program."""
    result = copy.deepcopy(inherited)
    for item in result["items"]:
        item["inherited_from"] = item["id"]
        item["id"] = item["id"].replace("impulse-0.1/", PROFILE + "/", 1)
        item["profile"] = PROFILE
        if item["kind"] == "destination":
            item.update(id=PROFILE + "/destination/ontokin.glb/0.5", name="ontokin.glb/0.5",
                        capability="ontokin.glb/0.5", signature="destination: ontokin.glb/0.5",
                        availability="available_in_bounded_profile", available_levels=["delivered"], specification=EXPORT,
                        description="Native source geometry and regional PBR with recorded force-driven rigid motion.",
                        domains=["Explicit force-0.1 entry and ontokin.glb/0.5 destination; no automatic migration",
                                 "The requested end bounds evaluation; later source events and completions remain outside the recording",
                                 "Every exact boundary in the interval retains complete source force and impulse state",
                                 "Acceleration-aware sampling bounds translation chords and inherited angular motion within declared limits",
                                 "Binary64 evaluated states can exceed bounded float32 GLB delivery",
                                 "Recorded playback supplies no destination force engine, contacts or live physics",
                                 "Earlier destinations are not a fallback for force programs"],
                        examples=[FIXTURE + "p01-single-interval.files.json"])
        elif item["kind"] == "protocol":
            item.update(id=PROFILE + "/protocol/ontokin.agent/0.5", name="ontokin.agent/0.5",
                        signature='ProgramAgentService(store, protocol="ontokin.agent/0.5")',
                        specification=AGENT, store_filename="force-program-agent.sqlite3",
                        store_schema="ontokin.force-program-agent-store/0.1",
                        description="Explicit finite-force source workflow, isolated durable state and atomic edits.",
                        domains=["Only source 0.5 / force-0.1 entries with compatible pinned definitions",
                                 "Python default stays Agent/0.2; CLI default stays Agent/0.1",
                                 "No host-only force, impulse or velocity mutation operation",
                                 "Accepted source revisions authorize edits; derived force identities do not",
                                 "The complete final response is budgeted before any successful effect commits",
                                 "Explicit GLB/0.5 delivery evaluates and records only its requested prefix",
                                 "A failed or cancelled delivery commits no artifact or accepted candidate"])
        elif item["name"] == "persistent_agent_editing_service":
            item.update(description="Isolated force-program-agent.sqlite3; immutable source closure, requests and runs; no older-store migration.", specification=AGENT)
        elif item["name"] == "general_external_delivery":
            item["description"] = "Only explicit GLB/0.5 recorded force-profile delivery; arbitrary engines and live simulation remain unsupported."
        elif item["name"] == "external_forces_and_actuators":
            item["description"] = "General actuators, continuous torque, fields and controllers remain unsupported. The separate source_com_forces capability supplies only finite constant world COM intervals."
        elif item["kind"] == "constant" and item["name"] == "dynamic":
            item.update(description="Free homogeneous sphere with uniform gravity, authored instantaneous impulses and finite constant world COM forces; no contacts or connected loads.", specification=SPEC)
        elif item["name"] == "import":
            item["domains"].append("A force-0.1 declaring module may import compatible 0.2/0.3/0.4/0.5 definitions; older modules cannot import a 0.5 dependency")
        elif item["name"] in ("geometry.surface", "surface.mesh_page"):
            item["domains"].append("The Agent/0.5 source entry is force-0.1; nested geometry and page remain surface-0.1")
            if item["name"] == "surface.mesh_page":
                item["domains"].append("Signed context binds Agent/0.5 and entry_profile=force-0.1; no cross-binding cursor reuse")
        elif item["name"] == "state.pose_authority":
            item["domains"].append("Changed COM acceleration reanchors the trajectory; zero/cancelling/replacement forces preserving acceleration do not")
    template = next(i for i in result["items"] if i["kind"] == "event" and i["name"] == "impulse")
    additions = [
        ("event", "force", "source_com_forces",
         'force object_path @ "key" using Vector3<Force> for Time;',
         "Apply a constant world force at the center of mass of an actually free homogeneous sphere.",
         ["Contextual event statement in an exact-time ordered source sequence; no host RPC",
          "Mandatory unique source key; canonical positive duration; exact rational completion clock",
          "Overlaps combine as one final active set at the atomic boundary",
          "Release and impulse ordering is inherited; invalid boundaries roll back completely",
          "A valid requested prefix never evaluates an unrequested future completion"]),
        ("projection", "state.forces", "bounded_force_state", 'inspect(..., fields=["state"]) -> state.forces',
         "Complete active and latest source-bound force records, canonical world totals and exact clocks.",
         ["Active records are sorted by key; latest change records are complete and retained through unrelated boundaries",
          "World force and acceleration fields stay world-expressed during self-frame inspection",
          "Nested records and the final response obey work, cancellation, entry and byte limits",
          "Source locations come from the accepted evaluator; derived IDs do not grant edit authority"]),
        ("capability", "source_com_forces", "source_com_forces", "source_com_forces",
         "Finite constant world COM-force intervals within the adopted free-sphere profile.", []),
        ("capability", "bounded_force_state", "bounded_force_state", "bounded_force_state",
         "Bounded exact-source influence inspection through Agent/0.5.", []),
    ]
    for kind, name, capability, signature, description, domains in additions:
        item = {**copy.deepcopy(template), "id": f"{PROFILE}/{kind}/{name}", "kind": kind,
                "name": name, "capability": capability, "signature": signature,
                "description": description, "domains": domains, "specification": AGENT if kind == "projection" else SPEC,
                "language_rules": [], "examples": [], "effects": ["source-defined influence" if kind == "event" else "read-only metadata"]}
        item.pop("inherited_from", None)
        item.pop("state_schema", None)
        if name == "state.forces":
            item["state_schema"] = "https://ontokin.org/schemas/force-v0.1/forces.schema.json"
        result["items"].append(item)
    result.update(schema_version="ontokin.agent-catalog/0.5", profile=PROFILE, language_version="0.5",
                  agent_contract="ontokin.agent/0.5", delivery_targets=["ontokin.glb/0.5"],
                  planned_delivery_targets=[],
                  source_header='ontokin "0.5"; module Example @ "example"; profile "force-0.1";',
                  compatible_definition_profiles=["construction-0.1", "surface-0.1", "impulse-0.1", PROFILE],
                  complete_examples=[FIXTURE + "sources/p01-single-interval.ok"],
                  example_file_manifests=[FIXTURE + "p01-single-interval.files.json"],
                  example_context="The force example is an actual pinned source bundle; older snippets retain their authored profile context. Discovery executes no source or delivery.")
    # These two immutable libraries are already published as part of the source corpus.
    dependencies = []
    for d in inherited["example_bundles"][0]["dependencies"]:
        if d["package_id"] in ("fixture.impulse-parts", "fixture.surface-parts"):
            dependencies.append({**d, "path": d["path"].replace("impulse-v0.1/", "force-v0.1/")})
    result["example_bundles"] = [{"entry": result["complete_examples"][0], "dependencies": dependencies}]
    result["impulse_examples"] = {"language_version": "0.4", "paths": list(inherited["example_file_manifests"])}
    result["unavailable_capabilities"] = sorted({i["capability"] for i in result["items"] if i["availability"] == "unsupported"})
    result["numeric_limitations"].append("Finite COM forces use exact rational canonical-operand sums and piecewise quadratic trajectories; this adds no continuous torque, contacts or general-body solver.")
    return result
