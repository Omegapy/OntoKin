# Git LFS storage integration tests

These tests require a separately prepared Git LFS 3.8.1 or newer client and Git on `PATH`. They use local temporary repositories, objects and filters, with no remote operations or product/SQLite execution.

```bash
python3 -m unittest discover -s tools/storage_tests -p 'test_storage_identity.py' -v
```

The default `tests/` suite retains its existing dependency contract. This dedicated verifier suite must run when changing the storage profile, migration tools or LFS-aware validation behavior. See [OK-ENG-010](../../docs/engineering/OK-ENG-010-git-lfs-archive-storage.md) for the identity contract, migration procedure and remote-publication acceptance gate.
