# C260 field origins and association limits

The [contract](CONTRACT.md) observes declaration metadata. Source values and
artifact claims are separate inputs. Every future source observation must
retain the actual filename, SHA-256 and integer UTF-8 byte interval
`[startByte, endByteExclusive)`. Every artifact claim must retain the actual
artifact SHA-256 and JSON pointer. Association does not turn an absent direct
artifact field into an observation.

## Field mapping

| Field | Independent source origin | Actual GLB origin and limit |
| --- | --- | --- |
| Hinge occurrence ID | Owning root/ordinary/generated occurrence keys plus the joint's literal member key | `/extras/ontokin/joints/i/element_id`; compared as a complete array |
| Hinge display path | Actual lexical occurrence/member names and correctly quoted keyed steps | `/extras/ontokin/joints/i/path`; not sufficient without full identity/class association |
| Hinge definition ID | Owning class definition identity plus joint key | No direct field; source-derived association through the mapped owning object/class and joint key |
| Hinge declaration span | Full actual `joint ... : hinge { ... }` byte span | Absent; object spans cannot be relabeled joint spans |
| Hinge kind | Actual declaration type token `hinge` | `/extras/ontokin/joints/i/kind` |
| Parent endpoint | Actual `parent` expression, lexical member/part/site lookup, terminal site key and defining class | `/extras/ontokin/joints/i/parent_site`, a path claim only |
| Child endpoint | Actual `child` expression and its separate lexical part/site lookup | `/extras/ontokin/joints/i/child_site`, a path claim only; do not reorder endpoints |
| Endpoint owning object IDs | The source occurrences on which the resolved sites are declared | Object node `path`, `element_id`, `class_name`, `source_mapping` and corresponding program occurrence claims |
| Endpoint site occurrence IDs | Actual endpoint object ID plus the terminal site's literal key | Absent as direct site IDs; associate the actual endpoint path with the independently derived site map |
| Endpoint site definition IDs/spans | Declaring source class identity, site key and site declaration bytes | Absent; no site table exists in either bound artifact |
| Endpoint interface/size | Literal site `interface` and `size`, checked for equal interface and canonical nonnegative size | Absent; retain as source-only compatibility facts |
| Endpoint site pose | The source `pose` assignment byte witness only | No direct site-pose field; value/frame/orientation are unobserved in this profile |
| Axis components | Three literal numeric tokens in the actual `vec3` expression, admitted signed-basis subset | `/extras/ontokin/joints/i/axis`; preserve sign and compare exact canonical components |
| Axis reference frame | Adopted hinge convention: the resolved **parent site's** axes | No separate axis-frame field; it is not inferred from node/world rotation |
| Lower and upper limits | The two ordered actual Angle literals in `range`, their signs and deg/rad factors | `/extras/ontokin/joints/i/limits/0` and `/1`, canonical radians |
| Initial coordinate | The actual initial Angle literal and unit factor | `/extras/ontokin/joints/i/initial`, canonical radians; not an animation sample |
| Source/program identity | Actual bytes, exact import digest and independently constructed canonical bundle manifest/revision | `/extras/ontokin/source`, `/extras/ontokin/program` and all repeated node/source-map claims |

Ownership, following, scene-root indices, node transforms, animation channels,
producer sidecars and C255 expected records are not origins for any hinge
value. Occurrence containment is used to identify where a declaration is
instantiated; it does not create a mechanical relationship by itself.

## Concrete frozen association

The source defines one `Finger.flex` hinge member and instantiates it three
times under `first` and five times under `second`. The same definition is
therefore associated with eight distinct hinge occurrences. The selected
middle finger's length edit changes neither this member nor its literal
hinge fields.

| Concept | Original first middle finger |
| --- | --- |
| Owning object occurrence | `["keyed-rack","demo","first","fingers","middle"]` |
| Joint occurrence | `["keyed-rack","demo","first","fingers","middle","flex"]` |
| Joint definition | `["package","example.hinges","hinges","definitions","finger","flex"]` |
| Parent site occurrence | `["keyed-rack","demo","first","fingers","middle","pivot"]` |
| Parent site definition | `["package","example.hinges","hinges","definitions","finger","pivot"]` |
| Child site occurrence | `["keyed-rack","demo","first","fingers","middle","blade","base"]` |
| Child site definition | `["package","example.hinges","hinges","definitions","blade","base"]` |
| Actual artifact row | `/extras/ontokin/joints/1` in each original artifact |
| Parent/child path claims | `first.fingers["middle"].pivot` and `first.fingers["middle"].blade.base` |
| Axis/limits/initial | `[0,0,1]` in parent-site axes; `[-0.7853981633974483,0.7853981633974483]` radians; `0` radians |

The row index is an observed location, not an identity rule. Reordering rows
changes pointers while retaining identities. All sixteen endpoint site
occurrences are source-associated; none is an embedded GLB site record.

[BASELINE-INSPECTION.json](BASELINE-INSPECTION.json) retains the actual source
witnesses, the manually derived eight occurrence/definition associations and
every actual joint row from each bound GLB. Its fixed-input inspection is
evidence for designing the contract. A future implementation must derive
changed source values independently instead of loading this baseline as an
answer table.
