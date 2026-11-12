"""Observe one actual Blender import, or reopen its saved native scene.

Use through run.py after the integrator's durable checkpoint. This script never
reconstructs product geometry, changes source, or executes source semantics.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from validation import (BUILD, INPUTS, REVISION, TIMES, TEXT_NAME, canonical,
                        require, validate_build, validate_inputs)

C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
INV = C.transposed()


def plain(value):
    if hasattr(value, 'to_dict'):
        return {k: plain(v) for k, v in value.to_dict().items()}
    if hasattr(value, 'to_list'):
        return [plain(v) for v in value.to_list()]
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if value is None or type(value) in (str, bool, int, float):
        return value
    return str(value)


def write(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def build_identity():
    return {'version': list(bpy.app.version), 'build_hash': bpy.app.build_hash.decode(),
            'binary_path': bpy.app.binary_path, 'python': sys.version,
            'executable_sha256': hashlib.sha256(Path(bpy.app.binary_path).read_bytes()).hexdigest()}


def material_values(material):
    require(material is not None and material.use_nodes, 'native material node tree missing')
    nodes = [n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']
    require(len(nodes) == 1, 'one actual Principled BSDF required')
    node = nodes[0]
    inputs = {'Base Color': list(node.inputs['Base Color'].default_value),
              'Metallic': node.inputs['Metallic'].default_value,
              'Roughness': node.inputs['Roughness'].default_value,
              'Alpha': node.inputs['Alpha'].default_value}
    require(not any(node.inputs[name].is_linked for name in inputs), 'unexpected linked material input')
    raw = {'name': material.name, 'use_nodes': material.use_nodes,
           'bsdf_type': node.type, 'bsdf_name': node.name, 'inputs': inputs,
           'use_backface_culling': material.use_backface_culling}
    values = {'baseColorFactor': inputs['Base Color'], 'metallicFactor': inputs['Metallic'],
              'roughnessFactor': inputs['Roughness'], 'alpha': inputs['Alpha'],
              'double_sided': not material.use_backface_culling}
    return raw, values


def observe_objects():
    rows = []
    for obj in sorted(bpy.context.scene.objects, key=lambda x: x.name):
        require(obj.type == 'MESH', 'unexpected native object: ' + obj.name)
        mesh = obj.data
        mesh.calc_loop_triangles()
        raw_triangles, source_triangles, material_indices = [], [], []
        for triangle in mesh.loop_triangles:
            raw_triangle, source_triangle = [], []
            for vertex_index, loop_index in zip(triangle.vertices, triangle.loops):
                position = mesh.vertices[vertex_index].co
                normal = mesh.corner_normals[loop_index].vector
                raw_triangle.append(list(position) + list(normal))
                source_triangle.append(list(INV.to_3x3() @ position) + list(INV.to_3x3() @ normal))
            raw_triangles.append(raw_triangle)
            source_triangles.append(source_triangle)
            material_indices.append(triangle.material_index)
        materials, values = [], []
        for slot in obj.material_slots:
            raw, value = material_values(slot.material)
            materials.append(raw)
            values.append(value)
        require(len(values) == 1, 'one native material slot required')
        rows.append({'name': obj.name, 'type': obj.type,
            'parent': obj.parent.name if obj.parent else None,
            'constraints': [x.type for x in obj.constraints], 'modifiers': [x.type for x in obj.modifiers],
            'rigid_body': obj.rigid_body is not None, 'vertex_count': len(mesh.vertices),
            'polygon_count': len(mesh.polygons), 'triangles_raw_blender': raw_triangles,
            'triangles': source_triangles, 'triangle_material_indices': material_indices,
            'materials': materials, 'material': values[0],
            'semantic_json': obj.get('ontokin_c211_semantic_json'),
            'element_id_json': obj.get('ontokin_c211_element_id_json'),
            'accepted_revision': obj.get('ontokin_c211_accepted_revision')})
    return rows


def observe_samples():
    rows = []
    scene = bpy.context.scene
    require(scene.render.fps == 60 and scene.render.fps_base == 1, 'native playback rate changed')
    for time in TIMES:
        frame = float(time)*60
        scene.frame_set(math.floor(frame), subframe=frame-math.floor(frame))
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        objects = {}
        for obj in sorted(scene.objects, key=lambda x: x.name):
            require(obj.type == 'MESH', 'unexpected sample object')
            native = obj.evaluated_get(depsgraph).matrix_world.copy()
            source = INV @ native @ C
            objects[obj.name] = {'matrix_world_blender': [list(row) for row in native],
                'matrix': [list(row) for row in source], 'position_m': list(source.to_translation()),
                'orientation_wxyz': list(source.to_quaternion()), 'scale': list(source.to_scale())}
        rows.append({'time_seconds': time, 'frame': frame, 'objects': objects})
    return rows


def observe(semantic, phase):
    scene = bpy.context.scene
    return {'schema': 'ontokin.c211.observations/0.1', 'phase': phase, 'build': build_identity(),
        'input_sha256': {n: v['sha256'] for n, v in INPUTS['files'].items()},
        'units': {'system': scene.unit_settings.system, 'scale_length': scene.unit_settings.scale_length,
                  'length_unit': scene.unit_settings.length_unit},
        'physics_world': scene.rigidbody_world is not None,
        'native_extras_before_mapping': json.loads(scene['ontokin_c211_native_extras_json']),
        'native_scene_extras_before_mapping': json.loads(scene['ontokin_c211_native_scene_extras_json']),
        'import_settings': json.loads(scene['ontokin_c211_import_settings_json']),
        'semantic_text': bpy.data.texts[TEXT_NAME].as_string(),
        'scene_mapping_json': scene['ontokin_c211_semantic_json'],
        'objects': observe_objects(), 'samples': observe_samples()}


def render_views(output):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 12
    scene.cycles.use_denoising = False
    for layer in scene.view_layers:
        layer.cycles.use_denoising = False
    scene.render.resolution_x, scene.render.resolution_y = 960, 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.12, 0.12, 0.12, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = 0.7
    camera_data = bpy.data.cameras.new('C211 review camera')
    camera = bpy.data.objects.new('C211 review camera', camera_data)
    scene.collection.objects.link(camera)
    camera_data.type, camera_data.ortho_scale = 'ORTHO', 5.3
    camera_data.clip_start, camera_data.clip_end = 0.01, 100
    light_data = bpy.data.lights.new('C211 review light', 'AREA')
    light = bpy.data.objects.new('C211 review light', light_data)
    scene.collection.objects.link(light)
    light_data.energy, light_data.shape, light_data.size = 1400, 'DISK', 6
    light.location = C.to_3x3() @ Vector((3, 5, 6))
    light.rotation_euler = (-light.location).to_track_quat('-Z', 'Y').to_euler()
    rows = []
    try:
        for label, time, eye in [('overview-t0', 0, (4, 3, 7)), ('overview-t1', 1, (4, 2, -7))]:
            scene.frame_set(int(time*60))
            camera.location = C.to_3x3() @ Vector(eye)
            camera.rotation_euler = (-camera.location).to_track_quat('-Z', 'Y').to_euler()
            scene.camera = camera
            path = output/(label+'.png')
            scene.render.filepath = str(path)
            require(bpy.ops.render.render(write_still=True) == {'FINISHED'}, 'native render did not finish')
            rows.append({'path': path.name, 'time_seconds': time, 'eye_source_m': eye,
                         'ortho_scale': camera_data.ortho_scale, 'engine': 'CYCLES', 'device': 'CPU',
                         'use_denoising': scene.cycles.use_denoising,
                         'view_layer_use_denoising': {layer.name: layer.cycles.use_denoising for layer in scene.view_layers},
                         'resolution': [960, 720], 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    finally:
        scene.camera = None
        bpy.data.objects.remove(camera, do_unlink=True)
        bpy.data.objects.remove(light, do_unlink=True)
        bpy.data.cameras.remove(camera_data)
        bpy.data.lights.remove(light_data)
        scene.frame_set(0)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mode', choices=('import', 'reopen'), required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    validate_build()
    require(list(bpy.app.version) == BUILD['version'] and bpy.app.build_hash.decode() == BUILD['build_hash'], 'runtime build differs')
    semantic, reference, reader = validate_inputs(args.inputs)
    if args.mode == 'reopen':
        require(bpy.ops.wm.open_mainfile(filepath=str(output/'received.blend'), load_ui=False, use_scripts=False) == {'FINISHED'}, 'native reopening failed')
        report = observe(semantic, 'reopen')
        write(output/'reopen-observations.json', report)
        return
    scene = bpy.context.scene
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1
    scene.unit_settings.length_unit = 'METERS'
    scene.render.fps, scene.render.fps_base = 60, 1
    bpy.ops.preferences.addon_enable(module='io_scene_gltf2')
    props = {p.identifier for p in bpy.ops.import_scene.gltf.get_rna_type().properties if p.identifier != 'rna_type'}
    require(props == set(BUILD['importer_properties']), 'importer operator property inventory changed')
    settings = {name: row['default'] for name, row in BUILD['importer_properties'].items()}
    settings['filepath'] = str((args.inputs/'after.glb').resolve())
    settings['files'] = []
    write(output/'actual-import-settings.json', settings)
    require(bpy.ops.import_scene.gltf(**settings) == {'FINISHED'}, 'GLB import did not finish')
    names = [o.name for o in scene.objects]
    require(len(names) == 18 and set(names) == set(reader.names), 'actual imported object inventory differs')
    native_extras = {o.name: {key: plain(o[key]) for key in o.keys()} for o in scene.objects}
    native_scene_extras = {key: plain(scene[key]) for key in scene.keys()}
    write(output/'native-extras-before-mapping.json', native_extras)
    for obj_record in semantic['objects']:
        obj = scene.objects[obj_record['path']]
        obj['ontokin_c211_semantic_json'] = canonical(obj_record)
        obj['ontokin_c211_element_id_json'] = canonical(obj_record['element_id'])
        obj['ontokin_c211_accepted_revision'] = REVISION
    text = bpy.data.texts.new(TEXT_NAME)
    require(text.name == TEXT_NAME, 'semantic text name collision')
    text.write(canonical(semantic))
    scene['ontokin_c211_semantic_json'] = canonical(semantic)
    scene['ontokin_c211_native_extras_json'] = canonical(native_extras)
    scene['ontokin_c211_native_scene_extras_json'] = canonical(native_scene_extras)
    scene['ontokin_c211_import_settings_json'] = canonical(settings)
    report = observe(semantic, 'import')
    # Persist raw measurements before rendering so a renderer failure cannot erase them.
    write(output/'import-observations.json', report)
    report['renders'] = render_views(output)
    write(output/'import-observations.json', report)
    require(bpy.ops.wm.save_as_mainfile(filepath=str(output/'received.blend'), check_existing=False) == {'FINISHED'}, 'native save failed')
    write(output/'native-save.json', {'path': 'received.blend', 'sha256': hashlib.sha256((output/'received.blend').read_bytes()).hexdigest(), 'bytes': (output/'received.blend').stat().st_size})


if __name__ == '__main__':
    main()
