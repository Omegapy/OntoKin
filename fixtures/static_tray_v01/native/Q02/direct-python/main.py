from tray import make_tray

left = {'base_m': 0.001, 'clearance_m': 0.001, 'headroom_m': 0.001, 'payload_m': [0.01, 0.01, 0.01], 'rotation_wxyz': [1, 0, 0, 0], 'translation_m': [-10, -10, -10], 'wall_m': 0.001}
right = {'base_m': 0.025, 'clearance_m': 0.05, 'headroom_m': 0.1, 'payload_m': [1, 0.5, 1], 'rotation_wxyz': [1, 0, 0, 0], 'translation_m': [10, 10, 10], 'wall_m': 0.025}
record = {'schema_version': 'ontokin.static-tray.record/0.1.0', 'profile': 'ontokin.static-tray/0.1.0', 'contract': 'OK-MAP-STATIC-TRAY-001/0.1.0', 'template_id': 'static-tray-six-box/0.1.0', 'length_unit': 'm', 'frame': 'ontokin-world-rh-y-up', 'numeric_encoding': 'binary64-be-hex/1', 'material_set': 'static-tray-materials/0.1.0'}
record["trays"] = [make_tray("left", left), make_tray("right", right)]
