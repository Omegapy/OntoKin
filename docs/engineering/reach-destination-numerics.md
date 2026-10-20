# Controlled recorded reach destination arithmetic

This is the implementation derivation for `ontokin-controlled-three-recording`
version `0.1.0`, implemented by `tools/reach_destination.mjs`. It supports the
adopted GLB/0.6 quantization contract. It is not a release result. Actual native
and browser execution, supplied-byte rejection probes and independent review
remain required. Certificates identify the exact implementation and this
derivation by SHA-256; a changed implementation cannot inherit an old identity.

## Reference, actual interpolation and finite domain

The format/reference rotation is exact shortest-arc SLERP between exact
normalized stored endpoints. The identified player uses a normalized quaternion
chord as a controlled approximation to that SLERP. Its error is charged in
`destination_numeric_rotation_bound_rad`; it is never called exact SLERP or
assigned zero error. The angle `theta` below is the quaternion sphere arc, half
the corresponding physical rotation angle.

Inputs are finite binary32 endpoint positions/quaternions and finite binary64
sample times. Times and all intermediate interpolation ratios are converted to
exact integer fractions before arithmetic. All fractions are reduced. Every
operation and integer-size growth is bounded; exhaustion rejects the request.
There are at most 100,000 destination arithmetic operations per sampled scene,
32,768 bits per integer, 10,000 keys, 250,000 expanded carrier poses and
16,777,216 repeated decoded components. The source's separate shared request
budget is not enlarged by these destination limits.

Carrier translation magnitude plus the full stored landmark radius must be at
most `2^400`. The certified quaternion sphere arc is at most the strict rational
lower bound `7853981633974483/10^16` on pi/4. Delivered carriers are scene roots
with identity ancestors and unit scale. The identified transform is the CPU
world matrix in Three.js revision 180, followed by its CPU point transform.
Rasterization, projection to screen pixels and arbitrary other players are not
part of this numerical statement; their actual rendered images are separately
inspected. Browser integration must invoke this player, not the default mixer.

## Integer rounding

IEEE component decoding extracts sign, exponent and significand with DataView.
Division to a binary64 component finds its exact binary exponent and rounds the
scaled integer quotient by comparing twice its remainder with the denominator;
an exact tie chooses an even significand. It explicitly handles normal,
subnormal, zero and overflow cases. Unpacking the selected bits does not decide
the rounding. Cancellation is polled before integer work.

To normalize a component `x` of a vector with exact squared norm `S`, form
`z=x^2/S`. Since `0<=z<=1`, choose the binary64 output grid from the exact
binary exponent of `z`. Integer square root finds the lower grid point `q`.
Compare `4*n` with `d*(2*q+1)^2` on that grid; equality chooses the even point.
This proves correctly rounded `sign(x)*sqrt(z)` without a floating square root.
The implementation uses Euclid and integer Newton iteration with finite guards.

Each rounded normalized component differs from its exact value by at most
`2^-53`, including subnormals. The Euclidean four-component error is at most
`2^-52`; the implementation uses the larger `E=2^-51` when bounding endpoints.
The resulting vector remains within that error of a unit vector.

## Uniform quaternion bound

Let exact normalized stored endpoints be `a,b`, with coherent positive dot
product, and let `S(u)` be their exact short SLERP. Its second derivative with
respect to `u` has norm `theta^2`. Therefore its chord `C(u)=(1-u)a+ub` obeys

`||S(u)-C(u)|| <= theta^2/8` for every `0<=u<=1`.

Normalization of a vector against a unit comparison point increases its error
by at most a factor of two: `||C/||C||-S|| <= 2||C-S||`. Hence exact normalized
chord interpolation is within `theta^2/4` of the exact reference quaternion.
The chord norm is at least `cos(theta/2)>0.9` in the supported range.

The actual algorithm first rounds each normalized endpoint with error at most
`E`. Exact rational interpolation of those endpoints perturbs the chord by at
most `E`. Normalization on this domain contributes less than `3E`, and final
component rounding contributes at most `2^-52`. The proper rotation associated
with the rounded output adds one further normalization error of at most
`2^-52`. The physical rotation difference is `4 asin(d/2)` for quaternion
distance `d`. For the present domain `4 asin(d/2)<=4d`, so the conservative
uniform bound is

`n_dr = theta^2 + 2^-44`.

It includes endpoint branches and the coincident-endpoint limit. Exact rational
time interpolation produces no additional amount error for the supplied
binary64 observation time. Held endpoint behavior applies before/after the
stored clip. The source-time shift between authored and stored clocks is a
different term in the complete certificate and remains mandatory.

To avoid host acos, the certificate obtains an outward bound `d` on the distance
between exact normalized endpoints. It normalizes by the integer method above,
bounds the computed difference by integer square root, and adds `2E`. For
`d<=1/2`,

`theta = 2 asin(d/2) <= d/sqrt(1-d^2/4) <= d/(1-d^2/4)`.

The final rational upper bound is checked against the arc cap before it is used.

## Translation, matrix defect and local points

Translation interpolation is an exact rational expression followed by one
correct rounding per component. If the coordinate magnitude is bounded by `M`,
its Euclidean origin error is at most `2^-51*(M+1)`. The `+1` also covers the
subnormal absolute error.

The rounded quaternion is within `2^-52` of a unit vector, so its squared norm
defect is below `2^-50`. Three's unnormalized quaternion compose formula is
`M(Q)=||Q||^2 R(Q)+(1-||Q||^2)I`, where `R(Q)` is the proper normalized rotation.
Its exact nonorthogonal defect is at most `2*abs(||Q||^2-1)<2^-49` in operator
norm. This error must be positional as well as rotational.

All compose operands are bounded by two. Each matrix entry involves fewer than
20 ordinary binary64 additions/multiplications. Under round-to-nearest IEEE
arithmetic their accumulated absolute error is below `2^-45`; three-dimensional
operator norm is below `2^-43`. Identity ancestor multiplication introduces no
new nonzero product and preserves these finite entries. CPU point application
uses at most four products and three additions per coordinate, adding less than
`2^-48*(M+r+e_v+1)` in Euclidean norm. The finite magnitude limit prevents any
overflow; subnormal absolute errors are included by the `+1` term.

The implementation uses the deliberately larger complete positional allowance

`n_dp = 2^-38*(M+r+e_v+1)`.

Here `r+e_v` covers every promised source landmark and stored native vertex after
local placement. This allowance contains origin rounding, nonorthogonal matrix
defect and matrix/point arithmetic. It is additional to `r*n_dr`, endpoint and
vertex conversion, source numerics and source-time-shift terms. It does not use
an unused tolerance remainder, sampled maximum or unverified host transcendental.

## Required independent checks

The supplied-byte validator must reconstruct the stored endpoints and radii,
recompute all bounds and exact bit identities, verify this method's implementation
and derivation hashes, and reject unsupported ranges. Fixed and dense native
probes compare actual Three CPU matrices and transformed native geometry against
independent source expectations. The browser must import this exact module and
retain its actual implementation identity in evidence. These are implementation
acceptance obligations; no passing execution is asserted by this document.
