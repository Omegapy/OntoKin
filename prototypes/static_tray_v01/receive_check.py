"""Compare actual receiving observations with independent decoded GLB evidence.

The reference must already have passed the separately authored geometry reader.
This comparator accepts coincident normal splits by measured corner identity,
while retaining oriented surfaces, actual dimensions, relationships and material
values. It imports no producer geometry, source lowerer or native constructor.
"""

from collections import Counter, defaultdict
from fractions import Fraction
from itertools import product
import math


DELTA = 0.000005
MATRIX_DELTA = 0.000001


def _safe(value):
    if isinstance(value,float) and not math.isfinite(value):
        return repr(value)
    if isinstance(value,dict):
        return {str(k):_safe(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):
        return [_safe(v) for v in value]
    return value


def _number(value):
    if type(value) not in (int,float):
        raise ValueError("Numeric observation has wrong type")
    try:
        valid=math.isfinite(value)
    except OverflowError:
        valid=False
    if not valid:
        raise ValueError("Numeric observation is nonfinite")
    return value


def _vertices(value):
    if not isinstance(value,list) or not 1<=len(value)<=256:
        raise ValueError("Measured vertex inventory is missing or out of bounds")
    rows=[]
    for row in value:
        if not isinstance(row,(list,tuple)) or len(row)!=3:
            raise ValueError("Measured vertex must have exactly three coordinates")
        rows.append(tuple(_number(v) for v in row))
    return rows


def _matrix(value):
    if not isinstance(value,list) or len(value)!=4:
        raise ValueError("Measured world matrix must have four rows")
    rows=[]
    for row in value:
        if not isinstance(row,(list,tuple)) or len(row)!=4:
            raise ValueError("Measured matrix row must have four values")
        rows.append(tuple(_number(v) for v in row))
    return rows


def _cycle(values):
    a,b,c=values
    return min((a,b,c),(b,c,a),(c,a,b))


def _dot(a,b):
    return sum(x*y for x,y in zip(a,b))


def _cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])


class _Checks:
    def __init__(self):
        self.findings=[]
        self.measurements=[]

    def flag(self,stage,name,reason):
        item={"stage":stage,"semantic_id":name,"code":"RECEIVING","reason":reason}
        if item not in self.findings:
            self.findings.append(item)

    def exact(self,stage,name,label,actual,expected):
        passed=actual==expected
        self.measurements.append({"stage":stage,"semantic_id":name,"name":label,
                                  "comparison":"exact","measured":_safe(actual),
                                  "expected":_safe(expected),"passed":passed})
        if not passed:
            self.flag(stage,name,label+" differs")
        return passed

    def near(self,stage,name,label,actual,expected,threshold=DELTA):
        _number(actual)
        _number(expected)
        difference=actual-expected
        passed=abs(difference)<=threshold
        self.measurements.append({"stage":stage,"semantic_id":name,"name":label,
                                  "comparison":"absolute_difference","measured":actual,
                                  "expected":expected,"difference":difference,
                                  "threshold":threshold,"passed":passed})
        if not passed:
            self.flag(stage,name,label+" exceeds its unchanged receiving allowance")
        return passed


def _matrices(actual,reference,stage,name,checks):
    actual,reference=_matrix(actual),_matrix(reference)
    for i in range(4):
        for j in range(4):
            tolerance=DELTA if j==3 and i<3 else MATRIX_DELTA
            checks.near(stage,name,"world_matrix_"+str(i)+"_"+str(j),actual[i][j],reference[i][j],tolerance)
    for i in range(3):
        for j in range(3):
            checks.near(stage,name,"rigid_row_dot_"+str(i)+"_"+str(j),
                        _dot(actual[i][:3],actual[j][:3]),int(i==j),MATRIX_DELTA)
    checks.near(stage,name,"rigid_determinant",_dot(actual[0][:3],_cross(actual[1][:3],actual[2][:3])),1,MATRIX_DELTA)


