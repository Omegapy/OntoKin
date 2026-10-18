"""Versioned discovery data for the bounded core and its local agent binding.

The catalog describes supported syntax and contracts; it does not execute the
examples or certify a particular program. Names/signatures follow LANG-003,
LANG-011--013, LANG-022--023 and the implemented validator. Capability values
are discovery labels, not extensions accepted by a source `requires` clause.
"""

from __future__ import annotations

import copy
import hashlib
import json

from .values import ALIASES


_LANG = "docs/language-design/OK-LANG-001-core-language-specification.md"
_FIXTURES = "docs/language-design/core-v0.1/"
_LEVELS = ["represented", "constructed", "evaluated"]


def _entry(kind, name, signature, description, *, capability="typed_quantities",
           domains=(), defaults=None, effects=("pure immutable description",),
           examples=(), rules=(), available=True, **extra):
    return {
        "id": f"core-0.1/{kind}/{name}", "kind": kind, "name": name,
        "capability": capability, "signature": signature,
        "description": description, "domains": list(domains),
        "defaults": {} if defaults is None else defaults,
        "effects": list(effects), "examples": list(examples),
        "available_levels": list(_LEVELS) if available else [],
        "availability": "available_in_bounded_profile" if available else "unsupported",
        "language_rules": list(rules), "specification": _LANG, **extra,
    }


