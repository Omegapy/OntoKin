"""Pure admitted planar IK and exact-clock pair sampling for reach/0.6.

Topology, ownership, source diagnostics and whole-boundary publication belong
to the evaluator. This module never changes a model, action or joint claim.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction as F

from .reach_numeric import (
    MAX_OPERAND_BITS, PRECISIONS, PI64_BITS, SIGN, ReachAdmissionError, ReachExecutionWork,
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
    # Decode and guard every actual input before looking up a pure law. The
    # elapsed clock remains independently checked on every call, while slopes
    # and published rates depend only on these immutable law operands.
    operands=tuple((rational(start,work),rational(target,work))
                   for start,target in zip(start_rad,target_rad))
    key=("reach_pair_law_v1",work.max_operand_bits,duration,operands,running)
    law=work.lookup(key)
    values=[]; rates=[]; exact_values=[]; exact_slopes=[]
    for index,(initial,goal) in enumerate(operands):
        slope=(exact(exact(goal,initial,"sub",work),duration,"div",work)
               if law is None else law[0][index])
        value=goal if elapsed==duration else exact(initial,exact(slope,elapsed,"mul",work),"add",work)
        exact_values.append(value)
        exact_slopes.append(slope)
        values.append(round_binary64(value,work=work))
        # Keep the original cold-path arithmetic order. A paused law can
        # have an unrepresentable derivative and a valid coordinate, so
        # never round an unused paused derivative eagerly.
        rates.append((round_binary64(slope,work=work) if running else 0.0)
                     if law is None else law[1][index])
    exact_slopes,rates=tuple(exact_slopes),tuple(rates)
    if law is None:
        work.remember(key,(exact_slopes,rates))
    return PairSample(tuple(values),rates,tuple(exact_values),exact_slopes if running else (F(0),F(0)))


def recording_pair(start_rad,target_rad,duration_s,elapsed_s,*,running,work: ReachExecutionWork):
    """Sample the same affine law with one bounded decoded-input record.

    A recording repeatedly supplies the same immutable canonical endpoints.
    Its exact clock and current finite operand domains are still admitted on
    every call; no source claim or state is implied by this numerical reuse.
    Narrowed operand limits execute the original scalar preflight sequence.
    """
    if len(start_rad)!=2 or len(target_rad)!=2:
        raise ReachAdmissionError("reach_domain","A reach has exactly two coordinates.")
    while True:
        cap=work.max_operand_bits
        if cap!=MAX_OPERAND_BITS:
            return sample_pair(start_rad,target_rad,duration_s,elapsed_s,running=running,work=work)
        duration,elapsed=rational(duration_s,work),rational(elapsed_s,work)
        work.charge("pair_clock_domain")
        if duration<=0 or not 0<=elapsed<=duration or type(running) is not bool:
            raise ReachAdmissionError("reach_numeric","Invalid reach interpolation clock or state.")
        work.charge("recording_pair_operand_domain")
        original=tuple(zip(start_rad,target_rad))
        if any(type(value) not in (int,float,F) for pair in original for value in pair):
            return sample_pair(start_rad,target_rad,duration_s,elapsed_s,running=running,work=work)
        for pair in original:
            for value in pair:
                if type(value) is float:
                    if float_bits(value)&0x7FF0000000000000==0x7FF0000000000000:
                        raise ReachAdmissionError("reach_domain","A reach operand must be finite.")
                else:
                    work.guard(value)
        if work.max_operand_bits!=cap:
            continue
        key=("recording_pair_law_v1",cap,duration,
             tuple(tuple((type(value),value) for value in pair) for pair in original),running)
        law=work.lookup(key)
        if work.max_operand_bits!=cap:
            continue
        operands=(tuple((rational(start,work),rational(target,work)) for start,target in original)
                  if law is None else law[0])
        work.guard(*(value for pair in operands for value in pair))
        values=[]; rates=[]; exact_values=[]; exact_slopes=[]
        for index,(initial,goal) in enumerate(operands):
            slope=(exact(exact(goal,initial,"sub",work),duration,"div",work)
                   if law is None else law[1][index])
            work.guard(slope)
            value=goal if elapsed==duration else exact(initial,exact(slope,elapsed,"mul",work),"add",work)
            exact_values.append(value)
            exact_slopes.append(slope)
            values.append(round_binary64(value,work=work))
            rates.append((round_binary64(slope,work=work) if running else 0.0)
                         if law is None else law[2][index])
        if work.max_operand_bits!=cap:
            continue
        exact_slopes,rates=tuple(exact_slopes),tuple(rates)
        if law is None:
            work.remember(key,(operands,exact_slopes,rates))
        if work.max_operand_bits==cap:
            return PairSample(tuple(values),rates,tuple(exact_values),
                              exact_slopes if running else (F(0),F(0)))


def measured_residual_squared(actual_end_base_m,target_base_m,*,work: ReachExecutionWork):
    if len(actual_end_base_m)!=3 or len(target_base_m)!=3:
        raise ReachAdmissionError("reach_domain", "A residual requires two three-dimensional positions.")
    # Separate source occurrences may have identical measured local positions.
    # Reuse only their completed scalar calculation; every new occurrence still
    # decodes and bounds its actual inputs before consulting the shared cache.
    while True:
        cap=work.max_operand_bits
        operands=tuple((rational(actual,work),rational(target,work))
                       for actual,target in zip(actual_end_base_m,target_base_m))
        if work.max_operand_bits!=cap:
            continue
        key=(METHOD,"measured_residual_squared",cap,operands)
        result=work.lookup(key)
        if work.max_operand_bits!=cap:
            continue
        if result is None:
            result=F(0)
            for actual,target in operands:
                delta=exact(actual,target,"sub",work)
                result=exact(result,exact(delta,delta,"mul",work),"add",work)
            if work.max_operand_bits!=cap:
                continue
            work.remember(key,result)
        work.charge("residual_result_guard")
        work.guard(result)
        if work.max_operand_bits==cap:
            return result


def rounded_sqrt(value,*,work):
    return sqrt_rational_binary64(value,work=work)
