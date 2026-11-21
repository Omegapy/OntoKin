# C271 P04 historical Node recovery investigation

## Verdict

The required historical Node executable was **not recovered from the inspected sources**. No inspected regular file, decoded complete archive member, Git blob, or parsed pack object result had both the required 126,939,688-byte size and SHA-256 `61ab14cd750fc24d5db53490ec5fc40f756e4b6e136b78cf7004265471d9bd1d`.

This is a scoped negative search result. It is not a claim that the executable is unavailable everywhere, that every historical source is recoverable, or that C225 prerequisites qualify. Incomplete archive prefixes, missing Git bases and inaccessible filesystem directories remain explicit limits. The required historical path and mode remain `/opt/codex/runtimes/codex-primary-runtime/dependencies/node/bin/node`, mode `0755`.

## Authority and source identity

The Director assigned investigator `/root/runtime_recovery` exclusive writes under this investigation directory. The source checkout was supplied at authentic branch commit `6d4324e8fd835351da2db165bf0907a3bf1916bc`; main was `e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d`. The Director later published documentation-only bootstrap commit `e7962d64cad08b52fb32cf4cf34c3f77e1337156`. This investigation retains its original read identities in `SOURCE-READ-BINDINGS.json`.

The governing AGENTS, ROLE, PROTOCOL, worker template and phase record were read. The assignment's shorthand `templates/WORKER.md` did not exist; the governing linked file `docs/workflow/templates/WORKER.md` was read in full. The saved early recovery receipt was confirmed before substantive investigation. No global startup, delivery, nested worker, shared Git/index, task-state, runtime or product-file mutation was performed by this worker.

The cached C262 ZIP was authenticated before use: 532,260,846 bytes, SHA-256 `b8af544f730a4d1f741d47b56eb3fcf76147ed392a9ebb020f3d966f2f305c90`, Library identity `libfile_fde3_f-99755ba096208191b599cd0087fa0a19_2ab2a24d43748191957f9bcc356b59de`. It contains 16,422 physical members. `C262-IDENTITY.json` and `C262-TOP-INVENTORY.json` retain the binding and inventory. The earlier P03 report explicitly excluded nested Git object traversal; this investigation added that inspection.

## Local installed and cached files

`LOCAL-NODE-SEARCH.json` records 522,126 regular-file observations across `/opt`, `/usr`, `/home`, `/root`, `/workspace`, `/tmp`, `/var/cache`, `/var/lib`, `/mnt`, `/srv` and `/app`, with existence recorded for each root. The supplemental `/etc` and remaining `/var` inspection adds 846 observations, for 522,972 total. These are observations, not a count of unique physical inodes. Every regular file was checked for the required size regardless of filename. Files named `node`, `nodejs` or `node-v<version>...` were additionally hashed in full.

Five named candidates were hashed. None matched the required size or digest:

| Candidate | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Primary runtime Node | 126,951,512 | `acbe4b8d9153b841ed0697cbfc4f93e767386620edb745ab9358306c0a6f31aa` | `0755` |
| CUA runtime Node | 126,951,512 | `acbe4b8d9153b841ed0697cbfc4f93e767386620edb745ab9358306c0a6f31aa` | `0555` |
| Playwright driver Node alias | 126,951,512 | `acbe4b8d9153b841ed0697cbfc4f93e767386620edb745ab9358306c0a6f31aa` | Target `0755`; symlink |
| Cached P03 official executable | 126,879,696 | `e32e2d16081cf644f88392934288086e7662529d0d43277c34f7aad2207cfafb` | `0755` |
| Cached official distribution archive | 32,026,916 | `6c172a9ab6718f7b801fb5a7bd486af2ee5e32758086a04b84fcce2aa77095e6` | `0644` |

The first scan's 373 stat errors were all confirmed broken symlinks. The supplement recorded 16 more broken symlinks and three permission-denied directories: `/etc/credstore`, `/etc/credstore.encrypted` and `/etc/ssl/private`. They were not bypassed or inspected further. Virtual/process and ephemeral runtime roots were excluded. Directory symlinks were recorded rather than followed recursively; ordinary root aliases point into the inspected `/usr` tree. The scan is a time-bounded live observation and does not cover deleted files, unmounted layers or remote runtime stores.

## C262 retained archive and Git object inspection

The initial recursive pass identified containers by content signatures, enumerated ZIP and tar members, fully decoded gzip/xz streams where valid, and imported retained Git bundles/packs into an isolated bare object database. It performed no checkout or offline project restore. Every unique stored blob was read in full; size checks did not depend on names.

