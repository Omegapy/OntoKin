# Exact unit offsets in native planar recording

This optimization changes only `Binary64RecordingOps._rotated_offset` in the
bounded planar recording implementation. The original coefficient order stays
unchanged:

```
c = RN64(RN64(w*w) - RN64(z*z))
s = RN64(RN64(w*z) * 2)
```

When the local Y component has its original structural-zero mask and the
actual local X operand is the exact native `float` value `+1.0`, the original
two products `RN64(c*1)` and `RN64(s*1)` are exactly `c` and `s`. Every finite
binary64 value multiplied by positive one retains its exact representation,
including positive/negative zero and subnormal values. No rounding,
normalization, addition or reassociation occurs. The original Z component and
all structural-zero masks remain unchanged.

The corresponding sparse local-Y case returns `(-s, c, z)`. Its existing
negation charge and live-domain check still precede the actual negation. That
negation retains the original signed-zero behavior. Each fold additionally
requires both computed coefficients to have strict native `float` type; a
direct-helper foreign operand that produced an integer coefficient retains the
ordinary multiplication and conversion. Boolean, integer, Fraction and float
subclass unit operands likewise retain their original arithmetic calls.

Both coefficients have already completed their original finite-intermediate
checks and callback/domain checks. There is no callback between that completed
proof and the X fold. The Y case retains its separate callback and domain check
before negation. A cancellation or narrowed operand cap at any surviving
coefficient, sign, cache lookup or publication callback prevents a native
return through the same original exception path. No executed operation loses
its charge: the two identity multiplications are no longer executed.

All other offsets keep their original kernel. Existing complete-offset cache
keys, entries, admission, eviction and capacity stay unchanged. No coefficient
cache or additional result table is introduced. Because every actual candidate
bit is unchanged, the existing enclosure equations and source authority remain
unchanged, as do every fixture, tolerance, recording setting and operation cap.

The read-only diagnostic on source `7a5a535907328f16b197e9405dd58561085406c4`
observed 563 eligible P16 calls, accounting for 1,126 executed identity
multiplications. P23 had one eligible call, accounting for two multiplications.
Both unmodified requests still exhausted the original 100,000-operation cap;
these counts are local arithmetic savings, not completed-release results.
The dedicated unit-offset tests compare the original ordered kernel's complete
bits, exceptional/cap behavior, an actual P16 captured phase and complete P16
prefix GLB bytes. Executed test and source results are recorded separately by
identified implementation revision.