def _reference_corners(vertices):
    minimum=tuple(min(v[k] for v in vertices) for k in range(3))
    maximum=tuple(max(v[k] for v in vertices) for k in range(3))
    if any(lo>=hi for lo,hi in zip(minimum,maximum)):
        raise ValueError("Reference world box has a nonpositive dimension")
    labels=list(product((0,1),repeat=3))
    candidate=[tuple(maximum[k] if label[k] else minimum[k] for k in range(3)) for label in labels]
    assigned=[]
    buckets=defaultdict(list)
    for vertex in vertices:
        matching=[i for i,corner in enumerate(candidate) if max(abs(a-b) for a,b in zip(vertex,corner))<=DELTA]
        if len(matching)!=1:
            raise ValueError("Passed reference has an ambiguous measured world corner")
        assigned.append(matching[0])
        buckets[matching[0]].append(vertex)
    if set(buckets)!=set(range(8)):
        raise ValueError("Reference does not contain all eight measured corners")
    representatives=[min(buckets[i]) for i in range(8)]
    for i,vertices in buckets.items():
        if any(max(abs(a-b) for a,b in zip(v,representatives[i]))>DELTA for v in vertices):
            raise ValueError("Reference normal split exceeds the fixed corner allowance")
    return assigned,representatives,minimum,maximum


def _triangles(triangles,labels,vertex_count):
    if not isinstance(triangles,list) or len(triangles)!=12:
        raise ValueError("Receiving box must expose exactly twelve actual triangles")
    counts=Counter()
    used=set()
    for triangle in triangles:
        if not isinstance(triangle,(list,tuple)) or len(triangle)!=3:
            raise ValueError("Malformed receiving triangle")
        if any(type(i) is not int or not 0<=i<vertex_count for i in triangle):
            raise ValueError("Receiving triangle index out of bounds")
        assigned=tuple(labels[i] for i in triangle)
        if len(set(assigned))!=3:
            raise ValueError("Receiving triangle is degenerate after measured welding")
        counts[_cycle(assigned)]+=1
        used.update(triangle)
    if used!=set(range(vertex_count)):
        raise ValueError("Receiving mesh contains an unreferenced actual vertex")
    return counts


def _counter_rows(counts):
    return [{"corners":list(key),"multiplicity":value} for key,value in sorted(counts.items())]


def _volume(vertices,triangles):
    rational=[tuple(Fraction(v) for v in point) for point in vertices]
    return sum(_dot(rational[a],_cross(rational[b],rational[c]))/6 for a,b,c in triangles)


def _mesh(actual,reference,stage,name,checks):
    if "world_vertices" not in reference:
        checks.exact(stage,name,"empty_root_geometry", "world_vertices" in actual,False)
        checks.exact(stage,name,"empty_root_triangles", "triangles" in actual,False)
        checks.exact(stage,name,"empty_root_material", "material" in actual,False)
        return
    if "world_vertices" not in actual:
        raise ValueError("Receiving mesh is missing")
    material=actual.get("material")
    if not isinstance(material,dict):
        raise ValueError("Receiving material is missing")
    if set(material)!=set(reference["material"]):
        checks.flag(stage,name,"Receiving material fields differ")
    for key in ("baseColorFactor","metallicFactor","roughnessFactor"):
        value=material.get(key)
        if key=="baseColorFactor":
            if not isinstance(value,list) or len(value)!=4:
                raise ValueError("Receiving material color is malformed")
            for v in value:
                _number(v)
        else:
            _number(value)
    checks.exact(stage,name,"fixed_material",material,reference["material"])
    observed=_vertices(actual["world_vertices"])
    delivered=_vertices(reference["world_vertices"])
    reference_labels,corners,refmin,refmax=_reference_corners(delivered)
    actual_labels=[]
    for vi,vertex in enumerate(observed):
        matching=[i for i,point in enumerate(corners) if max(abs(vertex[k]-point[k]) for k in range(3))<=DELTA]
        if len(matching)!=1:
            checks.flag(stage,name,"Measured vertex does not match exactly one retained world corner")
            label=min(range(8),key=lambda i:max(abs(vertex[k]-corners[i][k]) for k in range(3)))
            actual_labels.append(None)
        else:
            label=matching[0]
            actual_labels.append(label)
        for axis in range(3):
            checks.near(stage,name,"vertex_"+str(vi)+"_axis_"+str(axis),vertex[axis],corners[label][axis])
    checks.exact(stage,name,"complete_corner_inventory",sorted({v for v in actual_labels if v is not None}),list(range(8)))
    actual_min=tuple(min(v[k] for v in observed) for k in range(3))
    actual_max=tuple(max(v[k] for v in observed) for k in range(3))
    for axis in range(3):
        checks.near(stage,name,"world_min_"+str(axis),actual_min[axis],refmin[axis])
        checks.near(stage,name,"world_max_"+str(axis),actual_max[axis],refmax[axis])
        checks.near(stage,name,"world_full_side_"+str(axis),actual_max[axis]-actual_min[axis],refmax[axis]-refmin[axis])
    if None in actual_labels:
        return
    indices=reference.get("indices")
    if not isinstance(indices,list) or len(indices)!=36:
        raise ValueError("Passed independent reference lacks its actual triangle indices")
    reftris=[indices[i:i+3] for i in range(0,36,3)]
    expected_triangles=_triangles(reftris,reference_labels,len(delivered))
    actual_triangles=_triangles(actual.get("triangles"),actual_labels,len(observed))
    checks.exact(stage,name,"oriented_triangle_surfaces",_counter_rows(actual_triangles),_counter_rows(expected_triangles))
    volume=_volume(observed,actual["triangles"])
    checks.exact(stage,name,"positive_signed_volume",volume>0,True)
    bounds=reference.get("bounds",{})
    target=_number(bounds.get("expected_volume_m3"))
    allowance=_number(bounds.get("volume_allowance_m3"))
    if allowance<0:
        raise ValueError("Invalid independent volume allowance")
    checks.near(stage,name,"signed_volume_m3",float(volume),target,allowance)


