"""Synthetic C251 attachment model composed with unchanged C250 controls.

Host identity, tree membership, lifecycle, signals and all transforms are
fabricated Python data. This does not parse GDScript or execute a native tree.
"""
from copy import deepcopy
from dataclasses import dataclass, field
import importlib.util
import math
from pathlib import Path
import sys

_SPEC = importlib.util.spec_from_file_location('ontokin_c251_c250_model',
    Path(__file__).resolve().parents[1] / 'second-target-c250/inert_model.py')
c250 = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = c250
_SPEC.loader.exec_module(c250)
c249 = c250.c249
c247 = c249.c247
Name, PathValue, Facts, typed = c250.Name, c250.PathValue, c250.Facts, c250.typed
MESHES = c250.MESHES
TREE_SIGNALS = ('node_added', 'tree_changed')
WINDOW_SIGNALS = ('child_entered_tree', 'child_order_changed')
NODE_SIGNALS = ('tree_entered', 'tree_exiting', 'tree_exited', 'ready',
                'child_entered_tree', 'child_exiting_tree', 'child_order_changed',
                'renamed', 'replacing_by', 'visibility_changed', 'caches_cleared',
                'current_animation_changed')
IDENTITY_TRANSFORM = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0,
                      0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
PROCESS_FLAGS = ('processing', 'physics_processing', 'internal_idle',
                 'internal_physics', 'input_processing', 'shortcut_processing',
                 'unhandled_input_processing', 'unhandled_key_processing')


@dataclass
class HostView:
    identity: int = 8000
    native_class: str = 'SceneTree'
    alive: bool = True
    queued: bool = False
    script: object = None
    paused: bool = True
    physics_interpolation: bool = False
    editor_hint: bool = False
    main_thread_id: int = 1
    caller_thread_id: int = 1
    node_count: int = 1
    processed_tweens: int = 0
    current_scene: object = None
    main_loop: object = None
    window: object = None
    blocking_signals: bool = False
    signal_counts: dict = field(default_factory=lambda:{name:0 for name in TREE_SIGNALS})
    metadata: dict = field(default_factory=dict)


class Refusal(Exception):
    pass


