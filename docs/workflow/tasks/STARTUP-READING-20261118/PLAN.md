# Startup compression plan

Base: `ee509d5d7ce3a4c0fb61cdb9e2668575e3af370d`. Branch: `work/startup-reading-20261118`. Director: `startup-reading-root-e2dfdb529a6f`.

## P01. Archive and checkpoint baseline

Requirements: R01, R02, R03. Verification: Verify exact archived bytes and current refs; confirm early recovery save.

## P02. Compress and map obligations

Requirements: R01, R02, R03. Verification: Compare every original obligation with retained inline or explicitly routed text.

## P03. Review, validate and integrate

Requirements: R04, R05. Verification: Independent review and read-only scenarios; focused checks; verified conditional integration and actual-main checks.

## P04. Verify and save handoff

Requirements: R05. Verification: ZIP manifest and extraction; confirmed save identity; external receipt and lease release.

Project editor owns AGENTS, GOAL and STATUS prose; STATUS lease bytes stay unchanged while another owner holds it. Workflow editor owns START, ROLE, PROTOCOL, HANDOFF and the three project-owned skill bodies. Director owns archives, measurements, task records, integration and delivery. Independent reviewer owns only its assigned evidence file. All Git/index/remote writes remain with the Director.

If main advances, preserve current observations and reapply only the reviewed compression. Do not restore old C267 state, old integration ownership or stale delivery claims.

## Verified integration checkpoint

P01–P03 complete. PR263 merged reviewed source at `e7096a21e018f10e4d51b74cb5360c66eab4598a`; all four actual-main check groups passed and ancestry/automatic branch deletion were verified. P04 is the remaining gate: verify/freeze/save the session ZIP, publish its external receipt, close this task and release ownership. No further product work is selected.
