---
project: OntoKin
document_id: OK-LANG-001
title: "OntoKin Core Language Specification"
version: 0.1
date: 2026-10-17
status: language-specification
review_state: adopted-core-engineering-baseline
engineering_baseline: 2026-10-17
document_type: core-language-specification
repository: https://github.com/Omegapy/OntoKin
repository_snapshot: ded52f778418795c6dd523b32cd8470e188d5171
related_documents: [OK-CAP-001 v0.1, OK-PRD-001 v0.2, OK-SEM-001 v0.1, OK-001, OK-002, OK-003]
primary_operator: AI authoring agents
implementation_status: experimental-reference-prototype
---

# OntoKin Core Language Specification

| Document control | Value |
| --- | --- |
| Identifier | OK-LANG-001, language version 0.1; engineering baseline October 17, 2026 |
| Status | Adopted `core-0.1` engineering baseline; implementation support is measured separately |
| Purpose | Define source programs whose objects, relationships, validity, and behavior can be determined and checked against an implementation. |
| Language profile | `core-0.1`, a deliberately limited semantic contract |
| Initial demonstrations | Nested parts with independent prescribed motion; a carried sphere released into uniform gravity. |
| Authority | The owner's October 17 prototype task authorizes finalizing the twelve core decisions and implementing this bounded baseline. Broader PRD, CAP, SEM, and founding proposals retain their recorded status. |
| Implementation boundary | Python and its standard library are selected for the experimental headless reference prototype in OK-ENG-001. Production compiler, storage, physics-engine, controller, and renderer choices remain open. |
| Companion artifacts | [Complete grammar](core-v0.1/ontokin-core.ebnf), [source fixtures and validation cases](core-v0.1/validation-cases.json), [diagnostic schema](core-v0.1/diagnostic.schema.json), [requirement coverage](core-v0.1/requirement-coverage.json) |

## 1. Purpose, authority, and reading order

OntoKin is an object-oriented language for agents to describe reusable 3D objects, their parts, appearance, physical properties, mechanical relationships, and motion. The [capability definition](../product/OK-CAP-001-modeling-motion-and-object-structure.md) establishes the present modeling focus. The [PRD](../product/OK-PRD-001-product-requirements.md) records the broader product requirements. The [semantic model](OK-SEM-001-core-object-motion-and-physics-semantics.md) proposes what the concepts mean. This document defines one precise way to express a small, useful subset.