class AttachedReader(c250.BoundaryReader):
    """Explicit attached-scene predicate; the inherited detached reader is intact."""

    def __init__(self, host):
        super().__init__()
        self.host = host

    def scene(self, root, materials, out):
        self.scene_reads += 1
        if getattr(root, 'scene_hook', None) is not None:
            root.scene_hook(root, self.scene_reads)
        chain = materials['mesh_arrays']['chain']
        out.update(nodes=[], material_bindings=[])
        self.check(type(root) is c247.NodeView and root.alive and root.native_class == 'Node3D'
                   and root.parent is self.host.window and root.identity == chain['root']['instance_id']
                   and root.inside_tree and root.tree is self.host,
                   'returned root differs from the intentional attachment')
        self.check(len(materials['parts']) == 18, 'incomplete owned material receipt')
        wanted, retired = {}, set()
        for index, part in enumerate(materials['parts']):
            self.check((part['source_node'], part['source_mesh'], part['source_primitive'], part['native_surface'])
                       == (index, MESHES[index], 0, 0), 'owned source association differs')
            identity = part['native_node_instance_id']
            self.check(identity not in wanted and identity == chain['finals'][index]['new'], 'ambiguous owned identity')
            wanted[identity] = index
            retired.add(chain['originals'][index]['old'])
        pending, seen, meshes, players = [root], set(), {}, []
        while pending:
            self.check(len(seen) < c249.MAX_SCENE_NODES, 'animation scene traversal bound exceeded')
            node = pending.pop()
            self.check(type(node) is c247.NodeView and node.alive, 'invalid final scene member')
            row = {'identity':self.identity(node), 'script':self.identity(node.script),
                   'queued_for_deletion':node.queued, 'inside_tree':node.inside_tree,
                   'name':typed(node.name), 'parent':self.identity(node.parent),
                   'owner':self.identity(node.owner),
                   'path_from_root':typed(PathValue('.' if node is root else str(node.name)))}
            out['nodes'].append(row)
            self.check(node.identity not in seen and node.identity not in retired and node.script is None
                       and not row['queued_for_deletion'] and row['inside_tree'] and node.tree is self.host,
                       'duplicate retired scripted queued or wrong-tree member')
            seen.add(node.identity)
            if node is not root:
                self.check(node.parent is root, 'unexpected finite fixture hierarchy')
                if node.native_class == 'MeshInstance3D':
                    self.check(node.identity in wanted, 'unmapped final mesh')
                    meshes[wanted[node.identity]] = node
                elif node.native_class == 'AnimationPlayer':
                    players.append(node)
                else:
                    self.refuse('unsupported scene member or additional mixer')
            self.check(len(pending)+len(seen)+len(node.children) <= c249.MAX_SCENE_NODES,
                       'animation scene traversal bound exceeded')
            pending.extend(node.children)
        self.check(len(seen) == 20 and len(meshes) == 18 and len(players) == 1,
                   'missing mesh or ambiguous animation player')
        out['player_count'] = len(players)
        for index in range(18):
            node = meshes[index]
            expected = materials['parts'][index]['snapshot']
            mesh = node.mesh
            row = {'source_node':index, 'node':self.identity(node), 'mesh':self.identity(mesh)}
            out['material_bindings'].append(row)
            self.check(mesh is not None and mesh.native_class == 'ArrayMesh' and row['mesh'] == expected['mesh'],
                       'owned mesh binding changed')
            row.update(mesh_script=self.identity(mesh.script), surface_count=mesh.surface_count,
                       surface_override_count=node.surface_override_count)
            self.check(mesh.script is None and not getattr(mesh, 'queued', False)
                       and mesh.surface_count == 1 and node.surface_override_count == 1,
                       'mesh script lifetime or inventory changed')
            material = mesh.surface_material
            active = node.active_override if node.override_active else node.material_override or node.surface_override or material
            row['selection'] = {'node_override':self.identity(node.material_override),
                                'overlay':self.identity(node.material_overlay),
                                'surface_override':self.identity(node.surface_override),
                                'mesh_surface':self.identity(material), 'active':self.identity(active),
                                'precedence':'node override then surface override then mesh surface'}
            row['instance_transparency'] = typed(node.instance_transparency)
            self.check(row['selection'] == expected['selection']
                       and row['instance_transparency'] == expected['instance_transparency']
                       and material is not None and material is active, 'owned material or selector binding changed')
            script = material.read_field('script')
            row['material_script'] = self.identity(script)
            self.check(script is None and not getattr(material, 'queued', False),
                       'owned material script or lifetime changed')
        return {'meshes':meshes, 'player':players[0], 'source_by_instance':wanted}


