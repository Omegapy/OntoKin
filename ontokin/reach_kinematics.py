"""Pure admitted planar IK and exact-clock pair sampling for reach/0.6.

Topology, ownership, source diagnostics and whole-boundary publication belong
to the evaluator. This module never changes a model, action or joint claim.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction as F

from .reach_numeric import (
    PRECISIONS, PI64_BITS, SIGN, ReachAdmissionError, ReachExecutionWork,
    DyadicContext, _Refine, bits_float, bits_fraction, certify_rounding,
    compare, exact, float_bits, rational, round_binary64,
    sqrt_rational_binary64,
)

METHOD = "ontokin.planar-ik-dyadic-integer/0.1"
RESIDUAL_LIMIT_SQUARED = F(1,10**18)


@dataclass(frozen=True)
class PlanarSolution:
    target_rad: tuple[float,float]
    target_bits: tuple[int,int]
    residual_squared_upper_m2: F
    precision_bits: int
    method: str
    work: tuple[tuple[str,int],...]
    coordinate_enclosures: tuple[tuple[F,F],tuple[F,F]]


@dataclass(frozen=True)
class PairSample:
    coordinates_rad: tuple[float,float]
    rates_rad_s: tuple[float,float]
    exact_coordinates: tuple[F,F]
    exact_slopes: tuple[F,F]


def _sign(value):
    return (value>0)-(value<0)


def _radical_sign(a,b,d,work):
    work.charge("radical_sign")
    if not d or not b: return _sign(a)
    if not a or _sign(a)==_sign(b): return _sign(b)
    left=exact(a,a,"mul",work)
    right=exact(exact(b,b,"mul",work),d,"mul",work)
    return _sign(a)*compare(left,right,work)


def _limits(targets, limits, work):
    for index,(target,bounds) in enumerate(zip(targets,limits)):
        if compare(target,bounds[0],work)<0 or compare(target,bounds[1],work)>0:
            raise ReachAdmissionError("reach_limit", "Selected canonical coordinate exceeds its closed joint limits.",
                                      coordinate_index=index,
                                      target_rad=bits_float(float_bits(float(target))),
                                      limits_rad=[float(bounds[0]),float(bounds[1])])


def admit_planar(lengths_m, target_base_m, branch, limits_rad, *, work: ReachExecutionWork):
    """Prove canonical targets, then limits, then their real forward residual.

    The caller must already have checked immutable chain/frame domains and
    current modes/claims. The returned immutable mathematics grants no claim.
    """
    meter=work.admission()
    if (not isinstance(lengths_m,(tuple,list)) or len(lengths_m)!=2 or
        not isinstance(target_base_m,(tuple,list)) or len(target_base_m)!=3 or
        branch not in ("elbow_positive","elbow_negative") or
        not isinstance(limits_rad,(tuple,list)) or len(limits_rad)!=2 or
        any(not isinstance(row,(tuple,list)) or len(row)!=2 for row in limits_rad)):
        raise ReachAdmissionError("reach_domain", "Malformed planar numeric operands.")
    # Canonical source operands are binary64. Fractions are accepted only for
    # exact clocks in sample_pair, not as an alternate geometric input meaning.
    operands=(*lengths_m,*target_base_m,*(v for row in limits_rad for v in row))
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) for v in operands):
        raise ReachAdmissionError("reach_domain", "Planar geometry requires canonical binary64 operands.")
    values=tuple(rational(v,meter) for v in operands)
    a,b,x,y,z=values[:5]
    limits=(values[5:7],values[7:9])
    meter.charge("numeric_domain",7)
    if z:
        raise ReachAdmissionError("reach_frame", "The target must have exactly zero base-frame Z.")
    pi=bits_fraction(PI64_BITS,meter)
    if (not F(1,8)<=a<=4 or not F(1,8)<=b<=4 or abs(x)>8 or abs(y)>8 or
        any(not -pi<=lo<=hi<=pi for lo,hi in limits)):
        raise ReachAdmissionError("reach_domain", "Planar operands exceed the adopted closed domain.")
    canonical_bits=tuple(float_bits(round_binary64(v,work=meter)) for v in values[:5])
    key=(METHOD,canonical_bits,branch)
    cached=work.lookup(key)
    if cached is not None:
        _limits(tuple(bits_fraction(v,meter) for v in cached.target_bits),limits,meter)
        return replace(cached,work=tuple(meter.record().items()))
    op=lambda lhs,rhs,kind: exact(lhs,rhs,kind,meter)
    r2=op(op(x,x,"mul"),op(y,y,"mul"),"add")
    difference,total=op(a,b,"sub"),op(a,b,"add")
    if compare(r2,op(difference,difference,"mul"),meter)<0 or compare(r2,op(total,total,"mul"),meter)>0:
        raise ReachAdmissionError("reach_unreachable", "Target lies outside the exact closed reach annulus.")
    if a==b and r2==0:
        raise ReachAdmissionError("reach_singular", "Equal links at the origin leave the shoulder undetermined.")
    c=op(op(op(r2,op(a,a,"mul"),"sub"),op(b,b,"mul"),"sub"),op(F(2),op(a,b,"mul"),"mul"),"div")
    d=op(F(1),op(c,c,"mul"),"sub")
    if not -1<=c<=1 or d<0: raise AssertionError("Exact annulus invariant")
    s=F(1 if branch=="elbow_positive" else -1)
    t=op(a,op(b,c,"mul"),"add")
    xa,xb=op(t,x,"mul"),op(op(s,b,"mul"),y,"mul")
    ya,yb=op(t,y,"mul"),-op(op(s,b,"mul"),x,"mul")
    sx,sy=_radical_sign(xa,xb,d,meter),_radical_sign(ya,yb,d,meter)
    coefficients=tuple(op(v,r2,"div") for v in (xa,xb,ya,yb))
    for precision in PRECISIONS:
        context=DyadicContext(precision,meter)
        try:
            root=context.sqrt_point(d)
            xx=(context.point(0) if sx==0 else context.add(context.point(coefficients[0]),
                context.mul(context.point(coefficients[1]),root)))
            yy=(context.point(0) if sy==0 else context.add(context.point(coefficients[2]),
                context.mul(context.point(coefficients[3]),root)))
            shoulder=context.atan2(yy,xx,sy,sx)
            elbow=context.atan2(root,context.point(c),_sign(d),_sign(c),negative_axis=False)
            if s<0: elbow=context.neg(elbow)
            first,second=certify_rounding(context,shoulder),certify_rounding(context,elbow)
            if first==PI64_BITS: first^=SIGN
            targets=bits_fraction(first,meter),bits_fraction(second,meter)
            _limits(targets,limits,meter)
            sin1,cos1=context.sincos_point(targets[0])
            sin12,cos12=context.sincos_point(op(targets[0],targets[1],"add"))
            px=context.add(context.mul(context.point(a),cos1),context.mul(context.point(b),cos12))
            py=context.add(context.mul(context.point(a),sin1),context.mul(context.point(b),sin12))
            dx,dy=context.sub(px,context.point(x)),context.sub(py,context.point(y))
            residual=context.add(context.square(dx),context.square(dy))
            _,upper=context.bounds(residual)
            if compare(upper,RESIDUAL_LIMIT_SQUARED,meter)>0:
                raise _Refine("Rounded-pair residual is not certified")
            result=PlanarSolution((bits_float(first),bits_float(second)),(first,second),upper,
                precision,METHOD,tuple(meter.record().items()),
                (context.bounds(shoulder),context.bounds(elbow)))
            work.remember(key,result)
            return result
        except _Refine:
            continue
    raise ReachAdmissionError("reach_numeric", "Five finite precision passes could not prove the requested solution.",
                              precision_attempts=list(PRECISIONS),work=meter.record())


def sample_pair(start_rad,target_rad,duration_s,elapsed_s,*,running,work: ReachExecutionWork):
    if len(start_rad)!=2 or len(target_rad)!=2:
        raise ReachAdmissionError("reach_domain", "A reach has exactly two coordinates.")
    duration,elapsed=rational(duration_s,work),rational(elapsed_s,work)
    work.charge("pair_clock_domain")
    if duration<=0 or not 0<=elapsed<=duration or type(running) is not bool:
        raise ReachAdmissionError("reach_numeric", "Invalid reach interpolation clock or state.")
    values=[]; rates=[]; exact_values=[]; slopes=[]
    for start,target in zip(start_rad,target_rad):
        initial,goal=rational(start,work),rational(target,work)
        slope=exact(exact(goal,initial,"sub",work),duration,"div",work)
        value=goal if elapsed==duration else exact(initial,exact(slope,elapsed,"mul",work),"add",work)
        exact_values.append(value)
        slopes.append(slope if running else F(0))
        values.append(round_binary64(value,work=work))
        rates.append(round_binary64(slope,work=work) if running else 0.0)
    return PairSample(tuple(values),tuple(rates),tuple(exact_values),tuple(slopes))


def measured_residual_squared(actual_end_base_m,target_base_m,*,work: ReachExecutionWork):
    if len(actual_end_base_m)!=3 or len(target_base_m)!=3:
        raise ReachAdmissionError("reach_domain", "A residual requires two three-dimensional positions.")
    result=F(0)
    for actual,target in zip(actual_end_base_m,target_base_m):
        delta=exact(rational(actual,work),rational(target,work),"sub",work)
        result=exact(result,exact(delta,delta,"mul",work),"add",work)
    return result


def rounded_sqrt(value,*,work):
    return sqrt_rational_binary64(value,work=work)
