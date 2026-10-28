# Cartesian captured recording arithmetic

## Scope and status

This candidate extends the existing native scalar/Z recording calculations to
one Cartesian axis per complete captured ancestry. It is an optional producer
calculation; source kinematics and the independent supplied-byte reader remain
authoritative. The motivating original request is P11, whose Y-axis head and
eye frames previously used ordinary per-key graph traversal while its Z-axis
arm branches used captured native arithmetic.

Identified candidate `ade8500bbf2dfd2fc8ff5cd7bed529686faccc3f` passes
**197/197** native/captured regression methods with a complete log and stable
inputs. Original P11 still reaches100,001 during independent site rotation.
Complete original run017 after integration remains23/28. Checkpoint014 retains
this result, the earlier22/22 dedicated cohort and the failed broad attempt;
no additional full recording pass or release acceptance is claimed.

## Exact relationship to the existing kernel

For an axial unit vector with index `a`, define `u=(a+1) mod 3` and
`v=(a+2) mod 3`. The coordinate order `(u,v,a)` is a proper cyclic permutation.
It has determinant positive one, so it preserves the orientation of the cross
product and Hamilton quaternion multiplication.

The existing two-component rotation stores `(w,z)`. The private `z` member now
means the coefficient on the explicitly stored axis `a`. Public output places
that coefficient at quaternion component `a+1` and uses canonical positive
zero for the other two vector components. No rotation values are inferred from
an axis name or from a different carrier's sampled orientation.

For two same-axis rotations, the actual ordered native products remain
`w1*w2-z1*z2` and `w1*z2+z1*w2`, with the original canonical sign lift and
structural-zero rules. For a vector, the original Z calculation is applied to
components `(p[u],p[v],p[a])`, and the result is permuted back. This preserves
every arithmetic operation, its order, finite admission, signed-zero behavior,
positive-unit shortcut and charge. Proper coordinate permutation preserves L1
and component maximum norms and all scalar operand magnitudes. The original
finite-error derivation therefore applies without an additional allowance.

The only orientation products admitted are same-axis products and genuine
structural identities. Two different nonidentity axes decline the optional
calculation. The existing phase replay/fallback handles unsupported ancestry.

## Source and identity requirements

Each private native rotation includes an exact integer axis tag in `{0,1,2}`.
The tag participates in product, offset and relative-pose cache operands and
in public orientation placement. Complete carrier cursor keys already contain
their proved body axis and rate. Direct zero-angle seeds retain the explicit
axis hint even though their axial coefficient is numerically zero; they do not
become an unchecked structural identity in a history-dependent recurrence.

Capture accumulates the actual root, local-pose, hinge and proved-rate axes
through every dependency. More than one axis in an ancestry declines capture.
The temporary structural sets disappear after capture and retain no numeric
results. Different branches may independently use different axes. The current
source witnesses, copied immutable operands, owner identities, complete topology
receipt and delayed cursor publication all retain their previous roles.

Root spin and dynamic-root specialization retain their existing Z-only domain.
Nonzero head, neck and eye translations undergo their original ordered local
composition; no child or world origin is replaced with a parent origin unless
the existing independent zero-child proof already permits that result.

P11's actual head child site has an identity local rotation and translation
`(0,-0.25,0)`, parallel to its Y hinge. Capture additionally admits this bounded
shape for X/Y: all seven local components must be native finite floats, the
rotation must be exactly the identity, and both transverse translation
components must be exactly zero. Near-identity or nearly parallel values retain
ordinary fallback. The new local Pose is detached from the source before later
callbacks.

For this shape, the original placement is
`compose(compose(parent, hinge), inverse_child)`. The hinge has zero
translation. Every rotation in the same-axis ancestry fixes the inverse-child
translation. Consequently the complete independently seeded body orientation
can be placed at the original parent anchor, with depth `parent+1`, then the
original independently constructed inverse child is composed once, giving
depth `parent+2`. This retains the original source inverse, native offset
kernel and ordered world-origin addition. It does not use the zero-child-origin
shortcut for the nonzero offset. Eye translations still follow their ordinary
local composition from the correctly positioned head.

Cartesian calculations require an explicit private opt-in. Production phase
capture enables it only for unchanged standard topology, ordinary traversal and
recording methods, including the exporter's planning subclass. Instance or
class overrides retain the preceding Z/ordinary partition. The captured method
identities and fixed selector are checked again after callbacks and before
publication. The strict
float32-cell diagnostic and scalar fallback do not opt in. A captured graph's
cache identity and constant-projection, source-leaf and relative-pose identities
bind the opt-in, so a strict
caller cannot borrow a Cartesian value completed by another caller on the same
work object.

## Limits and verification requirements

The shared 100,000-operation request maximum, 32,768-bit numeric domain,
256-entry cache, original key times, source fixtures, tolerances, cursor step
limits, error constants and independent acceptance rules are unchanged.
Structural coordinate selection does not replace or suppress numeric charges.
Every executed scalar operation remains charged on the original work object.

The dedicated cohort covers exact cyclic bit/count symmetry, independent
interval checks for signed body rates, zero seeds and reseeds, frozen-source
projection checks, cache-axis separation, strict-mode separation, mixed-axis
fallback, persistent/transient source changes, cap/cancellation publication,
actual nonzero P11 origins, ordinary observers and a short original-source GLB
with its independent supplied-byte validation. The earlier mixed-phase cohort
explicitly disables the new opt-in to keep testing the original mixed path.

Before integration, execute the dedicated cohort and relevant native/captured
regressions, then the original P11 recording. After integration, execute the
complete original 28-recording suite. Preserve failed attempts and exact source
identities. A producer pass does not close Agent, independent rates,
compatibility, native/browser, visual or R01–R12/Q01–Q22 release gates.
