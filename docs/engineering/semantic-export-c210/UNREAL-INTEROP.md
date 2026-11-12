# Unreal interoperability boundary

Evidence checked: 2026-11-11 (America/Denver). This is the C210 conceptual boundary; it does not report destination execution.

## Implemented boundary

OntoKin's semantic export is experimental and engine-neutral. The current milestone produces source-bound semantic records and exact GLB references. It does not implement an Unreal/UEFN importer, a Verse generator, or a running Unreal object.

The concrete Scene Graph documentation verified here applies to **Unreal Editor for Fortnite (UEFN)**. Epic labels its Scene Graph feature **Beta**, and keeps some subfeatures in an **Experimental** category. This documentation is not evidence of a released Unreal Engine 6 API or of matching support in ordinary Unreal Engine projects. [E1, E2]

A later integration must name one installed receiving product and exact build, pin the relevant API surface, and execute the import in that application. The checked UEFN documentation says that from **36.00**, Scene Graph uses right-handed **Left-Up-Forward (LUF)** transforms from `/Verse.org`; the `/UnrealEngine.com` and `/Fortnite.com` transform types use XYZ. This is an API-boundary distinction, not a claim that 36.00 is the current release. The separate unit reference below is explicitly pinned to **Unreal Engine 5.6** and documents centimeter length defaults. It must not substitute for verification of a selected UEFN build's units. [E3, E4]

### Conceptual mappings for a later adapter

These are design proposals, not implemented support or a commitment to a destination API.

| OntoKin information | Candidate receiving representation | Required boundary |
| --- | --- | --- |
| Stable part identity and accepted source revision | External identity/provenance record associated with a receiving entity or asset | Preserve an explicit source-to-destination lookup; do not use display names or generated destination IDs as the only source identity |
| Reusable definition and occurrence | Prefab asset and instance, where the selected receiving application supports them | Check definition edits and occurrence overrides independently; resemblance to a prefab is not an automatic semantic equivalence |
| Ownership relationship | Metadata or a deliberately selected entity grouping | Ownership must not automatically create transform parenting, following, or a physical connection |
| Placement/frame and dimensions | Explicitly converted transform and geometry units | Declare the source and destination frames, length scale, handedness, and rotation convention; test with an asymmetric object |
| Material declarations | A finite supported destination material mapping | Record preserved values and any approximated or unsupported appearance; a material name alone does not prove a shader match |
| Sites and physical declarations | Preserved metadata until a receiving mapping is implemented and checked | Metadata for a site, mass, connection, or constraint does not establish destination collision or physics behavior |
| Motion authority | Destination-owned runtime behavior, when separately implemented | Do not infer motion, gameplay, or executable constraints from imported object metadata |

These boundaries matter because UEFN's entity hierarchy controls child lifetime, while its transform component can calculate a local transform relative to an explicit Origin instead of the hierarchy parent. Source ownership, transform placement, lifetime, following, and physical linkage therefore need separate treatment. Epic's prefab documentation supports reusable structures and instance overrides, but does not establish that OntoKin's definition/occurrence semantics map without loss. [E5, E6, E7]

## Official sources checked

All URLs below are Epic primary documentation. Retrieval date is above; the pages do not expose a stable publication date in the retrieved text.

- **E1 — Scene Graph**, UEFN/Fortnite documentation. Feature labeled Beta; Verse-native system. https://dev.epicgames.com/documentation/en-us/fortnite/scene-graph-in-unreal-editor-for-fortnite
- **E2 — Scene Graph Experimental Features**, UEFN/Fortnite documentation. Separate experimental category; currently lists skeletal animation. https://dev.epicgames.com/documentation/fortnite/scene-graph-experimental-features-in-fortnite
- **E3 — Left-Up-Forward Coordinate System**, UEFN/Fortnite documentation. Explicit version boundary 36.00; Scene Graph `/Verse.org` LUF vs legacy module XYZ types. https://dev.epicgames.com/documentation/en-us/fortnite/leftupforward-coordinate-system-in-unreal-editor-for-fortnite
- **E4 — Units of Measurement**, **Unreal Engine 5.6** documentation, version query pinned. Length centimeters; mass kilograms; angles degrees among documented defaults. https://dev.epicgames.com/documentation/en-us/unreal-engine/units-of-measurement-in-unreal-engine?application_version=5.6
- **E5 — Transforms in Scene Graph**, UEFN/Fortnite documentation. LocalTransform references hierarchy parent or explicit Origin; `/Verse.org/SceneGraph` transform component; right-handed LUF. https://dev.epicgames.com/documentation/en-us/fortnite/transforms-in-scene-graph-in-unreal-editor-for-fortnite
- **E6 — Working with Entities and Components**, UEFN/Fortnite documentation. Hierarchy/lifetime and component role; Beta. https://dev.epicgames.com/documentation/fortnite/working-with-entities-and-components-in-unreal-editor-for-fortnite
- **E7 — Prefabs and Prefab Instances**, UEFN/Fortnite documentation. Shared prefab information and per-instance overrides; Beta. https://dev.epicgames.com/documentation/fortnite/prefabs-and-prefab-instances-in-unreal-editor-for-fortnite


