# C104 verification scope

The C104 coordinator resumed the finite-torque draft at `18e5a69cfc4ea1470b0e31d56aa4fe75a160b532`. The prescribed first run tested the preceding packaging revision, `7cb961ed1ebed86eb1bbea6bafe5794660fb0518`, tree `534fe7f6050f45b1b9e3eda43f61c789e70e2878`. The two additional files at the starting head record C103 results.

The verification exposed three omissions from the isolated test checkout. The C104 correction at `643ab64523fbb18a244a788776d36076875ae623`, tree `133787f8877795f3ee5e63a5d4a6d16f907cc399`, changes the input lists in `tools/check_local.py` and adds a Git-backed regression test in `tests/test_local_checks.py`. The follow-up full run uses that revision. The C104 evidence publication is confined to `docs/engineering/torque-verification-c104/`.

The scope also covers review of browser captures, the frozen world-rate inventory, installed-wheel execution and a bounded interruption rehearsal. Main integration and release each have a separate acceptance procedure. The first-use documentation branch and frozen newcomer trial have their own scope.
