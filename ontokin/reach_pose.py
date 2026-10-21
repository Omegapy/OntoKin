"""Controlled source pose arithmetic for the explicitly adopted reach profile.

Private rotations are projective 96-bit dyadic quaternions. Composition never
feeds an exposed binary64 quaternion back into the chain. Homogeneous rotation
is a proper rotation even when the private quaternion is not exactly unit.
No host trigonometric function, float square root or preparation oracle is used.
The uniform derivation is in docs/engineering/reach-numeric-kernel.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction as F
from hashlib import sha256
from pathlib import Path

from .reach_numeric import (
    PRECISIONS, DyadicContext, ReachAdmissionError, ReachExecutionWork,
    compare, exact, rational, round_binary64, round_dyadic,
    sqrt_rational_binary64,
)

METHOD = "ontokin.source-pose-projective-dyadic/0.1"
BITS = 96
RHO = F(1,1 << 97)
VECTOR_ERROR = F(1,1 << 96)
PRODUCT_ERROR = F(1,1 << 91)
TRIG_ERROR = F(1,1 << 80)
AXIS_ERROR = F(1,1 << 74)
EXPOSED_ROTATION_ERROR = F(1,1 << 50)
ARGUMENT_ERROR = F(1,1 << 86)
_HORNER_TERMS = 13
ZERO = (F(0),F(0),F(0))
UNIT = (F(1),F(0),F(0),F(0))


@dataclass(frozen=True)
class RotationValue:
    components: tuple[F,F,F,F]
    error_rad: F = F(0)
    # Only materialized event anchors preserve an already exposed quaternion.
    frozen_projection: tuple[float,float,float,float] | None = None


@dataclass(frozen=True)
class SpinPlan:
    scaled_omega: tuple[F,F,F]
    maximum: F
    norm_bounds: tuple[F,F]
    pi_bounds: tuple[F,F]
    max_elapsed_s: F
    precision_bits: int
    argument_error_rad: F


@dataclass(frozen=True)
class SourceNumericBasis:
    name: str
    version: str
    implementation: str
    method: str
    derivation: str
    inputs: tuple[tuple[str,str],...]

    def as_dict(self):
        return {"name":self.name,"version":self.version,
                "implementation":self.implementation,"method":self.method,
                "derivation":self.derivation}


@dataclass(frozen=True)
class PoseValue:
    exact_position: tuple[F,F,F]
    rotation: RotationValue
    exact_velocity: tuple[F,F,F]
    exact_omega: tuple[F,F,F]
    position_error_m: F
    _ops: ReachPoseOps = field(repr=False,compare=False)
    _projection: dict = field(default_factory=dict,repr=False,compare=False)

    def __deepcopy__(self,memo):
        # Arithmetic state is immutable; the memoized projections do not alter
        # its value. In particular never copy a request callback/compiler.
        memo[id(self)]=self
        return self

    @property
    def position(self): return self._ops._expose(self,"position")

    @property
    def orientation(self): return self._ops._expose(self,"orientation")

    @property
    def velocity(self): return self._ops._expose(self,"velocity")

    @property
    def omega(self): return self._ops._expose(self,"omega")

    @property
    def angular_error_rad(self): return self.rotation.error_rad


class ReachPoseOps:
    """One request's deterministic pose helpers and auditable error bounds."""
    def __init__(self,work: ReachExecutionWork):
        self.work=work

    def _op(self,a,b,kind): return exact(a,b,kind,self.work)

    def _sum(self,values):
        result=F(0)
        for value in values: result=self._op(result,value,"add")
        return result

    def _vector(self,values,length=3):
        self.work.charge("pose_vector_domain")
        if not isinstance(values,(list,tuple)) or len(values)!=length:
            raise ReachAdmissionError("reach_numeric","A pose vector has the wrong dimension.")
        # Private Fraction tuples are already exact. Checking their bounded
        # representation does not require decoding each component again.
        if isinstance(values,tuple) and all(type(value) is F for value in values):
            self.work.guard(*values)
            return values
        return tuple(rational(value,self.work) for value in values)

    def _rounded_vector(self,values):
        self.work.charge("pose_grid_check")
        values=tuple(values)
        self.work.guard(*values)
        on_grid=tuple(value.denominator.bit_length()<=BITS+1 and
                      value.denominator & (value.denominator-1)==0 for value in values)
        if all(on_grid):
            return values
        return tuple(value if ready else round_dyadic(value,BITS,work=self.work)
                     for value,ready in zip(values,on_grid))

    def _l1(self,values):
        self.work.charge("pose_norm_bound",len(values))
        return self._sum(abs(value) for value in values)

    def add(self,a,b):
        a,b=self._vector(a),self._vector(b)
        return self._add_exact_vectors(a,b)

    def _add_exact_vectors(self,a,b):
        """Add already validated private three-vectors without decoding again."""
        self.work.charge("pose_add_zero_check")
        if not any(a): return b
        if not any(b): return a
        return tuple(y if not x else x if not y else self._op(x,y,"add")
                     for x,y in zip(a,b))

    def scale(self,vector,factor):
        vector,factor=self._vector(vector),rational(factor,self.work)
        self.work.charge("pose_scale_identity_check")
        if not factor or not any(vector): return ZERO
        if factor==1: return vector
        return tuple(self._op(value,factor,"mul") for value in vector)

    def cross(self,a,b):
        a,b=self._vector(a),self._vector(b)
        self.work.charge("pose_cross_zero_check")
        if not any(a) or not any(b): return ZERO
        return tuple(self._op(self._op(a[j],b[k],"mul"),self._op(a[k],b[j],"mul"),"sub")
                     for j,k in ((1,2),(2,0),(0,1)))

    def affine(self,initial,rate,elapsed):
        return self.add(initial,self.scale(rate,rational(elapsed,self.work)))

    def parabolic(self,initial,velocity,acceleration,elapsed):
        elapsed=rational(elapsed,self.work)
        half_square=self._op(self._op(elapsed,elapsed,"mul"),F(2),"div")
        return self.add(self.affine(initial,velocity,elapsed),self.scale(acceleration,half_square))

    def _rotation(self,value):
        if isinstance(value,RotationValue):
            self.work.charge("pose_rotation_reference")
            self.work.guard(*value.components,value.error_rad)
            return value
        values=self._vector(value,4)
        key=(METHOD,"constant_rotation",values)
        cached=self.work.lookup(key)
        if cached is not None: return cached
        result=self._rescale(values,F(0))
        self.work.remember(key,result)
        return result

    def _rescale(self,values,error):
        self.work.charge("quaternion_rescale",5)
        self.work.guard(*values,error)
        maximum=max(abs(value) for value in values)
        if not maximum:
            raise ReachAdmissionError("reach_numeric","A zero quaternion cannot represent a rotation.")
        # Exact power-of-two scaling leaves the represented rotation unchanged.
        exponent=maximum.numerator.bit_length()-maximum.denominator.bit_length()
        self.work.guard_bits(max(maximum.numerator.bit_length()+max(-exponent,0),
                                 maximum.denominator.bit_length()+max(exponent,0))+2)
        below=(maximum.numerator < maximum.denominator << exponent) if exponent>=0 else (
            maximum.numerator << -exponent < maximum.denominator)
        if below: exponent-=1
        shift=-exponent-1
        self.work.guard_bits(abs(shift)+2)
        if shift==0:
            result=self._rounded_vector(values)
        else:
            factor=F(1 << shift) if shift>=0 else F(1,1 << -shift)
            result=self._rounded_vector(self._op(value,factor,"mul") for value in values)
        self.work.charge("quaternion_sign",4)
        if next(value for value in result if value)<0: result=tuple(-value for value in result)
        return RotationValue(result,self._op(error,PRODUCT_ERROR,"add"))

    def multiply(self,a,b):
        a,b=self._rotation(a),self._rotation(b)
        # Different source objects can compose the same private rotations.
        # The complete mathematical operands include their error allowances;
        # materialized public projections do not enter the Hamilton product.
        key=(METHOD,"rotation_product",a.components,b.components,a.error_rad,b.error_rad)
        cached=self.work.lookup(key)
        if cached is not None: return cached
        result=self._multiply_uncached(a,b)
        self.work.remember(key,result)
        return result

    def _power_two_scalar(self,value):
        self.work.charge("quaternion_scalar_scale_check")
        if type(value) is not F or not value:
            return False
        numerator,denominator=abs(value.numerator),value.denominator
        return not (numerator & (numerator-1) or denominator & (denominator-1))

    def _scaled_identity_product(self,components,error):
        # Multiplication by a signed power of two is exactly undone by the
        # ordinary scale/sign canonicalization. Reuse an already canonical
        # grid tuple, or apply that same rescale to the unmultiplied operand.
        self.work.charge("quaternion_identity_canonical_check")
        if (isinstance(components,tuple) and all(type(value) is F for value in components) and
                F(1,2)<=max(map(abs,components))<1 and next(value for value in components if value)>0):
            self.work.charge("quaternion_identity_grid_check",4)
            if all(value.denominator.bit_length()<=BITS+1 and
                   value.denominator & (value.denominator-1)==0 for value in components):
                return RotationValue(components,self._op(error,PRODUCT_ERROR,"add"))
        return self._rescale(components,error)

    def _multiply_uncached(self,a,b):
        aw,ax,ay,az=a.components; bw,bx,by,bz=b.components
        mul=lambda x,y:self._op(x,y,"mul")
        self.work.charge("quaternion_sparse_check")
        error=self._op(a.error_rad,b.error_rad,"add")
        # A signed power-of-two scalar disappears under the same exact
        # rescale/sign operation. Other scalar scales retain the full product.
        if not any((bx,by,bz)):
            if all(type(value) is F for value in a.components) and self._power_two_scalar(bw):
                return self._scaled_identity_product(a.components,error)
            return self._rescale(tuple(mul(value,bw) for value in a.components),error)
        if not any((ax,ay,az)):
            if all(type(value) is F for value in b.components) and self._power_two_scalar(aw):
                return self._scaled_identity_product(b.components,error)
            return self._rescale(tuple(mul(aw,value) for value in b.components),error)
        if not any((ax,ay,bx,by)):
            return self._rescale((self._op(mul(aw,bw),mul(az,bz),"sub"),F(0),F(0),
                                  self._op(mul(aw,bz),mul(az,bw),"add")),error)
        self.work.charge("quaternion_signed_terms",6)
        values=(self._sum((mul(aw,bw),-mul(ax,bx),-mul(ay,by),-mul(az,bz))),
                self._sum((mul(aw,bx),mul(ax,bw),mul(ay,bz),-mul(az,by))),
                self._sum((mul(aw,by),-mul(ax,bz),mul(ay,bw),mul(az,bx))),
                self._sum((mul(aw,bz),mul(ax,by),-mul(ay,bx),mul(az,bw))))
        return self._rescale(values,error)

    def inverse_rotation(self,value):
        value=self._rotation(value)
        self.work.charge("quaternion_conjugate",3)
        q=value.components
        return RotationValue((q[0],-q[1],-q[2],-q[3]),value.error_rad)

    def rotate(self,rotation,vector):
        rotation,vector=self._rotation(rotation),self._vector(vector)
        q=rotation.components
        self.work.charge("rotation_sparse_check")
        if not any(vector): return ZERO
        if not any(q[1:]): return self._rounded_vector(vector)
        active=tuple(index for index,value in enumerate(q[1:]) if value)
        axis=(active[0] if len(active)==1 and all(type(value) is F for value in q) else None)
        if axis is not None:
            first,second=(axis+1)%3,(axis+2)%3
            # A vector on the sole quaternion axis is fixed exactly. It still
            # receives the same final grid projection as the full matrix path.
            if not vector[first] and not vector[second]:
                return self._rounded_vector(vector)
        result_key=(METHOD,"rotated_vector",q,vector)
        cached=self.work.lookup(result_key)
        if cached is not None: return cached
        if axis is not None:
            key=(METHOD,"axis_rotation_factors",q)
            factors=self.work.lookup(key)
            if factors is None:
                w,z=q[0],q[axis+1]
                w2,z2=self._op(w,w,"mul"),self._op(z,z,"mul")
                denominator=self._op(w2,z2,"add")
                diagonal=self._op(self._op(w2,z2,"sub"),denominator,"div")
                cross=self._op(self._op(self._op(F(2),w,"mul"),z,"mul"),denominator,"div")
                factors=(diagonal,cross)
                self.work.remember(key,factors)
            diagonal,cross=factors
            u,v=vector[first],vector[second]
            if not v:
                out_u,out_v=self._op(diagonal,u,"mul"),self._op(cross,u,"mul")
            elif not u:
                self.work.charge("rotation_axis_sign")
                out_u,out_v=-self._op(cross,v,"mul"),self._op(diagonal,v,"mul")
            else:
                out_u=self._op(self._op(diagonal,u,"mul"),self._op(cross,v,"mul"),"sub")
                out_v=self._op(self._op(cross,u,"mul"),self._op(diagonal,v,"mul"),"add")
            values=list(vector)
            values[first],values[second]=out_u,out_v
            result=self._rounded_vector(values)
            self.work.remember(result_key,result)
            return result
        key=(METHOD,"rotation_rows",q)
        rows=self.work.lookup(key)
        if rows is None:
            w,x,y,z=q; mul=lambda a,b:self._op(a,b,"mul")
            squares=tuple(mul(v,v) for v in q); denominator=self._sum(squares)
            two=F(2)
            diagonal=lambda i,j:self._op(denominator,mul(two,self._op(squares[i],squares[j],"add")),"sub")
            pair=lambda a,b,c,d,sign:mul(two,self._op(mul(a,b),mul(c,d),sign))
            numerators=((diagonal(2,3),pair(x,y,w,z,"sub"),pair(x,z,w,y,"add")),
                        (pair(x,y,w,z,"add"),diagonal(1,3),pair(y,z,w,x,"sub")),
                        (pair(x,z,w,y,"sub"),pair(y,z,w,x,"add"),diagonal(1,2)))
            rows=tuple(tuple(self._op(v,denominator,"div") for v in row) for row in numerators)
            self.work.remember(key,rows)
        self.work.charge("rotation_vector_support")
        support=tuple((index,value) for index,value in enumerate(vector) if value)
        result=self._rounded_vector(self._sum(self._op(row[index],value,"mul")
                                              for index,value in support if row[index]) for row in rows)
        self.work.remember(result_key,result)
        return result

    def _pi(self,precision):
        key=(METHOD,"pi",precision)
        cached=self.work.lookup(key)
        if cached is not None: return cached
        # Exact alternating sums have tighter enclosures than iterating rounded
        # interval powers. N is fixed by precision, and every recurrence is charged.
        count=(precision+15)//4
        def atan_inverse(denominator):
            z=F(1,denominator); square=self._op(z,z,"mul"); power=z; total=F(0)
            for k in range(count):
                self.work.charge("source_series_recurrence")
                term=self._op(power,F(2*k+1),"div")
                total=self._op(total,term,"add" if k%2==0 else "sub")
                power=self._op(power,square,"mul")
            tail=self._op(power,F(2*count+1),"div")
            other=self._op(total,tail,"add" if count%2==0 else "sub")
            return (total,other) if compare(total,other,self.work)<=0 else (other,total)
        a,b=atan_inverse(5),atan_inverse(239)
        lower=self._op(self._op(F(16),a[0],"mul"),self._op(F(4),b[1],"mul"),"sub")
        upper=self._op(self._op(F(16),a[1],"mul"),self._op(F(4),b[0],"mul"),"sub")
        context=DyadicContext(precision,self.work)
        low=context.point(lower).lo; high=context.point(upper).hi
        result=F(low,1 << precision),F(high,1 << precision)
        self.work.remember(key,result)
        return result

    def _coefficients(self):
        key=(METHOD,"horner_coefficients",_HORNER_TERMS)
        cached=self.work.lookup(key)
        if cached is not None: return cached
        factorials=[1]
        for k in range(1,2*_HORNER_TERMS):
            self.work.charge("source_factorial")
            self.work.guard_bits(factorials[-1].bit_length()+k.bit_length())
            factorials.append(factorials[-1]*k)
        self.work.charge("source_coefficients",2*_HORNER_TERMS)
        result=(tuple(F((-1)**k,factorials[2*k+1]) for k in range(_HORNER_TERMS)),
                tuple(F((-1)**k,factorials[2*k]) for k in range(_HORNER_TERMS)))
        self.work.remember(key,result)
        return result

    def _horner_sincos(self,value):
        self.work.charge("source_series_grid_guard")
        if type(value) is not F:
            raise ReachAdmissionError("reach_numeric","Source series requires an exact dyadic grid argument.")
        self.work.guard(value)
        denominator=value.denominator
        if (abs(value.numerator)>denominator or denominator.bit_length()>BITS+1 or
                denominator & (denominator-1)):
            raise ReachAdmissionError("reach_numeric","Source series argument is outside its proved grid and range.")
        sine_coefficients,cosine_coefficients=self._coefficients()
        # Exact 13-term recurrences stay below 2,600 prospective operand bits
        # on this grid. Only the two final projections incur rounding error.
        square=self._op(value,value,"mul")
        sine,cosine=sine_coefficients[-1],cosine_coefficients[-1]
        for k in range(_HORNER_TERMS-2,-1,-1):
            self.work.charge("source_series_recurrence")
            sine=self._op(self._op(sine,square,"mul"),sine_coefficients[k],"add")
            cosine=self._op(self._op(cosine,square,"mul"),cosine_coefficients[k],"add")
        sine=round_dyadic(self._op(value,sine,"mul"),BITS,work=self.work)
        return sine,round_dyadic(cosine,BITS,work=self.work)

    def _reduced_sincos(self,lower,upper,pi):
        pi_mid=self._op(self._op(pi[0],pi[1],"add"),F(2),"div")
        ratio=self._op(self._op(lower,upper,"add"),pi_mid,"div")
        k=round_dyadic(ratio,0,work=self.work).numerator
        self.work.charge("quadrant_preflight",3)
        self.work.guard(k)
        kl,kh=(self._op(F(k),v,"mul") for v in pi)
        if k<0: kl,kh=kh,kl
        lo=self._op(lower,self._op(kh,F(2),"div"),"sub")
        hi=self._op(upper,self._op(kl,F(2),"div"),"sub")
        middle=round_dyadic(self._op(self._op(lo,hi,"add"),F(2),"div"),BITS,work=self.work)
        error=max(self._op(middle,lo,"sub"),self._op(hi,middle,"sub"))
        if compare(error,ARGUMENT_ERROR,self.work)>0 or compare(abs(middle),F(1),self.work)>0:
            return None
        sine,cosine=self._horner_sincos(middle)
        self.work.charge("quadrant_restore",2)
        return ((sine,cosine),(cosine,-sine),(-sine,-cosine),(-cosine,sine))[k%4]

    def sincos(self,angle):
        angle=rational(angle,self.work)
        key=(METHOD,"sincos",angle)
        cached=self.work.lookup(key)
        if cached is not None: return cached
        if not angle: return F(0),F(1)
        if compare(abs(angle),F(1),self.work)<=0:
            middle=round_dyadic(angle,BITS,work=self.work)
            result=self._horner_sincos(middle)
        else:
            result=None
            for precision in PRECISIONS:
                result=self._reduced_sincos(angle,angle,self._pi(precision))
                if result is not None: break
            if result is None:
                raise ReachAdmissionError("reach_numeric","Finite source angle reduction could not be certified.")
        self.work.remember(key,result)
        return result

    def _scaled_axis(self,axis,precision=96):
        axis=self._vector(axis)
        key=(METHOD,"scaled_axis",axis,precision)
        cached=self.work.lookup(key)
        if cached is not None: return cached
        self.work.charge("axis_scale",3)
        maximum=max(abs(v) for v in axis)
        if not maximum:
            raise ReachAdmissionError("reach_numeric","A rotation axis must be nonzero.")
        scaled=tuple(self._op(v,maximum,"div") for v in axis)
        square=self._sum(self._op(v,v,"mul") for v in scaled)
        context=DyadicContext(precision,self.work)
        bounds=context.bounds(context.sqrt_point(square))
        result=scaled,maximum,bounds
        self.work.remember(key,result)
        return result

    def axis_rotation(self,axis,angle):
        angle=rational(angle,self.work)
        axis=self._vector(axis)
        key=(METHOD,"axis_rotation",axis,angle)
        cached=self.work.lookup(key)
        if cached is not None: return cached
        if not angle:
            # Still validate the axis; a zero axis does not become admissible.
            self._scaled_axis(axis)
            result=RotationValue(UNIT)
            self.work.remember(key,result)
            return result
        unit=self._normalized_axis(axis)
        sine,cosine=self.sincos(self._op(angle,F(2),"div"))
        values=(cosine,*(self._op(v,sine,"mul") for v in unit))
        result=self._rescale(values,AXIS_ERROR)
        self.work.remember(key,result)
        return result

    def _normalized_axis(self,axis):
        """The same immutable 96-bit axis reduction for every requested angle."""
        axis=self._vector(axis)
        key=(METHOD,"normalized_axis",axis)
        cached=self.work.lookup(key)
        if cached is not None: return cached
        scaled,_,norm=self._scaled_axis(axis)
        self.work.charge("pose_unit_axis_check")
        if norm==(F(1),F(1)):
            # A scaled vector has a component of magnitude one. A proved
            # exact unit norm therefore makes its other components zero;
            # division by one and grid rounding would preserve every bit.
            unit=scaled
        else:
            middle=self._op(self._op(norm[0],norm[1],"add"),F(2),"div")
            unit=self._rounded_vector(self._op(v,middle,"div") for v in scaled)
        self.work.remember(key,unit)
        return unit

    def spin_plan(self,omega,max_elapsed_s):
        omega=self._vector(omega); maximum_time=abs(rational(max_elapsed_s,self.work))
        key=(METHOD,"spin_plan",omega,maximum_time)
        cached=self.work.lookup(key)
        if cached is not None: return cached
        if not any(omega):
            result=SpinPlan(ZERO,F(0),(F(1),F(1)),(F(3),F(4)),maximum_time,96,F(0))
            self.work.remember(key,result); return result
        for precision in PRECISIONS:
            scaled,maximum,norm=self._scaled_axis(omega,precision)
            pi=self._pi(precision)
            extent=self._op(self._op(maximum,maximum_time,"mul"),norm[1],"mul")
            quotient=self._op(extent,pi[0],"div")
            self.work.charge("phase_quadrant_ceiling",3)
            kmax=quotient.numerator//quotient.denominator+2
            angular_width=self._op(self._op(maximum,maximum_time,"mul"),self._op(norm[1],norm[0],"sub"),"mul")
            pi_width=self._op(F(kmax),self._op(pi[1],pi[0],"sub"),"mul")
            error=self._op(self._op(self._op(angular_width,pi_width,"add"),F(4),"div"),RHO,"add")
            if compare(error,ARGUMENT_ERROR,self.work)<=0:
                result=SpinPlan(scaled,maximum,norm,pi,maximum_time,precision,error)
                self.work.remember(key,result); return result
        raise ReachAdmissionError("reach_numeric","Finite source spin phase reduction could not be certified.")

    def spin_rotation(self,omega,elapsed,*,phase_plan=None):
        elapsed=rational(elapsed,self.work)
        plan=phase_plan if phase_plan is not None else self.spin_plan(omega,abs(elapsed))
        if not isinstance(plan,SpinPlan) or compare(abs(elapsed),plan.max_elapsed_s,self.work)>0:
            raise ReachAdmissionError("reach_numeric","A source sample lies outside its proved spin phase.")
        supplied=self._vector(omega)
        reconstructed=tuple(self._op(v,plan.maximum,"mul") for v in plan.scaled_omega)
        self.work.charge("spin_plan_identity",3)
        if supplied!=reconstructed:
            raise ReachAdmissionError("reach_numeric","A spin plan belongs to different angular velocity.")
        if not plan.maximum or not elapsed: return RotationValue(UNIT)
        factor=self._op(self._op(plan.maximum,elapsed,"mul"),F(2),"div")
        lo,hi=(self._op(factor,v,"mul") for v in plan.norm_bounds)
        if elapsed<0: lo,hi=hi,lo
        pair=self._reduced_sincos(lo,hi,plan.pi_bounds)
        if pair is None:
            raise ReachAdmissionError("reach_numeric","A proved spin phase did not enclose its sample.")
        sine,cosine=pair
        middle=self._op(self._op(plan.norm_bounds[0],plan.norm_bounds[1],"add"),F(2),"div")
        unit=tuple(round_dyadic(self._op(v,middle,"div"),BITS,work=self.work) for v in plan.scaled_omega)
        return self._rescale((cosine,*(self._op(v,sine,"mul") for v in unit)),AXIS_ERROR)

    def advance_orientation(self,initial,omega,elapsed,*,phase_plan=None):
        initial=self._rotation(initial); elapsed=rational(elapsed,self.work)
        omega=self._vector(omega)
        self.work.charge("orientation_stationary",3)
        if not any(omega) or not elapsed: return initial
        return self.multiply(self.spin_rotation(omega,elapsed,phase_plan=phase_plan),initial)

    def identity(self):
        self.work.charge("pose_identity")
        return PoseValue(ZERO,RotationValue(UNIT),ZERO,ZERO,F(0),self)

    def make(self,position=ZERO,orientation=UNIT,velocity=ZERO,omega=ZERO):
        position,rotation=self._vector(position),self._rotation(orientation)
        velocity,omega=self._vector(velocity),self._vector(omega)
        self.work.charge("pose_stationary_check")
        stationary=not any(velocity) and not any(omega)
        key=(METHOD,"stationary_pose",position,rotation)
        if stationary:
            cached=self.work.lookup(key)
            if cached is not None: return cached
        result=PoseValue(position,rotation,velocity,omega,F(0),self)
        if stationary: self.work.remember(key,result)
        return result

    def constant_pose(self,pose):
        return self.make(pose.position,pose.rotation)

    def hinge_pose(self,axis,coordinate,exact_rate):
        axis=self._vector(axis)
        coordinate,exact_rate=rational(coordinate,self.work),rational(exact_rate,self.work)
        key=(METHOD,"hinge_pose",axis,coordinate,exact_rate)
        cached=self.work.lookup(key)
        if cached is not None:
            rotation,omega=cached
            return PoseValue(ZERO,rotation,ZERO,omega,F(0),self)
        result=self.make(orientation=self.axis_rotation(axis,coordinate),omega=self.scale(axis,exact_rate))
        self.work.remember(key,(result.rotation,result.exact_omega))
        return result

    def compose(self,parent,local):
        if not isinstance(parent,PoseValue) or not isinstance(local,PoseValue):
            raise TypeError("Controlled composition requires private PoseValue inputs")
        self.work.charge("composition_stationary_check")
        canonical_zero_rates=(parent.exact_velocity is ZERO and parent.exact_omega is ZERO and
                              local.exact_velocity is ZERO and local.exact_omega is ZERO)
        stationary=canonical_zero_rates or not any((
            *parent.exact_velocity,*parent.exact_omega,*local.exact_velocity,*local.exact_omega))
        # A translated scene produces many one-use whole-pose entries. Keep
        # the bounded cache for shared local arithmetic instead of displacing
        # it with each object's distinct world translation.
        cache_stationary=stationary and not any(parent.exact_position)
        key=(METHOD,"stationary_composition",parent,local)
        if cache_stationary:
            cached=self.work.lookup(key)
            if cached is not None: return cached
        # Parent translation and position errors do not enter the rotation or
        # derivative arithmetic. Project each caller's position and retain its
        # own error calculation even when those common operations are reused.
        relative_key=(METHOD,"relative_composition",parent.rotation,
                      parent.exact_velocity,parent.exact_omega,local.exact_position,
                      local.rotation,local.exact_velocity,local.exact_omega)
        self.work.charge("composition_operand_guard")
        parent_position=parent.exact_position
        if not (isinstance(parent_position,tuple) and len(parent_position)==3 and
                all(type(value) is F for value in parent_position)):
            parent_position=self._vector(parent_position)
        self.work.guard(*parent_position,*parent.rotation.components,parent.rotation.error_rad,
            *parent.exact_velocity,*parent.exact_omega,parent.position_error_m,
            *local.exact_position,*local.rotation.components,local.rotation.error_rad,
            *local.exact_velocity,*local.exact_omega,local.position_error_m)
        relative=self.work.lookup(relative_key)
        offset=(self.rotate(parent.rotation,local.exact_position) if relative is None else relative[0])
        # The precharged fixed-size composition guard also covers the bounded
        # private offset retrieved or computed above. Both vector operands are
        # now checked; the generic add helper would decode/check them again.
        self.work.guard(*offset)
        position=self._rounded_vector(self._add_exact_vectors(parent_position,offset))
        if relative is None:
            if canonical_zero_rates:
                # The four immutable private zero tuples prove both spatial
                # derivative expressions exactly zero, including every grid
                # projection. Other inputs still take the validating helpers.
                velocity=omega=ZERO
            else:
                self.work.charge("composition_derivative_zero_check")
                if local.exact_velocity is ZERO:
                    if offset is ZERO or parent.exact_omega is ZERO:
                        linear=self._vector(parent.exact_velocity)
                    else:
                        linear=self.add(parent.exact_velocity,self.cross(parent.exact_omega,offset))
                else:
                    linear=self.add(self.add(parent.exact_velocity,self.cross(parent.exact_omega,offset)),
                                    self.rotate(parent.rotation,local.exact_velocity))
                angular=(self._vector(parent.exact_omega) if local.exact_omega is ZERO else
                         self.add(parent.exact_omega,self.rotate(parent.rotation,local.exact_omega)))
                # The omitted exact-zero terms cannot change the sum. Keep
                # the ordinary final grid: a parent's rate may be off-grid.
                velocity=self._rounded_vector(linear)
                omega=self._rounded_vector(angular)
            offset_error=self._op(self._l1(local.exact_position),parent.angular_error_rad,"mul")
            offset_allowance=self._sum((offset_error,VECTOR_ERROR,VECTOR_ERROR))
        else:
            _,rotation,velocity,omega,offset_allowance=relative
        parent_error,local_error=parent.position_error_m,local.position_error_m
        # The complete charged operand guard above covers these private
        # Fraction identities. Keep the actual allowance addition for every
        # caller, including when relative composition arithmetic is cached.
        if type(parent_error) is F and type(local_error) is F and not parent_error:
            inherited_error=local_error
        elif type(parent_error) is F and type(local_error) is F and not local_error:
            inherited_error=parent_error
        else:
            inherited_error=self._op(parent_error,local_error,"add")
        position_error=self._op(inherited_error,offset_allowance,"add")
        if relative is None:
            rotation=self.multiply(parent.rotation,local.rotation)
            self.work.remember(relative_key,(offset,rotation,velocity,omega,offset_allowance))
        result=PoseValue(position,rotation,velocity,omega,position_error,self)
        if cache_stationary: self.work.remember(key,result)
        return result

    def inverse_pose(self,pose):
        value=pose if isinstance(pose,PoseValue) else self.constant_pose(pose)
        key=(METHOD,"inverse_pose",value.exact_position,value.rotation,value.position_error_m)
        cached=self.work.lookup(key)
        if cached is not None: return cached
        rotation=self.inverse_rotation(value.rotation)
        self.work.charge("pose_position_negate",3)
        position=self.rotate(rotation,tuple(-x for x in value.exact_position))
        # This is a static frame inverse. Spatial derivatives are intentionally
        # zero; use relative_point for the measured moving-frame position.
        error=self._sum((value.position_error_m,
            self._op(self._l1(value.exact_position),value.angular_error_rad,"mul"),VECTOR_ERROR))
        result=PoseValue(position,rotation,ZERO,ZERO,error,self)
        self.work.remember(key,result)
        return result

    def relative_point(self,base,world_point):
        if not isinstance(base,PoseValue): raise TypeError("A private base pose is required")
        point=world_point.exact_position if isinstance(world_point,PoseValue) else self._vector(world_point)
        difference=tuple(self._op(a,b,"sub") for a,b in zip(point,base.exact_position))
        return self.rotate(self.inverse_rotation(base.rotation),difference)

    def _unit_projection(self,rotation):
        if rotation.frozen_projection is not None:
            self.work.charge("frozen_quaternion_projection")
            return rotation.frozen_projection
        self.work.charge("quaternion_projection_operand_guard")
        self.work.guard(*rotation.components)
        # Error allowances and pose identity do not affect this projection.
        key=(METHOD,"unit_projection",rotation.components)
        cached=self.work.lookup(key)
        if cached is not None: return cached
        self.work.charge("quaternion_projection_support")
        # Exact zero terms do not change q dot q. Reuse each actual square in
        # its output ratio, and start the nonempty exact sum at its first term.
        squares=tuple(self._op(value,value,"mul") if value else F(0)
                      for value in rotation.components)
        nonzero=tuple(value for value in squares if value)
        if not nonzero:
            raise ZeroDivisionError("Exact zero divisor")
        denominator=nonzero[0]
        for value in nonzero[1:]: denominator=self._op(denominator,value,"add")
        result=[]
        for value,square in zip(rotation.components,squares):
            if not value:
                self.work.charge("known_zero_quaternion_projection")
                result.append(0.0)
                continue
            square=self._op(square,denominator,"div")
            component=sqrt_rational_binary64(square,work=self.work)
            self.work.charge("quaternion_projection_sign")
            result.append(-component if value<0 and component else component)
        result=tuple(result)
        self.work.remember(key,result)
        return result

    def _expose(self,pose,field_name):
        self.work.charge("pose_projection_lookup")
        if field_name not in pose._projection:
            value=(self._unit_projection(pose.rotation) if field_name=="orientation" else
                   self._vector_projection(getattr(pose,"exact_"+field_name)))
            pose._projection[field_name]=value
        return pose._projection[field_name]

    def _vector_projection(self,values):
        if values is ZERO:
            self.work.charge("known_zero_vector_projection")
            return (0.0,0.0,0.0)
        self.work.charge("vector_projection_operand_guard")
        self.work.guard(*values)
        self.work.charge("vector_projection_zero_check")
        if not any(values): return (0.0,0.0,0.0)
        key=(METHOD,"vector_projection",values)
        cached=self.work.lookup(key)
        if cached is not None: return cached
        result=tuple(round_binary64(value,work=self.work) for value in values)
        self.work.remember(key,result)
        return result

    def materialize(self,pose):
        """Freeze the actual exposed release anchor without normalization drift."""
        projections={name:getattr(pose,name) for name in ("position","orientation","velocity","omega")}
        values={name:self._vector(value,4 if name=="orientation" else 3) for name,value in projections.items()}
        # Importing the already exposed orientation defines the new anchor's
        # exact projective rotation; preserve its actual saved public bits.
        rotation=RotationValue(values["orientation"],
            self._op(pose.angular_error_rad,EXPOSED_ROTATION_ERROR,"add"),projections["orientation"])
        rounding=self._sum(abs(self._op(a,b,"sub")) for a,b in zip(values["position"],pose.exact_position))
        return PoseValue(values["position"],rotation,values["velocity"],values["omega"],
            self._op(pose.position_error_m,rounding,"add"),self,projections)

    def source_bounds(self,pose,*,maximum_position_m=None):
        """Point bounds including final floats; never a whole-phase certificate.

        A supplied uniform L1 extent bounds the final projection alone. The
        composed pose's position_error_m may still depend on this sample's
        offsets. Use uniform_source_bounds for an entire phase.
        """
        extent=self._l1(pose.exact_position) if maximum_position_m is None else rational(maximum_position_m,self.work)
        if compare(extent,F(0),self.work)<0:
            raise ReachAdmissionError("reach_numeric","A source position bound cannot be negative.")
        rounding=self._op(self._op(extent,F(1,1<<53),"mul"),F(3,1<<1075),"add")
        return {"method":METHOD,"position_m":self._op(pose.position_error_m,rounding,"add"),
                "rotation_rad":self._op(pose.angular_error_rad,EXPOSED_ROTATION_ERROR,"add"),
                "proper_rotation_defect":F(0),"uniform_extent_supplied":maximum_position_m is not None}