`C262-OBJECT-NODE-SEARCH.json` records 69 successfully imported bundle/pack payloads, 18,208 enumerated objects and 14,104 unique inspected blobs. The object types are 706 commits, 3,398 trees and 14,104 blobs. There were no exact-size blob candidates. The initial pass identified 529 unique container payloads, including content that subsequently required split-archive or incomplete-prefix classification. The inventories and original parser/import errors remain unchanged.

Thirty-five apparent ZIP errors were first fragments of declared split archives. Their retained manifests were found through actual Git tree/object paths. The two fragment passes verified every part's SHA-256 and size, joined parts in the declared order, and verified the assembled archive's declared SHA-256 and size. They covered all 35 first-fragment paths, corresponding to 35 unique archives. Forty-three manifest records were accepted because eight were duplicate declarations. Their ZIP scans examined 37,798 additional member observations. No expected-size candidate or matching binary appeared. These were archive reconstructions only; no archived script, project or product program was executed.

`C262-DECLARED-FRAGMENTS.json` and `C262-DECLARED-FRAGMENTS-2.json` preserve both passes. Their nested member inventories and source bindings are included in the artifact manifest.

## Residual limits and preserved failures

The following limits prevent a claim of complete historical source closure:

- Two thin bundles could not import because required delta bases were absent. Their retained packs were nevertheless parsed completely and their pack SHA-1 trailers verified. The 29-object C174 pack has a maximum resulting object length of 9,232 bytes; the 197-object local-source-history pack has a maximum of 72,311 bytes. Neither declares an exact-size Node result. Missing prerequisite commits are `038370794d828972cf5a06cdceac50275eda65f0` and `767a1d7e88a946d4936122fe21d5abf769488f81`. Unavailable delta bases were not substituted. A small delta result could itself encode compressed content, so size parsing does not certify all nested contents.
- One 188-byte item with bundle magic is a retained header text record. It has no pack payload and is not a binary source.
- Fragment inspection exposed one additional 20,602-byte author-history bundle. Its valid pack trailer and all 49 object headers/delta result sizes were parsed. The largest resulting object is 206,759 bytes; none has the Node size. Its non-delta objects contain no recognized nested-archive magic. Delta-derived content remains a stated limit because this supplemental bundle was not materialized.
- C239's 538,764-byte truncated XZ produces 93,935,507 available decoded bytes but does not reach the decoder's end marker. Forty-nine tar headers are readable before unexpected end-of-data. None declares the Node size. No missing suffix was invented, and this original archive remains incomplete.
- Five retained incomplete ZIP prefixes expose 242, 518, 2,030, 922 and 2,022 local-file headers respectively. Standard local-header/deflate inspection stops within compressed member data in each. None declares the Node size; the largest available decoded member is 8,259,005 bytes. Central-directory/original archive completeness is not claimed.

The precise sources, hashes, sizes, headers, errors and available-prefix observations are in `UNRESOLVED-PACK-SIZES.json`, `C262-ERROR-PATHS.json` and `RESIDUAL-SOURCE-LIMITS.json`. No search limit was silently converted into a successful closure claim.

The first fragment-investigation script stopped with a `KeyError` because a duplicate-container-reference inventory row lacked `size_bytes`. The original script and failure log were preserved. The follow-up changed only the investigator's field-presence filter and completed. This was an investigation-tool failure, not a product test failure. Both successful and failed Git index attempts remain in `git-logs/` and `GIT-COMMANDS.jsonl`.

## Blocker and next action

The concrete blocker is the lack of an authenticated copy of the required historical Node bytes among the inspected installed/cached files and retained recoverable payloads. Frozen C225 requires those exact bytes at its absolute runtime binding; version text alone cannot satisfy that requirement. No C225 helper, Node executable, `ldd`, product/native test or full routine was run. No shared runtime replacement, namespace installation, guard/pin/test change, recompilation or speculative binary transformation was attempted.

The next action is a **separately versioned current-host qualification decision and review**, as already contemplated by C225's preparation contract. That proposal should bind the selected current interpreter, loader/shared libraries, absolute paths/aliases and the unchanged 24 retained dependency files; define fresh behavioral and refusal evidence for the new environment; preserve all frozen historical inventories, expectations, per-source budgets and previous failures; and obtain independent acceptance before any aggregate rerun. This phase implements none of that proposal and does not close R03 or parent acceptance.

There are no active investigator processes or unknown writes at this checkpoint. The Director owns review, publication, task state and saved delivery.