class Capture:
    def __init__(self):
        self.used = False
        self.errors = []
        self.result = {}
        self.preparation = c250.Capture()
        self.preparation_calls = 0
        self.boundary_reads = 0
        self.attachment_calls = 0
        self.attachment_hook = None
        self.boundary_hook = None

    def refuse(self, reason):
        if not self.errors:
            self.errors.append(reason)
        self.result.update(phase='REFUSED', component_complete=False)
        raise Refusal(reason)

    def check(self, condition, reason):
        if not condition:
            self.refuse(reason)

    def identity(self, value):
        if value is None:
            return {'type':0, 'instance_id':0, 'class':'null'}
        self.check(getattr(value, 'alive', False), 'invalid live identity')
        return {'type':24, 'instance_id':value.identity, 'class':value.native_class}

    def metadata(self, value, out):
        try:
            Facts().metadata(value, out)
        except ValueError as error:
            self.refuse('unsupported or incomplete metadata: ' + str(error))

    def host_snapshot(self, host, root, attached, out):
        out['tree'] = self.identity(host)
        self.check(type(host) is HostView and host.native_class == 'SceneTree' and host.main_loop is host,
                   'host is not the actual main-loop SceneTree')
        out.update(script=self.identity(host.script), queued=host.queued, paused=host.paused,
                   physics_interpolation=host.physics_interpolation, editor_hint=host.editor_hint,
                   main_thread=host.main_thread_id, caller_thread=host.caller_thread_id,
                   node_count=host.node_count, processed_tweens=host.processed_tweens,
                   current_scene=self.identity(host.current_scene),
                   blocking_signals=host.blocking_signals, signals={}, metadata=[])
        self.metadata(host, out['metadata'])
        for signal in TREE_SIGNALS:
            count = host.signal_counts.get(signal, -1)
            out['signals'][signal] = count
            self.check(type(count) is int and count == 0, 'tree lifecycle signal has a receiver or unknown coverage')
        self.check(not host.queued and host.paused is True and host.physics_interpolation is False
                   and host.editor_hint is False and host.caller_thread_id == host.main_thread_id
                   and host.current_scene is None and host.processed_tweens == 0
                   and not host.blocking_signals, 'unsupported host state')
        window = host.window
        row = {'identity':self.identity(window)}
        out['window'] = row
        self.check(type(window) is c247.NodeView and window.native_class == 'Window', 'host parent is not the root Window')
        row.update(script=self.identity(window.script), parent=self.identity(window.parent),
                   owner=self.identity(window.owner), name=typed(window.name), queued=window.queued,
                   inside_tree=window.inside_tree, ready=window.ready, tree=self.identity(window.tree),
                   process_mode=window.process_mode, process_thread_group=window.process_thread_group,
                   physics_interpolation_mode=window.physics_interpolation_mode,
                   interpolated=window.interpolated, can_process=window.can_process,
                   blocking_signals=window.blocking_signals,
                   children=[self.identity(child) for child in window.children], signals={}, metadata=[])
        self.metadata(window, row['metadata'])
        self.check(window.script is None and window.parent is None and window.owner is None
                   and not window.queued and window.inside_tree and window.ready and window.tree is host
                   and window.process_mode == 4 and window.process_thread_group in (0, 1)
                   and window.physics_interpolation_mode == 2 and not window.interpolated
                   and not window.blocking_signals and not window.can_process, 'unsupported Window parent state')
        self.check(host.node_count == (21 if attached else 1)
                   and len(window.children) == (1 if attached else 0)
                   and (not attached or window.children[0] is root), 'host children differ from declared root-only attachment')
        for signal in WINDOW_SIGNALS:
            count = window.signal_counts.get(signal, -1)
            row['signals'][signal] = count
            self.check(type(count) is int and count == 0, 'Window lifecycle signal has a receiver or unknown coverage')

    def node_snapshot(self, host, root, attached, out):
        pending, seen = [root], set()
        while pending:
            self.check(len(seen) < 20, 'unexpected node count')
            node = pending.pop()
            row = {'identity':self.identity(node)}
            out.append(row)
            self.check(type(node) is c247.NodeView and node.identity not in seen, 'duplicate or unsupported node')
            seen.add(node.identity)
            row.update(metadata=[], script=self.identity(node.script), queued=node.queued,
                       parent=self.identity(node.parent), owner=self.identity(node.owner), name=str(node.name),
                       inside_tree=node.inside_tree, ready=node.ready, tree=self.identity(node.tree),
                       process_mode=node.process_mode, process_thread_group=node.process_thread_group,
                       physics_interpolation_mode=node.physics_interpolation_mode,
                       interpolated=node.interpolated, groups=deepcopy(node.groups),
                       can_process=({'status':'NOT_OBSERVED', 'reason':'native getter requires SceneTree membership'}
                                    if not attached else node.can_process),
                       blocking_signals=node.blocking_signals, flags={}, signals={})
            self.metadata(node, row['metadata'])
            self.check(node.script is None and not node.queued and node.inside_tree is attached
                       and node.ready is attached and node.tree is (host if attached else None),
                       'node lifetime membership or readiness differs')
            self.check(node.process_mode == 0 and node.process_thread_group == 0
                       and node.physics_interpolation_mode == 0 and (not attached or not node.can_process)
                       and not node.groups and not node.blocking_signals and (not attached or not node.interpolated),
                       'node processing or interpolation policy differs')
            if attached:
                node.can_process_reads += 1
            for flag in PROCESS_FLAGS:
                row['flags'][flag] = getattr(node, flag)
                self.check(row['flags'][flag] is False, 'node has enabled processing: ' + flag)
            self.check(isinstance(node.signal_counts, dict) and len(node.signal_counts) <= 128,
                       'unknown or excessive signal inventory')
            for signal, count in node.signal_counts.items():
                row['signals'][signal] = count
                self.check(isinstance(signal, str) and type(count) is int and count == 0,
                           'product signal has a receiver or unknown coverage')
            if node.native_class in ('Node3D', 'MeshInstance3D'):
                row.update(top_level=node.top_level, scale_disabled=node.scale_disabled,
                           local_transform=deepcopy(node.local_transform),
                           local_transform_layout='basis columns x/y/z then origin; raw 12 components')
                self.check(not node.top_level and not node.scale_disabled, 'unsupported spatial transform policy')
                self.check(type(node.local_transform) is list and len(node.local_transform) == 12
                           and all(type(v) in (int, float) and math.isfinite(v) for v in node.local_transform),
                           'malformed or nonfinite raw local transform')
            else:
                self.check(node.native_class == 'AnimationPlayer', 'unsupported product node class')
            self.check(len(pending)+len(seen)+len(node.children) <= 20, 'unexpected subtree size')
            pending.extend(node.children)
        self.check(len(seen) == 20, 'incomplete node control inventory')

    def player_control(self, player, out):
        out.update(identity=self.identity(player), animation_active=player.animation_active,
                   internal_idle=player.internal_idle, internal_physics=player.internal_physics,
                   active=player.settings['active'], callback_mode_process=player.settings['callback_mode_process'],
                   playing=player.settings['playing'], current_animation=str(player.settings['current_animation']),
                   assigned_animation=str(player.settings['assigned_animation']), autoplay=str(player.settings['autoplay']))
        if not player.animation_active:
            out['omitted'] = 'position and length need assigned playback pointer'
            self.refuse('assigned playback pointer disappeared')
        player.position_reads += 1
        player.length_reads += 1
        out.update(position=player.current_position, length=player.current_length)
        self.check(not player.internal_idle and not player.internal_physics and not player.blocking_signals
                   and not player.signal_connections and player.settings['active']
                   and player.settings['callback_mode_process'] == 2 and not player.settings['playing']
                   and not player.settings['current_animation'] and not player.settings['autoplay']
                   and player.current_position == 0.0 and player.current_length == 2.0,
                   'prepared stopped player changed at attachment boundary')

    def boundary(self, registry, root, host, materials, expected, attached, receipt=None):
        self.boundary_reads += 1
        if receipt is None:
            receipt = {}
        receipt.update(complete=False, host={}, inventory={}, nodes=[], player_control={}, errors=[])
        reader = AttachedReader(host) if attached else c250.BoundaryReader()
        try:
            if self.boundary_hook is not None:
                self.boundary_hook(self.boundary_reads, attached, self)
            self.host_snapshot(host, root, attached, receipt['host'])
            reader.inventory(root, materials, receipt['inventory'], expected)
            live_scene = {}
            live = reader.scene(root, materials, live_scene)
            reader.check(live_scene == expected['scene'], 'scene drift before node control capture')
            player = live['player']
            self.node_snapshot(host, root, attached, receipt['nodes'])
            self.player_control(player, receipt['player_control'])
            receipt['inventory_recheck'] = {}
            reader.inventory(root, materials, receipt['inventory_recheck'], expected)
            receipt['host_recheck'] = {}
            self.host_snapshot(host, root, attached, receipt['host_recheck'])
            receipt['nodes_recheck'] = []
            self.node_snapshot(host, root, attached, receipt['nodes_recheck'])
            self.check(receipt['host_recheck'] == receipt['host'] and receipt['nodes_recheck'] == receipt['nodes'],
                       'host or node controls changed across readbacks')
            receipt['player_control_recheck'] = {}
            self.player_control(player, receipt['player_control_recheck'])
            self.check(receipt['player_control_recheck'] == receipt['player_control'],
                       'late stopped player control drift')
            self.check(not registry.faults and not self.errors, 'registry or component fault at boundary')
            receipt['complete'] = True
        except c249.Refusal:
            receipt['errors'] = reader.errors[:]
        except Refusal:
            receipt['errors'] = self.errors[:]
        return receipt

    @staticmethod
    def attached_inventory(original, host, root):
        result = deepcopy(original)
        for row in result['scene']['nodes']:
            row['inside_tree'] = True
            if row['identity']['instance_id'] == root.identity:
                row['parent'] = {'type':24, 'instance_id':host.window.identity, 'class':'Window'}
        return result

    def compare_transition(self, before, after, host, root):
        expected_host = deepcopy(before['host'])
        expected_host['window']['children'] = [self.identity(root)]
        expected_host['node_count'] = 21
        self.check(after['host'] == expected_host, 'host changed beyond intentional root attachment')
        expected_nodes = deepcopy(before['nodes'])
        for row in expected_nodes:
            row.update(inside_tree=True, ready=True, tree=self.identity(host), interpolated=False, can_process=False)
            if row['identity']['instance_id'] == root.identity:
                row['parent'] = self.identity(host.window)
        self.check(after['nodes'] == expected_nodes and after['player_control'] == before['player_control'],
                   'node metadata local transforms or controls changed beyond declared attachment lifecycle')

    def attach(self, host, root):
        """Fabricated add_child/lifecycle effects; never a native call."""
        self.attachment_calls += 1
        root.parent = host.window
        host.window.children.append(root)
        host.node_count += 20
        for node in [root] + root.children:
            node.inside_tree = True
            node.ready = True
            node.tree = host
            node.interpolated = False
            node.can_process = False
        if self.attachment_hook is not None:
            self.attachment_hook(host, root, self)

    def finish(self, registry, host):
        self.result['finish_threads'] = {'caller_thread':host.caller_thread_id,
                                         'main_thread':host.main_thread_id}
        if host.caller_thread_id != host.main_thread_id:
            self.result['registry_finish'] = {'status':'NOT_OBSERVED', 'reason':'unsupported thread'}
            if 'registry_final' not in self.result:
                self.result['registry_final'] = {'status':'NOT_OBSERVED', 'reason':'unsupported thread'}
            if not self.errors:
                self.errors.append('unsupported thread at registry finish')
            self.result.update(phase='REFUSED', component_complete=False)
        else:
            self.result['registry_final'] = {
                'faults':deepcopy(registry.faults),
                'model_registry_closed':registry.closed,
                'model_close_calls':registry.close_calls,
                'scope':'synthetic provider state; native active and closed session records are not modeled'}
            self.result['registry_finish'] = {'status':'OBSERVED'}
            if self.result['registry_final']['faults']:
                if not self.errors:
                    self.errors.append('registry fault observed at component finish')
                self.result.update(phase='REFUSED', component_complete=False)
        self.result['errors'] = self.errors[:]
        return deepcopy(self.result)

    def capture(self, registry, state, root, host):
        try:
            if self.used:
                self.refuse('attachment is single use; reentry or retry refused')
            self.used = True
            self.result = {'schema':'ontokin.c251.native-controlled-attachment/0.1', 'phase':'CAPTURING',
                           'component_complete':False, 'execution_admission':False, 'native_acceptance':False,
                           'R07':'PENDING', 'value_origin':'native-api-readback', 'mutations':[],
                           'diagnostic_coverage':'UNESTABLISHED',
                           'rollback':'never attempted; partial observed changes remain',
                           'omissions':['seek and advancement', 'world transforms and 126 poses',
                                        'raw sealing and serialization', 'complete native diagnostics']}
            self.result['entry_threads'] = {'caller_thread':host.caller_thread_id,
                                            'main_thread':host.main_thread_id}
            self.result['playback_preparation'] = {'status':'NOT_ATTEMPTED'}
            self.check(host.caller_thread_id == host.main_thread_id,
                       'wrong caller thread before any owned playback preparation')
            self.preparation_calls += 1
            preparation = self.preparation.capture(registry, state, root)
            self.result['playback_preparation'] = preparation
            self.check(preparation.get('component_complete') is True
                       and preparation.get('phase') == 'DETACHED_MANUAL_STOPPED_ASSIGNMENT_PREPARED_POSES_PENDING'
                       and not self.errors, 'owned playback preparation refused')
            inventory = preparation['animation_inventory']
            materials = inventory['materials']
            expected = deepcopy(preparation['mutations'][-1]['after']['inventory'])
            before = {}
            self.result['before_attachment'] = before
            self.boundary(registry, root, host, materials, expected, False, before)
            self.check(before['complete'] and not self.errors, 'attachment preflight refused')
            mutation = {'operation':'add_child', 'requested':{'parent':self.identity(host.window),
                         'child':self.identity(root), 'force_readable_name':False, 'internal':0},
                        'status':'ATTEMPTED', 'before':before, 'after':{'status':'NOT_OBSERVED'}}
            attached_expected = self.attached_inventory(expected, host, root)
            self.result['mutations'].append(mutation)
            self.attach(host, root)
            mutation['status'] = 'RETURNED'
            mutation['after'] = {}
            self.boundary(registry, root, host, materials, attached_expected, True, mutation['after'])
            if not mutation['after']['complete'] or self.errors:
                mutation['outcome'] = 'REFUSED_AFTER_ATTEMPT'
                self.refuse('attachment readback refused; changes retained')
            try:
                self.compare_transition(before, mutation['after'], host, root)
            except Refusal:
                mutation['outcome'] = 'REFUSED_AFTER_ATTEMPT'
                raise
            mutation['outcome'] = 'DECLARED_CHANGE_OBSERVED'
            self.result.update(phase='CONTROLLED_ATTACHMENT_CAPTURED_POSES_PENDING', component_complete=True,
                               stability='bounded readbacks; no atomicity transient-mutation or native-lifetime guarantee')
        except Refusal:
            pass
        return self.finish(registry, host)


