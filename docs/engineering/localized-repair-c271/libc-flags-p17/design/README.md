# P17 reviewer entry

Read `DECISION.md`, `SOURCE-EVIDENCE.md`, `CONTROL-CONTRACT.md` and `FUTURE-SURFACE.json`. Review the exact source bodies and cited ranges under `sources/`, then the literal controls and expectations. `CANDIDATE-MANIFEST.json` binds every payload byte; `FIXTURE-MANIFEST.json` separately binds inert inputs. `READSET.json` records full and partial reads without equating a hash check with a semantic read.

The author permits only static integrity verification of these artifacts. From any directory, supply the candidate directory, authentic repository and the verified historical input directory:

```
python3 -I -B CANDIDATE/verify_static.py --candidate CANDIDATE --repo ONTOKIN --historical-inputs P15_INPUTS --report FRESH_EXTERNAL_REPORT.json
```

The report path must not exist. The checker imports only Python standard-library modules and never imports a product module. It does not evaluate the proposed flags rule or run a product control. Independent review should challenge the design and literal expected semantics with separately authored inspection rather than treating this checker as acceptance.

`INPUTS.json` pins the predecessor P16 archive and historical P15 source/package/capture inputs. Those large originals remain exact external dependencies of this candidate; it is not a full offline restoration package. The Director owns publication, the full phase handoff and final save.

Candidate source-time status is proposed. No future adoption, review result, Git commit, saved receipt or current-host success is fabricated inside this freeze. Later reports bind this candidate's actual manifest hash externally.
