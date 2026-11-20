# H26 inspection correction

During preliminary inspection, this worker told the parent that the permission
control had run as UID 0 and therefore had only injected-denial evidence.
That statement was an unverified assumption about an earlier/environmental
context. It was corrected immediately after reading the selected latest
historical result.

The controlling evidence is
`docs/engineering/localized-repair-c268/evidence/finalization-a3de3dd23bbf/main-integration/c268-controls/results.json`,
SHA-256 `4b76b7b56de0e9f0e0d8af69615391fc787de413a79d3d2e1e42f920e109c6db`.
Its `/notes/0` records `actualPermissionDenial: true` and
`effectiveUid: 1000` for the actual mode-000 permission control. The original
run separately records injected EACCES outcomes. The result is bound to the
retained actual-main execution at
`5084dd69312e8da5a49aadd33cf83ba56db7c058`.

The map and report use that corrected result. The preliminary statement was
an **audit interpretation error**, not a product failure, control failure or
newly executed experiment. No behavioral rerun followed it. This note keeps
the original assumption and its resolution visible rather than silently
replacing the earlier account.

## Final document patch transport interruption

The first attempt to add the final inspection-log reference to `REPORT.md`
returned `apply_patch verification failed: Failed to read file to update ...:
exec-server transport closed`. The subsequent file listing and report tail
confirmed all saved artifacts remained present and that the attempted text
had not been applied. The same document-only patch was then applied. No
behavioral operation, Git mutation or unresolved write was involved.
