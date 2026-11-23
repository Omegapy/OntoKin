# P23 ldd-candidate observation review

**Accepted for one bounded raw data observation.** Eleven independent source/launch checks passed; no mandatory finding remains. H0 is unaccepted.

The exact script is SHA-256 `c99af2c7ca26db8fce518419ca980af60fbc0d9cb61257a35a89b2f612b9f93a`; its launch is `16e75599cdbfdfd10d4fa20057753487d029297661333124f26a38c8f672b77b`. The collector reads `/usr/bin/ldd` as data and records its literal loader list, then twice records only each candidate's and immediate parent's file metadata. It never opens or executes a candidate, invokes ldd, imports a project or starts a child process.

The frozen inspector fixes the ldd role and future command to `/usr/bin/ldd`. `_check_resolution` requires every literal RTLDLIST candidate in its original order. An absent candidate has closed keys `path`, `state`, `parent` and must have an existing immediate parent directory. Unlike origin variants, these records cannot use a more distant first-absent ancestor.

Therefore a raw observation of an absent mandatory candidate whose immediate parent does not exist would establish an unrepresentable required input under the frozen source. That is a source-backed prerequisite blocker, not an observed public-inspector error. No such current-host finding is asserted before the collector runs.

The Director must preserve the reviewed 10-second internal and 20-second outer limits, exact clean environment, exclusive output capture and prelaunch hash check. Run once, retain any failure/unknown state, and stop technical work if independent outcome review confirms the first concrete blocker.

Exact descriptors, source anchors and all checks are in `LDD-CANDIDATE-REVIEW.json`.
