"""Build the spacer with Blender and write a glTF binary in metres."""
from pathlib import Path
import sys

import bpy


def main():
    output_dir = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_cube_add(size=1)
    spacer = bpy.context.object
    spacer.name = "spacer"
    spacer.data.name = "spacer"

    # These lengths are expressed along the exported glTF axes.
    x_mm, y_mm, z_mm = 50, 12, 24
    spacer.scale = (x_mm / 1000, z_mm / 1000, y_mm / 1000)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.export_scene.gltf(
        filepath=str(output_dir / "spacer.glb"),
        export_format="GLB", export_yup=True, export_animations=False,
    )


if __name__ == "__main__":
    main()
