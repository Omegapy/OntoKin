# Opaque labels on native surfaces

The [adopted C080 contract](ADOPTION.md) defines an explicitly selected experimental texture path: source `0.13`, profile `textured-surfaces-0.1`, immutable bundle/files `0.2`, Agent `0.13`, and recorded GLB `0.13`. Earlier defaults and meanings remain unchanged. Implementation checks and integration are separate from this language guide and the [independent input freeze](../../../examples/textured-surfaces/acceptance-freeze.json).

## Author a label

Start from the complete [RGB panel source](../../../examples/textured-surfaces/sources/rgb-panel.ok) and its [file manifest](../../../examples/textured-surfaces/rgb-panel.files.json). The source wraps an existing native surface with `texture_surface`, names a stable material-region key, and assigns `texture_binding(png_asset(...), planar_uv(...))` to that region. The PNG digest is a literal source dependency. The manifest supplies the exact named bytes; no network or ambient image lookup occurs.

`planar_uv` takes a local origin in meters, two inverse-meter vectors, and two dimensionless offsets. Mapping uses raw recipe coordinates before rigid placement. For the 4-by-2-meter panel, `(0.25, 0, 0)` and `(0, -0.5, 0)` with offsets `(0, 1)` orient the image over the top region. The image's upper left is UV `(0, 0)`; V increases downward. Explicit scaling, reflection, shear and offsets retain their authored meaning. Values beyond the image edge use clamp-to-edge sampling.

The image multiplies the region's existing linear base-color factor after sRGB decoding. Opaque RGB or RGBA PNGs are supported; RGBA alpha must be 255 and the material alpha factor must be 1. Existing metallic and roughness values remain unchanged. Image sampling is nearest with no mipmaps.

## Transfer and edit exact bytes

Use the explicit manifest and destination:

```bash
python3 -m ontokin export examples/textured-surfaces/rgb-panel.files.json \
  --bundle --target ontokin.glb/0.13 --output /tmp/textured-panel.glb
```

The [Agent/0.13 contract](../agent-v0.13/README.md) describes source-and-asset transactions, source-only preservation, revision preconditions, metadata inspection and bounded exact byte retrieval. Image replacement normally changes both the attachment and its literal source digest in one transaction. A rejected edit preserves the previously accepted source and images.

## Finite scope

Each bundle admits at most four images, each at most 300,000 original PNG bytes and 256 by 256 pixels. PNG parsing, decompression and reconstruction run under the current execution budget. Normal limits remain 100,000 operations and 30,000 ms. Higher source requests require independent host authorization; retained revisions and previous validation do not grant authority.

One through sixteen existing material regions can be textured on a native loft, extrusion, holes, ring loft, framed loft or pockets recipe. Texture mapping does not add physical mass, collision, deformation or motion authority. Automatic unwrapping, transparency, texture atlases, normal maps, live engine physics and Unreal import are outside this finite contract. The full [OntoKin goal](../../../GOAL.md) remains open.
