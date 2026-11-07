# Independent runtime authority follow-up

**The reviewed authority corrections pass at `ae91606e1d8b2128c12422403112f3ad0c313ac7`; final integration acceptance remains pending.** The companion JSON pins every reviewed file and exact verification receipt.

The first independent reproduction demonstrated that retaining a Python clock function's identity did not retain its executable code. A poll replaced the same reader's code, the changed clock mutated source after the sole source scan, and the ledger accepted the tick. The corrected candidate now refuses before the changed code runs, preserves the exact consumed count, and leaves the source sentinel unchanged.

Source inspection covers the complete successful native clock path: executable function state, actual builtin name resolutions, the original math/isfinite and monotonic bindings, native finite clock fields, and ordinary attribute lookup and assignment. The elapsed-time reader receives the corresponding executable and field-lookup admission. Original polls and custom clocks retain their full checks. A poll that reads the original clock itself retains the second source scan.

The public evaluator now captures native source authority before its inherited first zero-charge callback. Nested record-count preflights restore the original guard and admit it after successful scoped use. I independently compared all five retained public-route result byte streams and all five full callback/charge trace byte streams: all ten match exactly, without normalization or sampling. Nineteen focused actual unit methods also passed in my replay.

Retained dictionary views remain live views of strongly retained native source owners. Complete type, length and identity checks still cover every key/value/member and Fraction integer slot. The optimization removes repeated view allocation, not source coverage.

This is a source-bound follow-up review. The final corrected artifact/Agent/native/hostile matrices and the independent reader's general exact-axis completeness are still distinct open integration gates.