def _build():
    items = []
    types = {
        "Int": ("Int", "Signed 64-bit integer; implicit Real widening must be exact.",
                ["-9223372036854775808 <= value <= 9223372036854775807"], "12"),
        "Real": ("Real", "Finite binary64 scalar; integer division yields Real.",
                 ["No NaN or infinity", "No implicit dimension from a bare scalar"], "0.5"),
        "Bool": ("Bool", "Boolean value with short-circuit and/or; no truthiness conversion.", [], "true"),
        "String": ("String", "UTF-8 source string representing Unicode text.", [], '"marker"'),
        "Quantity": ("Quantity[unit]", "Scalar with normalized length/mass/time/angle dimensions.",
                     ["Normalized exponents from -16 through 16", "Dimensionless arithmetic results are Real"], "1[N]"),
        "Vec3": ("Vec3<Q>", "Unframed triple of compatible numeric/quantity components.",
                 ["No implicit frame", "Integer constructor components widen to Real"], "vec3(1, 0, 0)"),
        "Vector3": ("Vector3<Q>", "Triple with an expressed-in frame identity.",
                    ["Compatible dimensions and identical frame required for vector arithmetic"],
                    "vector(world, 1[m/s], 0[m/s], 0[m/s])"),
        "Point3": ("Point3", "Position with length coordinates and an explicit frame.",
                   ["Adding two points is invalid"], "point(world, 0[m], 1[m], 0[m])"),
        "Rotation": ("Rotation", "Proper rigid orientation, source projections in (w,x,y,z) order.",
                     ["No Euler convention, reflection, shear or scale", "No source equality operator"], "quat(1, 0, 0, 0)"),
        "Pose": ("Pose", "Rigid position/orientation relative to an identified frame.",
                 ["No scale", "No source equality operator"], "pose(world, vec3(0[m], 0[m], 0[m]), quat(1, 0, 0, 0))"),
        "Range": ("Range<Q>", "Ordered closed scalar/quantity interval.",
                  ["Compatible bounds", "lower <= upper"], "range(0[m], 1[m])"),
        "Color": ("Color", "Immutable linear RGBA appearance, independent of physical matter.",
                  ["Each component is finite and in [0,1]"], "rgba(0.2, 0.6, 0.9, 1)"),
        "Geometry": ("Geometry", "Immutable empty/sphere/box description; details inspectable.",
                     ["No implicit physical body"], "sphere(0.2[m])"),
        "BodyModel": ("BodyModel", "No matter or a homogeneous solid-sphere physical proxy.",
                      ["Visible geometry may differ", "No box-body model"], "sphere_body(0.2[m], 1[kg])"),
        "MotionMode": ("MotionMode", "Initial static, prescribed, or passive dynamic mode.",
                       ["Dynamic mode requires the supported free sphere contract"], "prescribed"),
        "CollisionMode": ("CollisionMode", "Collision setting; only disabled exists in core.", [], "disabled"),
        "Ref": ("Ref<C>", "Non-owning nominal object reference; copying preserves identity.",
                ["C is Object or a declared class", "No null reference", "No structural typing"], "Ref<Object>"),
        "FrameRef": ("FrameRef", "Reference to world, an object frame, or an attachment frame.", [], "world"),
        "SiteRef": ("SiteRef", "Reference to an immutable attachment site.", [], "rig.origin"),
        "JointRef": ("JointRef", "Reference to a fixed, hinge, slider, or grip joint.", [], "rig.yaw"),
        "Action": ("Action", "Immutable move/spin/tween description; creation does not start it.",
                   ["A named action declaration supplies an independent lifecycle identity"],
                   "tween(rig.yaw, 90[deg], 1[s])"),
        "Object": ("Object", "Implicit nominal root of user classes; can be an empty container.",
                   ["Construction uses object/part declarations, not a constructor call"], 'object root @ "root": Object {}'),
    }
    for name, (signature, description, domains, example) in types.items():
        items.append(_entry("type", name, signature, description, domains=domains,
                            examples=[example], rules=["LANG-003", "LANG-004", "LANG-006"]))
    units = {"Length": "m", "Area": "m^2", "Volume": "m^3", "Mass": "kg", "Time": "s",
             "Angle": "rad", "Speed": "m/s", "Acceleration": "m/s^2", "AngularSpeed": "rad/s",
             "Force": "N", "Torque": "N*m", "Density": "kg/m^3", "Inertia": "kg*m^2"}
    for name, dimension in ALIASES.items():
        items.append(_entry("type", name, f"Quantity[{units[name]}]",
                            "Named checked quantity alias; having a type does not supply a physical solver.",
                            examples=[f"1[{units[name]}]"], rules=["LANG-003", "LANG-005"],
                            normalized_dimension=list(dimension), canonical_unit=units[name]))

    # Each tuple is (name, signature, result type, domains, example, capability).
    calls = [
        ("real", "real(Int) -> Real", "Real", ["Explicit rounded integer conversion"], "real(9007199254740993)", "typed_quantities"),
        ("abs", "abs(Q) -> Q", "Q", ["Numeric scalar or quantity", "Integer minimum overflows"], "abs(-2[m])", "typed_quantities"),
        ("min", "min(Q,Q) -> Q", "Q", ["Compatible numeric scalar/quantity arguments"], "min(1[m], 2[m])", "typed_quantities"),
        ("max", "max(Q,Q) -> Q", "Q", ["Compatible numeric scalar/quantity arguments"], "max(1[m], 2[m])", "typed_quantities"),
        ("near", "near(Q,Q,Q) -> Bool", "Bool", ["Compatible scalar/quantity arguments", "Third argument is a nonnegative absolute tolerance"], "near(1[m], 1.001[m], 0.002[m])", "typed_quantities"),
        ("sqrt", "sqrt(Real) -> Real", "Real", ["Argument >= 0", "Quantity square root is unavailable"], "sqrt(4.0)", "typed_quantities"),
        ("sin", "sin(Angle) -> Real", "Real", ["Angle interpreted in canonical radians"], "sin(90[deg])", "typed_quantities"),
        ("cos", "cos(Angle) -> Real", "Real", ["Angle interpreted in canonical radians"], "cos(0[rad])", "typed_quantities"),
        ("vec3", "vec3(Q,Q,Q) -> Vec3<Q>", "Vec3<Q>", ["Compatible components; integer components widen to Real"], "vec3(1, 0, 0)", "typed_quantities"),
        ("vector", "vector(FrameRef,Q,Q,Q) -> Vector3<Q>", "Vector3<Q>", ["Explicit expressed-in frame", "Compatible components; integer components widen to Real"], "vector(world, 1[m/s], 0[m/s], 0[m/s])", "typed_quantities"),
        ("point", "point(FrameRef,Length,Length,Length) -> Point3", "Point3", ["Explicit position frame and length components"], "point(world, 0[m], 1[m], 0[m])", "typed_quantities"),
        ("quat", "quat(Real,Real,Real,Real) -> Rotation", "Rotation", ["Components are w,x,y,z", "Finite nonzero tuple; norm differs from one by at most 1e-12", "Normalize and choose canonical sign"], "quat(1, 0, 0, 0)", "typed_quantities"),
        ("axis_angle", "axis_angle(Vec3<Real>,Angle) -> Rotation", "Rotation", ["Nonzero dimensionless axis; norm differs from one by at most 1e-12", "Right-hand angle in radians"], "axis_angle(vec3(0, 1, 0), 90[deg])", "typed_quantities"),
        ("pose", "pose(FrameRef,Vec3<Length>,Rotation) -> Pose", "Pose", ["Rigid transform relative to named frame; no scale"], "pose(world, vec3(0[m], 1[m], 0[m]), quat(1, 0, 0, 0))", "typed_quantities"),
        ("range", "range(Q,Q) -> Range<Q>", "Range<Q>", ["Compatible scalar/quantity bounds", "lower <= upper", "Integer bounds widen to Real"], "range(-90[deg], 90[deg])", "typed_quantities"),
        ("rgba", "rgba(Real,Real,Real,Real) -> Color", "Color", ["Each component is finite and in [0,1]", "Linear RGB; alpha does not change matter"], "rgba(0.2, 0.6, 0.9, 1)", "appearance"),
        ("empty", "empty() -> Geometry", "Geometry", ["No visible surface"], "empty()", "primitive_geometry"),
        ("sphere", "sphere(Length) -> Geometry", "Geometry", ["Strictly positive radius", "Centered at object frame"], "sphere(0.2[m])", "primitive_geometry"),
        ("box", "box(Vec3<Length>) -> Geometry", "Geometry", ["Three strictly positive full side lengths", "Centered at object frame"], "box(vec3(1[m], 2[m], 0.5[m]))", "primitive_geometry"),
        ("no_body", "no_body() -> BodyModel", "BodyModel", ["Contributes no physical matter"], "no_body()", "sphere_body"),
        ("sphere_body", "sphere_body(Length,Mass) -> BodyModel", "BodyModel", ["Strictly positive radius and mass", "Homogeneous solid sphere; COM at object origin", "Derived isotropic inertia (2/5)*mass*radius^2 remains positive and finite", "No collision response"], "sphere_body(0.2[m], 1[kg])", "sphere_body"),
        ("move", "move(Ref<Object>,Vector3<Speed>,Time) -> Action", "Action", ["Positive duration; vector expressed in world axes", "At admission target is a free prescribed root and its translation channel is available"], "move(rig, vector(world, 1[m/s], 0[m/s], 0[m/s]), 2[s])", "move_spin_tween"),
        ("spin", "spin(Ref<Object>,Vector3<AngularSpeed>,Time) -> Action", "Action", ["Positive duration; vector expressed in world axes", "At admission target is a free prescribed root and its orientation channel is available"], "spin(rig, vector(world, 0[rad/s], 1[rad/s], 0[rad/s]), 1[s])", "move_spin_tween"),
        ("tween", "tween(JointRef,Angle,Time) -> Action | tween(JointRef,Length,Time) -> Action", "Action", ["Hinge requires Angle; slider requires Length", "Positive duration", "Target within mandatory joint range and coordinate channel available at admission"], "tween(rig.yaw, 90[deg], 1[s])", "move_spin_tween"),
    ]
    for name, signature, result_type, domains, example, capability in calls:
        items.append(_entry("builtin", name, signature, "Built-in positional callable; no optional arguments or user overload resolution.",
                            capability=capability, domains=domains, examples=[example],
                            effects=["construct immutable action description; no start effect"] if result_type == "Action" else ["pure value construction"],
                            rules=["LANG-023", "LANG-004"], result_type=result_type))

    fields = [
        ("role", "String", "occurrence key", "Metadata independent of display name", 'role = "marker";'),
        ("geometry", "Geometry", "empty()", "Visible description; no implicit matter", "geometry = sphere(0.2[m]);"),
        ("appearance", "Color", "rgba(0.5,0.5,0.5,1)", "Linear RGB independent of physical matter", "appearance = rgba(0.2,0.6,0.9,1);"),
        ("physical", "BodyModel", "no_body()", "Own matter counted once", "physical = sphere_body(0.2[m],1[kg]);"),
        ("motion", "MotionMode", "prescribed", "Dynamic state only for supported free sphere model", "motion = prescribed;"),
        ("collision", "CollisionMode", "disabled", "disabled is the only supported value", "collision = disabled;"),
        ("placement", "Pose", "world identity if no incoming pose relation", "Authored placement requires world and no incoming relation; class-authored defaults also count", "placement = pose(world,vec3(0[m],1[m],0[m]),quat(1,0,0,0));"),
        ("velocity", "Vector3<Speed>", "world zero", "World-measured COM velocity in world axes; nonzero values only initialize free dynamic bodies", "velocity = vector(world,0[m/s],0[m/s],0[m/s]);"),
        ("omega", "Vector3<AngularSpeed>", "world zero", "World-measured/expression angular velocity; nonzero values only initialize free dynamic bodies", "omega = vector(world,0[rad/s],0[rad/s],0[rad/s]);"),
    ]
    for name, typ, default, domain, example in fields:
        items.append(_entry("member", "Object." + name, f"Object.{name}: {typ}", "Elaborated built-in object field.",
                            capability="independent_parts", domains=[domain], defaults={"profile_fallback": default},
                            examples=[example], rules=["LANG-011"], value_type=typ,
                            writable="direct occurrence initializer or class default; nested paths only for public user parameters"))

    readonly = {
        "Object.frame": ("FrameRef", "Implicit object frame; ownership does not determine its world pose"),
        "Object.origin": ("SiteRef", "Identity offset; interface rigid.origin; size 0[m]"),
        "Vec3.x,y,z": ("Q", "Immutable unframed components"),
        "Vector3.x,y,z": ("Q", "Immutable components expressed in frame"),
        "Vector3.frame": ("FrameRef", "Expressed-in axes; operation defines measurement meaning"),
        "Point3.x,y,z": ("Length", "Position coordinates"),
        "Point3.frame": ("FrameRef", "Position reference frame"),
        "Rotation.w,x,y,z": ("Real", "Rounded projections of normalized (w,x,y,z) coordinates"),
        "Pose.frame": ("FrameRef", "Pose reference frame"),
        "Pose.position": ("Vec3<Length>", "Translation in reference frame"),
        "Pose.rotation": ("Rotation", "Local axes mapped into reference axes"),
        "Range.lower,upper": ("Q", "Immutable ordered bounds"),
        "Color.r,g,b,a": ("Real", "Linear RGB and alpha in [0,1]"),
        "SiteRef.frame": ("FrameRef", "Identified site frame"),
        "SiteRef.pose": ("Pose", "Constant pose in owning object frame"),
        "SiteRef.interface": ("String", "Nonempty ideal compatibility identifier"),
        "SiteRef.size": ("Length", "Nonnegative canonical compatibility size"),
        "JointRef.parent,child": ("SiteRef", "Connection endpoint sites"),
        "JointRef.axis": ("Vec3<Real>", "Hinge/slider only; unit axis in parent-site axes"),
        "JointRef.limits": ("Range<Angle> | Range<Length>", "Hinge/slider only; closed mandatory coordinate range"),
        "JointRef.initial": ("Angle | Length", "Hinge/slider only; initial coordinate in range"),
    }
    for name, (typ, description) in readonly.items():
        items.append(_entry("member", name, name + ": " + typ, description,
                            domains=["Read-only source value; current physical state requires run inspection"],
                            rules=["LANG-022"], value_type=typ, writable=False))

    for mode, meaning in {
        "static": "Fixed world placement; no action channel claims or nonzero initial velocities.",
        "prescribed": "Externally imposed motion by root actions or one incoming relation; no dynamic load solution.",
        "dynamic": "Contact-free homogeneous sphere with uniform gravity; pose resolved in world.",
        "disabled": "Collision response is absent; this is the only CollisionMode value.",
        "world": "Shared right-handed inertial FrameRef with +Y up and one world clock.",
    }.items():
        items.append(_entry("constant", mode, mode, meaning, examples=[mode], rules=["LANG-006", "LANG-011", "LANG-015"]))

    items.append(_entry("relation", "site", "site { pose: Pose; interface: String; size: Length; }",
                        "Owned fixed attachment frame; not a physical contact patch.", capability="sites",
                        domains=["All three fields required exactly once", "pose references self.frame", "Nonempty interface; nonnegative size"],
                        examples=['public site tip @ "tip" { pose = pose(self.frame,vec3(0[m],1[m],0[m]),quat(1,0,0,0)); interface = "rigid.origin"; size = 0[m]; }'],
                        rules=["LANG-012"]))
    items.append(_entry("relation", "follow", "follow { parent: FrameRef; child: Ref<Object>; offset: Pose; }",
                        "One-way massless spatial following; no ownership or force transfer.", capability="follow",
                        domains=["Child prescribed with no_body()", "Offset references exact parent frame", "One incoming pose authority; acyclic dependencies"],
                        effects=["derive child world pose once from parent and constant offset"], rules=["LANG-012", "LANG-014"],
                        examples=[_FIXTURES + "04-ownership-reuse-and-follow.ok"]))
    for kind in ("fixed", "hinge", "slider", "grip"):
        coordinate = "Angle" if kind == "hinge" else "Length"
        signature = "parent: SiteRef; child: SiteRef;"
        domains = ["Distinct endpoint objects; equal interface and canonical size", "Parent static/prescribed; child prescribed", "Acyclic single incoming pose authority", "Externally prescribed; no reaction load or motor solution"]
        if kind in ("hinge", "slider"):
            signature += f" axis: Vec3<Real>; limits: Range<{coordinate}>; initial: {coordinate};"
            domains += ["Axis norm within 1e-12 of one", "Closed ordered range contains initial coordinate"]
        if kind == "grip":
            domains += ["Child has sphere_body and no other joint", "Initially active; live capture unavailable", "May have outgoing massless followers"]
        items.append(_entry("joint", kind, "joint " + kind + " { " + signature + " }",
                            "Prescribed site alignment; child-site offset is included.", capability="fixed_hinge_slider_grip",
                            domains=domains, effects=["derive the child's rigid transform; no extra ownership transform"],
                            examples=[_FIXTURES + ("02-gravity-and-release.ok" if kind == "grip" else "01-independent-parts.ok")],
                            rules=["LANG-013", "LANG-014"]))

    for name, requirement, effect in [
        ("start", "Named action pending; admissible mode/frame/limits and free channel", "Claim its channel and begin local progression"),
        ("pause", "Named action running", "Hold local progression and retain the channel; world time continues"),
        ("resume", "Named action paused", "Continue local progression on the retained channel"),
        ("stop", "Named action running or paused", "Hold current prescribed value and release its channel"),
        ("release", "Named grip active with complete finite incoming state", "Remove precisely that grip and transfer incoming world pose/COM velocity/omega to a free dynamic sphere"),
    ]:
        syntax = "release grip_path using incoming;" if name == "release" else name + " action_name;"
        items.append(_entry("event", name, syntax, "Ordered event inside an exact-time sequence block.",
                            capability="ordered_events", domains=[requirement, "Scene time within the authored horizon"],
                            effects=[effect], examples=[syntax], rules=["LANG-017", "LANG-019", "LANG-020"]))

    for name, typ, domain, example in [
        ("duration", "Time", "Required once; strictly positive finite horizon", "duration = 2[s];"),
        ("gravity", "Vector3<Acceleration>", "Required once; explicit constant vector in world axes; no assumed magnitude", "gravity = vector(world,0[m/s^2],-9.81[m/s^2],0[m/s^2]);"),
    ]:
        items.append(_entry("member", "Scene." + name, f"Scene.{name}: {typ}", domain,
                            capability="uniform_gravity", domains=[domain], defaults={"required": True},
                            examples=[example], rules=["LANG-015", "LANG-020"], value_type=typ))

    supported = {
        "classes": "Nominal single inheritance, parameters/derived values, explicit keys and finite composition.",
        "pure_functions_and_methods": "Typed positional calls, immutable lets, return, assertions and exact-signature overrides; no mutation/I/O or recursion.",
        "typed_quantities": "Checked length/mass/time/angle dimensions and explicit frame tags.",
        "independent_parts": "Separate occurrences and ownership; no implicit ownership transform or duplicate matter.",
        "primitive_geometry": "Empty, sphere and centered full-size box descriptions and bounded display meshes.",
        "appearance": "Linear RGBA and the disclosed simple GLB material; no texture/deformation contract.",
        "sites": "Fixed local sites with explicit ideal interface/size compatibility.",
        "follow": "One-way massless rigid following.",
        "fixed_hinge_slider_grip": "Prescribed acyclic joints and initialization grip.",
        "move_spin_tween": "Independent root translation/orientation and joint-coordinate action descriptions.",
        "ordered_events": "Exact event times, explicit sequence order, lifecycle and incoming-state release.",
        "sphere_body": "Explicit positive-mass homogeneous sphere, isotropic derived inertia and no contacts.",
        "uniform_gravity": "Constant authored world gravity on participating free dynamic spheres.",
        "persistent_agent_editing_service": "Local SQLite candidate acceptance, request/run identity, bounded inspection and retained outcomes.",
    }
    for name, description in supported.items():
        items.append(_entry("capability", name, name, description, capability=name,
                            rules=["LANG-025"] if name == "persistent_agent_editing_service" else [],
                            effects=["profile feature; discover/validate the actual source before claiming success"]))
    unsupported = {
        "contact_and_collision_response": "Every core collision pair is disabled.",
        "dynamic_articulated_joints": "Prescribed joints do not calculate dynamic load transmission.",
        "closed_mechanical_loops": "Acyclic single incoming pose dependencies only.",
        "general_rigid_body_dynamics": "Only the disclosed homogeneous free-sphere model.",
        "external_forces_and_actuators": "No force/torque integration, motors, impulses, wind or controllers.",
        "live_capture_or_multiple_grips": "Only one initially active ideal grip and its release.",
        "relative_frame_velocity": "Axes may change; measurement remains world, without subtracting frame motion.",
        "skinning_and_deformation": "Rigid primitive geometry only.",
        "textures_and_regional_materials": "Simple linear RGBA appearance only.",
        "modules_packages_and_procedural_generators": "One source module and finite authored occurrences; no imports or general loops.",
        "general_external_delivery": "Only the named ontokin.glb/0.1 baked asset contract.",
        "live_destination_physics": "GLB stores sampled poses; it does not run OntoKin physics.",
        "distributed_or_multi_tenant_service": "One host's local store; no remote authentication/authorization or consensus service.",
        "agent_benefit_certification": "No measured LLM-versus-direct-tool authoring benchmark is implied.",
    }
    for name, description in unsupported.items():
        items.append(_entry("capability", name, name, description, capability=name, available=False,
                            effects=["unsupported request is explicit; never substitute a lower-stage success"]))
    items.append(_entry("destination", "ontokin.glb/0.1", "destination: ontokin.glb/0.1",
                        "Self-contained glTF 2.0 binary with primitive meshes and baked world motion.",
                        capability="ontokin.glb/0.1", domains=["Full authored timeline preflight", "Finite sampled float32 checks; no continuous-time proof", "Declared geometry/motion/metadata losses"],
                        defaults={"fps": 60, "position_tolerance_m": 0.001, "rotation_tolerance_rad": 0.001,
                                  "time_tolerance_s": 0.000001, "helpers": True},
                        effects=["produce revision-bound GLB and conversion report; preserve editable source"],
                        examples=["examples/visual/01-independent-parts.ok", "examples/visual/02-gravity-and-release.ok"],
                        available_levels=["delivered"], specification="docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md"))

    result = {
        "schema_version": "ontokin.agent-catalog/0.1", "profile": "core-0.1", "language_version": "0.1",
        "agent_contract": "ontokin.agent/0.1", "items": items,
        "supported_output_levels": list(_LEVELS), "delivery_targets": ["ontokin.glb/0.1"],
        "capability_labels": "Discovery filter labels, not supplied extensions for source requires declarations; nonempty requires still yields unsupported construction.",
        "unavailable_capabilities": sorted(unsupported),
        "example_context": "Expressions/declarations are syntax snippets requiring their stated surrounding bindings; fixture paths identify complete source. Discovery does not execute examples.",
        "complete_examples": [_FIXTURES + name for name in (
            "01-independent-parts.ok", "02-gravity-and-release.ok", "03-rotating-release.ok", "04-ownership-reuse-and-follow.ok")],
        "units": {"base": ["m", "kg", "s", "rad"], "scaled": {"cm": "1/100 m", "mm": "1/1000 m", "g": "1/1000 kg", "ms": "1/1000 s", "deg": "Pi64/180 rad"},
                  "derived": {"N": "kg*m/s^2"}, "Pi64": "3.141592653589793", "no_implicit_fps_unit": True},
        "numeric_limitations": ["General correctly rounded transcendental functions are not certified.",
                                "Exact represented rotations are approximated by binary64 spatial calculations.",
                                "Whole-interval range proofs for arbitrary rotating chains remain future work."],
        "limits": {"max_objects": 1000, "max_operations": 100000, "max_result_items": 1000, "max_elapsed_ms": 30000,
                   "max_source_bytes": 2 * 1024 * 1024, "max_request_bytes": 4 * 1024 * 1024, "max_artifact_chunk_bytes": 65536},
        "full_product_conformance_certified": False,
    }
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    result["revision"] = "sha256:" + hashlib.sha256(encoded).hexdigest()
    return result


_CATALOG = _build()


def catalog() -> dict:
    """Return fresh JSON-compatible metadata with a content-pinned revision."""
    return copy.deepcopy(_CATALOG)
