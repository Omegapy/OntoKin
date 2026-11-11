from tray import make_tray

left = {'base_m': 0.006, 'clearance_m': 0.005, 'headroom_m': 0.02, 'payload_m': [0.2, 0.06, 0.12], 'rotation_wxyz': [1, 0, 0, 0], 'translation_m': [-0.3, 0, 0], 'wall_m': 0.004}
right = {'base_m': 0.006, 'clearance_m': 0.005, 'headroom_m': 0.02, 'payload_m': [0.16, 0.04, 0.1], 'rotation_wxyz': [1, 0, 0, 0], 'translation_m': [0.3, 0, 0], 'wall_m': 0.004}
record = {'schema_version': 'ontokin.static-tray.record/0.1.0', 'profile': 'ontokin.static-tray/0.1.0', 'contract': 'OK-MAP-STATIC-TRAY-001/0.1.0', 'template_id': 'static-tray-six-box/0.1.0', 'length_unit': 'm', 'frame': 'ontokin-world-rh-y-up', 'numeric_encoding': 'binary64-be-hex/1', 'material_set': 'static-tray-materials/0.1.0'}
record["trays"] = [make_tray("left", left), make_tray("right", right)]
