# C075 fixture preparation correction 001

The original decision and all original frozen files remain unchanged. Initial execution of the frozen inputs found two preparation errors. The import alias `parts` is a reserved language keyword, so the assembly and generated scenes failed at parsing. Their corrected copies use `libparts`. The wrong-unit point correctly raised the inherited `OKL-E-UNIT`; the original expected file had named `OKL-E-TYPE`.

[Correction 001](../../../examples/polygon-extrusions/acceptance-correction-001.json) selects the new corrected source/expected files and records their exact hashes. The original failed inputs and expectations remain available. No geometry, source-budget, acceptance tolerance, original test or runtime rule changes. The pinned parts library remains byte-identical. All analytic area, volume, winding, topology, materials, motion and sibling expectations retain their original values.

This correction is preparation evidence, not an executed pass. The final acceptance must check both original and corrected hashes, use the explicitly selected corrected fixture names, and retain the original parser/diagnostic failures separately.
