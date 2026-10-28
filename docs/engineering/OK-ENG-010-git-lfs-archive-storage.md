# OK-ENG-010: Git LFS archive storage

Version: 0.1.0. Scope: repository storage and verification tooling. This contract does not change OntoKin source semantics, numerical limits, release requirements or the authority of historical evidence.

## Current state

The owner requested Git LFS on October 28, 2026. The repository's **Include Git LFS objects in archives** setting was enabled and independently observed after reload during C059 reconciliation. That setting concerns GitHub-generated ZIP/tar downloads; it does not convert files or establish successful object uploads. The separate storage implementation supplies exact migration planning and pointer/payload verification. [GitHub's archive documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/managing-git-lfs-objects-in-archives-of-your-repository) explains the tracking and bandwidth behavior.

**Repository conversion and authenticated remote availability remain pending.** No archive pointer has been published by this implementation. The connected GitHub Git-data operations cannot transfer LFS payloads, and the current local Git executor has no authenticated route to the private repository. Preserve the ordinary Git payloads until authenticated upload and independent retrieval succeed. An already authenticated maintainer environment can execute the procedure below without another design decision.

The committed [root attributes](../../.gitattributes) activate tracking for future archive payloads only under the currently unused `docs/engineering/lfs-archives/` directory. Its four rules cover ZIP, numeric ZIP parts, TAR.XZ and TAR.GZ. They match no existing tracked or working-tree payload, so all existing archive bytes and Git identities remain unchanged. This completes repository tracking configuration; successful LFS object upload and independent retrieval remain separate requirements.

The implementation and its measured focused checks are recorded in [the storage validation record](lfs-storage-validation-2026-10-28/README.md). C059's runtime checks remain attributed to C059's exact implementation; these later verification-tool changes have their own evidence.

## Bounded storage profile

`engineering-archives/0.1` permits only regular nonexecutable archive files beneath `docs/engineering/`: `.zip`, `.zip.partNNN` with exactly three decimal digits, `.tar.xz` and `.tar.gz`. Active tracking is initially restricted to the unused `lfs-archives/` subdirectory. For the later migration of existing archives, the planner writes these expanded proposed root attributes to an external output directory:

```gitattributes
docs/engineering/**/*.zip filter=lfs diff=lfs merge=lfs -text
docs/engineering/**/*.zip.part[0-9][0-9][0-9] filter=lfs diff=lfs merge=lfs -text
docs/engineering/**/*.tar.xz filter=lfs diff=lfs merge=lfs -text
docs/engineering/**/*.tar.gz filter=lfs diff=lfs merge=lfs -text
```

Readable manifests, `.ok` programs, specifications, code, schemas, oracles, PNG/SVG evidence and ordinary example GLBs remain ordinary Git files in this profile. A `*.part*` rule would also select part manifests and must not be substituted. Preserve each archive part and member exactly; storage migration is not permission to repack historical evidence.

