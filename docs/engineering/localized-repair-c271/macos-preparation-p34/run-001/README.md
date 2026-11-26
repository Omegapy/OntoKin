# run-001: portable copies of the preparation's run evidence

These files are path-portable copies of the exact files beside the clone, in
`../OntoKin-local/c271-p34/receipts/run-001/`. The SHA-256 of each exact file is in
[EXACT-RECEIPTS-SHA256SUMS.txt](../EXACT-RECEIPTS-SHA256SUMS.txt).

The copies differ from the exact files in these ways only:
- **Labels:** the worktree root, the evidence root, the base installation's prefix and the name of
  its package manager are replaced by `<worktree>`, `<local>`, `<prefix>` and `<package-manager>`
  (result review R-02).
- **Trailing spaces:** in `00-steps.txt`, the two dry-run lines end without the trailing space
  that the run script wrote after their empty flag list.

`venv-verify-rerun.md` is a record written for this copy, not a copy of an exact file.
