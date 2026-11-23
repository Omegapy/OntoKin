# Seven-wheel provenance review

**Provenance consistent; current P21 payload verification pending.** Missing wheel bytes in P22 are a remediable external dependency, not a phase blocker.

The supplied P22 amended archive contains no `.whl` members or manifest payload hashes equal to the seven wheels. Its SOURCE-INPUTS record explicitly points to the external P21 handoff. The exact P21 wheel inventory agrees with P20 preparation results, the P20 installation report, and the lock at frozen source `527368bd5195c439762b43e2cc836ff9822213f8`.

## Exact retrieval archive

- Filename: `OntoKin_C271_P21_H0_Plan_Handoff_2026-11-22.zip`
- Library path: `/OntoKin/OntoKin_C271_P21_H0_Plan_Handoff_2026-11-22.zip`
- Stable ID: `libfile_fde3_f-f7764c5437c0819187cf0a63308bdd64_2ab2a24d43748191957f9bcc356b59de`
- Backing file ID: `file_0000000011ac81f5b70aa78d1332480b`; version `0`.
- Bytes: 9327161; SHA-256: `ba03995347ed65a5a37b4283211841daf4da74fe4a04dbe0617f9e833e9bb64f`.

## Seven members

All seven members are under `inputs/wheels/`. Their historical wheel modes are `0o644`; no current-host mode is inferred.

| Filename | Bytes | SHA-256 |
| --- | ---: | --- |
| attrs-26.1.0-py3-none-any.whl | 67548 | `c647aa4a12dfbad9333ca4e71fe62ddc36f4e63b2d260a37a8b83d2f043ac309` |
| jsonschema-4.26.0-py3-none-any.whl | 90630 | `d489f15263b8d200f8387e64b4c3a75f06629559fb73deb8fdfb525f2dab50ce` |
| jsonschema_specifications-2025.9.1-py3-none-any.whl | 18437 | `98802fee3a11ee76ecaca44429fda8a41bff98b00a0f2838151b113f210cc6fe` |
| pillow-13.0.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl | 7144542 | `42d63be3af4f9b951b199b0a9d23365d37ab14687e6d77b74940432c8515c4ca` |
| referencing-0.37.0-py3-none-any.whl | 26766 | `381329a9f99628c9069361716891d34ad94af76e461dcb0335825aecc7692231` |
| rpds_py-2026.5.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl | 376280 | `b6825cc329b290e93c5f6a9be2393118a763f6ccf6abd83704e0c102ca583644` |
| typing_extensions-4.16.0-py3-none-any.whl | 45571 | `481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8` |

The seven payloads total 7769774 bytes. Original P20 archive: `OntoKin_C271_P20_Isolated_Environment_Handoff_2026-11-22.zip`, 9137029 bytes, SHA-256 `1a37a3e5e535c74fba366382ae8a1c3a80c6b1150caa436e24a5a98a03f7f632`; Library identity and source/readset details are in WHEEL-PROVENANCE.json.

No inconsistent hash, size, package version, or archive identity was found. The next verification is the newly materialized P21 archive and its seven members. Previous `manifest_equal` and `INSTALLED_EXACT` reports remain historical evidence. Do not use their old wheelhouse paths as current inputs.

This reviewer performed no download, import, installation, historical-code execution, Git mutation, or Library write. No active job remains.