def compare(observations,audit):
    checks=_Checks()
    compared=[]
    try:
        if not isinstance(audit,dict) or audit.get("passed") is not True or not isinstance(audit.get("nodes"),dict):
            raise ValueError("Receiving comparison requires a passed independent geometry audit")
        expected=audit["nodes"]
        if len(expected)!=14:
            raise ValueError("Independent reference does not contain fourteen qualified nodes")
        if not isinstance(observations,dict):
            raise ValueError("Receiving observations must be an object")
        checks.exact("receipt","","schema",observations.get("schema"),"ontokin.static-tray.receiving-observations/0.1.0")
        checks.exact("receipt","","blender_version",observations.get("blender_version"),[4,5,3])
        checks.exact("receipt","","build_hash",observations.get("build_hash"),"67807e1800cc")
        for stage in ("native_scene","imported_glb"):
            scene=observations.get(stage)
            if not isinstance(scene,dict) or not isinstance(scene.get("nodes"),dict):
                checks.flag(stage,"","Actual receiving stage is missing")
                continue
            measured=scene["nodes"]
            compared.append(stage)
            checks.exact(stage,"","physics_world",scene.get("physics_world"),False)
            checks.exact(stage,"","measurement_frame",scene.get("measurement_frame"),"source-rh-y-up-metres")
            checks.exact(stage,"","object_count",scene.get("object_count"),14)
            checks.exact(stage,"","object_identity_inventory",sorted(measured),sorted(expected))
            for name in sorted(set(measured)&set(expected)):
                actual,reference=measured[name],expected[name]
                try:
                    if not isinstance(actual,dict):
                        raise ValueError("Receiving node observation is malformed")
                    checks.exact(stage,name,"name",actual.get("name"),name)
                    checks.exact(stage,name,"identity_role_relationships",actual.get("extras"),reference["extras"])
                    checks.exact(stage,name,"children",actual.get("children"),sorted(reference["children"]))
                    expected_parent=None if reference["extras"]["role"]=="tray-root" else "/".join(reference["extras"]["owner_id"])
                    checks.exact(stage,name,"parent",actual.get("parent"),expected_parent)
                    _matrices(actual.get("world_matrix"),reference["world_matrix"],stage,name,checks)
                    _mesh(actual,reference,stage,name,checks)
                except (ValueError,TypeError,KeyError,IndexError,OverflowError) as exc:
                    checks.flag(stage,name,str(exc))
    except (ValueError,TypeError,KeyError,IndexError,OverflowError) as exc:
        checks.flag("receipt","",str(exc))
    return {"schema":"ontokin.static-tray.receiving-check/0.1.0","passed":not checks.findings,
            "findings":sorted(checks.findings,key=lambda row:(row["stage"],row["semantic_id"],row["code"],row["reason"])),
            "measurements":sorted(checks.measurements,key=lambda row:(row["stage"],row["semantic_id"],row["name"])),
            "geometry_tolerance_m":DELTA,"matrix_tolerance":MATRIX_DELTA,
            "compared_native_scene":"native_scene" in compared,
            "compared_imported_glb":"imported_glb" in compared,
            "scope":"Actual receiving observations versus passed independent GLB geometry; visual review remains separate"}
