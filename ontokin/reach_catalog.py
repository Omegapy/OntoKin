"""Additive discovery for the adopted, explicitly selected planar reach profile."""
from __future__ import annotations

import copy

from .program_bindings import PROFILE_BINDINGS

PROFILE = "planar-reach-0.1"
SPEC = "docs/language-design/OK-LANG-006-reusable-planar-reach-actions.md"
AGENT = "docs/language-design/planar-reach-v0.1/agent-operations.md"
ADOPTION = "docs/language-design/planar-reach-v0.1/ADOPTION.md"
FIXTURE = "docs/language-design/planar-reach-v0.1/"


def reach_catalog(inherited):
    """Copy the earlier catalog; discovery does not evaluate any example."""
    result = copy.deepcopy(inherited)
    binding = PROFILE_BINDINGS[PROFILE]
    for item in result["items"]:
        item["inherited_from"] = item["id"]
        item["id"] = item["id"].replace("force-0.1/", PROFILE + "/", 1)
        item["profile"] = PROFILE
        if item["kind"] == "destination":
            item.update(id=PROFILE + "/destination/" + binding.destination,
                        name=binding.destination, capability=binding.destination,
                        signature="destination: " + binding.destination,
                        availability="available_in_bounded_profile" if binding.delivery_available else "unsupported",
                        available_levels=["delivered"] if binding.delivery_available else [],
                        specification=ADOPTION,
                        description="Recorded planar reach motion with complete source histories and stored-motion bounds.",
                        domains=["Explicit source 0.6 / planar-reach-0.1 and GLB/0.6; no older fallback",
                                 "Only the requested source prefix authorizes evaluation and delivery",
                                 "Exact source clocks round directly to stored binary32 values",
                                 "Complete before/after reach and incoming-release histories are required",
                                 "Unknown uniform numerical bounds cause rejection",
                                 "Recorded playback supplies no destination IK, contacts, grasp or live physics"],
                        examples=[FIXTURE + "p01.files.json"])
        elif item["kind"] == "protocol":
            item.update(id=PROFILE + "/protocol/" + binding.protocol, name=binding.protocol,
                        signature='ProgramAgentService(store, protocol="ontokin.agent/0.6")',
                        specification=AGENT, store_filename=binding.store_filename,
                        store_schema=binding.store_schema,
                        description="Twelve source-authoritative operations with complete reach context and isolated durable state.",
                        domains=["Only source 0.6 / planar-reach-0.1 entries and compatible pinned definitions",
                                 "Python default remains Agent/0.2 and CLI default remains Agent/0.1",
                                 "No host reach, joint-coordinate or goal-state mutation operation",
                                 "Named action/source scopes grant edit authority; derived projections do not",
                                 "Current accepted-source context and retained candidate-run provenance remain distinct",
                                 "Final complete response guards precede committed acceptance, run or artifact effects"])
        elif item["name"] == "persistent_agent_editing_service":
            item.update(description="Isolated planar-reach-program-agent.sqlite3 with immutable source, request and run identities; no older-store migration.",
                        specification=AGENT)
        elif item["name"] == "general_external_delivery":
            item["description"] = "Only the explicitly implemented recorded destination is available; arbitrary engines, live IK and physics remain unsupported."
        elif item["name"] == "import":
            item["domains"].append("A planar-reach-0.1 module may import compatible 0.2/0.3/0.4/0.5/0.6 definitions; older modules do not acquire reach builtins")
        elif item["name"] in ("geometry.surface", "surface.mesh_page"):
            item["domains"].append("Agent/0.6 entry context is planar-reach-0.1; nested geometry retains surface-0.1")
            if item["name"] == "surface.mesh_page":
                item["domains"].append("Signed context binds Agent/0.6 and entry_profile=planar-reach-0.1")

    template = next(item for item in result["items"] if item["name"] == "force" and item["kind"] == "event")
    additions = [
        ("type", "ReachBranch", "ReachBranch", "A typed branch value with no String or Int conversion.",
         ["Exactly elbow_positive and elbow_negative"]),
        ("constant", "elbow_positive", "elbow_positive: ReachBranch", "Select the nonnegative canonical elbow branch.", []),
        ("constant", "elbow_negative", "elbow_negative: ReachBranch", "Select the nonpositive canonical elbow branch.", []),
        ("function", "reach_planar", "reach_planar(JointRef, JointRef, SiteRef, Point3, Time, ReachBranch) -> Action",
         "Create an immutable description of a supported two-hinge reach.",
         ["Construction is pure; naming an Action binds its occurrence and lifecycle identity",
          "Target frame is exactly the shoulder parent-site frame; target z is zero",
          "Closed link lengths 0.125 through 4 m; absolute target components at most 8 m",
          "Closed duration 1/1024 through 60 s; canonical closed joint limits within ±Pi64",
          "At most 32 distinct chain tuples, 128 named reaches and 32 running or paused reaches",
          "Start proves exact annulus membership, canonical selected coordinates, limits and residual",
          "Both joints are claimed atomically; pause retains both claims; stop/completion releases both"]),
        ("projection", "actions.reach_planar", 'inspect(selector={"kind":"action"}, fields=["actions"])',
         "Complete source-bound two-joint state, sampled goal outcome and immutable terminal history.",
         ["Unrun current is unavailable with value null; construction is explicitly before-zero with no run",
          "Sampled observations name their actual run, source revision, time and boundary side",
          "Current goals are pending, active, satisfied or interrupted; failed admission is a boundary diagnostic",
          "Physical joint rates are distinct from this action's rates after a new owner starts",
          "Stopped/completed terminal snapshots are latched; paused completion clocks are null",
          "All repeated projections and the entire response consume the applicable output budget"]),
        ("capability", "reusable_planar_reach", "reusable_planar_reach",
         "Typed reusable prescribed planar reach descriptions and atomic lifecycle within OK-LANG-006/0.1.0.", []),
    ]
    for kind, name, signature, description, domains in additions:
        item = {**copy.deepcopy(template), "id": f"{PROFILE}/{kind}/{name}", "kind": kind,
                "name": name, "capability": "reusable_planar_reach", "signature": signature,
                "description": description, "domains": domains, "specification": AGENT if kind == "projection" else SPEC,
                "language_rules": [], "examples": [],
                "effects": ["pure immutable action description" if name == "reach_planar" else "read-only metadata"]}
        item.pop("inherited_from", None)
        item.pop("state_schema", None)
        if kind == "projection":
            item["state_schema"] = "https://omegapy.github.io/OntoKin/proposals/planar-reach-v0.1/reach-projection.schema.json"
            item["schema_authority"] = ADOPTION
        result["items"].append(item)

    result.update(schema_version="ontokin.agent-catalog/0.6", profile=PROFILE, language_version="0.6",
                  agent_contract=binding.protocol, adoption=ADOPTION,
                  delivery_targets=[binding.destination] if binding.delivery_available else [],
                  planned_delivery_targets=[] if binding.delivery_available else [binding.destination],
                  source_header='ontokin "0.6"; module Example @ "example"; profile "planar-reach-0.1";',
                  compatible_definition_profiles=["construction-0.1", "surface-0.1", "impulse-0.1", "force-0.1", PROFILE],
                  complete_examples=[FIXTURE + "sources/p01-bench-positive.ok"],
                  example_file_manifests=[FIXTURE + "p01.files.json"],
                  example_context="The adopted examples retain their original source bytes and proposal comments. Discovery describes their context and executes no source, admission or delivery.")
    dependencies = [
        ("reach-assets", "6551d3dd5a772e85e92547d71db081e6ae7c21a0f3d57424b01c64a18191d6ba"),
        ("reach-exterior", "3b94fc91ca96f8fb0b21a90a1d6b4d78cdbd19600383a10cb6a3646ba67af763"),
        ("reach-parts", "aa04a78696122cd18def6993b1056971f8990a21e8617b3ee73ca98be9b9b0cb"),
    ]
    result["example_bundles"] = [{"entry": result["complete_examples"][0], "dependencies": [
        {"package_id": "proposal." + name, "version": "0.1.0", "digest": "sha256:" + digest,
         "path": FIXTURE + "libraries/" + name + ".ok"} for name, digest in dependencies]}]
    result["limits"].update(max_reach_chain_tuples=32, max_named_reach_actions=128,
                            max_running_or_paused_reaches=32, max_reach_time_tolerance_s=1e-6)
    result["numeric_limitations"].append("Planar admission uses bounded proof of the selected binary64 coordinates; inconclusive proof and exhausted request work fail explicitly. This adds no load solution, world-target tracking, grasp, balance or locomotion.")
    result["unavailable_capabilities"] = sorted({item["capability"] for item in result["items"] if item["availability"] == "unsupported"})
    return result
