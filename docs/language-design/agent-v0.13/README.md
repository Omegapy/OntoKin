# Agent/0.13 textured native surfaces

The [C080 adoption](../textured-surfaces-v0.1/ADOPTION.md) selects source `0.13`, profile `textured-surfaces-0.1`, immutable `ontokin.bundle/0.2` and `ontokin.files/0.2`, explicit Agent/0.13, and recorded GLB/0.13. This increment adds editable offline PNG attachments and affine texture mappings to the existing native surface recipes.

`TextureAgentService` retains the complete source and image snapshot in `texture-program-agent.sqlite3`, with store schema `ontokin.texture-program-agent-store/0.1`. Select it explicitly with `agent --protocol ontokin.agent/0.13`. The explicit file transport is `export --bundle PROGRAM.files.json --target ontokin.glb/0.13 --output MODEL.glb`. The manifest names every input; PNG paths never appear as implicit source lookups.

## Contracts and inherited operations

- [request.schema.json](request.schema.json) defines all twelve operations and exact source/module/asset edit shapes.
- [response.schema.json](response.schema.json) includes immutable attachment metadata, bounded raw slices, texture mapping metadata and actual per-corner UVs.
- [diagnostic.schema.json](diagnostic.schema.json) retains source-bound diagnostics, including the adopted `OKL-E-ASSET-*` and `OKL-E-TEXTURE-*` families.
- [bundle.schema.json](../textured-surfaces-v0.1/bundle.schema.json) describes inline source and canonical base64 attachments.
- [files.schema.json](../textured-surfaces-v0.1/files.schema.json) describes explicit root-confined ordinary-file inputs.

The twelve operations are `discover`, `create`, `edit`, `validate`, `inspect`, `surface.mesh_page`, `evaluate`, `reset`, `export`, `artifact`, `status`, and `cancel`. Asset inspection uses `inspect`; it introduces no thirteenth operation. Source edits retain exact UTF-8 file scopes, source revisions, byte offsets and expected-text checks.

Agent/0.13 permits at most 8,388,608 UTF-8 bytes in a complete request JSON envelope. Logical JSON entry/depth limits and the 4 MiB response limit are unchanged. Earlier protocols keep their earlier request limits and bundle/0.1 loaders. Schemas describe JSON shapes; transport code additionally requires integer tokens where specified, finite numbers, canonical base64, exact digests and cross-field equality.

## One immutable source and image revision

An inline bundle has exactly `schema_version`, `entry`, `modules`, and `assets`. Source descriptors keep their previous fields and byte identities. Every asset descriptor has exactly:

```json
{
  "asset_id": "label",
  "sha256": "sha256:5f87c7071d06327a077e05e1f57253370bc0b2eff1fa7f2025765825b7dcdd6e",
  "media_type": "image/png",
  "data_base64": "<canonical base64 of the complete original PNG>"
}
```

The placeholder above describes where the full canonical byte encoding belongs; it is not a valid PNG descriptor. The complete runnable [RGB panel manifest](../../../examples/textured-surfaces/rgb-panel.files.json) pins actual image bytes. File descriptors replace `data_base64` with `path` and retain the other three fields.

Asset IDs match `[a-z][a-z0-9._-]{0,63}`. A bundle contains zero through four distinct IDs, each at most 300,000 original PNG bytes, with at most 1,200,000 total bytes. Distinct IDs may retain identical bytes. The bundle revision includes sorted source and image identity descriptors under the `ontokin.bundle/0.2` domain. Reordering supplied arrays preserves the revision; changing bytes or an asset ID changes it. Each source's own revision still hashes only its exact source bytes.

Transport sealing checks sizes, canonical base64 and complete-byte digests. Current source validation checks the declared image closure and PNG semantics under the request's execution ledger. A retained candidate can therefore contain a semantically invalid PNG while preserving its exact inspectable bytes for repair.

## Atomic source, module and attachment edits

An edit still supplies `expected_program_revision`, `patches` and `requested_level`. `patches` may be empty when the request has a nonempty `module_changes` or `asset_changes` array. There are at most eight asset changes. Each original asset ID may be touched at most once.

| Change | Exact additional fields | Preconditions |
| --- | --- | --- |
| `add` | `asset` | The descriptor's ID is absent from the original bundle. |
| `replace` | `asset_id`, `expected_sha256`, `asset` | The original asset has the exact digest; the replacement keeps the same ID. |
| `remove` | `asset_id`, `expected_sha256` | The original asset has the exact digest. |

`asset` is the complete four-field descriptor shown above. Add, replace and remove records also contain `operation` with the corresponding value. Source-only edits preserve every attachment byte and ID. All source, module and asset changes form one candidate before validation or acceptance.