def synthetic_fixture():
    registry, state, root = c250.synthetic_fixture()
    host = HostView()
    host.main_loop = host
    host.window = c247.NodeView(8001, native_class='Window')
    window = host.window
    window.name, window.owner, window.queued = Name('root'), None, False
    window.inside_tree, window.ready, window.tree = True, True, host
    window.process_mode, window.process_thread_group = 4, 0
    window.physics_interpolation_mode, window.interpolated = 2, False
    window.blocking_signals, window.metadata = False, {}
    window.can_process = False
    window.signal_counts = {name:0 for name in WINDOW_SIGNALS}
    for node in [root] + root.children:
        node.ready, node.tree = False, None
        node.process_mode, node.process_thread_group = 0, 0
        node.physics_interpolation_mode, node.interpolated = 0, True
        node.can_process, node.blocking_signals = False, False
        node.can_process_reads = 0
        node.groups = []
        node.metadata = deepcopy(getattr(node, 'metadata', {}))
        node.signal_counts = {name:0 for name in NODE_SIGNALS}
        for flag in PROCESS_FLAGS:
            setattr(node, flag, False)
        if node.native_class in ('Node3D', 'MeshInstance3D'):
            node.top_level, node.scale_disabled = False, False
            node.local_transform = IDENTITY_TRANSFORM[:]
            node.local_transform[9] = float(node.identity % 7)
    return registry, state, root, host


def fixture_objects(root):
    return c250.fixture_objects(root)
