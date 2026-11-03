"""Independent .22 storage for immutable source and image revisions."""
from contextlib import contextmanager
import sqlite3
from threading import Lock

from .torque_protocol import TorqueProtocol
from .texture_store import TextureProgramStore


class TorqueProgramStore(TextureProgramStore):
    def __init__(self, path, implementation, *, protocol=None):
        self._connection_lock = Lock()
        self._connection_busy = False
        self._reuse_ready = False
        self._wal_keeper = None
        super().__init__(path, implementation, protocol=protocol or TorqueProtocol())
        # An idle autocommit handle avoids repeated setup and last-connection
        # WAL checkpoints. It never retains a transaction or a read snapshot.
        # Overlapping/nested contexts use the inherited fresh connections;
        # all requests keep their original transaction boundaries.
        keeper = None
        try:
            keeper = sqlite3.connect(self.database_path, timeout=10,
                                     isolation_level=None, check_same_thread=False)
            keeper.row_factory = sqlite3.Row
            keeper.execute("PRAGMA busy_timeout=10000")
            keeper.execute("PRAGMA synchronous=FULL")
            # One fixed, bounded SQLite page cache, independent of requests
            # and of the separate at-most-64-MiB immutable byte proof.
            keeper.execute("PRAGMA cache_size=-8192")
            # Opening a handle alone does not join the WAL until it reads.
            keeper.execute("SELECT value FROM metadata WHERE name='schema_version'").fetchone()
            self._wal_keeper = keeper
            self._reuse_ready = True
        except BaseException:
            if keeper is not None:
                keeper.close()
            super().close()
            raise

    @contextmanager
    def connection(self):
        with self._connection_lock:
            cached = self._wal_keeper if self._reuse_ready and not self._connection_busy else None
            if cached is not None:
                self._connection_busy = True
        if cached is None:
            # Do not wait for a checked-out connection, share its transaction,
            # or serialize a callback's cancellation behind its own work.
            with super().connection() as db:
                yield db
            return
        try:
            yield cached
        finally:
            try:
                # The inherited transaction context commits or rolls back
                # first. A caller leaving an explicit unfinished transaction
                # gets the same rollback as closing its former fresh handle.
                if cached.in_transaction:
                    cached.rollback()
            finally:
                with self._connection_lock:
                    self._connection_busy = False
                    release = self._wal_keeper is not cached
                if release:
                    cached.close()

    def close(self):
        try:
            super().close()
        finally:
            with self._connection_lock:
                keeper, self._wal_keeper = self._wal_keeper, None
                release = not self._connection_busy
            # An active borrower closes the handle when its context ends.
            # close() never invalidates a connection in another thread.
            if keeper is not None and release:
                keeper.close()