Replacing image bytes generally changes the literal digest used by `png_asset`. Patch that source literal and replace the image in the same edit. Adding an image also needs a matching reachable source declaration; removing an image needs removal of its declarations. A stale digest, duplicate touch or invalid candidate leaves the previous accepted source and attachments unchanged. Valid source-only mapping changes preserve image bytes, and an asset-only change cannot silently alter a source declaration.

## Metadata and bounded byte retrieval

To list attachments, submit `inspect` with `selector: {"kind":"texture_asset"}`, `fields: ["identity","source"]`, the immutable `program_revision`, and a positive `limit`. To select one asset, use the exact `selector: {"element_id":["assets","label"]}`. These selectors support only `identity` and `source` field groups. Asset IDs are a separate namespace from source-file identities.

Each item always has `element_id`, `kind: "texture_asset"`, and `name`. Requested identity fields contain `asset_id`, `element_id`, and `kind`. Requested source fields contain `asset_id`, `program_revision`, `sha256`, `media_type`, and `total_bytes`. These fields describe immutable transport identity. They make no claims about dimensions, opacity, valid PNG decoding or successful source construction.

Metadata pagination uses the existing response `next_cursor`. It binds the project, program revision, selector, field set, protocol and implementation. A changed source mapping produces a new program revision and invalidates use of an old cursor against that new revision. The original revision remains separately addressable.

For bytes, add `asset_slice: {"offset":0,"max_bytes":4096}` to an exact single-asset inspection. Do not include `cursor`, `run_id`, `time`, or `frame`, including explicit null values. `offset` is an integer from zero through the exact image length; `max_bytes` is an integer from 1 through 65,536. A successful result adds these fields:

| Field | Meaning |
| --- | --- |
| `asset_id`, `element_id`, `program_revision` | Exact attachment and immutable program context. |
| `sha256`, `media_type`, `total_bytes` | Complete original byte identity and length. |
| `offset`, `returned_bytes` | Starting byte and actual slice length. |
| `data_base64` | Canonical encoding of exactly this byte slice. |
| `next_offset` | Next byte offset, or null at the end. |
| `complete` | True when this slice reaches the end. |

An offset equal to `total_bytes` returns an empty, complete slice. An offset beyond it rejects. Concatenate decoded slices and verify the advertised complete-byte digest. Slice continuation uses byte offsets rather than metadata cursors.

## Surface inspection and recorded delivery

The underlying six geometry summary families retain their own fields and profiles. A textured summary additionally contains a `texture_bindings` object keyed by material region and `texture_coordinate_system: "raw_unplaced_recipe_local_affine"`. Each binding contains `asset_id`, `sha256`, `origin_m`, `u_per_m`, `v_per_m`, `offset`, `source_id`, `start`, `end`, and `mapping_id`. Source offsets identify the original UTF-8 `texture_binding` constructor call. Mapping IDs are prefixed SHA256 identities.

Every .13 `surface.mesh_page` includes these two texture fields, including an empty binding object for untextured geometry, plus `texcoords_0` aligned with `positions_m`. Each textured corner supplies its actual binary64 `[u,v]`; each untextured corner supplies null. A page contains at most 256 triangles. Revision, actual geometry, image identity and mapping/UV content bind its fingerprint and cursor. Image bytes are retrieved separately through attachment inspection.

Mappings are evaluated in raw unplaced recipe coordinates using exact rational affine sums followed by one binary64 rounding. Rigid visual placement and carrier motion leave these mappings attached to the surface. GLB/0.13 exports actual binary32 `TEXCOORD_0`, exact original PNG bytes, nearest filtering, clamp-to-edge wrapping, and the adopted sRGB texture sample multiplied by the material's linear color factor. Destination checks inspect actual emitted bytes before artifact publication.

## Current authority and durable outcomes

All work uses the current trusted host policy, one cumulative request counter and the original deadline. Source defaults remain 100,000 operations and 30,000 ms. An explicit larger source request requires an independently sufficient current host; caller caps only reduce the admitted allowance. Asset snapshot and read work is charged in addition to inherited source, compiler, geometry and response work. PNG parsing and reconstruction are admitted work, not unmetered transport work.

Reopening an accepted program grants no authority from its old receipt. New inspection, slices, export and artifact reads reauthorize under current host policy and caller limits. Source/module/asset acceptance, runs and successful artifacts keep the inherited publication transaction. Cancellation and interrupted publication cannot publish a successful partial texture artifact. Identical request IDs with identical canonical payloads return their durable outcomes; changed payloads under an existing identity reject.

The schemas and this interface do not establish complete release acceptance. Recorded GLB results do not establish Unreal import or live destination physics.