**A valid core program has a specified meaning; an implementation must establish which parts of that meaning it has demonstrated.** MUST, MUST NOT, and rejection conditions are normative within the adopted `core-0.1` engineering baseline. [Section 16](#16-engineering-baseline-adoption-and-clarifications) records the adoption and its clarifications. The [engineering plan and evidence](../engineering/OK-ENG-001-core-reference-implementation-and-conformance-plan.md) identify the experimental implementation's measured support. This adoption does not retrospectively approve all PRD or SEM proposals.

The source grammar and this document jointly define `core-0.1`. Grammar determines whether text is syntactically well formed. The type, relationship, and state rules determine whether a well-formed program is valid. The behavior equations determine the intended state over time. A discovered disagreement between grammar, examples, and prose is a specification defect; a tool must report it rather than choose its preferred interpretation silently.

| Reader's task | Relevant sections |
| --- | --- |
| Review the semantic foundation and decisions | 2 and 3 |
| Write valid source | 4 through 7 and the complete grammar |
| Predict motion, release, and timing | 8 through 10 |
| Create, inspect, or repair through an agent | 11 |
| Study complete programs and invalid cases | 12 and 13 |
| Review remaining work and source evidence | 14 and 15 |
| Identify the adopted engineering baseline and changes from the original draft | 16 and OK-ENG-001 |

The earlier `entity`, `position(t)`, indentation-based, and `sin(t)` examples in OK-001 through OK-003 remain historical sketches. They did not define a grammar or unit contract. They are not valid `core-0.1` programs unless rewritten under this specification. The founding architecture options remain available for later engineering decisions.

## 2. Focused review of the semantic foundation

### 2.1 Review result

All SEM-01 through SEM-28 and all SC-01 through SC-24 were reviewed against the product and capability documents. No direct contradiction was found that requires discarding a semantic rule. The main gap is that several rules delegate details to a future "supported contract." This specification either supplies that contract for `core-0.1` or explicitly leaves the broader case outside it.

The distinction between composition, spatial following, and physical connection is essential. An owner organizes the lifetime of its parts. A following relation calculates one frame from another. A mechanical relationship constrains permitted relative motion under a stated physical interpretation. These meanings cannot be substituted for one another.

The dispositions below apply to this core specification only. **Retain** carries the meaning into the core. **Clarify** supplies a previously open rule. **Limit** preserves the general meaning while defining only a restricted case. None of these labels means a product requirement has passed implementation testing.

| Semantic rule | Disposition | Decision in this core |
| --- | --- | --- |
| SEM-01 | Clarify | Explicit declaration keys, independently expanded instances, value/reference distinctions, and revision-pinned definitions; source cloning creates new occurrence keys. |
| SEM-02 | Clarify | Single nominal inheritance; exact method override signatures; pure dispatch; no multiple inheritance or runtime part replacement. |
| SEM-03 | Clarify | Instance override, most-specific class default, inherited default, then profile fallback; derived properties form an acyclic graph. |
| SEM-04 | Retain | Finite acyclic composition, one lifecycle owner, dependency-checked removal, and no runtime ownership transfer. |
| SEM-05 | Clarify | Separate composition, `follow`, site frames, and named joints; one incoming prescribed pose relation; closed mechanical loops deferred. |
| SEM-06 | Limit | Geometry and physical matter are separately declared and traceable; skinning and many-to-many deformation mappings remain future work. |
| SEM-07 | Clarify | Right-handed world, +Y up, explicit frame tags, center-of-mass velocity, radians, and checked quantities. |
| SEM-08 | Clarify | Exact rigid-transform composition for `follow` and prescribed joint coordinates; no transform scale. |
| SEM-09 | Clarify | Free dynamic state is world-resolved; ownership adds no transform; local inspection is a conversion of that state. |
| SEM-10 | Limit | Root translation and orientation are separate channels; independent joint coordinates; unit conversion preserves size; runtime resizing and world-target tracking deferred. |
| SEM-11 | Limit | Prescribed fixed, hinge, slider, and grip relationships; endpoints and allowed motion are exact; dynamic load-bearing joints and loops deferred. |
| SEM-12 | Limit | Hard parameter/joint bounds are enforced; goals cannot relax them; motors, soft preferences, and search-based goals deferred. |
| SEM-13 | Limit | Every core collision pair is disabled and disclosed; a grip is an explicit ideal attachment, with no finger/friction claim. Contact response is deferred. |
| SEM-14 | Clarify | Static, prescribed, and passive dynamic modes are distinct; only a uniform sphere has the core dynamic contract. |
| SEM-15 | Clarify | Own matter and owned aggregate mass are separate; sphere mass is counted once; connected loads do not change ownership. |
| SEM-16 | Limit | One explicit uniform gravity field and explicit appearance/mass separation; general forces, torque, wind, impulses, and material response are deferred. |
| SEM-17 | Clarify | Immutable action descriptions, named instances, exact target channels, finite timing, and lifecycle outcomes. |
| SEM-18 | Clarify | Exclusive channel claims; disjoint actions coexist; overlap is rejected; no implicit override, priority, or blending. |
| SEM-19 | Limit | Prescribed motion is labeled as externally imposed; passive dynamics follows its equations; bounded physical controllers are deferred. |
| SEM-20 | Limit | Grip construction is an initialization relation that derives alignment; capture of moving bodies during a run is deferred. |
| SEM-21 | Clarify | `release ... using incoming` transfers the full one-sided world state and removes precisely the named grip. Already-dynamic and multiple-grip cases remain deferred. |
| SEM-22 | Limit | Prescribed-grip to free-sphere transition is defined; other live mode changes, teleportation, resizing, and representation switches are deferred. |
| SEM-23 | Clarify | Definition, derived initialization, current state, and sampled output remain separate; reset starts a new run from the accepted revision. |
| SEM-24 | Clarify | Action pause holds its local progression and channel; world time and unrelated dynamic bodies continue. |
| SEM-25 | Clarify | Pre-boundary snapshot, natural completions, and explicit ordered event transaction; before/after sampling; no generated zero-time event chains. |
| SEM-26 | Clarify | Revision/run-consistent bounded inspection, effective-value origins, pose authority, and physical assumptions are required. |
| SEM-27 | Clarify | Separate invalid, unsupported, conflict, failed evaluation, stale result, and success-at-a-requested-level outcomes. |
| SEM-28 | Retain | Future profiles preserve identity, relationships, units, authority, and honest state transfer; product breadth remains in the PRD. |

### 2.2 Material decisions and remaining approval scope

The following choices were proposed in the original language draft. They are now adopted for the bounded `core-0.1` engineering baseline under the owner's prototype instruction, as recorded in section 16. A later semantic change requires an explicit specification revision. The earlier SEM draft did not already settle them.

| Decision | Chosen rule and reason |
| --- | --- |
| D-01: Language form | A small declarative language with explicit braces, semicolons, types, and stable keys. An agent can make localized edits and a reader can see declaration boundaries. |
| D-02: Object orientation | Single inheritance with nominal types and exact override signatures. This provides actual specialization without an unresolved method-resolution order. |
| D-03: Effects | Construction and pure methods are separated from timeline effects. Ordinary expressions cannot mutate a running scene. |
| D-04: Numeric meaning | Checked binary64 scalar arithmetic, explicit integer rules, dimensioned quantities, and an angle tag. Continuous behavior has mathematical equations and stated comparison tolerances. |
| D-05: Frames | A right-handed inertial world with +Y up; poses contain a named reference frame; physical vectors carry frame information. |
| D-06: Control | Exclusive claims on root translation, root orientation, or a particular joint coordinate. A conflict must be repaired explicitly. |
| D-07: Mechanical subset | Prescribed joints define allowed motion without claiming a load solution. Free dynamic motion is limited to an isotropic uniform sphere. |
| D-08: Release | An explicit incoming-state handoff includes all ancestor/local motion and the rotational offset contribution. The released sphere acquires one dynamic authority. |
| D-09: Events | One ordered `sequence` per timestamp. Natural completions precede it; release explicitly refers to the saved incoming state. |
| D-10: Program size | One finite module and one scene; no imports, loops, recursion, runtime allocation, or extension execution in this profile. |
| D-11: Agent editing | The accepted source revision is authoritative; structured edits are atomic and revision-checked; retries with the same identity cannot duplicate a change. |
| D-12: Scope reporting | A language-design profile is separate from an implementation's measured support. No constructed, simulated, rendered, or delivered result is claimed by this document. |

Questions requiring later design include contact selection and tolerances, arbitrary rigid-body dynamics, physical joints and actuators, deformation, broader modules and generators, controller contracts, and delivery mappings. They do not leave the four core fixtures without a meaning.

## 3. Minimum language scope

### 3.1 Included and deferred capabilities

| Area | Specified in `core-0.1` | Outside this profile |
| --- | --- | --- |
| Definitions | Classes, subclasses, typed parameters, derived properties, pure functions/methods, assertions, explicit public/private members | Multiple inheritance, interfaces, user generics, mutable user state, runtime class edits |
| Composition | Finite nested parts, separate instances, scoped parameter overrides, stable occurrence keys | Runtime allocation/removal/reparenting, automatic part replacement, procedural loops |
| Mathematics | Integer/scalar arithmetic, quantities, Boolean conditions, triples, framed vectors/points, rotations, rigid poses, ranges, references | User collections/records/enumerations, matrices as author values, arbitrary algorithms |
| Visible shape | Empty geometry, centered sphere, centered box, RGBA appearance | Mesh import, constructive solid geometry, skinning, textures, lights, cameras, rendering |
| Relationships | Named sites, separate spatial following, prescribed fixed/hinge/slider joints, an initial ideal grip | Dynamic constraint solutions, closed mechanisms, multi-grip support, capture during motion |
| Motion | World translation, world-axis spin, linear joint tween, start/pause/resume/stop, independent channels | Blending, priority overrides, inverse kinematics, walking/balance controllers, tracking |
| Physics | Own and aggregate mass, uniform sphere inertia, constant uniform gravity, contact-free free flight, release continuity | Contact/collisions, general torque/force/impulse actuation, non-spherical dynamic inertia, drag, wind, deformable matter, fluids |
| Time | One scene clock, finite event sequence, exact event ordering, reset, before/after sampling | Sensor events, source event handlers, wall-clock-driven behavior, arbitrary interactive event injection |
| Agents | Discovery, bounded inspection, revision-checked edits, diagnostics, validation-stage and retry contracts | A concrete transport/server, implementation jobs, GUI previews, external delivery |

This is a first language-specification scope, not a definition of the final product release. For example, a collision-free sphere is adequate for testing release continuity but is not evidence of the PRD's contact, creature, vehicle, or game-delivery capabilities. The [coverage register](core-v0.1/requirement-coverage.json) accounts for all 226 PRD requirements and all 18 capability requirements without marking them implemented.

### 3.2 Profile and output levels

A program declares `profile "core-0.1";`. This identifies the semantic rules used to interpret it. An implementation must separately publish which of those rules it supports and the evidence for that claim.

A `requires "capability-name";` declaration requests additional support. It has no hidden effect or plugin loading behavior. The core recognizes capability requests as data but provides no extension payload grammar. Such requests are disclosed but do not block `represented` acceptance of otherwise valid source. Every request becomes an obligation at `constructed` and above; unavailable support produces an unsupported result at that requested level. This deliberately conservative rule avoids guessing which later stage a capability affects. Unknown class members or misspelled built-ins remain invalid source; they are not silently treated as extensions.

Output levels retain the PRD's distinction:

| Level | Claim permitted after actual evidence |
| --- | --- |
| `represented` | Source is well formed and satisfies the applicable structural/type rules; unresolved support requests are disclosed. |
| `constructed` | Required geometry and physical descriptions for the revision have been produced and checked. |
| `evaluated` | A requested time interval has valid behavior under the declared semantic and numerical contract. |
| `delivered` | The specified external artifact has been checked against its destination contract. |

This specification provides expected results and structural contracts. Actual achieved levels are reported by the experimental implementation and its separate engineering evidence. The original grammar checks recorded in section 13 remain editorial evidence; they do not by themselves establish `represented` acceptance.

## 4. Source text and complete grammar

### 4.1 Lexical rules — LANG-001

Source is UTF-8 without a byte-order mark. Insignificant whitespace consists only of space U+0020, tab U+0009, LF U+000A, and CR U+000D. LF and CRLF line endings have the same meaning; source spans count the original UTF-8 bytes. Comments are `//` up to CR, LF, or end of source, or non-nesting `/* ... */` blocks that end at the first `*/`. Unterminated strings/comments are errors. Comments inside strings are ordinary text.

The complete syntactic grammar is [ontokin-core.ebnf](core-v0.1/ontokin-core.ebnf). In this Extended Backus-Naur Form (EBNF), quoted strings are terminals, commas mean concatenation, `|` means an alternative, `[...]` means zero or one, and `{...}` means zero or more. The following lexical terminals complete that grammar:

| Terminal | Exact form |
| --- | --- |
| `IDENT` | `[A-Za-z_][A-Za-z0-9_]*`, excluding the reserved words below |
| `INTEGER` | `0` or `[1-9][0-9]*`; used in unit exponents |
| `NUMBER` | `(0\|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?`, where the backslash before the vertical bar in this table is Markdown escaping only |
| `STRING` | Double quotes enclosing Unicode scalar values except raw control characters, quote, and backslash; escapes are `\"`, `\\`, `\n`, `\r`, `\t`. Other escapes, including `\u`, are invalid in 0.1. |

A leading minus is a unary operator, not part of `NUMBER`; unary plus is absent. Raw string control characters are U+0000–U+001F and U+007F–U+009F. An escaped newline, carriage return, or tab is permitted as string data. A leading decimal point, numeric digit separators, hexadecimal source literals, and leading zeroes such as `01` are invalid. Longest-token matching applies. A keyword must end at an identifier boundary; `className` is one identifier. `->`, `<=`, `>=`, `==`, and `!=` are indivisible tokens.

Reserved words are:

`ontokin module profile requires class extends public private param derive override method fn let return part site joint follow scene object action at sequence start pause resume stop release using incoming assert if then else and or not true false Quantity`.

Core type names, function names, `self`, `world`, `static`, `prescribed`, `dynamic`, and `disabled` are predefined symbols, not additional grammar keywords. A user declaration may not shadow a predefined symbol in its lookup scope. Units have their own namespace.

### 4.2 Program form — LANG-002

A program has exactly this order:

1. `ontokin "0.1";`
2. One named module with a stable key.
3. `profile "core-0.1";`
4. Zero or more capability requests.
5. Zero or more class/function definitions.
6. Exactly one scene.

There are no imports or implicit source concatenation. Identical module names in two independent source bundles do not link those bundles. Versioned package linking is future work.

Every declaration marked `identity` in the grammar supplies `@ "key"`. Keys match `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`. A display identifier and a key serve different purposes: changing the spelling `head` does not require changing its key `"head"`.

Assignments and assertions require semicolons. Declaration blocks do not take a trailing semicolon. Calls use positional arguments only. Field access and calls bind tighter than unary operators; arithmetic binds tighter than comparison, equality, `and`, `or`, and the conditional expression. Arithmetic operators associate left to right. Chained comparisons such as `a < b < c` are invalid. `if c then x else y` evaluates exactly one branch.

The grammar accepts some broadly shaped forms whose meaning is then checked. Class `joint` and `follow` declarations require explicit `public` or `private` visibility; scene relations prohibit a visibility modifier. The following assignment allowlist is exhaustive. A disallowed target is `OKL-E-NAME`, or `OKL-E-READONLY` when it names an existing read-only field. These assignments describe a revision; none mutates a running scene.

| Assignment context | Permitted left-hand sides |
| --- | --- |
| Scene body | Bare `duration` and `gravity` only, exactly once each |
| Class body | Bare writable built-in instance fields from section 7.1; inherited explicit defaults require `override`; inherited parameter defaults change only through the section 6.2 override form |
| Object or part initializer | Its direct public parameters and writable built-in fields; nested public part paths ending in a public parameter under section 6.2 |
| Site block | Bare `pose`, `interface`, and `size`, exactly once each |
| Follow block | Bare `parent`, `child`, and `offset`, exactly once each |
| Joint block | The exact bare fields for its kind in section 7.3, exactly once each |

Grammatical acceptance is never sufficient. For example, an omitted class-relation visibility or an extra relation field is a binding error, even when the broad production can parse it.

## 5. Types, units, and mathematical values

### 5.1 Value categories — LANG-003

| Type | Meaning and copying |
| --- | --- |
| `Int` | Signed 64-bit integer; value copy |
| `Real`, `Bool`, `String` | Finite scalar, Boolean, Unicode text; value copy |
| `Quantity[unit]` and named aliases | A scalar with a normalized dimension and angle tag; value copy |
| `Vec3<Q>` | Three values of the same scalar/quantity type; an unframed tuple, useful for dimensions or coordinates supplied to an explicitly framed operation |
| `Vector3<Q>` | A triple plus an expressed-in frame identity; displacement, velocity, gravity, or angular velocity has the meaning declared by its operation |
| `Point3` | A position with length coordinates and a frame identity |
| `Rotation` | A proper rigid orientation value; its reference is established when used in a pose |
| `Pose` | A named reference frame, a length triple, and a rotation mapping an object's local axes into that reference |
| `Range<Q>` | Ordered closed lower and upper bounds of the same quantity type |
| `Color`, `Geometry`, `BodyModel`, `MotionMode`, `CollisionMode` | Immutable core descriptions; not interchangeable with strings |
| `Ref<C>` | A non-owning reference to an instance of nominal class C or its subclass |
| `FrameRef`, `SiteRef`, `JointRef` | References to an identified frame, attachment site, or joint |
| `Action` | An immutable action description that captures typed arguments and target references; it does not start behavior by being evaluated |

A bare class name in a parameter/return type is shorthand for `Ref<ClassName>`. User-defined value records, collections, generic classes, and nullable references are not in the core. Copying a reference identifies the same object. Constructing another `object` or `part` occurrence creates independent state; copying a `Vec3` or `Pose` does not create an object.

The grammar permits type parameters, but only `Vec3<Q>`, `Vector3<Q>`, `Range<Q>`, and `Ref<C>` are defined. Wrong arity or unsupported type constructors are errors. Quantity annotations have the additional form `Quantity[unit_expr]`. Numeric/quantity compatibility is defined by the normalized dimension, not the spelling of an alias.

### 5.2 Numeric rules — LANG-004

`Real` and quantity magnitudes use binary64 values: 53 bits of significand precision; normal exponents from -1022 through 1023; subnormal values down to 2^-1074; maximum finite magnitude (2 - 2^-52) × 2^1023. These are scalar representation choices, not a hardware or compiler selection. The standard binary64 format is described in [T3].

Decimal conversion and each scalar arithmetic operation round to nearest, with ties to even. Evaluation follows the written expression tree. Reassociation and a fused operation that changes the result are not permitted. Positive and negative zero compare equal and serialize as positive zero.

An unannotated token without a decimal point or exponent is `Int`; otherwise it is `Real`. An immediately negated integer literal is range-checked with its sign, allowing -9223372036854775808. Other integer overflow is an error. `+`, `-`, and `*` on two integers return `Int`. Int/Int `/` forms the exact rational quotient and rounds once to `Real`, without first widening its operands. Integer division by zero is an error. The exact-widening rule below governs mixed-type operations and arguments.

An `Int` widens implicitly to `Real` only when it is exactly representable. A larger in-range integer requires explicit `real(value)`, which rounds under the rule above. A bare zero never widens to a dimensioned quantity. Write `0[m]` or `0[s]` where that dimension is required.

Division by zero, overflow to a non-finite result, invalid square root, or invalid mathematical domain returns `OKL-E-NUMERIC`. NaN and infinity are not authorable values and cannot propagate as successful state. Underflow to a finite subnormal or zero is permitted but reported as `OKL-W-UNDERFLOW`; positive-mass, radius, and duration conditions are checked afterward.

Scalar/quantity equality is exact equality of the stored canonical values. Ordering requires the same compatible type. There is no hidden tolerance in `==`, assertions, timestamp equality, or joint limits. `near(a,b,tolerance)` is an explicit scalar/quantity test with an authored nonnegative absolute tolerance.

Unless stated otherwise, a mathematical built-in evaluates its specified expression over the exact values of its canonical inputs, checks domains on that mathematical value, and rounds each exposed scalar result once under this section. Its internal host-language operation order is not normative. This includes axis/quaternion norms and the derived sphere inertia. Structured `Rotation` values have the proper-rotation interpretation in section 5.4.

The static `sqrt`, `sin`, and `cos` functions return the correctly rounded binary64 value of their mathematical result. `sin` and `cos` require `Angle` and interpret radians. `sin(1[s])` is invalid. `sqrt` accepts a nonnegative `Real` only in this core; a square root of a quantity needs a later overload.

### 5.3 Dimensions and conversions — LANG-005

Dimensions are exponent tuples for length L, mass M, time T, and a checked angle tag A. The angle tag prevents time, a scalar, and an angle from being confused in source. Geometric operations explicitly interpret the numeric radian value; generic multiplication does not erase the tag.

| Alias | Unit expression | Dimension |
| --- | --- | --- |
| `Length`, `Area`, `Volume` | `m`, `m^2`, `m^3` | L, L², L³ |
| `Mass`, `Time`, `Angle` | `kg`, `s`, `rad` | M, T, A |
| `Speed`, `Acceleration` | `m/s`, `m/s^2` | LT^-1, LT^-2 |
| `AngularSpeed` | `rad/s` | AT^-1 |
| `Force`, `Torque` | `N`, `N*m` | MLT^-2, ML²T^-2 |
| `Density`, `Inertia` | `kg/m^3`, `kg*m^2` | ML^-3, ML² |

Any normalized combination is expressible as `Quantity[unit_expr]`. A dimensionless result is `Real`. A units suffix makes a number a quantity even when its token would otherwise be `Int`. Unit exponents are integers from -16 through 16; normalized exponents outside that range are unsupported in this profile.

Supported unit symbols and factors relative to the table above are `m`, `cm = 1/100 m`, `mm = 1/1000 m`, `kg`, `g = 1/1000 kg`, `s`, `ms = 1/1000 s`, `rad`, `deg = Pi64/180 rad`, and `N = kg*m/s^2`. `Pi64` is the binary64 value 3.141592653589793. The decimal literal and unit factors are combined as an exact mathematical expression over those factors and rounded once to canonical binary64. There is no unit named `frame` or `fps`.

`*` and `/` add/subtract dimension exponents. `+` and `-` require equal dimensions. Therefore `1[m] / 2[s]` is `Speed`, whereas `1[m] + 1[kg]` is invalid. `Torque / Inertia` does not automatically acquire an angle tag; a future actuation operator must define that physical conversion explicitly.

Unit changes preserve the canonical quantity. A presentation request may express a length in centimeters, but it cannot resize geometry. No scaling operation is present in the pose type. A radius parameter edit re-elaborates the geometry and sphere inertia for the next accepted revision; it does not rescale a running body.

### 5.4 Frames and spatial operators — LANG-006

The world is a right-handed inertial frame, with +X to the right, +Y up, and +Z completing the right-handed basis. Gravity is explicitly authored; no terrestrial magnitude is assumed. An orientation follows the right-hand rule. The world has one shared time.

Each instance has an implicit `frame` and an implicit `origin` site. That frame's origin is also the center of mass for a `sphere_body`. A site adds a constant offset frame within its owning instance. Ownership alone does not determine either frame's pose.

`Vec3` is an unframed tuple. It must be placed in a stated frame through `vector`, `point`, or `pose` before it can serve as a spatial value. `Vector3` arithmetic requires the same frame identity as well as compatible dimensions. A point minus a point in the same frame is a `Vector3<Length>`; point plus/minus a length vector in that frame is a point. Adding two points is invalid.

Frame tags are refinements of these types. All source frame references in the core resolve at elaboration, so incompatible frames are diagnosed before evaluation. A frame conversion in inspection changes the coordinates and axes used to describe an already evaluated state. It does not introduce a following relation or move an object.

`Rotation` uses a unit quaternion in `(w,x,y,z)` order. `quat` requires a finite nonzero tuple whose Euclidean norm differs from one by at most 10^-12; it then normalizes. A tuple outside that tolerance is rejected rather than silently repaired. The canonical sign makes the first nonzero component positive. Equivalent `q` and `-q` are the same orientation. Quaternion construction is coordinate data, not four independently blendable pose channels.

`axis_angle(axis, angle)` requires a dimensionless axis whose norm differs from one by at most 10^-12, normalizes it, and uses the radian angle. A zero axis is invalid even for a zero angle. It defines q = (cos(θ/2), axis sin(θ/2)). No Euler-angle convention, reflection, shear, or transform scale is implicit.

Both constructors denote the exact normalized proper rotation obtained from those mathematical expressions and use the same canonical sign. Their source-readable quaternion components are individually rounded binary64 projections; four rounded components need not have an exactly unit norm. Copying a `Rotation` retains its represented orientation, not a reconstruction from those projections. Composition and physical differentiation use the represented rotation. A quaternion sign change affects coordinates only and cannot create a physical angular-velocity jump.

## 6. Classes, instances, names, and effects

### 6.1 Binding and stable identity — LANG-007

The module contains one namespace of class/function names. A scene contains one namespace of object, relation, and action names. An effective class contains one namespace of properties, parts, sites, relations, and methods. Names and declaration keys must each be unique within the relevant namespace, except for an explicit compatible override.

Class members use `self.member`. A method first resolves its parameters and earlier `let` bindings, then module/predefined symbols. A function has no `self`. A class cannot capture a scene object or a name from a caller's local scope. A scene expression can refer to any declared scene object, relation, or action, subject to dependency checks. Source declaration order does not resolve competing defaults or bindings.

A part initializer's right-hand expressions use the enclosing class occurrence's lexical scope: `self` names the owner containing that part declaration. A scene object's initializer uses scene scope and has no `self`. Its assignment left-hand paths target the occurrence being initialized. Thus `radius = self.radius;` in a part initializer passes its owner's parameter to the child; it does not read the child's value recursively.

Each instance's identity is the tuple of module key, scene key, and its object/part occurrence keys. For example, the first fixture's hand is `["independent-parts","demo","rig","arm","hand"]`. A site, joint, or property extends its owning tuple with its member key. An element kind is also included in every inspection record. Definition records use the separate namespace `["module-key","definitions","class-or-function-key",...]`; `definitions` is not a permitted scene key. Built-in elements use a reserved system namespace.

The lexical name is resolved to that identity in the accepted revision. Renaming a symbol must update its lexical uses atomically; leaving a stale spelling is a name error. Its key and resolved references remain the same after a valid rename. Merely keeping a stale textual reference is not a successful rename.

Two occurrences of the same class expand their own parts and relations, using their respective occurrence paths. Internal `self` references resolve inside the new occurrence. Immutable descriptions may be shared, but parameter overrides, action state, and dynamic state may not be shared accidentally. Source-level duplication requires a new root occurrence key. Relationships to external objects are recreated only by explicit source declarations.

Replacing an occurrence with a different concrete class requires a new occurrence key and explicit rebinding of affected references. A normal parameter edit or an identifier rename retains the key. This makes replacement different from editing the same instance. Live replacement, cloning during evaluation, and ownership transfer are outside the profile.

### 6.2 Inheritance and defaults — LANG-008

A class has zero or one base class. The inheritance graph is acyclic. Class references are nominal: a value of a subclass type can be used through its base type; a similar list of fields does not make unrelated classes compatible.

An inherited parameter's default can be changed with `override name = expression;`. The parameter keeps its type, visibility, and declaration key. An inherited derived property, part, site, or relation cannot be replaced in 0.1. A subclass can add new members with unused names and keys.

An overriding method must use `override method`, retain the original method name and key, and have exactly the same ordered parameter names/types, return type, visibility, and pure effect. Overloading, covariant override returns, default call arguments, `super` calls, and multiple dispatch are absent. A call resolves to the most specific override on the referenced instance. Ambiguity or an incompatible override is an error. Private members cannot be overridden or accessed outside their declaring class.

Effective parameter resolution is:

1. An explicit override in the particular occurrence's initializer, including a nested public parameter path.
2. The most specific class's explicit override/default.
3. Inherited class defaults.
4. A documented profile fallback, where the relevant built-in field defines one.

Repeated writes at the same level are errors even if the values happen to be equal. A class overriding an explicitly inherited built-in default such as `geometry` also uses `override geometry = ...;`. Instance initializers use ordinary assignments because their override scope is already explicit.

For a descendant parameter, an enclosing occurrence's explicit nested override takes precedence over assignments in reusable inner part initializers. Search explicit initializer scopes from the outermost occurrence toward the target's own part initializer, then apply its class defaults. For example, an outer `ball.radius = 0.3[m];` overrides a reused part initializer's `radius = 0.25[m];`. Duplicate assignments within one initializer remain invalid.

Derived properties do not compete in this precedence list. They are calculated from the resolved inputs and cannot be assigned in an instance initializer. Mandatory assertions and bounds apply after resolution and cannot be overwritten as defaults.

A nested initializer such as `ball.radius = 0.3[m];` changes that public parameter only. It cannot rewrite a private parameter, method, joint definition, or another occurrence's state. Each traversed part must be public. A direct initializer can set that instance's documented built-in fields. Nested paths are restricted to public parameters; they cannot alter another object's built-in motion or relationship fields indirectly.

### 6.3 Elaboration and initialization — LANG-009

Elaboration means resolving a source definition into typed object descriptions. It is a language stage, not a choice of compiler architecture.

The required order is:

1. Parse the complete source and bind names and keys.
2. Validate class inheritance, method signatures, allowed members, and types.
3. Expand finite object/part occurrences and bind their internal references.
4. Resolve parameters, derived properties, geometry/body descriptions, site offsets, and action arguments through their dependency graph.
5. Check static assertions and all required parameter domains.
6. Resolve ownership and incoming pose relationships; derive the initial world poses and physical state.
7. Validate the requested capability level and the timeline's action/transition conditions.

Pure dependencies may refer forward. The graph of derived values, action construction, and applicable function/method calls must be acyclic after specialization. Recursive calls, recursive part expansion, cyclic inheritance, and cyclic derivations are distinct errors. A resource budget can stop expansion with `resource_limit`; that result is not proof of a logically cyclic definition.

A class parameter default and a property's declared expression run once per elaborated revision/instance. A `let` in a pure call is evaluated in source order, and all positional arguments are evaluated left to right. Short-circuit Boolean operations and conditional branches do not evaluate the unused operand/branch. Their types must still be valid.

The accepted definition is immutable for an existing run. An accepted edit creates a new definition revision and invalidates derived products *as products of the new revision*. Old runs remain attributable to their original revision. They cannot be relabeled as evaluations of the edited source.

### 6.4 Pure methods, assertions, and side effects — LANG-010

Functions and methods contain zero or more typed immutable `let` bindings followed by exactly one `return`. Their result can be a value or an `Action` description. They cannot mutate parameters, create objects, change the clock, start actions, query current physical state, perform I/O, load code, or call an agent. A call such as `rig.look(...)` constructs a request; only `start look;` has a timeline effect.

A class assertion is evaluated for each instance after its static descriptions resolve. A scene assertion is evaluated after all scene descriptions resolve. Its condition must be Boolean and cannot read current time or simulation state. Failure produces the authored message plus source location and `OKL-E-ASSERT`. Source assertions therefore establish definition conditions; behavior outcomes are checked through the time-specific validation cases.

Public members expose the source contract. Private members restrict ordinary source access. Authorized diagnostic inspection can still report a private member's origin, resolved value, and dependency path; encapsulation must not hide why a valid or invalid result was produced.

## 7. Object descriptions, geometry, and relationships

### 7.1 Built-in instance fields — LANG-011

Every object supports the fields below. A class supplies defaults; an occurrence can override its own fields in its initializer. Unknown fields are errors. Fields such as `frame` and `origin` are read-only references, not assignable configuration.

| Field | Type | Profile fallback and conditions |
| --- | --- | --- |
| `role` | `String` | The occurrence key; separate from its display identifier |
| `geometry` | `Geometry` | `empty()` |
| `appearance` | `Color` | `rgba(0.5,0.5,0.5,1)` in linear RGB |
| `physical` | `BodyModel` | `no_body()`; contributes no matter |
| `motion` | `MotionMode` | `prescribed` |
| `collision` | `CollisionMode` | `disabled`; it is the only core value |
| `placement` | `Pose` | Identity in `world` only when no incoming pose relation exists |
| `velocity` | `Vector3<Speed>` | Zero, world-measured at the center of mass and expressed in world axes; initial free dynamic state only |
| `omega` | `Vector3<AngularSpeed>` | Zero, world-measured and world-expressed; initial free dynamic state only |

An authored `placement` must reference `world` and is permitted only without an incoming pose relation. Authored `velocity` and `omega`, including zero values, must be world-expressed; another frame returns `OKL-E-FRAME`. Explicit zero velocity/omega is allowed on a static or prescribed object as initialization data, with no motion effect. An explicit nonzero value on either mode is invalid. Nonzero prescribed velocity must come from an action, a moving relation, or both. An explicitly authored `placement` on a relation-controlled child is invalid even if it numerically matches the derived pose. An explicitly inherited class placement counts as authored; only the profile's unassigned fallback yields to relationship derivation.

A source expression may read `placement` only on an instance without an incoming pose relation. A relation-controlled child's initial world pose is derived during initialization and is available through inspection, not through that source field. Such a source read returns `OKL-E-POSE-AUTHORITY`; it cannot introduce an implicit following relation or an initialization-order dependency.

`sphere(radius)` creates a mathematical sphere centered on the object's frame. `box(size)` creates an axis-aligned box centered there, with the three positive *full* side lengths. `empty()` supplies no visible surface. These descriptions do not choose meshing, shading, or rendering algorithms.

Appearance is independent of physical matter. RGBA components must be finite and in [0,1]. Alpha changes appearance information only. `sphere_body(radius,mass)` declares a positive-radius, positive-mass, homogeneous solid sphere with its center at the object origin. Its physical shape can intentionally differ from visible geometry; inspection must disclose that proxy. A visible box with a sphere proxy has sphere physics, not the inertia or contact behavior of a solid box. No box-body model exists in this profile.

### 7.2 Sites and spatial following — LANG-012

A named site is a fixed attachment frame owned by an instance. It has exactly three required fields:

| Site field | Type and meaning |
| --- | --- |
| `pose` | Pose relative to the owning object's `self.frame` |
| `interface` | Nonempty compatibility identifier |
| `size` | Nonnegative length, compared in canonical units |

The implicit `origin` site has identity offset, interface `"rigid.origin"`, and size `0[m]`. A zero-size site is an ideal point connection, not a modeled contact patch. Site values cannot depend on time.

A `follow` relation has exactly `parent: FrameRef`, `child: Ref<C>`, and `offset: Pose`. The offset's reference must be the exact parent frame. The child must be prescribed and have `no_body()`. The relation does not transmit force, create ownership, or establish a mechanical joint. It may follow a dynamic parent's already resolved frame because its child is purely visual/logical.

Writing T_AB for a rigid transform that maps B coordinates into A coordinates, the relation means:

$$
T_{W C}(t)=T_{W P}(t)\,T_{P C}.
$$

Offset T_PC is constant in this core. Parent motion is composed once. A pose query in another frame merely calculates an equivalent representation. The rigid-transform convention follows the mathematical background in [T1]; the `follow` declaration is an OntoKin design choice.

### 7.3 Prescribed joints and initial grip — LANG-013

A joint identifies a `parent` and `child` of type `SiteRef`. Endpoint sites must belong to distinct instances, have equal `interface` strings, and equal canonical `size` values. Matching those two values establishes this core's ideal compatibility contract. It does not prove anatomical, manufacturing, or contact compatibility.

| Kind | Required fields beyond `parent` and `child` | Relative transform J(q) |
| --- | --- | --- |
| `fixed` | None | Identity |
| `hinge` | Unit `axis: Vec3<Real>`, `limits: Range<Angle>`, `initial: Angle` | Rotation by q about the parent site's axis |
| `slider` | Unit `axis: Vec3<Real>`, `limits: Range<Length>`, `initial: Length` | Translation by axis × q in parent-site axes |
| `grip` | None | Identity while active; releasable under section 8.3 |

For hinge/slider, the axis is normalized under the same 10^-12 unit-vector condition used for `axis_angle`. Limits are closed and ordered; initial q must lie inside them. A zero-width range is permitted and means no change is available. Extra or missing fields are errors.

Let P be the parent site, B the child instance frame, and C the child site fixed in B. Then:

$$
T_{W B}(t)=T_{W P}(t)\,J(q(t))\,T_{B C}^{-1}.
$$

This equation aligns the actual sites, including a nonzero child-site offset. It does not assume the child origin coincides with its attachment point. The joint controls the child frame; it does not also add the ownership parent's transform.

**These are prescribed connections.** Their parent must be static or prescribed; their child must be prescribed. They enforce the stated kinematic relation and limits. They do not calculate reaction loads, solve dynamic articulated motion, impose actuator torque limits, or establish frictional grip strength. Inspection reports `coupling: externally_prescribed_no_load_solution`. A request for dynamic load transmission requires another profile and cannot be silently satisfied by these relations.

A `grip` additionally requires a `sphere_body` on its child and no other joint involving that child. It can have outgoing massless `follow` dependents. The grip begins active at initialization. It derives the child's initial pose before world-time evolution begins; it is not a capture impulse or a teleport during a run. Acquiring a grip on an already moving object is deferred.

### 7.4 Relationship validation and mass accounting — LANG-014

Each instance has at most one incoming relation that determines its pose. An instance with no incoming relation uses its world placement and mode. The directed union of all active following and prescribed-joint pose dependencies must be acyclic. A cycle containing only follow edges returns `OKL-E-FOLLOW-CYCLE`. A cycle containing any joint, two incoming joints, or a multi-grip configuration returns `OKL-E-CAPABILITY-UNSUPPORTED` under this profile. Multiple incoming relations involving a follow, without a cycle or multiple-joint case, return `OKL-E-POSE-AUTHORITY`. These are pose dependencies, not ownership cycles or duplicate bodies.

Composition remains an independent acyclic graph. A part can be dynamically free while its organizational owner moves. Removing source declarations must leave no surviving unresolved references. No relation changes ownership; a scene-owned payload stays scene-owned while held and after release.

An instance's own mass is its `sphere_body` mass or zero. Owned aggregate mass is the sum of the own masses of the instance and its transitive owned descendants, with each occurrence counted once. Reference copies, sites, geometry, actions, and joints add no mass. An external grip is a connection, not an extra contribution to owned aggregate mass.

Sphere inertia about the center of mass is isotropic:

$$
I_C=\frac{2}{5}mr^2\,\mathbf{1}.
$$

The exposed scalar (2/5)mr² is rounded once under section 5.2 and must remain positive and finite; a zero result after underflow is `OKL-E-PHYSICAL-DOMAIN`. Mass is explicitly authored; this profile does not infer it from density. Aggregate inertia is not a scalar sum in this core; a query for it returns unsupported rather than a misleading number. Owned mass and the list of connected external loads are separately inspectable. Gravity acts once on each participating dynamic sphere.

## 8. Physical state and release

### 8.1 Modes and physical assumptions — LANG-015

| Mode | Pose/velocity authority | Gravity and reaction interpretation |
| --- | --- | --- |
| `static` | Constant world placement; no incoming relation or action channel | External anchoring; the core does not solve its support reaction |
| `prescribed` | Root actions or one incoming relation; idle channels hold their current coordinate | Motion is imposed externally; gravity does not alter it |
| `dynamic` | The free-sphere equations below | Uniform gravity changes linear momentum; no prescribed pose writer |

A dynamic instance must have `sphere_body` and no incoming follow/joint. It can still have an ownership parent. Geometry alone is insufficient to infer physical participation.

Each scene must author `duration: Time` and `gravity: Vector3<Acceleration>`. Duration is positive; gravity must be world-expressed, constant, and finite. There are no default ground planes, air resistance, contacts, collision detection, self-collision, external force, torque, or release impulses. `collision = disabled` means that overlap and crossing a visual surface cause no response. A run must disclose this assumption in its resolved profile.

A prescribed massive sphere records its matter, but gravity is inactive for its movement until it becomes dynamic. This is reported as `gravity_participation: inactive_prescribed`, not hidden physical enforcement. A user-requested collision or dynamic-joint capability is unsupported, even if a picture of the scene would appear convincing.

### 8.2 Free-sphere state — LANG-016

The physical state is world position p of the center of mass, proper orientation R, world-measured/world-expressed center-of-mass velocity v, and world angular velocity ω. The initial authored dynamic state or a successful release sets p₀, R₀, v₀, and ω₀ at time t₀.

For Δ = t - t₀ ≥ 0:

$$
p(t)=p_0+v_0\Delta+\frac{1}{2}g\Delta^2,\qquad
v(t)=v_0+g\Delta.
$$

The homogeneous sphere has isotropic inertia and no applied torque, so:

$$
\omega(t)=\omega_0,\qquad
R(t)=\operatorname{Rot}(\widehat{\omega_0},\|\omega_0\|\Delta)\,R_0.
$$

If ω₀ is zero, R(t)=R₀; no zero-vector normalization is attempted. The angle is the numeric radian angular speed integrated over seconds. The rotation increment multiplies on the left because ω is expressed in world axes.

These equations define the semantic trajectory. They do not specify an integrator. Constant angular velocity here relies on isotropic inertia; it is not a general promise for torque-free asymmetric bodies. General rigid-body rotation requires a separate contract.

For an initially dynamic object, the constants are the elaborated canonical source values and represented rotation. At release, the constants are the saved incoming semantic state. The transition introduces no additional rounding jump. Between events the equations define mathematical real-valued trajectories over those constants. Each implementation chooses its numeric machinery and must meet the comparison contract in section 13. Exact event order does not imply bit-identical floating-point results across implementations.

Every accepted evaluated interval must keep each exposed scalar state component within the finite binary64 magnitude range. A request crossing that range fails with `OKL-E-NUMERIC` and identifies the boundary of its valid interval; an out-of-range mathematical value cannot be serialized as infinity or certified as a valid core sample. This range condition is separate from the fixture comparison tolerances.

### 8.3 Release transaction — LANG-017

The only core release form is:

`release hold using incoming;`

`hold` identifies one active grip. `incoming` explicitly selects the one-sided physical state immediately before that timestamp's boundary processing. It is not a zero-velocity default. The required snapshot and ordering are defined in section 9.3.

The transition is atomic:

1. Validate that the named grip is active and the child's sphere representation remains valid.
2. Obtain the child's incoming world pose, center-of-mass velocity, and angular velocity from the *complete* carried motion.
3. Remove that grip's imposed pose relationship.
4. Change the child from prescribed to dynamic and initialize its free-sphere state from those values.
5. Recompute affected dependency/status records and expose the consistent after-state.

Identity, ownership, mass, and geometry do not change. Outgoing massless visual followers remain and follow the released sphere. Gravity remains the same scene field. No stale carry transform or ancestor velocity is added after the transition.

For a rigid offset from a moving support origin G to the sphere center C, the velocity contribution is:

$$
v_C=v_G+\omega_G\times(p_C-p_G).
$$

For a changing local offset there is also the rotated local derivative. For relative joint rotation there is also the corresponding angular contribution. The implementation must obtain these from the complete transform chain, not only the root action. The reference-point and moving-frame distinction is described in [T2]. In these physical equations, angular components are numeric radian rates.

A finite incoming derivative is required. A source/evaluation extension that supplies discontinuous placement with no finite left derivative cannot use this handoff; it must report `OKL-E-HANDOFF`. If a core action completes or pauses at the same time, `using incoming` explicitly selects its pre-boundary derivative. A position or velocity jump introduced by a different future transition would need its own contract.

Already-dynamic physical grips, multiple simultaneous grips, capture impulses, throws with additional impulses, and arbitrary mode switches are outside the core. Their preserved SEM requirements remain visible in the coverage tables.

## 9. Actions, control channels, and time

### 9.1 Built-in actions and authority — LANG-018

Action construction is pure. Admission happens at `start`, using the then-current state. Captured scalar values and references come from the accepted definition; the starting coordinate comes from the current state.

| Builder | Required types | Channel and mathematical meaning while running |
| --- | --- | --- |
| `move(object, velocity, duration)` | Free prescribed object; world `Vector3<Speed>`; positive `Time` | Root translation only: p = p_start + velocity × local_elapsed |
| `spin(object, omega, duration)` | Free prescribed object; world `Vector3<AngularSpeed>`; positive `Time` | Root orientation only: R = Rot(omega × local_elapsed) R_start |
| `tween(joint, target, duration)` | Prescribed hinge with `Angle` or slider with `Length`; positive `Time` | That joint coordinate only: q = q_start + (target - q_start) × local_elapsed / duration |

`local_elapsed` advances at one second per world second while running and holds while paused. Its final value is duration. An all-zero spin rate is valid and holds orientation without normalization. A tween target must lie within the closed mandatory range. Because interpolation is linear and its endpoints are inside the range, the complete coordinate path lies inside it.

A root target must have no incoming relation and be prescribed at admission. A move/spin cannot directly move a dynamic, static, or relation-controlled frame. A fixed joint or grip has no tweenable coordinate. Frame, type, mode, and limit errors are localized to the request and target.

The three-component root translation is one channel, the complete root orientation is a second, and each hinge/slider coordinate is one channel. Two move actions conflict even if their nonzero vector components differ. A move and spin on the same root can coexist. A root move and a head-joint tween can coexist because their resolved channels differ.

A running or paused action owns its channel exclusively. No priority, blending, additive overwrite, or "last declaration wins" policy is inferred. `stop old; start replacement;` in an explicitly ordered event block is the available replacement mechanism. Forces are not pose channels, although only gravity is defined in the dynamic subset.

### 9.2 Lifecycle and holding — LANG-019

| Current state | Event | Result |
| --- | --- | --- |
| `pending` | `start` | Capture current coordinate, claim channel, set local elapsed to zero, become `running` |
| `running` | `pause` | Capture current coordinate/elapsed; hold both progression and channel; become `paused` |
| `paused` | `resume` | Continue remaining local progression; become `running` |
| `running` or `paused` | `stop` | Latch current coordinate, release channel, become `stopped` |
| `running` | Natural endpoint | Latch exact endpoint, release channel, become `completed` |

Any other transition is `OKL-E-ACTION-STATE`. An instance cannot be restarted after completion or stopping; another named action instance can use the same immutable description. A paused action does not naturally complete while its clock is held.

A latched free prescribed channel holds its final value with zero outgoing derivative until another action claims it. A latched joint holds its local coordinate while its parent may still move. Stopping a root move therefore does not erase a head's local pose. Completing an unrelated carrier action cannot stop a sphere that has already been released.

There is no implicit jump to an initial/default pose on stop, resume, or replacement. `move` and `spin` preserve their cumulative progression through pauses. A tween resumes toward its originally captured target over the remaining duration. A new action captures the current coordinate when it starts.

Pausing an action does not pause world time, other actions, or gravity. Evaluation is independent of rendering or wall-clock cadence. Suspending world evaluation means no further world-time advancement; resuming it adds no elapsed wall-clock time. Reset creates a fresh run at t=0, `before`, from the accepted initialization and resets every action to pending. Evaluation processes any t=0 source transaction before advancing to its after-state.

### 9.3 Event ordering and boundary sampling — LANG-020

Event times and durations are nonnegative/positive `Time` values respectively. An `at` time must lie in [0, scene.duration]. The value is computed at elaboration. Times are ordered by their canonical values with no epsilon grouping. Two `at` blocks with equal time are invalid; the author must combine them into one explicit `sequence`.

The ordered statements inside `sequence` express an intentional order. Arrival timing, hash iteration, and the ordering of separate declarations do not decide behavior. The number of source events is finite; source handlers cannot generate more events.

For a boundary t:

1. Evaluate continuous motion to t from the preceding interval. Save `S(t,before)`, including finite incoming derivatives. At t=0 this is the initialized state, before any action starts.
2. Complete actions whose local elapsed reaches duration at t. Latch endpoints and release their claims.
3. Apply the one source `sequence` for t, if any, in its written order on a staged state.
4. Validate the full result, then expose `S(t,after)` and use its authority for the following interval.

All explicit statements at the timestamp form one transaction. If one fails, no explicit statement at that timestamp becomes accepted. Evaluation records the last valid incoming state and the failed boundary; it does not expose a half-applied sequence as valid. The natural completions can be reconstructed deterministically, but no after-state is certified for the failed boundary.

`release ... using incoming` reads the saved child's incoming state from step 1, even if its carrier naturally completes in step 2. This resolves the otherwise ambiguous derivative at a hold boundary. An earlier explicit statement in the same sequence must not change a channel, mode, or relation on that grip's incoming dependency chain; such a combination returns `OKL-E-EVENT-CONFLICT`. Put the release first when stopping/replacing its carrier in the same sequence. Independent releases can use the same incoming snapshot.

At a non-event sample, before and after are equal. At an event, callers must request `before` or `after`; `after` is the documented default when omitted. Inspection never advances time. Natural completion is also a boundary even without an authored `at` block.

Canonical source times are binary64 values interpreted exactly as rational numbers for event scheduling. Sums of elapsed intervals and natural endpoints use exact rational time in the semantic model; a numeric implementation must not reorder simultaneous events through accumulated clock error. Protocol time values use exact decimal strings for that rational timestamp. This specifies observable ordering, not a scheduler algorithm.

For example, source `0.1[s]` denotes exactly 0.1000000000000000055511151231257827021181583404541015625 seconds. Protocol `"0.1"` denotes exactly one tenth of a second, a different instant. Discovery/inspection must expose the exact canonical boundary timestamp; agents must reuse that value to address an authored event. A source sum rounded to binary64 can likewise differ from the exact sum used for a natural endpoint. The fixtures use exactly representable integer/half-second sample times.

A scene duration is an observation horizon. An action may still be running or paused at that horizon; its actual status must be reported. Successfully evaluating the requested interval is not a claim that every action completed. Sampling outside the accepted horizon is unavailable; extending it requires a new source revision and run.

## 10. Formal validity and the core built-in catalog

### 10.1 Typing and evaluation judgments — LANG-021

The following notation states the rules independently of any implementation:

- Γ is the environment of bound names, nominal types, frame identities, and declarations.
- Γ ⊢ e : τ means expression e has type τ and is pure.
- D ⇓ M means definition D elaborates to model M under sections 6 and 7.
- Admit(M,S,a) means action a may claim its channels in state S.
- Flow(M,S,Δ) gives the state after continuous evolution for elapsed time Δ.
- Step(M,S,e) gives an accepted event transition or a diagnostic.

For scalar quantities of equal dimension d, addition preserves d:

$$
\frac{\Gamma\vdash a:Q_d\qquad\Gamma\vdash b:Q_d}
     {\Gamma\vdash a+b:Q_d}.
$$

For framed vectors, both dimensions and frame identity must match:

$$
\frac{\Gamma\vdash a:V_{d,F}\qquad\Gamma\vdash b:V_{d,F}}
     {\Gamma\vdash a+b:V_{d,F}}.
$$

Let claims(a) be the resolved channel set. Admission requires a valid action state, valid target/mode/frame/bounds, and:

$$
claims(a)\cap claims(active(S))=\varnothing.
$$

The runtime source of a body's pose is exclusive: world placement/held prescribed channels, one incoming prescribed relation, or free dynamic evaluation. Ownership is absent from this choice. Transition failure returns a diagnostic and no accepted partial state.

An accepted evaluated interval requires all of the following: well-formed source; valid bindings/types/defaults; finite acyclic construction; supported physical/relationship contracts; admissible actions and events; finite evaluated values; and satisfaction of the requested output-level conditions. A syntactically accepted file can still fail any later condition.

### 10.2 Operators and accessible fields — LANG-022

| Operation | Defined operands and result |
| --- | --- |
| Unary `-` | Numeric scalar, quantity, or vector/tuple; preserve type |
| `+` and `-` | Compatible numeric/quantity values; compatible tuples/vectors componentwise; point operations only as defined in 5.4 |
| `*` and `/` | Scalars/quantities combine dimensions; a tuple/vector may multiply or divide by a scalar/quantity; scalar × vector is also defined |
| Vector × vector using `*` | Invalid; no hidden dot, cross, or componentwise product |
| `< <= > >=` | Compatible numeric scalar/quantity types only |
| `== !=` | Compatible scalars/quantities, Booleans, strings, references, modes, and componentwise tuples/vectors/points/ranges |
| `and or not` | Boolean only, with the stated short-circuit rules |
| Function call | One bound function or method; exact positional arity and compatible argument/return types |
| Conditional | Boolean condition; branches with the same type, allowing the explicit integer widening or nominal reference upcast already defined |

There is no unary `+`, assignment expression, implicit string-to-enum conversion, string arithmetic, or truthiness conversion. Tuple/vector equality requires the same compatible element type; vector/point equality also requires matching frame identity. Reference equality compares identity after a permitted nominal upcast. `Rotation`, `Pose`, `Geometry`, `BodyModel`, `Color`, and `Action` have no source equality operator in this core; diagnostic/sampling comparison uses their documented fields and rotation-error metric.

The following immutable fields can be read in expressions:

| Value | Fields |
| --- | --- |
| `Vec3<Q>` | `x`, `y`, `z` |
| `Vector3<Q>` / `Point3` | `x`, `y`, `z`, `frame` |
| `Rotation` | `w`, `x`, `y`, `z`, the rounded projections of its canonical normalized coordinates |
| `Pose` | `frame`, `position: Vec3<Length>`, `rotation` |
| `Range<Q>` | `lower`, `upper` |
| `Color` | `r`, `g`, `b`, `a` |
| `SiteRef` | `frame`, `pose`, `interface`, `size` |
| `JointRef` | `parent`, `child`; `axis`, `limits`, `initial` only for hinge/slider |
| Object reference | Accessible user members and its immutable elaborated built-in fields, `frame`, and `origin`; `placement` is source-readable only without an incoming pose relation |

`Geometry`, `BodyModel`, and `Action` are otherwise opaque source values; their structured details are available through inspection. A pure expression reading `object.motion` reads the elaborated initial declaration, not its state after a release. Current state is available only through the run inspection contract.

Every user class implicitly derives from the predefined `Object` root unless it names another base. `Ref<Object>` can refer to any instance. `Object` supplies the built-in instance fields and can be instantiated as an empty container. A class/type name is not a runtime constructor function; object construction uses `object` or `part` declarations.

### 10.3 Complete callable core catalog — LANG-023

In this table Q is a numeric scalar or quantity type permitted for that operation. Integer arguments in numeric constructors widen to `Real` under section 5.2; no dimension is invented. The listed overloads are built-in contracts, not user-defined overload resolution.

| Signature | Result and domain |
| --- | --- |
| `real(Int) -> Real` | Explicit rounded integer conversion |
| `abs(Q) -> Q` | Absolute value; integer minimum overflow is an error |
| `min(Q,Q) -> Q`, `max(Q,Q) -> Q` | Compatible scalar/quantity values |
| `near(Q,Q,Q) -> Bool` | Same compatible type; third argument is a nonnegative absolute tolerance; compare mathematical absolute difference |
| `sqrt(Real) -> Real` | Nonnegative argument |
| `sin(Angle) -> Real`, `cos(Angle) -> Real` | Numeric radians |
| `vec3(Q,Q,Q) -> Vec3<Q>` | Common compatible element type |
| `vector(FrameRef,Q,Q,Q) -> Vector3<Q>` | Explicit expressed-in frame |
| `point(FrameRef,Length,Length,Length) -> Point3` | Explicit position frame |
| `quat(Real,Real,Real,Real) -> Rotation` | (w,x,y,z), validated/normalized under 5.4 |
| `axis_angle(Vec3<Real>,Angle) -> Rotation` | Unit axis and radian angle |
| `pose(FrameRef,Vec3<Length>,Rotation) -> Pose` | Position and orientation relative to the named reference |
| `range(Q,Q) -> Range<Q>` | Scalar/quantity lower ≤ upper |
| `rgba(Real,Real,Real,Real) -> Color` | Each component in [0,1] |
| `empty() -> Geometry` | No surface |
| `sphere(Length) -> Geometry` | Positive radius |
| `box(Vec3<Length>) -> Geometry` | Three positive full side lengths |
| `no_body() -> BodyModel` | No physical matter |
| `sphere_body(Length,Mass) -> BodyModel` | Positive radius and mass; positive finite derived isotropic inertia |
| `move(Ref<Object>,Vector3<Speed>,Time) -> Action` | Root translation builder; target preconditions checked at admission |
| `spin(Ref<Object>,Vector3<AngularSpeed>,Time) -> Action` | Root orientation builder; target preconditions checked at admission |
| `tween(JointRef,Angle,Time) -> Action` | Hinge coordinate builder |
| `tween(JointRef,Length,Time) -> Action` | Slider coordinate builder |

Action-argument types, frame requirements, finite numeric values, and positive duration are checked when the description is elaborated. The tween target's membership in the target joint's mandatory range is an admission precondition, checked at the start boundary together with current mode, action state, and channel availability. This distinction preserves N14's required admission-phase diagnostic. A timeline preflight can identify those later failures in advance without changing their phase, timestamp, or meaning. Section 16 records this clarification to the original draft's broader action-domain wording.

A named declaration `action a @ "a" = expression;` gives an immutable `Action` description its own lifecycle identity. Referring to `a` in another action initializer copies the description and target references but creates a separate lifecycle instance. Referring to `a` in `start a;` selects the named instance. Cyclic description references are invalid.

### 10.4 Diagnostic code registry — LANG-024

Codes are stable within this specification version. English messages and details may add context. A validator must identify the relevant rule and location and must not use an unsupported result to conceal an invalid construct.

| Code | Required meaning |
| --- | --- |
| `OKL-E-LEXICAL` | Invalid encoding, token, escape, or unterminated literal/comment |
| `OKL-E-SYNTAX` | Tokens do not match the complete grammar |
| `OKL-E-NAME` | Unknown, ambiguous, or duplicated lexical name; invalid member access |
| `OKL-E-ID` | Missing, malformed, reused, or improperly changed stable key |
| `OKL-E-TYPE` | Incompatible non-unit types, arity, or unsupported operator/type constructor |
| `OKL-E-UNIT` | Incompatible quantity dimensions or unit expression |
| `OKL-E-FRAME` | Missing/incompatible spatial frame or world-only operation supplied another frame |
| `OKL-E-NUMERIC` | Division by zero, invalid scalar domain, overflow, or non-finite value |
| `OKL-W-UNDERFLOW` | Scalar conversion/arithmetic produced a finite underflowed value |
| `OKL-E-AXIS` | Invalid zero/non-unit joint or axis-angle axis |
| `OKL-E-ROTATION` | Invalid quaternion or improper rotation description |
| `OKL-E-OVERRIDE` | Invalid specialization, visibility, signature, or override identity |
| `OKL-E-ACCESS` | Source access to a private member outside its declaring class |
| `OKL-E-READONLY` | Attempt to override a derived/read-only member |
| `OKL-E-DEPENDENCY-CYCLE` | Cyclic derived values or function/method/action-description dependency |
| `OKL-E-INHERITANCE-CYCLE` | Cyclic nominal class inheritance |
| `OKL-E-RECURSIVE-COMPOSITION` | Part expansion is not finite |
| `OKL-E-ASSERT` | Authored static assertion is false |
| `OKL-E-PHYSICAL-DOMAIN` | Invalid radius, mass, size, or required physical description |
| `OKL-E-MOTION-MODE` | A target/state is incompatible with its declared motion authority |
| `OKL-E-POSE-AUTHORITY` | Competing pose sources, or a forbidden source placement read on a relation-controlled child |
| `OKL-E-FOLLOW-CYCLE` | Cyclic ordinary spatial following |
| `OKL-E-SITE-INTERFACE` | Incompatible attachment-site interface or size |
| `OKL-E-JOINT-LIMIT` | Initial coordinate or requested target violates a mandatory joint range |
| `OKL-E-CONTROL-CONFLICT` | Two active/paused actions claim the same channel |
| `OKL-E-ACTION-STATE` | Invalid start, pause, resume, or stop lifecycle transition |
| `OKL-E-EVENT-ORDER` | Invalid timestamp, duration, or multiple source blocks at one timestamp |
| `OKL-E-EVENT-CONFLICT` | Earlier same-time explicit edit conflicts with an incoming release dependency |
| `OKL-E-RELEASE-STATE` | Named grip is inactive or not a releasable grip |
| `OKL-E-HANDOFF` | No valid finite incoming pose/velocity transfer is available |
| `OKL-E-CAPABILITY-UNSUPPORTED` | Requested profile, output operation, mechanical loop, or physical model lacks the required contract/support |
| `OKL-E-REVISION` | Revision precondition fails, references are stale, or supplied span/text does not match the revision |
| `OKL-E-REQUEST-ID` | Same operation identity is reused for a different request payload |
| `OKL-E-RESOURCE` | Explicit work/result budget prevents completion |
| `OKL-E-SAMPLE` | Requested run, time, boundary side, or field is unavailable |

When several independent problems exist, diagnostics may be returned together. The primary phase order is lexical, syntax, binding/type, elaboration, support, then chronological admission/transition/evaluation. A phase that cannot be interpreted because an earlier phase failed is not simulated speculatively. At one event, state/precondition checks precede a new channel claim, so restarting a running action reports action-state failure before a secondary overlap report.

## 11. AI-agent authoring, inspection, and repair contract

### 11.1 Source authority and versioned operations — LANG-025

An agent must be able to discover the contract, write source, inspect a bounded part of it, apply a local edit, and determine whether the requested result is valid. This section defines the data and effects of those operations. It does not define an HTTP endpoint, editor protocol, server, or working tool.

The native UTF-8 source is authoritative for an accepted revision. Its parsed structured representation is a versioned view derived from that source. Structured edits must update source and relevant comments; no second independently authoritative object graph may diverge from it. A formatter must preserve meaning and keys.

All operations use schema version `ontokin.agent/0.1`, a `project_id`, and a nonempty `request_id`. A `source_revision` is an opaque immutable identity for an exact source snapshot, including a rejected candidate. An `accepted_revision` identifies the snapshot currently accepted for the project and is null before its first successful create. Snapshot existence does not imply source validity or acceptance. Diagnostics always identify the snapshot containing the reported bytes. A Git commit may contain a snapshot, but the protocol does not require Git or equate a repository commit with a running simulation.

| Operation | Required request data | Observable contract |
| --- | --- | --- |
| `discover` | Semantic profile; optional type/capability filter; result limit | Return versioned type/member/built-in catalog, domains, defaults, effects, examples, supported stages, and unavailable capabilities. |
| `create` | File name, full source, expected accepted revision `null`, requested output level | Create an immutable candidate snapshot; accept only if its requested level succeeds. A project with an accepted revision requires `edit` instead. |
| `edit` | Expected accepted revision; nonempty list of patches; requested output level | Apply all patches to that revision as one candidate and accept atomically after required validation. |
| `validate` | Source revision; requested output level; budgets | Return structural, support, and requested-stage results separately. It does not advance an existing run. |
| `inspect` | Source revision; bounded selector; fields; optional run/time/boundary side; result limit/cursor | Read a consistent definition or evaluated snapshot without changing it. |
| `evaluate` | Accepted source revision; `run_id` or `null`; exact until-time; budgets | Null creates a fresh run. A supplied run identity must already exist and match the revision; otherwise `OKL-E-SAMPLE`. Evaluate forward to the requested time and identify the valid interval and failures. |
| `reset` | Source revision | Create a new run at its initialization; retain old run identity/history separately. |
| `status` | The target request identity | Return known progress/outcome for a previous operation without repeating its effects. |
| `cancel` | The target request identity | Request termination of pending work; report whether cancellation occurred before acceptance or work had already completed. |

A create/edit/validate request explicitly names `represented`, `constructed`, `evaluated`, or `delivered`. Evaluate requests target `evaluated`. An unavailable higher level cannot be silently replaced with success at a lower level. A caller can issue a separate represented-level request when retaining a valid description is its intended outcome.

For create/edit/validate, requesting `evaluated` means a fresh evaluation from initialization through `scene.duration`, including the horizon's after-state. It never advances an existing run. The result supplies the isolated run identity if one was produced, including a failed candidate run retained only for diagnosis. A delivered request additionally needs an external destination contract; this core supplies none and must return unsupported. Explicit `evaluate` supports a shorter interval; its until-time must not precede an existing run's current after-state. Only accepted source can start an ordinary evaluate/reset run.

An edit patch contains `element_id`, `start_byte`, `end_byte`, `expected_text`, and `replacement`. Offsets are zero-based UTF-8 byte offsets, start inclusive/end exclusive, aligned to character boundaries in the named source revision. The expected text must match exactly. Patches must be non-overlapping; two insertions at the same offset conflict. A patch must lie inside its identified element's source span; adding a declaration targets its enclosing element. The candidate must rebind references and pass its requested checks.

An instance parameter inherited from a shared declaration does not acquire that declaration's writable source span. Changing only that instance inserts or edits an override in the selected occurrence's initializer and targets the occurrence identity. Changing the shared default explicitly targets its definition identity in the `definitions` namespace and therefore affects its dependent occurrences.

Repair offsets in a diagnostic refer to its `source_revision`, which may be rejected. An agent may apply them to that candidate in its editor to form corrected source, then compute a new patch set against the current accepted revision before submitting `edit`. It must not submit candidate-relative offsets as accepted-relative offsets. Before any accepted revision exists, corrected full source is submitted through a new `create` request. Rejected snapshots remain inspectable as source and diagnostic context; unresolved fields are labeled unavailable, and they never replace the accepted model.

The smallest relevant expression or declaration is the preferred edit scope. A rename updates the declaration identifier and all lexical uses while retaining its key. A removal includes its selected owned descendants and must explicitly repair all surviving dependencies. A failed patch list, broken reference, or invalid candidate preserves the previously accepted source. It does not leave part of the candidate in the accepted model.

### 11.2 Retry, cancellation, and result states — LANG-026

The request identity is unique within a project. A retry with the same identity and same canonical request returns the original in-progress/completed result; it must not duplicate edits, runs, or future effects. Reusing the identity with a different payload returns `OKL-E-REQUEST-ID`. JSON member order is ignored when comparing canonical requests; meaningful values and array order are not.

The service must retain either the result or a tombstone stating that the outcome is unknown. An expired/unknown outcome is `unknown_outcome`; it does not authorize an automatic rerun under the same or a fabricated new identity. A caller must reconcile the accepted revision/run before deliberately issuing a new request.

Operation statuses are `queued`, `running`, `succeeded`, `rejected`, `failed`, `cancelled`, and `unknown_outcome`. Status is separate from the requested/achieved output level. Rejection before acceptance preserves the old revision. Numerical/evaluation failure records its last valid state and does not label later samples valid. Cancellation after an edit already committed must report the accepted result, not pretend the edit was cancelled.

A result includes schema/request identity, status, source/accepted revision where applicable, requested and achieved level, run identity where applicable, diagnostics, result payload, and pagination/continuation state where needed. These contextual fields must not be inferred from the caller's latest editor view.

Budgets state permitted work, such as maximum elaborated objects, maximum operations, result items, and elapsed job time. Resource exhaustion is distinct from invalid mathematics or impossible mechanics. Cancellation and budget termination retain inspectable progress or explicitly identify which partial results are unavailable.

### 11.3 Bounded inspection — LANG-027

An inspection query selects by exact identity, nominal type, role, or relation, plus requested fields. It has an explicit result limit of at most 1,000 items. A cursor is bound to the same source revision, run, sample, selector, and field set. A continuation cannot silently switch to a newer revision. Truncation is labeled and returns a continuation token; a completed result returns `next_cursor: null`.

| Inspectable record | Required information |
| --- | --- |
| Identity and structure | Kind, key path, class/definition revision, role, display identifier, owner, child identities, source span |
| Effective values | Typed canonical value and display unit, origin category and source, dependencies, unresolved/stale status |
| Geometry and matter | Geometry description, body model/proxy, own mass, owned aggregate mass, explicitly separate connected loads |
| Frames and relations | Frame identity, incoming authority, sites, follow/joint endpoints, offsets/coordinates, physical interpretation, collision-disabled state |
| Actions | Instance/description identity, target and channel, lifecycle, local elapsed, start/current/target values, pause/stop/completion state |
| Run state | Source revision, run identity, time and boundary side, world pose/COM velocity/angular velocity, gravity participation, last valid interval |
| Support and validity | Requested level, available/unavailable capabilities, limits, approximation assumptions, failures and their evidence |

A value origin is `authored`, `inherited`, `defaulted`, `derived`, `estimated`, or `unresolved`. The core does not silently introduce estimates; its uniform-sphere inertia is derived from a disclosed model. An implementation returning an estimate must identify the additional contract.

World position, world-measured center-of-mass velocity, and world angular velocity are the default physical state. A requested local pose uses T_FW T_WB at the same time. A velocity may be re-expressed in different axes using the frame rotation, but its `measured_in` field remains `world`. **Velocity measured relative to a moving frame is a different operation and is not supplied in this core.** Rotation of components alone must never be labeled relative velocity.

Current-state fields require a matching run and an available evaluated sample/interval. A source-only query cannot return invented current state. Queries outside [0, scene.duration], after an unresolved failed boundary, or from a stale cursor return an explicit unavailable/stale result. Sampling a completed evaluated interval is read-only; it neither advances time nor changes action state.

### 11.4 Structured diagnostics and a repair cycle — LANG-028

The machine-readable contract is [diagnostic.schema.json](core-v0.1/diagnostic.schema.json). The [illustrative diagnostic](core-v0.1/diagnostic-example.json) is a fabricated example of that contract, not output from an OntoKin implementation.

Each diagnostic includes schema version, stable code, severity, category, phase, message, source revision, run/time, primary and related source locations, element identity, rule IDs, details, repair, and blocked output levels. The `run_id`, `time`, and `repair` fields are always present and are null when inapplicable. An unresolved location's `element_id` is likewise null. Source ranges use the UTF-8 convention above. Time uses an exact decimal seconds string and a before/after side.

The schema checks data shape. Additional semantic conditions still apply: end offset ≥ start offset; valid UTF-8 boundaries; locations and non-null resolved identities must exist in the diagnostic's source snapshot; code/phase/blocked-level combinations must be truthful; repair patches must satisfy snapshot-relative edit preconditions. Schema validation alone does not establish these conditions.

For example, the illustrative diagnostic assigns `1[kg]` to a length parameter and reports `OKL-E-UNIT` with expected `Length`, actual `Mass`, the exact expression span, and LANG-003/LANG-005 references. It may suggest authoring a length value. It must not silently convert kilograms to meters or change unrelated objects.

The normal repair cycle is: discover the needed contract; inspect the identified revision and field; submit a localized revision-checked edit; validate the requested level; inspect the result and affected dependencies. No language-model call is required for each animation sample. Human review can inspect the same source, diagnosis, and result context.

## 12. Complete source programs and expected behavior

These four programs are independent source bundles. Each has its own module, scene, and declared horizon. Their expected results were fixed before the reference prototype was implemented. Measured execution results are recorded separately in OK-ENG-001 and its linked conformance report; the examples remain independent expectations.

The adjacent `.ok` files are the complete source fixtures. Their copies below must remain byte-for-byte equivalent after normalizing the final newline. The [validation manifest](core-v0.1/validation-cases.json) derives additional complete candidates by exact, ordered replacements. It records requirement IDs, language rules, semantic-check associations, and expected diagnostics or state.

All sample tables below use seconds, meters, meters per second, and radians where applicable. Samples use the after-state unless explicitly marked otherwise. Decimal values are displayed at useful precision; the equations over canonical source values determine the reference result.

### 12.1 P01: An object with independently moving parts

**Source:** [01-independent-parts.ok](core-v0.1/01-independent-parts.ok).

```ontokin
ontokin "0.1";
module IndependentParts @ "independent-parts";
profile "core-0.1";

fn twice @ "twice"(value: Length) -> Length {
    return 2 * value;
}

class Marker @ "marker" {
    public param radius @ "radius": Length = 0.2[m];
    public derive diameter @ "diameter": Length = twice(self.radius);
    geometry = box(vec3(self.diameter, self.radius, self.radius / 2));
    appearance = rgba(0.2, 0.6, 0.9, 1);
}

class SmallMarker @ "small-marker" extends Marker {
    override radius = 0.1[m];
}

class Arm @ "arm" {
    public part hand @ "hand": SmallMarker {}
    public joint extension @ "extension": slider {
        parent = self.origin;
        child = self.hand.origin;
        axis = vec3(1, 0, 0);
        limits = range(0.25[m], 0.75[m]);
        initial = 0.25[m];
    }
    public method reach @ "reach"(distance: Length, duration: Time) -> Action {
        return tween(self.extension, distance, duration);
    }
}

class Rig @ "rig-type" {
    public part head @ "head": Marker {}
    public part arm @ "arm": Arm {}
    public site neck @ "neck" {
        pose = pose(self.frame, vec3(0[m], 1[m], 0[m]), quat(1, 0, 0, 0));
        interface = "rigid.origin";
        size = 0[m];
    }
    public site shoulder @ "shoulder" {
        pose = pose(self.frame, vec3(0[m], 0.5[m], 0[m]), quat(1, 0, 0, 0));
        interface = "rigid.origin";
        size = 0[m];
    }
    public joint yaw @ "yaw": hinge {
        parent = self.neck;
        child = self.head.origin;
        axis = vec3(0, 1, 0);
        limits = range(-90[deg], 90[deg]);
        initial = 0[rad];
    }
    public joint mount @ "mount": fixed {
        parent = self.shoulder;
        child = self.arm.origin;
    }
    public method look @ "look"(angle: Angle, duration: Time) -> Action {
        return tween(self.yaw, angle, duration);
    }
}

scene Demo @ "demo" {
    duration = 3[s];
    gravity = vector(world, 0[m/s^2], -9.81[m/s^2], 0[m/s^2]);
    object rig @ "rig": Rig {
        placement = pose(world, vec3(0[m], 0[m], 0[m]), quat(1, 0, 0, 0));
    }
    action advance @ "advance" =
        move(rig, vector(world, 1[m/s], 0[m/s], 0[m/s]), 2[s]);
    action look @ "look" = rig.look(90[deg], 1[s]);
    action reach @ "reach" = rig.arm.reach(0.75[m], 2[s]);
    at 0[s] sequence {
        start advance;
        start look;
        start reach;
    }
}
```

The rig owns a head and arm; the arm owns a hand. Ownership defines their occurrence structure. The yaw hinge, shoulder mount, and arm slider separately define their motion relationships. Nothing in the ownership tree adds another transform.

Three actions start at t=0. The rig translates along world X at 1 m/s for two seconds; its head turns locally through 90 degrees in one second; its hand extends from 0.25 m to 0.75 m over two seconds. These requests claim different channels, so all are admissible. A method call creates each tween description before the timeline starts it.

For 0 ≤ t ≤ 2, the rig's X position is t and the hand's slider coordinate is 0.25 + 0.25t. Its world position is therefore (0.25 + 1.25t, 0.5, 0). From t=2 through the horizon at t=3, the completed channels hold their endpoints.

| Time | Rig world X | Head's local yaw | Hand's local slider coordinate | Hand's world X |
| --- | ---: | ---: | ---: | ---: |
| 0 | 0 | 0° | 0.25 | 0.25 |
| 0.5 | 0.5 | 45° | 0.375 | 0.875 |
| 1 | 1 | 90° | 0.5 | 1.5 |
| 1.5 | 1.5 | 90° | 0.625 | 2.125 |
| 2 | 2 | 90° | 0.75 | 2.75 |
| 3 | 2 | 90° | 0.75 | 2.75 |

At t=1 the head is at world (1,1,0); its look action is completed while translation and reach continue. The hand retains identity `["independent-parts","demo","rig","arm","hand"]`. Its inherited radius is 0.1 m and its derived diameter is 0.2 m. No instance has physical matter, so the explicitly declared gravity does not move these prescribed objects.

This fixture exercises typed functions, parameters, derived values, specialization, recursive parts, named attachment sites, pure methods returning actions, fixed/hinge/slider relationships, and independent channels. Its principal links are CAP-01, CAP-02, CAP-08, LNG-001, OBJ-005, ANM-018, SEM-01–SEM-05, SEM-08, and SEM-17–SEM-19.

### 12.2 P02: Gravity and an ordinary release

**Source:** [02-gravity-and-release.ok](core-v0.1/02-gravity-and-release.ok).

```ontokin
ontokin "0.1";
module GravityRelease @ "gravity-release";
profile "core-0.1";

class Carrier @ "carrier-type" {
    geometry = box(vec3(0.2[m], 0.2[m], 0.2[m]));
    appearance = rgba(0.3, 0.3, 0.3, 1);
}

class Payload @ "payload-type" {
    public param radius @ "radius": Length = 0.1[m];
    public param mass @ "mass": Mass = 1[kg];
    geometry = sphere(self.radius);
    physical = sphere_body(self.radius, self.mass);
    appearance = rgba(0.9, 0.4, 0.1, 1);
    motion = prescribed;
    collision = disabled;
}

scene Demo @ "demo" {
    duration = 2[s];
    gravity = vector(world, 0[m/s^2], -9.81[m/s^2], 0[m/s^2]);
    object carrier @ "carrier": Carrier {
        placement = pose(world, vec3(0[m], 2[m], 0[m]), quat(1, 0, 0, 0));
    }
    object payload @ "payload": Payload {}
    joint hold @ "hold": grip {
        parent = carrier.origin;
        child = payload.origin;
    }
    action carry @ "carry" =
        move(carrier, vector(world, 1[m/s], 0[m/s], 0[m/s]), 2[s]);
    at 0[s] sequence { start carry; }
    at 1[s] sequence { release hold using incoming; }
}
```

The carrier and payload are separately scene-owned. The initial grip aligns their origins and imposes the carrier's pose on the payload. The payload supplies its own 1 kg sphere body. While prescribed, it does not fall under gravity.

At t=1, `release hold using incoming;` preserves the payload's world position (1,2,0), velocity (1,0,0), and zero angular velocity, then makes it dynamic. Writing Δ=t−1, its later trajectory is:

$$
p(t)=(1+\Delta,\;2-\tfrac12(9.81)\Delta^2,\;0),\qquad
v(t)=(1,\;-9.81\Delta,\;0).
$$

| Time / side | Grip | Payload mode | Payload world position | Payload world velocity |
| --- | --- | --- | --- | --- |
| 0 after | Active | Prescribed | (0,2,0) | (1,0,0) |
| 1 before | Active | Prescribed | (1,2,0) | (1,0,0) |
| 1 after | Inactive | Dynamic | (1,2,0) | (1,0,0) |
| 1.5 | Inactive | Dynamic | (1.5,0.77375,0) | (1,−4.905,0) |
| 2 after | Inactive | Dynamic | (2,−2.905,0) | (1,−9.81,0) |

At t=2 the carrier's move completes and its outgoing X velocity becomes zero. The released payload retains X velocity 1 m/s. Its acceleration changes at release; its position and velocity do not jump. There is no implicit ground at Y=0, so a negative Y position is expected.

This fixture links OBJ-015, PHY-001, PHY-014, ANM-007, CAP-12, SEM-14–SEM-16, and SEM-20–SEM-25. It defines a state-transfer example without requiring a complete character, a contact solver, or a physical finger model.

### 12.3 P03: Release from a translating and rotating support

**Source:** [03-rotating-release.ok](core-v0.1/03-rotating-release.ok).

```ontokin
ontokin "0.1";
module RotatingRelease @ "rotating-release";
profile "core-0.1";

class Carrier @ "carrier-type" {
    geometry = box(vec3(0.2[m], 0.2[m], 0.2[m]));
    public site tip @ "tip" {
        pose = pose(self.frame, vec3(0.5[m], 0[m], 0[m]), quat(1, 0, 0, 0));
        interface = "rigid.origin";
        size = 0[m];
    }
}

class Payload @ "payload-type" {
    public param radius @ "radius": Length = 0.1[m];
    public param mass @ "mass": Mass = 1[kg];
    geometry = sphere(self.radius);
    physical = sphere_body(self.radius, self.mass);
    motion = prescribed;
    collision = disabled;
}

scene Demo @ "demo" {
    duration = 2[s];
    gravity = vector(world, 0[m/s^2], -9.81[m/s^2], 0[m/s^2]);
    object carrier @ "carrier": Carrier {
        placement = pose(world, vec3(0[m], 2[m], 0[m]),
                         axis_angle(vec3(0, 0, 1), -2[rad]));
    }
    object payload @ "payload": Payload {}
    joint hold @ "hold": grip {
        parent = carrier.tip;
        child = payload.origin;
    }
    action carry @ "carry" =
        move(carrier, vector(world, 1[m/s], 0[m/s], 0[m/s]), 2[s]);
    action turn @ "turn" =
        spin(carrier, vector(world, 0[rad/s], 0[rad/s], 2[rad/s]), 2[s]);
    at 0[s] sequence {
        start carry;
        start turn;
    }
    at 1[s] sequence { release hold using incoming; }
}
```

The carrier translates at (1,0,0) m/s and rotates about world Z at 2 rad/s. Its tip is 0.5 m along its local X axis. The initial angle is −2 rad, so its orientation is identity at the release time t=1.

Before release, define θ=2t−2. The payload's center and velocity are:

$$
p_C(t)=(t+\tfrac12\cos\theta,\;2+\tfrac12\sin\theta,\;0),
\qquad
v_C(t)=(1-\sin\theta,\;\cos\theta,\;0).
$$

At t=1, the center is (1.5,2,0). The rotational contribution is (0,0,2) × (0.5,0,0) = (0,1,0) m/s, giving total velocity (1,1,0) m/s. Transferring only the carrier origin's linear velocity would produce the wrong trajectory.

After release:

$$
p_C(t)=(1.5+\Delta,\;2+\Delta-\tfrac12(9.81)\Delta^2,\;0),
\qquad
v_C(t)=(1,\;1-9.81\Delta,\;0).
$$

| Time / side | Payload world position | Payload world velocity | Payload world angular velocity |
| --- | --- | --- | --- |
| 1 before | (1.5,2,0) | (1,1,0) | (0,0,2) |
| 1 after | (1.5,2,0) | (1,1,0) | (0,0,2) |
| 1.5 | (2,1.27375,0) | (1,−3.905,0) | (0,0,2) |
| 2 after | (2.5,−1.905,0) | (1,−8.81,0) | (0,0,2) |

The sphere continues rotating about Z; its angle relative to its release orientation is 1 rad at t=1.5 and 2 rad at t=2. Its carrier's eventual stop cannot change that free state. The uniform sphere model is what makes constant torque-free angular velocity a valid core contract.

This is the exact numerical setup of SC-13, connected to SEM-07 and SEM-21. It also exercises LNG-009, OBJ-015, PHY-014, CAP-07, and CAP-12. This table is the analytical specification expectation; measured prototype values belong to the separate engineering report.

### 12.4 P04: Ownership, reuse, specialization, and visual following

**Source:** [04-ownership-reuse-and-follow.ok](core-v0.1/04-ownership-reuse-and-follow.ok).

```ontokin
ontokin "0.1";
module OwnershipReuse @ "ownership-reuse";
profile "core-0.1";

class Ball @ "ball-type" {
    public param radius @ "radius": Length = 0.1[m];
    public param mass @ "mass": Mass = 1[kg];
    public derive diameter @ "diameter": Length = 2 * self.radius;
    geometry = sphere(self.radius);
    physical = sphere_body(self.radius, self.mass);
    motion = dynamic;
    public method width @ "width"() -> Length {
        return self.diameter;
    }
}

class WideBall @ "wide-ball-type" extends Ball {
    override radius = 0.2[m];
    public override method width @ "width"() -> Length {
        return 2 * self.radius;
    }
}

class Label @ "label-type" {
    geometry = box(vec3(0.05[m], 0.05[m], 0.05[m]));
}

class Group @ "group-type" {
    public part ball @ "ball": WideBall {
        placement = pose(world, vec3(0[m], 2[m], 0[m]), quat(1, 0, 0, 0));
    }
}

scene Demo @ "demo" {
    duration = 1[s];
    gravity = vector(world, 0[m/s^2], -9.81[m/s^2], 0[m/s^2]);
    object first @ "first": Group {}
    object second @ "second": Group {
        ball.radius = 0.3[m];
    }
    object label @ "label": Label {}
    follow caption @ "caption" {
        parent = first.ball.frame;
        child = label;
        offset = pose(first.ball.frame, vec3(0[m], 0.5[m], 0[m]),
                      quat(1, 0, 0, 0));
    }
    action shift_group @ "shift-group" =
        move(first, vector(world, 1[m/s], 0[m/s], 0[m/s]), 1[s]);
    at 0[s] sequence { start shift_group; }
    assert first.ball.width() == 0.4[m], "first ball uses its inherited default";
    assert second.ball.width() == 0.6[m], "second ball uses its instance override";
}
```

Each group expands its own ball occurrence. The first ball inherits radius 0.2 m from `WideBall`. The second's explicit nested override gives it radius 0.3 m. Their width assertions therefore evaluate to 0.4 m and 0.6 m respectively, and changing the second radius does not mutate the first ball.

Both balls have their own initial world placement and are dynamic. Moving `first`, their organizational owner in one branch, does not add its translation to `first.ball`. The label has no physical matter; its explicit following relation places it 0.5 m above the first ball.

| Time | First owner's world X | Either ball's world position | Label's world position |
| --- | ---: | --- | --- |
| 0 | 0 | (0,2,0) | (0,2.5,0) |
| 0.5 | 0.5 | (0,0.77375,0) | (0,1.27375,0) |
| 1 | 1 | (0,−2.905,0) | (0,−2.405,0) |

At t=0.5, inspecting the first ball's pose in its owner's frame gives (−0.5,0.77375,0). Converting that pose back to world space yields (0,0.77375,0); it does not add a second owner displacement.

Each group has owned aggregate mass 1 kg. The scene's total is 2 kg. The label, ownership references, and following relation add no matter. The spheres' center-of-mass inertia scalars are approximately 0.016 and 0.036 kg·m² because their radii differ. Their overlapping world positions remain valid with collision disabled.

This fixture links LNG-018, OBJ-002, OBJ-006, OBJ-011, OBJ-018, CAP-03, SEM-01–SEM-03, SEM-05, SEM-08, SEM-09, and SEM-15. It supplies smaller counterparts of SC-02, SC-05, SC-07, and SC-12, without claiming the full character or mass-layout examples have been implemented.

## 13. Validation cases, traceability, and verification limits

### 13.1 Positive variations

The manifest contains twelve expected-valid cases. P01–P04 are the complete files above. P05–P12 apply exact replacements to those files; each replacement must match once, or the fixture itself is defective. They are complete candidate programs after that operation.

| Case | Variation | Required distinguishing outcome |
| --- | --- | --- |
| P05 | Pause the carrier at 1.25 s and resume at 1.75 s after releasing at 1 s | At 1.5 s the carrier holds X=1.25 while the payload reaches X=1.5 and Y=0.77375; repeated inspection changes neither state nor time. |
| P06 | Release at the carrier's natural endpoint, 2 s | The carrier completes first, but the release still receives saved incoming payload velocity (1,0,0). |
| P07 | At 1 s: release, stop the old carry, then start a new move | The payload keeps X velocity 1; the carrier takes its newly requested X velocity 2. No stale claim survives. |
| P08 | Write 20 cm in place of 0.2 m | Canonical geometry, dimensions, and behavior remain equivalent. |
| P09 | Rename `hand` to `palm` and update its lexical reference, retaining key `"hand"` | Stable identity and behavior remain unchanged; the new spelling binds successfully. |
| P10 | Call width through `Ref<Ball>` while the object is a `WideBall` | The most-specific compatible method override is selected. |
| P11 | Annotate radius with `Quantity[cm]` in place of `Length` | Both annotations have the same normalized dimension and canonical value meaning. |
| P12 | Stop the rig translation at 1 s while its local reach continues | At 1.5 s the rig holds X=1, the hand reaches X=1.625, and the head retains its 90° local angle. |

These variants distinguish action lifecycle, value identity, and coordinate meaning. They do not demonstrate a physics integration algorithm, general locomotion, or broad numerical performance.

### 13.2 Invalid, conflicting, and unsupported candidates

The following expected outcomes are normative design cases. Syntax rejection is expected only for N01, N02, N03, and N19. The remaining candidates must reach their specified later checks; accepting their grammar does not certify validity.

| Case | Invalid or unsupported request | Expected phase and code |
| --- | --- | --- |
| N01 | Missing semicolon | syntax: `OKL-E-SYNTAX` |
| N02 | Leading zero in a number | lexical: `OKL-E-LEXICAL` |
| N03 | Unsupported string escape | lexical: `OKL-E-LEXICAL` |
| N04 | Duplicate occurrence key | binding: `OKL-E-ID` |
| N05 | Unknown method spelling | binding: `OKL-E-NAME` |
| N06 | Mass assigned to a length parameter | type: `OKL-E-UNIT` |
| N07 | Local axes supplied to a world-only move | type: `OKL-E-FRAME` |
| N08 | Zero hinge axis | elaboration: `OKL-E-AXIS` |
| N09 | Derived/default dependency cycle | elaboration: `OKL-E-DEPENDENCY-CYCLE` |
| N10 | Incompatible method override return type | type: `OKL-E-OVERRIDE` |
| N11 | Recursive part expansion | elaboration: `OKL-E-RECURSIVE-COMPOSITION` |
| N12 | Authored placement competes with a grip | elaboration: `OKL-E-POSE-AUTHORITY` |
| N13 | Concurrent actions claim the same root channel | admission: `OKL-E-CONTROL-CONFLICT` |
| N14 | Goal exceeds a mandatory hinge limit | admission: `OKL-E-JOINT-LIMIT` |
| N15 | Division by zero in a derived expression | elaboration: `OKL-E-NUMERIC` |
| N16 | Zero physical mass | elaboration: `OKL-E-PHYSICAL-DOMAIN` |
| N17 | Separate event blocks at the same time | elaboration: `OKL-E-EVENT-ORDER` |
| N18 | Release the same grip a second time | transition: `OKL-E-RELEASE-STATE` |
| N19 | Omit the explicit incoming handoff policy | syntax: `OKL-E-SYNTAX` |
| N20 | Stop a dependency before incoming release | transition: `OKL-E-EVENT-CONFLICT` |
| N21 | Prescribed movement targets a dynamic body | admission: `OKL-E-MOTION-MODE` |
| N22 | A dynamic object has no physical representation | elaboration: `OKL-E-PHYSICAL-DOMAIN` |
| N23 | Ordinary spatial following cycle | elaboration: `OKL-E-FOLLOW-CYCLE` |
| N24 | Incompatible attachment site | elaboration: `OKL-E-SITE-INTERFACE` |
| N25 | Unavailable collision capability is requested | support: `OKL-E-CAPABILITY-UNSUPPORTED` |
| N26 | Private method access | binding: `OKL-E-ACCESS` |
| N27 | Assign a derived property | type: `OKL-E-READONLY` |
| N28 | Non-finite numeric literal | elaboration: `OKL-E-NUMERIC` |
| N29 | Restart an already running action | admission: `OKL-E-ACTION-STATE` |
| N30 | Time passed to an angle-only function | type: `OKL-E-UNIT` |
| N31 | Mechanical loop remains unsupported, not cyclic ownership | support: `OKL-E-CAPABILITY-UNSUPPORTED` |

The case IDs beginning with N include unsupported requests as well as invalid source. N25 preserves the capability request as represented data but cannot satisfy an evaluated request in this profile. N31 preserves valid independent ownership and explicit joint records but cannot construct/evaluate the closed mechanism under core support. A future supported profile may give these meaningful requests additional behavior; spelling and type errors do not acquire that exemption.

A timeline preflight may discover a later admission/transition error in advance. It must retain the authored failure phase, time, and causal condition instead of claiming that an action or event actually ran.

### 13.3 Mapping all original semantic checks

Every original semantic check is accounted for below. “Related case” identifies an exact or reduced-language example, not a passed implementation test. Broader scenarios remain explicit where the core cannot express their required mechanics or control.

| SEM check | Core disposition and evidence |
| --- | --- |
| SC-01: Rename a hand | P09 preserves the occurrence key and updates the name plus its uses; LANG-007 and LANG-025 define revision-safe identity. |
| SC-02: Isolate an instance change | P04 uses independently expanded balls and a local radius override; this is the smaller object counterpart of the character case. |
| SC-03: Clone an assembly | Separate source occurrences expand new internal identities and references under LANG-007. Live cloning and automatic external-link policy are deferred; no full SC-03 execution case is claimed. |
| SC-04: Ownership cycle | Finite construction and acyclic ownership are required. N11 checks recursive part expansion, a related structural failure; runtime reparenting cannot be authored in this profile. |
| SC-05: Move an organizational owner | P04 gives the owned dynamic ball no following/joint to its moving owner; its world motion remains independent. |
| SC-06: Apply parent displacement once | P01 exercises transform composition while local coordinates also change. LANG-012/LANG-013 state the unchanged-local-pose special case exactly; P01 is related evidence, not the original isolated 2 m scenario. |
| SC-07: Inspect a dynamic local pose | P04 supplies the local/world round-trip example; local inspection converts the resolved state once. |
| SC-08: Track a world target | Deferred. No tracking or inverse-kinematics action exists in core; a fixed local tween is not reported as tracking. |
| SC-09: Reach conflicts with arm swing | N13 checks the core's same-channel conflict policy. Walking and arm-swing controllers are deferred. |
| SC-10: Equal-priority conflicting targets | N13 checks unresolved overlap. Core has no priorities or implicit target selection. |
| SC-11: Gravity, wind, and motor torque | Only uniform gravity is defined. Wind and motors need additional physical contracts; no combined-force case is claimed. |
| SC-12: Count matter once | P04 counts two separately owned 1 kg bodies and a massless label. The exact 4 kg + 1 kg character layout is a future case. |
| SC-13: Transfer rotational offset velocity | P03 uses the original numerical setup and requires incoming velocity (1,1,0) m/s. |
| SC-14: Release an already dynamic gripped body | Deferred. Core's initial ideal grip carries a prescribed sphere; it cannot establish the dynamic physical grip in this scenario. |
| SC-15: Release one of two grips | Deferred. Multi-grip is unsupported; no operation may claim it released all constraints successfully. |
| SC-16: Discontinuous motion without handoff | LANG-017 requires a finite incoming derivative and defines `OKL-E-HANDOFF`. Discontinuous source trajectories are not in core. N19 checks mandatory handoff syntax only, not the full discontinuous case. |
| SC-17: Limit or drive failure | N14 checks a hard hinge range. Insufficient actuator output requires a future physical-drive contract. |
| SC-18: Falling articulated character | Deferred. Free spheres and mass accounting are specified, but dynamic jointed bodies are not. |
| SC-19: Stop walking while looking continues | P12 checks independent root/local behavior with a continuing reach and retained head angle. Walking and world-target tracking remain deferred. |
| SC-20: Pause, inspect, resume | P05 and agent check A05 require continuing world dynamics and side-effect-free inspection. |
| SC-21: Centimeters versus meters | P08 preserves canonical dimensions; editing a radius is a different revision change. |
| SC-22: Wind on rigid and flexible objects | Deferred. Neither wind nor deformable foliage is supplied by this profile. |
| SC-23: Incompatible hand replacement | N24 checks attachment interface mismatch; A02 checks atomic rejected edits. Automated replacement/adaptation and runtime replacement are deferred. |
| SC-24: Closed mechanical linkage | N31 is syntactically expressible with acyclic ownership; core support rejects the mechanical cycle explicitly. |

The [requirement coverage register](core-v0.1/requirement-coverage.json) separately accounts for all 226 PRD rows and 18 capability rows. Of the PRD rows, 68 have a language-subset treatment, 70 have an agent-contract treatment, and 88 are deferred. Of the capability rows, 14 have a language-subset treatment and four have an agent-contract treatment. These are design dispositions, not percentages of completed implementation. Every addressed requirement remains partial.

### 13.4 Agent-operation cases

A01–A10 in the manifest are protocol scenarios, not additional source programs. They require:

| Case | Required protocol behavior |
| --- | --- |
| A01 | Reject an edit whose expected accepted revision is stale. |
| A02 | Reject an invalid multi-patch candidate atomically and preserve the prior accepted source. |
| A03 | Return the same outcome for the same request identity and canonical payload without duplicate effects. |
| A04 | Reject reuse of a request identity with different payload. |
| A05 | Repeated inspection of the same context returns the same state without advancing time. |
| A06 | Reject or mark stale a continuation whose revision/run/sample/query context changed. |
| A07 | Return unsupported for an unavailable requested level without substituting a lower success. |
| A08 | Report the accepted result if cancellation arrives after commit. |
| A09 | Reconcile unknown outcomes before a deliberate new request; never infer safe replay. |
| A10 | Re-express velocity axes while retaining its world measurement frame; do not label it relative velocity. |

A failed first create or rejected edit uses an immutable candidate `source_revision` for its diagnostics. The accepted-revision precondition and candidate repair coordinates remain separate under LANG-025. This makes the unit-error example inspectable even when no accepted program yet exists.

### 13.5 Numeric comparison and actual editorial checks

The mathematical rules define exact intended behavior over the elaborated constants. A later implementation's outputs for these small bounded fixtures are compared as follows:

| Quantity | Permitted comparison error |
| --- | --- |
| Position | Maximum component absolute error ≤ 10^-9 m |
| Linear velocity | Maximum component absolute error ≤ 10^-9 m/s |
| Angular velocity | Maximum component absolute error ≤ 10^-9 rad/s |
| Orientation | Geodesic rotation-angle error ≤ 10^-9 rad |
| Other scalar quantities | Absolute error ≤ max(10^-12 canonical units, 10^-12 × absolute reference value) |
| Identity, authority, lifecycle, event order, and diagnostic code | Exact match |

For unit quaternions, the orientation error is 2 arccos(min(1, |q_ref · q_result|)) after normalization; equivalent signs have zero error. Mathematically equivalent robust computations are permitted. Componentwise quaternion subtraction is not the orientation metric.

These tolerances apply to the fixture comparisons only. They do not relax type checks, exact canonical source equality, hard bounds, transaction atomicity, or timestamp ordering. They are not a promise of broad scientific accuracy, long-term stability, or real-time performance.

The following October 17, 2026 checks were completed when the original language draft was written, before the engineering prototype began. They remain the record of that drafting work:

- All four base programs and all 43 complete manifest candidates were materialized and checked against the EBNF and explicit lexer. The expected 39 candidates parse; the expected four lexical/syntax negatives reject.
- All 43 grammar productions were checked for undefined references, reachability, productivity, problematic left recursion, and nullable repetition. No such grammar defect was found.
- Every manifest replacement was confirmed to match its target exactly once. Case IDs, declared case counts, and requirement/rule references were checked.
- Independent analytical calculation confirmed the four base motion examples, including rotational velocity transfer, continuing gravity, local/world pose conversion, and aggregate-mass expectations.
- The JSON artifacts were parsed and checked for their stated structure, source IDs, codes, and exact diagnostic UTF-8 spans. No claim of an external JSON Schema implementation's complete metaschema certification is made.
- A separate review checked the normative sections against the examples and closed the identified gaps in initializer binding, nested overrides, mixed relation cycles, numeric projection, and candidate-revision diagnostics.
- The repository's existing preservation checker and the current local links were checked after adding the specification and updating navigation.

**That original drafting task built or executed no OntoKin type checker, compiler, runtime, physics simulation, renderer, or agent service.** Its temporary grammar and equation checks are editorial evidence. The later prototype is recorded in [OK-ENG-001](../engineering/OK-ENG-001-core-reference-implementation-and-conformance-plan.md), with its own execution evidence and limitations. The diagnostic and trajectory expectations above remain the conformance targets.

## 14. Review decisions and the next engineering gate

Version 0.1 supplies one usable written language contract. The twelve choices in section 2.2 are adopted for the engineering baseline in section 16. The questions below remain review criteria for the implementation and for later language revisions.

| Review question | Evidence needed for the engineering baseline |
| --- | --- |
| Does the syntax make local authoring and repair practical? | An agent can write each base fixture from this document alone and explain every declaration. |
| Are identity, inheritance, parts, and overrides predictable? | Renaming, independent instances, exact dispatch, and nested parameter edits have unambiguous outcomes and scope. |
| Are ownership, following, and mechanical connection distinct? | The same program yields one pose authority per instance, no duplicated transforms, and no duplicated matter. |
| Does release transfer the intended state? | P02 and P03 preserve incoming COM pose/velocity/angular velocity; same-time completion and replacement cases have the stated order. |
| Are physical limits honestly reported? | Contact, loads, actuators, deformation, and general body dynamics stay visibly outside the profile; no visual result substitutes for them. |
| Can an agent diagnose and repair failure? | Source and candidate identities, exact spans, stable codes, requested levels, atomic patches, and retry outcomes are sufficient. |
| Is the future conformance target reviewable? | Each case has complete source or an exact protocol setup, expected outcome, tolerances where appropriate, and traceability. |

[OK-ENG-001](../engineering/OK-ENG-001-core-reference-implementation-and-conformance-plan.md) now defines the prototype responsibilities and conformance gates against this contract, including diagnostics, exact event ordering, preserved identities, and declared physical limits.

Potential later profiles must separately settle contacts and numerical tolerances, general rigid-body inertia and torque, dynamic joints and loops, actuator feasibility, capture and multi-grip, tracking and locomotion, deformation, materials/environmental fields, imports/generators, external events, and delivery mappings. Existing product requirements remain the source for that broader scope.

The reference prototype's implementation choices are recorded in OK-ENG-001. They do not select the production compiler, serialized intermediate representation, physics engine, integration method, or rendering engine. Those decisions require evidence from the relevant workload and physical or delivery contract.

## 15. Source review, companion inventory, and references

### 15.1 Repository documentation reviewed

The review used main-branch snapshot `ded52f778418795c6dd523b32cd8470e188d5171`. All 29 tracked files were inventoried. The documentation consisted of two navigation files, six substantive Markdown records, the alternate HTML edition, fifteen diagram/source files representing six figures, and four maintenance/evidence files. The remaining tracked file was repository configuration.

| Source group | Material reviewed and use |
| --- | --- |
| Current product definition | [OK-CAP-001 v0.1](../product/OK-CAP-001-modeling-motion-and-object-structure.md) and [OK-PRD-001 v0.2](../product/OK-PRD-001-product-requirements.md): modeling focus, full requirement register, output-level distinctions, and agent responsibilities |
| Semantic foundation | [OK-SEM-001 v0.1](OK-SEM-001-core-object-motion-and-physics-semantics.md): all 28 proposed rules, all 24 semantic checks, worked examples, open decisions, and traceability |
| Founding records | [OK-001](foundations/OK-001-project-vision-and-architecture.md), [OK-002](foundations/OK-002-language-foundations-and-minimal-specification.md), and [OK-003](foundations/OK-003-compilation-and-runtime-architecture.md): original language sketches, rationale, alternatives, decision registers, and architecture proposals |
| Alternate format and figures | [OK-003 HTML](foundations/OK-003-compilation-and-runtime-architecture.html) and all files in [diagrams](foundations/diagrams/): six PNG, six SVG, and three DOT sources |
| Navigation and preservation | Root overview, [documentation guide](../README.md), and the four files in [reorganization evidence](../maintenance/reorganization-2026-10-17/): retained navigation, source map, record, and verification procedure |

The earlier substantive records and historical evidence retain their contents and statuses. Current navigation points to this formal specification and the subsequent engineering work. A reference to an earlier syntax or architecture choice is read in its original proposed context, not silently promoted into this core.

### 15.2 Companion artifacts

| File | Normative role |
| --- | --- |
| [ontokin-core.ebnf](core-v0.1/ontokin-core.ebnf) | Complete syntactic productions, with lexical terminals defined in section 4 |
| [01-independent-parts.ok](core-v0.1/01-independent-parts.ok) | P01 source |
| [02-gravity-and-release.ok](core-v0.1/02-gravity-and-release.ok) | P02 source |
| [03-rotating-release.ok](core-v0.1/03-rotating-release.ok) | P03 source |
| [04-ownership-reuse-and-follow.ok](core-v0.1/04-ownership-reuse-and-follow.ok) | P04 source |
| [validation-cases.json](core-v0.1/validation-cases.json) | Twelve valid, 29 invalid/conflicting, and two unsupported expected source cases; ten agent-operation cases |
| [diagnostic.schema.json](core-v0.1/diagnostic.schema.json) | JSON shape for an individual structured diagnostic |
| [diagnostic-example.json](core-v0.1/diagnostic-example.json) | Explicitly synthetic unit-error diagnostic with exact source and repair spans |
| [requirement-coverage.json](core-v0.1/requirement-coverage.json) | Complete PRD/CAP design-disposition register; no implementation-completion claim |

### 15.3 External mathematical background and task authority

External references support the mathematical conventions; they do not supply OntoKin syntax, choose an engine, or establish product approval.

**[T1]** Kevin M. Lynch and Frank C. Park, *Modern Robotics*, [3.3.1: Homogeneous Transformation Matrices](https://modernrobotics.northwestern.edu/nu-gm-book-resource/3-3-1-homogeneous-transformation-matrices/). Primary educational material for rigid-transform notation, composition, and inverse transforms.

**[T2]** Drake project, [SpatialVelocity class documentation](https://drake.mit.edu/doxygen_cxx/classdrake_1_1multibody_1_1_spatial_velocity.html). Primary technical documentation distinguishing a spatial velocity's measurement frame, expressed-in axes, and reference point, including velocity shifts between points. Citing this mathematical reference does not select Drake.

**[T3]** Oracle, *Numerical Computation Guide*, [IEEE Arithmetic](https://docs.oracle.com/cd/E19957-01/806-3568/ncg_math.html). Primary technical reference for binary64 representation and rounding concepts. This specification states its own source and semantic-trajectory contract.

**[U1]** Project owner task, October 17, 2026: examine the documentation; review the 28 SEM rules against product requirements; define minimum language scope and precise source, types, objects, mechanics, physical behavior, actions, time, and agent operations; create valid/invalid programs with expected behavior and traceability. Begin with independent parts and gravity/release. Leave compiler, physics-engine, and renderer choices for later requirements-driven work.

## 16. Engineering baseline adoption and clarifications

### 16.1 Adoption and version boundary

The owner's subsequent October 17, 2026 instruction authorizes moving from this written specification to the first working prototype: finalize the twelve core decisions, build a parser and validator, evaluate headless motion and release, and execute the four programs and 43 source cases. That instruction supplies the authority for this engineering adoption. No additional approval of the earlier product or founding proposals is inferred.

Language version `0.1`, profile `core-0.1`, stable rule IDs, grammar, source fixtures, and expected case outcomes are retained. The document's `engineering_baseline: 2026-10-17` field identifies this adoption. The pre-engineering repository snapshot is `1a9a52a7eedf4170d864c0d37d0f32ae69bf9a69`; its Git history preserves the original proposed draft. The `repository_snapshot` field near the beginning remains the earlier source-review basis for that draft, rather than being relabeled as implementation evidence.

| Decisions adopted | Consequence for this baseline |
| --- | --- |
| D-01, D-02, D-03 | Preserve the declared source form, nominal single inheritance, exact overrides, and separation of pure construction from timeline effects. |
| D-04, D-05 | Preserve checked numeric and unit rules, proper rotations, explicit frames, and the specified mathematical trajectories. Fixture tolerances do not weaken canonical arithmetic or exact event ordering. |
| D-06, D-07, D-08, D-09 | Preserve exclusive channels, prescribed joints, the limited uniform-sphere model, complete incoming-state release, and ordered event transactions. |
| D-10 | Keep the finite single-module scope; no host execution or hidden extension loading enters ordinary source evaluation. |
| D-11 | Adopt the revision-safe agent-editing contract as a required future service contract. A file-based prototype does not establish service, retry, cancellation, or edit-transaction conformance. |
| D-12 | Publish measured support separately from language and product requirements. Passing the finite source corpus establishes evidence for that corpus and its additional checked observations. |

### 16.2 Clarifications made for execution

| ID | Original ambiguity or reporting issue | Baseline treatment |
| --- | --- | --- |
| C-01 | Section 10.3's general action-argument domain wording could place an out-of-range tween target in elaboration, while N14 requires admission. | Section 10.3 now separates scalar/type/frame/duration checks from target-joint range admission. N14 retains `admission` and `OKL-E-JOINT-LIMIT`; no expected result is changed to accommodate an implementation. |
| C-02 | Original fixture and coverage metadata say no implementation or conformance execution exists. | Those files remain the original design record and expected-outcome register. Current implementation evidence is the separate versioned engineering report. Their historical Boolean/status fields must not be read as current repository status. |
| C-03 | The written agent-operation contract could be mistaken for an implemented service when a CLI is added. | The prototype exposes documented file-based operations. A01–A10 remain separately tracked protocol scenarios; overlapping local checks do not certify the full service contract. |
| C-04 | Passing the small numerical examples could be mistaken for proof of all normative arithmetic behavior. | Correct rounding of static mathematical functions, exact represented rotations, finite-interval guarantees, and full-range behavior retain their normative meanings. The prototype must disclose any unproved support instead of claiming universal arithmetic conformance. |

The original PRD/CAP requirement coverage, all SEM rules and checks, founding documents, alternate editions, diagrams, and reorganization evidence retain their substantive content. The engineering plan adds implementation decisions and measurements without using the earlier preservation task as authority to revise language behavior.

