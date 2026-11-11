"""Read pinned Blender Python source through AST, without importing bpy."""
from pathlib import Path
import ast
import hashlib
import json

ROOT = Path('/workspace/scratch/801d9d641f68/deps/blender-4.5.3-linux-x64')
OUT = Path('/workspace/scratch/801d9d641f68/c199-independent-preflight')
sources = {
    'gltf': ROOT / '4.5/scripts/addons_core/io_scene_gltf2/__init__.py',
    'io_utils': ROOT / '4.5/scripts/modules/bpy_extras/io_utils.py',
}
classes = {}
source_info = []

def compatible(value):
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, tuple):
        return [compatible(x) for x in value]
    if isinstance(value, list):
        return [compatible(x) for x in value]
    if isinstance(value, dict):
        return {k:compatible(v) for k,v in value.items()}
    return value

for key, path in sources.items():
    b = path.read_bytes()
    source = b.decode()
    source_info.append({'name':key,'path':str(path),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
    tree = ast.parse(source)
    for cls in tree.body:
        if not isinstance(cls, ast.ClassDef):
            continue
        props = {}
        for node in cls.body:
            if not isinstance(node, ast.AnnAssign) or not isinstance(node.annotation, ast.Call):
                continue
            row = {'name':node.target.id, 'declaring_class':cls.name, 'source':key, 'line':node.lineno, 'property_type':ast.unparse(node.annotation.func), 'declaration':ast.get_source_segment(source,node), 'keywords':{}, 'default_declared':False}
            for kw in node.annotation.keywords:
                item = {'expression':ast.unparse(kw.value)}
                try:
                    item['literal'] = compatible(ast.literal_eval(kw.value))
                    item['is_literal'] = True
                except (ValueError,TypeError):
                    item['is_literal'] = False
                row['keywords'][kw.arg] = item
                if kw.arg == 'default':
                    row['default_declared'] = True
                    row['declared_default'] = item
            props[row['name']] = row
        classes[cls.name] = props

def merged(names):
    result = {}
    for name in names:
        result.update(classes[name])
    return result

exports = merged(['ExportHelper','ConvertGLTF2_Base','ExportGLTF2_Base','ExportGLTF2'])
imports = merged(['ImportHelper','ConvertGLTF2_Base','ImportGLTF2'])
report = {'schema':'ontokin.c199.static-operator-inventory/0.1', 'method':'AST inspection only; no bpy import or Blender execution', 'sources':source_info,'export':exports,'import':imports,'limitations':['Maps declared inherited Python operator properties. Does not claim a dynamically observed RNA property dump.', 'Omitted defaults remain explicitly unidentified in the declared-default record.', 'export_format uses dynamic callback items and declared numeric default 0. get_format_items lists GLB first; explicit invocation should use GLB.', 'execute methods may derive internal exporter options from these operator inputs; those method bytes are pinned with the whole archive.']}
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'BLENDER-OPERATOR-PROPERTIES.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
for kind, props in [('EXPORT',exports),('IMPORT',imports)]:
    defaults = {name: row['declared_default']['literal'] for name,row in props.items() if row['default_declared'] and row['declared_default'].get('is_literal')}
    omitted = [name for name,row in props.items() if not row['default_declared']]
    dynamic = [name for name,row in props.items() if row['default_declared'] and not row['declared_default'].get('is_literal')]
    (OUT/(kind+'-DECLARED-DEFAULTS.json')).write_text(json.dumps(defaults,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'kind':kind,'properties':len(props),'explicit_literal_defaults':len(defaults),'omitted_default_properties':omitted,'dynamic_defaults':dynamic},sort_keys=True))