def uniform_source_bounds(*,max_position_l1_m,path_offset_l1_m,trig_count,
                          product_count,vector_round_count,coordinate_angle_error_rad,
                          anchor_position_error_m,anchor_rotation_error_rad,
                          radius_m=F(0),work):
    """Bound every source pose in a caller-identified continuous phase.

    The caller supplies whole-phase magnitudes, actual helper path counts and
    independently propagated anchor discrepancies. Counts are conservative
    maxima, not measured errors or merely the number of published samples.
    ``path_offset_l1_m`` sums all local offset extents on the selected path.
    ``vector_round_count`` covers every rounded position-vector stage on it.
    """
    counts=(trig_count,product_count,vector_round_count)
    work.charge("uniform_bound_counts",3)
    if any(type(value) is not int or value<0 for value in counts):
        raise ReachAdmissionError("reach_numeric","Source path counts must be nonnegative integers.")
    work.guard(*counts)
    values=tuple(rational(v,work) for v in (max_position_l1_m,path_offset_l1_m,
        coordinate_angle_error_rad,anchor_position_error_m,anchor_rotation_error_rad,radius_m))
    if any(compare(value,F(0),work)<0 for value in values):
        raise ReachAdmissionError("reach_numeric","Source uniform allowances must be nonnegative.")
    extent,offset,coordinate,anchor_position,anchor_rotation,radius=values
    op=lambda a,b,kind:exact(a,b,kind,work)
    rotation=op(op(anchor_rotation,coordinate,"add"),
        op(op(F(trig_count),AXIS_ERROR,"mul"),op(F(product_count),PRODUCT_ERROR,"mul"),"add"),"add")
    position=op(op(anchor_position,op(offset,rotation,"mul"),"add"),
        op(F(vector_round_count),VECTOR_ERROR,"mul"),"add")
    position=op(position,op(op(extent,F(1,1<<53),"mul"),F(3,1<<1075),"add"),"add")
    rotation=op(rotation,EXPOSED_ROTATION_ERROR,"add")
    return {"method":METHOD,"position_m":position,"rotation_rad":rotation,
            "point_m":op(position,op(radius,rotation,"mul"),"add"),
            "proper_rotation_defect":F(0)}


