# C193 independent recovery audit

**Pass for the assigned evidence scope. No evidence blocker was found.**

Reviewed candidate `bc8c0918045248cd3d34c64e40c135fff0eec985`, tree `631034be6fcd5249af753a9852a13f76baf44493`, from the isolated `work/c193-recovery-review` checkout. No repository file was changed. This recovery executed zero native builds, zero saved-scene simulations and zero receiving-application jobs.

## Verified results

- The recorded-only replay passed all 14 artifact audits. Every retained 481-sample scene replay matches its original capture, all repeats and both authoring-route comparisons are exact, and all base/right-lane native matrices and bounds match C192. The fresh replay summary is byte-identical to the previously published summary (`71f47214748346433b5fa65ed5b22434f5b536df23f5407fdcef84d1ed1a2d20`).
- The highest continuous mapping bound remains **0.181935687 mm**, below the unchanged **0.2 mm** gate. E and F remain at 0.116436993 and 0.181935687 mm respectively. All published per-case numerical values match exactly.
- All five archive hashes and **2,177 payload-file identities** match their manifests. All 11 implementation modules and eight adoption pins match. The adoption text and pins also match their bytes in publication commit `868949b9641eb96d7f59f5e18adff987f2d51da7`. Its timestamp is 16:43:15 UTC; the retained formal build start is 16:43:49.331 UTC. Publication/readback reconciliation belongs to the coordinator.
- All **474 historical files** match both the frozen inventory and the actual blobs in C192 main commit `294d84ac5c5a15e07d042e5225646c2dab440293`.
- The fresh recorded lifecycle audit passes **42 cases across 19 methods**, two store-namespace controls and preservation of the accepted state and 33 artifact files. Its complete report is byte-identical to the retained lifecycle review. Cancellation remains 522.436 ms against the original 2,000 ms limit; descendant cleanup is a retained-receipt finding.
- All **28 receiving paths / 11 GLB hashes** match the formal outputs. Khronos receipts retain zero errors, zero warnings and 12 informational sampler findings. Three.js receipts cover 84 poses. Six Blender imports and 18 PNGs match their recorded inputs and hashes. All pinned receiving dependencies and scripts match C191 originals.
- I visually inspected all **18 original panels** in the six retained review sheets. Pixel comparisons confirm that each displayed panel equals its original PNG. Enabled cases show stop contact; D shows the intended pass-through. The assemblies remain visibly intact, with fixed base/stops and right-lane final clearance. These three-pose views support, and do not replace, the continuous numerical checks.

The original receiving execution summary still records visual review as pending at the end of rendering; the subsequent visual receipt and combined result establish its completion. The inherited C191 render labels and actual eight-thread CPU setting remain accurately interpreted in the existing receiving note.

## Provenance limitation

The original native worker commit `61d20e9a941b14cea091dc38ed1e43232280ecb5` and reviewer commit `8e7123f120e1bfb02c21c26a1e78013ad0813275` are absent from this recovered Git object database. The coordinator reports they are not accessible remotely, and the original scratch checkouts are gone. The current publication retains verifiable implementation, adoption and evidence bytes; this does **not** re-establish the original worker ancestry. Record that limitation in a new recovery note and preserve the original receipts as written. It did not prevent exact-byte or numerical revalidation.

## Remaining coordination gates

The coordinator owns the current legacy regression disposition, serialized main integration, post-merge checks and C193 handoff with C194 next-task instructions. This audit does not close those gates, rerun the participant comparison, or establish a general authoring advantage.

Machine-readable result: `AUDIT.json`. Detailed byte checks: `retained-byte-audit.json`. Recorded numerical replay: `recorded-replay/summary.json`. Recorded lifecycle replay: `lifecycle-recorded-audit.json`.
