# The .venv check: the failed first attempt and its rerun

Result review 001, finding R-01. Times are UTC. Paths are named relative to the clone.

- **First attempt (22:17:08Z),** inside `run_preparation.sh`, after the `.venv` install. The
  Director's check script `venv_verify.py` crashed before checking anything, with
  `ValueError: unsupported marker: python_version < '3.13'` (`venv-verify.txt`).
  - **Cause:** its marker parser accepted only double quotes, and the installed METADATA quotes the
    version with single quotes.
- **The failed version was not kept.** The fix overwrote it. Two edits were made to the function
  `marker_applies`, and nothing else in the script changed:
  1. The double-quote pattern `python_version\s*(>=|<=|==|!=|<|>)\s*"([0-9.]+)"` became a comment
     line and `python_version\s*(>=|<=|==|!=|<|>)\s*(["'])([0-9.]+)\2`, which accepts either
     quote style. The version is now taken from group 3, and the function returns on a match.
  2. The old two-line return on a match, which read group 2, was removed.

  The net change is one line, which matches the shift of the traceback's line numbers
  (55, 67, 144 and 171 before; 56, 68, 145 and 172 after).
- **The fixed script:** SHA-256 `ef6cc0f5c4da36988044cc8f9f57db01e30b7609e751d7cd6156ac515277cefc`.
- **Rerun (22:17:58Z).** It ran from the worktree root, after a check that HEAD was the bound
  commit `601f3936` and that `git status --porcelain --ignored` showed only `.venv/`. It used the
  retained snapshots, and nothing was installed again. Exit status 0, result
  `venv-verify-002.json`:

  ```sh
  .venv/bin/python -I -S -B ../OntoKin-local/c271-p34/director/venv_verify.py \
    ../OntoKin-local/c271-p34/receipts/run-001/venv-before.json \
    ../OntoKin-local/c271-p34/receipts/run-001/venv-after.json \
    ../OntoKin-local/c271-p34/plans/venv-expectation.json \
    ../OntoKin-local/c271-p34/receipts/run-001/venv-verify-002.json
  ```

- **Clean check afterwards (22:31:44Z):** HEAD is `601f3936`, and `git status --porcelain --ignored`
  shows only `.venv/`.
- **Independent support:** the result reviewer W2 reproduced every check the script makes, from the
  wheels and the files, without the script ([RESULT-REVIEW-001](../reviews/RESULT-REVIEW-001.md)).