def source_numeric_basis(*,work):
    """Hash bounded, identified implementation inputs under the execution lock.

    The caller must retain the execution rule's stable source identity. Missing
    source/derivation files fail explicitly instead of publishing an invented
    or stale implementation hash. No paths are supplied by a request.
    """
    key=(METHOD,"source_numeric_basis")
    cached=work.lookup(key)
    if cached is not None: return cached
    root=Path(__file__).resolve().parent.parent
    implementation_names=("ontokin/reach_numeric.py","ontokin/reach_kinematics.py","ontokin/reach_pose.py",
                          "ontokin/reach_phase.py","ontokin/reach_runtime.py")
    derivation_names=("docs/engineering/reach-numeric-kernel.md",
                      "docs/engineering/reach-source-kernel.md")
    names=implementation_names+derivation_names
    entries=[]
    for name in names:
        work.charge("numeric_basis_open")
        digest=sha256(); size=0
        try:
            with (root/name).open("rb") as source:
                while True:
                    work.charge("numeric_basis_read")
                    block=source.read(16384)
                    work.charge("numeric_basis_read_return")
                    if not block: break
                    size+=len(block)
                    if size>262144:
                        work.resource("numeric_basis_input_bytes",262144,size)
                    work.charge("numeric_basis_hash")
                    digest.update(block)
        except OSError as error:
            raise ReachAdmissionError("reach_numeric","The source numerical basis cannot be identified.",
                                      missing_basis_input=name) from error
        entries.append((name,digest.hexdigest()))
    def aggregate(values):
        work.charge("numeric_basis_digest")
        return sha256("".join(name+"\0"+digest+"\n" for name,digest in values).encode("ascii")).hexdigest()
    implementation=aggregate(entries[:len(implementation_names)])
    derivation=aggregate(entries[len(implementation_names):])
    result=SourceNumericBasis("OntoKin controlled source poses","0.1","sha256:"+implementation,
        METHOD,"sha256:"+derivation,tuple(entries))
    work.remember(key,result)
    return result
