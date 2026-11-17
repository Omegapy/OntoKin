# C260: finite hinge-declaration observation contract

C260 defines what a later independent reader may say about the existing
keyed-rack hinges. A hinge joins two named attachment sites and declares an
axis, angular limits and an initial angle. Those declarations are separate
from object ownership, spatial following and recorded motion.

This increment contains a **contract and input inspection only**. It adds no
hinge reader and establishes no hinge implementation qualification. It follows
the [C258 integrated next task](../localized-repair-c258/INTEGRATED-NEXT-TASK.md)
under [scope #247](https://github.com/Omegapy/OntoKin/issues/247).

## Selected boundary

The future reader will derive class-member hinge declarations from the two
supplied `.ok` files and compare the corresponding rows in the actual GLB JSON.
The supported subset uses literal signed coordinate axes and literal angular
limits/initial values. It resolves ordered endpoint references to declared
sites on the current object or a direct ordinary part. It retains complete
occurrence, definition and source-byte associations.

The existing artifacts contain eight joint rows at each endpoint. They contain
no site table, joint-definition table or joint/site source-span records.
Therefore site identity and definition associations come from the supplied
source; site poses and the resulting world motion remain unobserved here.
No missing artifact field is filled with a producer sidecar or an expected
semantic record.

## Read in order

1. [Version 0.1.0 contract](CONTRACT.md): authority, supported forms, comparison
   policy, refusals and implementation gate.
2. [Field origins](FIELD-ORIGINS.md): source witnesses, actual JSON pointers and
   unavailable artifact provenance.
3. [Input bindings](INPUTS.json) and [baseline inspection](BASELINE-INSPECTION.json):
   exact hashes, 37 source witnesses, eight source-derived joint associations
   and the 16 actual rows across the two artifacts.
4. [Independent control plan](CONTROL-PLAN.md): required future checks; these
   are planned cases, not passed implementation tests.
5. [Next bounded task](NEXT-TASK.md): implement and independently check this
   finite reader after the reviewed contract is integrated and handed off.

## Evidence and limitations

The inspected baseline is published main
`003b3a7827486405c3d00f039c1c9746c9be75fc`, tree
`325c7e50b42000e7c2976e3dd8c3babcec2649ba`. The inspection checked twelve source,
specification and artifact bindings and read the actual GLB JSON bytes without
importing the product parser, evaluator, exporter or C255 expected records.
It confirms that the proposed subset covers both frozen endpoints. It does
not exercise the future control plan.

The [C253 protocol](../localized-repair-c253/README.md), earlier component
implementations, all numerical tolerances and prior failures retain their
existing meanings. Complete semantic records, site-frame transport, motion
agreement, revision authenticity, invalid-edit atomicity, clean rebuilds,
native/model trials and comparative advantage remain separate unmet gates.

Applicable integration checks are independent contract review, exact binding
verification, the unchanged C253 manifest check and the repository documentation
preservation/link check. The integrator records their actual revision and
outcome separately. A specification review cannot substitute for a future
implementation check.