Use a normal new commit. Keep every original commit and the archival history reachable. No-rewrite adoption retains old binary Git objects; it does not shrink existing history. The [Git LFS migration manual](https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-migrate.adoc) distinguishes ordinary history rewriting from its explicit no-rewrite mode. The procedure here uses exact-path `git add --renormalize` in a new commit. Adding `.gitattributes` alone does not convert already tracked payloads; [GitHub's configuration procedure](https://docs.github.com/en/repositories/working-with-files/managing-large-files/configuring-git-large-file-storage) requires adding, committing and pushing associated files.

## Two identities, both checked

`tools/storage_identity.py` defines `ontokin.storage-binding/0.1`. For ordinary tracked files, the actual bytes must still equal the captured Git blob. Pointer-looking text without committed LFS attributes retains its ordinary-file meaning.

For LFS files, the verifier records the pointer's Git object separately from the payload. It requires the canonical three-line v1 pointer, a lowercase SHA-256 object ID and canonical nonnegative byte length. It independently hashes the hydrated file and checks its exact size. Missing, unhydrated, malformed or corrupt data fails. Unsupported pointer extensions and LFS selection outside the bounded profile fail explicitly.

Attribute authority comes from the identified commit, or the stage-zero index for the source-corpus snapshot. A private temporary Git repository resolves only those attribute bytes. Source `.git/info/attributes`, global/system attributes and caller Git overrides cannot redefine that authority. No source credentials or remotes are copied.

The local driver now inventories and copies root `.gitattributes` and `.lfsconfig` when present. Its isolated Git repository independently verifies copied hydration, installs only known local offline filters and populates its own verified object cache. The filters skip automatic downloads and disable hooks. No source configuration or shared LFS cache is inherited. Git LFS **3.8.1 or newer** must be separately prepared when the checkout actually contains LFS-selected files; ordinary non-LFS validation does not require that client.

`run_reach_source_corpus.py` preserves its original payload-size, payload-SHA-256 and raw-payload-Git-blob fields and adds an explicit storage binding for LFS inputs. The committed pointer's Git identity is never substituted for the actual evidence bytes. Existing release records and raw equality checks for their eligible ordinary source inputs are unchanged.

## Prepare and apply the exact migration

Use the current integrated main as the base and one bounded work branch under [the integration policy](OK-ENG-009-development-integration-and-branch-lifecycle.md). Check the integration lease before publication. The following examples use external directories that must be new; replace the branch and paths with the actual reviewed scope.

1. Prepare Git LFS 3.8.1 or newer and authenticated ordinary Git/LFS access on the chosen executor. Record the actual client version and access result without retaining credentials. Inspect `git remote -v` and preserve any existing pre-push hook when installing repository-local LFS support. Do not set `lfs.allowincompletepush` or place credentials in `.lfsconfig`.
2. From a clean checkout, prepare the immutable path and payload plan:

   ```bash
   python3 tools/prepare_lfs_archives.py --output-dir /tmp/ontokin-lfs-plan
   ```

   Review `plan.json`, `gitattributes.proposed` and `archive-paths.nul`. The command verifies every selected ordinary archive against its original Git blob and records its payload SHA-256/length and proposed pointer identity. It changes no repository files, configuration, refs or object storage. It accepts either no attributes or the exact reviewed bootstrap rules with zero existing LFS payloads. Any other attributes, nested attributes, LFS config or existing LFS payloads require a separately reviewed incremental plan.

3. After authentication is available, apply the exact attributes and convert only the planned paths:

   ```bash
   git lfs install --local
   cp /tmp/ontokin-lfs-plan/gitattributes.proposed .gitattributes
   git add -- .gitattributes
   git add --renormalize --pathspec-from-file=/tmp/ontokin-lfs-plan/archive-paths.nul --pathspec-file-nul
   git diff --cached --stat
   git commit -m "Store engineering archives in Git LFS without rewriting history"
   git lfs fsck --objects --pointers HEAD
   python3 tools/prepare_lfs_archives.py --verify-plan /tmp/ontokin-lfs-plan/plan.json --output-dir /tmp/ontokin-lfs-local-verified
   ```

   The verification command requires the original planned commit to be an ancestor, permits changes only to the exact planned archives and root attributes, checks the proposed attributes and each pointer, and verifies that every hydrated payload still equals its original bytes. It does not establish remote availability.

4. Upload the local commit's objects before publishing its branch ref, using the actual remote and scope:

   ```bash
   git lfs push origin HEAD
   git push origin HEAD:work/lfs-archive-migration
   ```

   Retain successful upload/verification receipts. A failed upload leaves the migration unaccepted. Do not publish the pointer tree through a different API to bypass the failure.

5. Fetch that branch into an independent checkout with an empty LFS cache through the authenticated remote. Hydrate its payloads, make the original plan commit available for ancestry/tree comparison, and run the same `--verify-plan` command there with a new output directory. Bind its exact commit, successful remote retrieval and payload hashes. A second local cache copy is not a remote-download test.
6. Run the dedicated storage tests and documentation/evidence checks on the exact resulting candidate, then reconcile and merge through the expected-head integration procedure. Check the resulting main. Leave historical manifests and C059 execution attribution unchanged; retain the new storage evidence separately.

Both manual hosted workflows request `lfs: true` for their existing checkouts, so a deliberately authorized future hosted run will hydrate tracked objects. Their `workflow_dispatch`, default-false input and job guards remain unchanged. No hosted job was dispatched by this storage work. The ordinary local validation path remains the default.

## Focused verification

With the separately prepared Git LFS client on the task's `PATH`:

```bash
python3 -m unittest discover -s tools/storage_tests -p 'test_storage_identity.py' -v
python3 -m unittest discover -s tests -p 'test_local_checks.py' -v
python3 docs/maintenance/reorganization-2026-10-17/verify_reorganization.py
```

The dedicated suite uses real isolated Git repositories and local LFS objects. It exercises ordinary-file strictness, literal pointer text, malformed/unhydrated/corrupt/missing payloads, attribute authority, cache/configuration isolation, source snapshots, exact migration scope and unchanged payloads. Keeping real-client tests in `tools/storage_tests` avoids making Git LFS an unrelated prerequisite for every default core test run. The tests perform no remote transfers and import no product runtime or SQLite store.

Local object verification, repository archive settings, successful upload and independent authenticated retrieval are four distinct facts. Report each from its own observed evidence; only the latter two establish published payload availability.
