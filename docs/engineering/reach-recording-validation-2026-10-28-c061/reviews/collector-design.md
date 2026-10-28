# C061 reader-setup collector design

Prepared by `/root/c061_collector` under the parent-owned C061 scope. This is a static implementation note. No OntoKin import, product request, runtime test, numerical replay, or archive operation was executed by this worker.

## Source and changes

The new `tools/capture_reach_reader_setup.py` is a dedicated extension of the source-bound C060 `tools/capture_reach_recording_work.py`. The C060 file, all product files, and the original request probe are unchanged. A separate entry point avoids misidentifying a composed driver's executable or argument vector. The new entry point preserves C060's request, key, failure-local, raw-byte, source-input, callback and exception evidence formats and adds `reader-setup.json`.

The collector installs 18 higher-level setup wrappers only after the existing `gltf.validate_export` entry observation has admitted the actual native work and construction callback owners. It rechecks the existing native dispatch inventory before installation. It never wraps charged arithmetic, `tick`, `charge`, cache lookup/insertion, native Fraction operations, `_Bounds`, or trace/profile hooks.

All setup targets are restored before the first `_key_comparisons` call. Reader-exit and outer-finally cleanup restore them again. The wrapper list excludes `_verify_certificates`, whose call spans both setup and all key validation. Its pre-key admission and other unwrapped work remain an explicit residual. Nested `_l1` and `_axis_transport` observations run only while an `_axial_derivatives` span is active. Recursive `_assert_projection` calls forward unchanged inside the outermost span.

## Ledger and bounds

- Maximum 4,096 spans and nesting depth 64. Exhaustion records an observation failure and disables further setup observation; it does not alter the product request or its limits.
- Every span has an ID, parent ID, depth, contiguous entry/exit event ordinals, outcome, argument counts/names, and entry/exit work snapshots. Reader entry is event 0; for N completed spans the first-key cutoff is event 2N+1 and event_count is 2N+2.
- All snapshots contain shared operations, admitted Reach operations, and the generic `checkpoint` count. Coarse boundaries additionally copy the complete native work-category dictionary, work-cache occupancy, and bounded independent arithmetic/cache-category occupancy. Nested spans deliberately do not claim complete category attribution.
- The independent offline auditor must derive exclusive work by subtracting immediate children, then add the unwrapped residual. Inclusive parent/child totals are not additive. Zero-charge spans remain ordered by endpoint events.
- `_phase` and `_axial_derivatives` copy exact interval/carrier and within-process reference/state/model identities. A returned phase also supplies its actual source path. `_l1` and `_axis_transport` copy exact typed native scalar/vector operands and results. Fractions, floats, integers, intervals, tuple/list distinctions, and nulls retain explicit type tags. Serialization occurs after product execution.
- Snapshot copying uses exact native types and direct stored fields. It does not call reference helpers, properties, cache operations, source samplers, or charged arithmetic. Primitive-copy depth, element counts and integer bit lengths are bounded.

## Meaning and verification limits

Repeated typed operands and opaque identities are diagnostic observations. They are not proof of live-source authority, safe cache admission, prospective operand widths, or complete-request saving. A future candidate must establish those separately. The collector makes no elapsed-time neutrality or speedup claim.

Span cleanup records argument-object, work-owner, callback-owner and observer preservation. Setup restoration is recorded at the first key, reader exit and final cleanup. The inherited C060 audit can retain its exact wrapper-frame inventory when the request fails in the original key loop, with its collector path explicitly bound to the new file. An early setup failure or observation defect fails the C061 scope; it must not be normalized into an accepted attribution.

Only static parsing has been performed on this worker's file. The parent must publish the exact tooling cut, finish independent review, pause all workers, and run the authorized original control/capture pairs under an exclusive execution window before claiming observation neutrality.
