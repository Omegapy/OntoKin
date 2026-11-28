"""Independently frozen controls of C271-P37 for the corrected derived route of the 0.2.0 source check.

C271-P37, stage S4, worker W2, the independent control author, who wrote none of the implementation
(W1's correction, or MI's), the contracts or the decision. The expected outcomes come from P05's contract
section 3 and from sections 1, 8 and 9 (MC19, MC21) of ontokin.current-host-readback/0.2.0. The contract
names no rule for status lines; where these controls need one, they take it from C271-P37 DECISION-001,
which states it within those sections. docs/engineering/localized-repair-c271/derived-workspace-p37/
CONTROLS-FROZEN.json records each control's inputs, entry point, expected outcome, expected starts, label
and sources. One test method is one control, named test_cNN_<case>; its docstring starts with its label.
An implementation defect is corrected in the implementation, never in these expectations.

Labels. "Real": the code under test runs with no boundary substituted. The fixture trees are synthetic,
and Git runs through a /bin/sh wrapper that logs each start and execs the Git found on PATH; the wrapper
is bound with tools.check_local.bind_git, as a qualifying run binds HOST's Git, or, for an ordinary run,
stands first on PATH. "Simulated": one named boundary produces the case's condition. "Mocked": named
components are replaced by stand-ins, and the 0.2.0 provider labels its own records "mocked".

Starts. No control starts Node, ldd, codesign or otool. Inside each recorded window, a recorder keeps the
argv of every subprocess start, and an os-level spawn fails the control. The fixtures start Git directly,
outside the recorded windows. The account's global Git ignore and attributes files are kept out:
XDG_CONFIG_HOME names an empty directory during each control (Q-10 of gate MR's freeze review).

Temporary directories are resolved (realpath). No machine path is hard-coded.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock

from prototypes.static_tray_v01 import current_host_readback_v02 as provider
from tools import check_local


# ---------------------------------------------------------------------------
# Values fixed by the contract, the decision and the driver (CONTROLS-FROZEN.json gives the sources)
# ---------------------------------------------------------------------------

SOURCE_SCHEMA = "ontokin.current-host-readback-source/0.2.0"
CONFIG_SCHEMA = "ontokin.current-host-readback-config/0.2.0"
CONTRACT_ID = "ontokin.current-host-readback/0.2.0"
CONTRACT_MD = "docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md"
ADOPTION_RECORD = "docs/engineering/localized-repair-c271/macos-implementation-p33/ADOPTION-AMENDMENT-001.json"
SOURCE = "CH-SOURCE"
WORKSPACE = "CH-WORKSPACE"
DIRTY = "Dirty source: "
UNTRACKED = "Untracked source input: "
MALFORMED = "The copied-source inventory record is malformed"
OTHER_CHECKOUT = "Provider belongs to another source checkout"
UNBOUND = "Source reads require the selection's bound Git executable"
IDENTITY = "Source commit/tree differs or is unavailable"
INVENTORY_DIFFERS = "Complete CPU source inventory differs"
# The observer's path check, which the source set's walk applies to each source role before its own test.
PATH_MISSING = "Bound path or ancestor is missing: "
LOCKED_DIFFERS = "Locked file identity differs: "
COPY_LINK = "Cannot copy a source symbolic link: "
INVENTORY_LINK = "Source file is a symbolic link: "
REFRESH_FAILED = "Cannot record the isolated workspace's index stat data: "
REFRESH = ["update-index", "-q", "--refresh"]
OS_SPAWNS = ("system", "popen", "posix_spawn", "posix_spawnp", "fork", "forkpty", "execv", "execve", "execvp",
             "execvpe", "spawnv", "spawnve", "spawnvp", "spawnvpe")
FORBIDDEN_PROGRAMS = ("node", "ldd", "codesign", "otool")
PLATFORM_LEAF = "control: mocked platform metadata leaf"
ORDINARY = {"status": "absent", "run_kind": "ordinary"}
# The summary of tools/check_local.py run() at the declaration commit 2f728998, for a run that reaches its end.
SUMMARY_KEYS = {"schema_version", "profile", "selected_roles", "started_at", "status", "source_root", "environment",
                "git", "steps", "release_certified", "full_product_conformance_certified", "remote_checks_executed",
                "limits", "planned_steps", "readback_selection", "git_binding", "source_inventory",
                "workspace_generated_exclusions", "workspace_storage", "workspace_git", "git_after",
                "git_revision_unchanged", "source_unchanged", "pending_external_cases", "not_executed_steps",
                "finished_at", "duration_seconds", "exit_code"}
WORKSPACE_GIT_KEYS = {"available", "local_head", "local_tree", "tracked_worktree_status", "untracked_source_files",
                      "head_is_base_revision", "source_inventory_includes_untracked_files", "remote_head_verified",
                      "index_basis", "copied_worktree_changes_preserved", "source_staging_preserved"}
TIMES = ("started_at", "finished_at", "duration_seconds")

# The real tree's seven tracked entries outside the copied set (FZ-01; S2's measurement).
SKILLS = ("communication", "ontokin-delivery", "ontokin-learning", "ontokin-session", "to-implementation-plan", "to-trd")
SEVEN_LINES = [" D .claude/.gitignore"] + [" D .claude/skills/" + name for name in SKILLS]

FILE, LINK = "file", "link"
UNCOPIED_FILE = ".claude/.gitignore"
UNCOPIED_LINK = ".claude/skills/alpha"
GENERATED = "examples/visual/demo-data.js"
GENERATED_PRODUCT = "examples/visual/a.glb"
NOTES = "docs/notes.md"
# Every other kind of tracked path that the driver's copy leaves out, by the decision's definition of the
# copied set: a first component outside SOURCE_DIRS (other than ROOT_FILES), or a component that ignored() matches.
OTHER_UNCOPIED = {
    ".claude/hooks/check.sh": (FILE, b"#!/bin/sh\nexit 0\n", 0o755),
    "Makefile": (FILE, b"all:\n\t@true\n", 0o644),
    "outside/nested/deep/notes.txt": (FILE, b"nested outside the copied set\n", 0o644),
    "tools/build/generated.py": (FILE, b"print('an ignored directory component')\n", 0o644),
    "docs/_build/page.html": (FILE, b"<p>an ignored directory component</p>\n", 0o644),
    "tools/node_modules/package/index.js": (FILE, b"module.exports = 1;\n", 0o644),
    "tools/node_modules/.bin/tool": (LINK, "../package/index.js"),
    "docs/.env": (FILE, b"CONTROL=1\n", 0o644),
    "TRDs/.env.local": (FILE, b"CONTROL=2\n", 0o644),
    "docs/.env.example": (LINK, "../README.md"),
    "fixtures/__pycache__/cached.cpython-312.pyc": (FILE, b"\x00control bytecode\n", 0o644),
    "tools/stale.pyo": (FILE, b"\x00control bytecode\n", 0o644),
}


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_sha256(path):
    return digest(Path(path).read_bytes())


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def remove(path):
    path = Path(path)
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif os.path.lexists(path):
        os.unlink(path)


def write(path, data, mode=0o644, *, mtime=None):
    """Create or replace one regular file with exactly these bytes and this mode."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    remove(path)
    path.write_bytes(data)
    os.chmod(path, mode)
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


def link(path, target, *, mtime=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    remove(path)
    os.symlink(target, path)
    if mtime is not None:
        os.utime(path, (mtime, mtime), follow_symlinks=False)
    return path


def descriptor(path):
    data = Path(path).read_bytes()
    return {"path": str(path), "sha256": digest(data), "size_bytes": len(data),
            "mode": oct(stat.S_IMODE(os.lstat(path).st_mode))}


def provider_reads(root, commit):
    """The five reads of the source check, in order, as their argv after the Git executable."""
    prefix = ["-c", "core.fsmonitor=false", "-C", str(root)]
    return [prefix + ["rev-parse", "--show-toplevel"], prefix + ["rev-parse", "--verify", "HEAD^{commit}"],
            prefix + ["rev-parse", "--verify", commit + "^{tree}"],
            prefix + ["status", "--porcelain=v1", "--untracked-files=no"],
            prefix + ["ls-files", "--others", "--exclude-standard", "-z"]]


def wrapper_script(log, git, *, fail_refresh=False):
    """A /bin/sh Git wrapper that logs each start and execs the real Git; optionally fails only the refresh."""
    for text in (str(log), git):
        if "'" in text:
            raise AssertionError("a fixture path holds a single quote")
    lines = ["#!/bin/sh", "printf '%s\\n' \"$*\" >> '" + str(log) + "'"]
    if fail_refresh:
        lines.append('case " $* " in *" update-index -q --refresh "*) '
                     'echo "control: simulated refresh failure" >&2; exit 128 ;; esac')
    lines.append("exec '" + git + "' \"$@\"")
    return ("\n".join(lines) + "\n").encode("ascii")


def standin_script(log, root, commit, answers):
    """A /bin/sh stand-in for the bound Git that answers the source check's five exact reads from files."""
    for text in (str(log), str(root), str(answers)):
        if "'" in text:
            raise AssertionError("a fixture path holds a single quote")
    return ("#!/bin/sh\n"
            "printf '%s\\n' \"$*\" >> '" + str(log) + "'\n"
            "if [ \"$#\" -lt 5 ] || [ \"$1\" != -c ] || [ \"$2\" != core.fsmonitor=false ] || [ \"$3\" != -C ] "
            "|| [ \"$4\" != '" + str(root) + "' ]; then exit 97; fi\n"
            "shift 4\n"
            "case \"$*\" in\n"
            "  'rev-parse --show-toplevel') exec cat '" + str(answers / "toplevel") + "' ;;\n"
            "  'rev-parse --verify HEAD^{commit}') exec cat '" + str(answers / "commit") + "' ;;\n"
            "  'rev-parse --verify " + commit + "^{tree}') exec cat '" + str(answers / "tree") + "' ;;\n"
            "  'status --porcelain=v1 --untracked-files=no') exec cat '" + str(answers / "status") + "' ;;\n"
            "  'ls-files --others --exclude-standard -z') exec cat '" + str(answers / "untracked") + "' ;;\n"
            "esac\n"
            "exit 98\n").encode("ascii")


def index_entries(path):
    """A Git index file's entries (versions 2 to 4, SHA-1), read without Git: path -> stat data, mode, object, stage."""
    raw = Path(path).read_bytes()
    if raw[:4] != b"DIRC":
        raise AssertionError("not a Git index file")
    version, count = struct.unpack(">II", raw[4:12])
    if version not in (2, 3, 4):
        raise AssertionError("unsupported index version %d" % version)
    offset, previous, entries = 12, b"", {}
    for _ in range(count):
        fields = struct.unpack(">10I", raw[offset:offset + 40])
        oid = raw[offset + 40:offset + 60].hex()
        (flags,) = struct.unpack(">H", raw[offset + 60:offset + 62])
        position = offset + 62 + (2 if flags & 0x4000 else 0)
        if version == 4:
            byte = raw[position]
            position += 1
            strip = byte & 0x7F
            while byte & 0x80:
                byte = raw[position]
                position += 1
                strip = ((strip + 1) << 7) | (byte & 0x7F)
            end = raw.index(b"\0", position)
            name = previous[:len(previous) - strip] + raw[position:end]
            offset = end + 1
        else:
            end = raw.index(b"\0", position)
            name = raw[position:end]
            offset += (end - offset + 8) // 8 * 8
        previous = name
        ctime_s, ctime_ns, mtime_s, mtime_ns, dev, ino, mode, uid, gid, size = fields
        entries[name.decode("utf-8")] = {"stat": (ctime_s, ctime_ns, mtime_s, mtime_ns, dev, ino, uid, gid, size),
                                         "mode": mode, "oid": oid, "stage": (flags >> 12) & 0x3}
    return version, entries


ZERO_STAT = (0,) * 9


# ---------------------------------------------------------------------------
# Fixture trees
# ---------------------------------------------------------------------------

def base_tree():
    """The copied part of every fixture: the provider's 0.2.0 source set, and a few other copied files."""
    tree = {name + "/control_fixture.txt": (FILE, b"synthetic source tree file\n", 0o644) for name in provider.SOURCE_TREES}
    for name in (*provider.SOURCE_FILES, provider.PROVIDER, provider.PROBE):
        tree[name] = (FILE, ("synthetic copied source: %s\n" % name).encode("ascii"), 0o644)
    tree.update({
        "README.md": (FILE, b"control fixture readme\n", 0o644),
        ".gitignore": (FILE, b"# control fixture: no ignore patterns\n", 0o644),
        NOTES: (FILE, b"a copied file outside the 0.2.0 source set\n", 0o644),
        ".agents/skills/alpha/SKILL.md": (FILE, b"a copied file that an uncopied link names\n", 0o644),
        GENERATED: (FILE, b"a generated example\n", 0o644),
        ADOPTION_RECORD: (FILE, b'{"control": "synthetic adoption record of the fixture"}\n', 0o644),
    })
    return tree


def basic_tree(*paths):
    tree = base_tree()
    basic = {UNCOPIED_FILE: (FILE, b"local-only\n", 0o644), UNCOPIED_LINK: (LINK, "../../.agents/skills/alpha")}
    tree.update({path: basic[path] for path in paths})
    return tree


def full_tree(**extra):
    tree = basic_tree(UNCOPIED_FILE, UNCOPIED_LINK)
    tree.update(OTHER_UNCOPIED)
    tree[GENERATED_PRODUCT] = (FILE, b"glTF control product\n", 0o644)
    tree.update(extra)
    return tree


def full_uncopied():
    return [UNCOPIED_FILE, UNCOPIED_LINK, *OTHER_UNCOPIED]


def seven_tree():
    """The real tree's shape: .claude/.gitignore and six links under .claude/skills/ to copied directories."""
    tree = base_tree()
    tree[UNCOPIED_FILE] = (FILE, b"settings.local.json\n", 0o644)
    for name in SKILLS:
        tree[".agents/skills/%s/SKILL.md" % name] = (FILE, ("copied skill %s\n" % name).encode("ascii"), 0o644)
        tree[".claude/skills/" + name] = (LINK, "../../.agents/skills/" + name)
    return tree


def source_set(tree):
    """The fixture's 0.2.0 source path set: every file under SOURCE_TREES, and SOURCE_FILES."""
    return sorted(rel for rel, spec in tree.items() if spec[0] == FILE and (
        rel in provider.SOURCE_FILES or any(rel.startswith(name + "/") for name in provider.SOURCE_TREES)))


def deletions(paths):
    return sorted((" D " + path for path in paths), key=lambda line: line.encode("utf-8"))


# ---------------------------------------------------------------------------
# Base case
# ---------------------------------------------------------------------------

class Harness:
    """The fixtures' own Git starts: the real Git by absolute path, with the driver's isolating environment."""

    def __init__(self):
        found = shutil.which("git")
        if found is None or not os.path.isabs(found):
            raise AssertionError("These controls need a Git on PATH")
        self.git_path = os.path.abspath(found)

    def environment(self, root):
        environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0",
                           GIT_ATTR_NOSYSTEM="1", GIT_OPTIONAL_LOCKS="0", GIT_CEILING_DIRECTORIES=str(Path(root).parent))
        return environment

    def git(self, root, *args):
        completed = subprocess.run([self.git_path, "-c", "core.fsmonitor=false", "-C", str(root), *args],
                                   capture_output=True, env=self.environment(root), timeout=120)
        if completed.returncode:
            raise AssertionError("fixture Git %r failed: %s" % (args, completed.stderr.decode("utf-8", "replace")))
        return completed.stdout.decode("utf-8")

    def status(self, root):
        return self.git(root, "status", "--porcelain=v1", "--untracked-files=no").splitlines()

    def untracked(self, root):
        return [name for name in self.git(root, "ls-files", "--others", "--exclude-standard", "-z").split("\0") if name]

    def tree(self, root, commit):
        rows = {}
        for record in self.git(root, "ls-tree", "-r", "-z", commit).split("\0"):
            if record:
                metadata, name = record.split("\t", 1)
                mode, _, oid = metadata.split()
                rows[name] = (int(mode, 8), oid)
        return rows


class ControlCase(unittest.TestCase):
    """A resolved temporary directory per control, isolated Git state, and a logging Git wrapper."""

    BIND = True

    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        parent = os.path.realpath(tempfile.gettempdir())
        self.base = Path(self.stack.enter_context(tempfile.TemporaryDirectory(prefix="ontokin-w2-p37-", dir=parent)))
        self.assertEqual(str(self.base), os.path.realpath(str(self.base)), "the temporary directory is not resolved")
        self.counter = 0
        self.stack.enter_context(mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.fresh("xdg-config-home"))}))
        self.stack.enter_context(mock.patch.object(check_local, "_GIT_STATE", None))
        self.harness = Harness()
        self.log = self.base / "wrapper.log"
        self.wrapper = write(self.base / "bin/git-wrapper", wrapper_script(self.log, self.harness.git_path), 0o755)
        self.binding = {"path": str(self.wrapper), "sha256": file_sha256(self.wrapper)}
        if self.BIND:
            # As a qualifying run binds HOST's Git before its first Git start (S9).
            check_local.bind_git(self.binding["path"], self.binding["sha256"])

    def fresh(self, stem):
        self.counter += 1
        path = self.base / ("%s-%d" % (stem, self.counter))
        path.mkdir()
        return path

    def log_lines(self):
        return self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []

    def evidence(self, **values):
        """One line of execution evidence on stderr for the retained log; the temporary directory is a label."""
        text = json.dumps({"control": self._testMethodName, **values}, sort_keys=True, ensure_ascii=True, default=str)
        sys.stderr.write("CONTROL-EVIDENCE " + text.replace(str(self.base), "<tmp>") + "\n")

    @staticmethod
    def described(outcome):
        if outcome.error is not None:
            return [outcome.error.code, outcome.error.reason]
        return "accepted" if outcome.result is not None else "no result"

    @contextlib.contextmanager
    def recording(self):
        """Every subprocess start inside the window, with each run's timeout; any os-level spawn fails."""
        record = SimpleNamespace(starts=[], runs=[])
        real_popen, real_run = subprocess.Popen, subprocess.run

        class Recording(real_popen):
            def __init__(self, args, *pargs, **kwargs):
                record.starts.append([os.fspath(item) for item in args] if isinstance(args, (list, tuple))
                                     else [os.fspath(args)])
                super().__init__(args, *pargs, **kwargs)

        def run(*args, **kwargs):
            argv = args[0] if args else kwargs.get("args")
            record.runs.append({"argv": [os.fspath(item) for item in argv], "timeout": kwargs.get("timeout")})
            return real_run(*args, **kwargs)
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(subprocess, "Popen", Recording))
            stack.enter_context(mock.patch.object(subprocess, "run", run))
            for name in OS_SPAWNS:
                if hasattr(os, name):
                    stack.enter_context(mock.patch.object(
                        os, name, side_effect=AssertionError("process start outside subprocess: os." + name)))
            yield record

    def assert_no_forbidden_program(self, starts):
        programs = [os.path.basename(row[0]) for row in starts]
        self.assertFalse([name for name in programs if name in FORBIDDEN_PROGRAMS], programs)

    # -- fixtures ---------------------------------------------------------

    def fixture(self, tree):
        """A committed checkout of tree, with old modification times, clean, and its frozen records."""
        root = self.fresh("checkout") / "source"
        old = time.time() - 600
        for rel, spec in sorted(tree.items()):
            if spec[0] == FILE:
                write(root / rel, spec[1], spec[2], mtime=old)
            else:
                link(root / rel, spec[1], mtime=old)
        self.harness.git(root, "-c", "init.defaultBranch=control", "init", "--quiet", "--template=")
        self.harness.git(root, "add", "--all", "--force")
        self.harness.git(root, "-c", "user.name=derived-route control fixture", "-c", "user.email=fixture@example.invalid",
                         "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "derived-route control fixture")
        commit = self.harness.git(root, "rev-parse", "HEAD").strip()
        self.assertEqual(len(commit), 40)
        fixture = SimpleNamespace(root=root, tree_spec=tree, commit=commit,
                                  tree=self.harness.git(root, "rev-parse", "HEAD^{tree}").strip())
        self.assertEqual(sorted(name for name in self.harness.git(root, "ls-files", "-z").split("\0") if name),
                         sorted(tree), "the fixture does not track exactly its tree")
        self.assertEqual((self.harness.status(root), self.harness.untracked(root)), ([], []), "the fixture is not clean")
        files = {}
        for rel in source_set(tree):
            data = (root / rel).read_bytes()
            files[rel] = {"sha256": digest(data), "size_bytes": len(data), "mode": oct(stat.S_IMODE(os.lstat(root / rel).st_mode))}
        document = {"schema": SOURCE_SCHEMA, "files": files}
        fixture.document = document
        fixture.inventory = descriptor(write(self.fresh("inventory") / "source.json", canonical(document), 0o644))
        # The derivation's source_before: the driver's own inventory of the original checkout.
        fixture.record = check_local.inventory(root)
        return fixture

    def source(self, fixture, root=None, **changes):
        record = {"root": str(fixture.root if root is None else root), "commit": fixture.commit, "tree": fixture.tree,
                  "inventory": fixture.inventory}
        record.update(changes)
        return record

    def prepare(self, fixture, *, refresh=True, output=None):
        """The driver's own workspace preparation: its copy, workspace Git, storage step and index refresh."""
        output = self.fresh("evidence") if output is None else output
        with contextlib.ExitStack() as stack:
            if not refresh:
                stack.enter_context(mock.patch.object(check_local, "refresh_workspace_index", lambda workspace: None))
            workspace = check_local.prepare_workspace(fixture.root, output, False)
        self.assertEqual(workspace, output / "workspace")
        self.assertEqual(check_local.inventory(workspace), fixture.record, "the copy differs from the driver's record")
        return workspace

    def verify(self, source, *, derived=True, copied=None, own_root=False, git="bound"):
        """The source check of the 0.2.0 provider, inside a recorded window."""
        git = dict(self.binding) if git == "bound" else git
        observed = (self.harness.status(source["root"]), self.harness.untracked(source["root"]))
        if self.log.exists():
            self.log.unlink()
        with self.recording() as record:
            try:
                result, error = provider._verify_source(source, git=git, derived=derived, own_root=own_root,
                                                        copied=copied), None
            except provider.CurrentHostBindingError as exc:
                result, error = None, exc
        outcome = SimpleNamespace(result=result, error=error, starts=record.starts, log=self.log_lines())
        self.evidence(route="derived" if derived else "original", record=type(copied).__name__, status=observed[0],
                      untracked=observed[1], outcome=self.described(outcome), git_reads=len(record.starts))
        return outcome

    def assert_reads(self, outcome, root, commit, count, *, program=None):
        program = str(self.wrapper) if program is None else program
        expected = provider_reads(root, commit)[:count]
        self.assertEqual([row[1:] for row in outcome.starts], expected)
        self.assertEqual({row[0] for row in outcome.starts}, {program} if count else set())
        self.assertEqual(outcome.log, [" ".join(row) for row in expected])
        self.assert_no_forbidden_program(outcome.starts)

    def assert_accepted(self, outcome, fixture, root):
        self.assertIsNone(outcome.error, outcome.error.as_dict() if outcome.error is not None else None)
        self.assertEqual(outcome.result, fixture.document)
        self.assert_reads(outcome, root, fixture.commit, 5)

    def assert_refused(self, outcome, code, reason, *, root, commit, reads):
        self.assertIsNone(outcome.result, "the source was accepted")
        self.assertIsInstance(outcome.error, provider.CurrentHostBindingError)
        self.assertEqual((outcome.error.code, outcome.error.reason), (code, reason), outcome.error.as_dict())
        self.assert_reads(outcome, root, commit, reads)

    # -- the selection, with HOST, dependencies and methods substituted -----

    def selection(self, fixture):
        evidence = self.fresh("evidence-root")
        config = {"schema": CONFIG_SCHEMA, "contract": CONTRACT_ID,
                  "contract_source": descriptor(fixture.root / CONTRACT_MD),
                  "amendment_adoption": descriptor(fixture.root / ADOPTION_RECORD),
                  "source": self.source(fixture),
                  "host": {"control": "not read: HOST's reader is substituted"},
                  "dependencies": {"control": "not read: the dependency check is substituted"},
                  "runtime": {"control": "not read: the host check is substituted"},
                  "methods": {"control": "not read: the method check is substituted"},
                  "evidence_root": str(evidence), "parent": None}
        path = write(self.fresh("selection") / "config.json", canonical(config), 0o600)
        return SimpleNamespace(config=config, path=path, sha256=file_sha256(path), evidence=evidence)

    @contextlib.contextmanager
    def substituted(self, provider_root):
        """Mocked boundaries: HOST's Git, HOST, the cross bindings, dependencies and methods; the provider's own root."""
        host = {"labels": {"os": "control: substituted HOST", "node": "control: substituted HOST"},
                "python": {"inventory_sha256": "0" * 64}, "git": dict(self.binding)}
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(provider, "ROOT", provider_root))
            stack.enter_context(mock.patch.object(provider, "_host_git", return_value=dict(self.binding)))
            stack.enter_context(mock.patch.object(provider, "_verify_host", return_value=host))
            stack.enter_context(mock.patch.object(provider, "_cross_bindings", return_value=None))
            stack.enter_context(mock.patch.object(provider, "_verify_dependencies", return_value={"files": {}}))
            stack.enter_context(mock.patch.object(provider, "_verify_methods", return_value={"methods": []}))
            yield

    def run_driver(self, root, output, *, plan=(), refresh=True, path_git=None, **selection):
        """tools.check_local.run with a substituted plan and platform metadata leaf; every start recorded."""
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(check_local, "_GIT_STATE", None))
            if path_git is not None:
                stack.enter_context(mock.patch.dict(os.environ, {"PATH": str(path_git.parent) + os.pathsep + os.environ["PATH"]}))
            stack.enter_context(mock.patch.object(check_local, "build_plan", return_value=list(plan)))
            stack.enter_context(mock.patch.object(check_local.platform, "platform", return_value=PLATFORM_LEAF))
            if not refresh:
                stack.enter_context(mock.patch.object(check_local, "refresh_workspace_index", lambda workspace: None))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            record = stack.enter_context(self.recording())
            code = check_local.run(root, output, False, 60, **selection)
        summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        self.evidence(run="qualifying" if selection else "ordinary", refresh=refresh, exit=code, status=summary["status"],
                      error=summary.get("error"), readback_selection=summary.get("readback_selection", {}).get("status"),
                      starts=len(record.starts))
        return code, summary, record


# ---------------------------------------------------------------------------
# The derived route accepts the tracked paths that the copy leaves out (real Git, the driver's own preparation)
# ---------------------------------------------------------------------------

class DerivedRouteAcceptanceControls(ControlCase):

    def assert_derived_acceptance(self, tree, uncopied, *, expected_lines=None):
        fixture = self.fixture(tree)
        for path in uncopied:
            self.assertFalse(check_local.copied_source_path(path), path)
        self.assertFalse({item["path"] for item in fixture.record["files"]} & set(uncopied))
        workspace = self.prepare(fixture)
        self.assertEqual([path for path in uncopied if os.path.lexists(workspace / path)], [], "the copy reached them")
        lines = deletions(uncopied) if expected_lines is None else expected_lines
        self.assertEqual(self.harness.status(workspace), lines)
        self.assertEqual(self.harness.untracked(workspace), [])
        self.assert_accepted(self.verify(self.source(fixture, workspace), copied=fixture.record), fixture, workspace)
        return fixture, workspace

    def test_c01_a_regular_file_outside_the_source_directories_is_accepted(self):
        """Label: real. The derived workspace of a tree that tracks .claude/.gitignore, which the copy leaves out."""
        self.assert_derived_acceptance(basic_tree(UNCOPIED_FILE), [UNCOPIED_FILE])

    def test_c02_a_symbolic_link_outside_the_source_directories_is_accepted(self):
        """Label: real. The derived workspace of a tree that tracks the link .claude/skills/alpha -> ../../.agents/skills/alpha."""
        self.assert_derived_acceptance(basic_tree(UNCOPIED_LINK), [UNCOPIED_LINK])

    def test_c03_every_other_kind_of_tracked_path_that_the_copy_leaves_out_is_accepted(self):
        """Label: real. An executable file, a root file outside ROOT_FILES, nested directories, ignored directory
        components, ignored file names, links inside an ignored directory and with an ignored name, and bytecode."""
        self.assert_derived_acceptance(full_tree(), full_uncopied())

    def test_c04_the_real_trees_seven_uncopied_entries_are_accepted(self):
        """Label: real. FZ-01's shape: .claude/.gitignore and six links under .claude/skills/ give exactly the seven
        status lines of S2's measurement, and the derived check accepts them."""
        self.assert_derived_acceptance(seven_tree(), [line[3:] for line in SEVEN_LINES], expected_lines=SEVEN_LINES)

    def test_c05_the_derivation_and_the_unit_selection_accept_the_seven_entries(self):
        """Label: mocked (HOST, HOST's Git, cross bindings, dependencies and methods substituted; the provider's own
        root is the fixture checkout). tools.check_local.bind_readback_workspace derives the workspace binding, and the
        derived selection then passes as the unit process checks it."""
        fixture = self.fixture(seven_tree())
        world = self.selection(fixture)
        output = world.evidence / "run"
        output.mkdir()
        workspace = self.prepare(fixture, output=output)
        selection = {"config_path": str(world.path), "config_sha256": world.sha256}
        self.log.unlink()
        with self.substituted(fixture.root), self.recording() as record:
            derived = check_local.bind_readback_workspace(selection, root=fixture.root, workspace=workspace, output=output,
                                                          source_before=fixture.record,
                                                          workspace_inventory=check_local.inventory(workspace))
        self.assertEqual(set(derived), {"config_path", "config_sha256", "parent_config_sha256", "workspace_binding_path",
                                        "workspace_binding_sha256"})
        self.assertEqual(derived["parent_config_sha256"], world.sha256)
        self.assertEqual(derived["config_path"], str(output / "readback-binding/selection.json"))
        self.assertEqual(file_sha256(derived["config_path"]), derived["config_sha256"])
        self.assertEqual(json.loads((output / "readback-binding/source-before.json").read_bytes()), fixture.record)
        derived_config = json.loads(Path(derived["config_path"]).read_bytes())
        self.assertEqual(derived_config["source"]["root"], str(workspace))
        self.assertEqual(derived_config["parent"]["source_root"], str(fixture.root))
        expected = (provider_reads(fixture.root, fixture.commit) + provider_reads(workspace, fixture.commit)
                    + provider_reads(workspace, fixture.commit))
        self.assertEqual([row[1:] for row in record.starts], expected)
        self.assertEqual({row[0] for row in record.starts}, {str(self.wrapper)})
        self.assertEqual(self.log_lines(), [" ".join(row) for row in expected])
        # The unit process checks the derived selection with the workspace as the provider's own root.
        self.log.unlink()
        with self.substituted(workspace), self.recording() as record:
            unit = provider._selection(derived["config_path"], derived["config_sha256"], workspace)
        self.assertEqual(unit["config"], derived_config)
        self.assertEqual([row[1:] for row in record.starts], provider_reads(workspace, fixture.commit))
        self.assertEqual({row[0] for row in record.starts}, {str(self.wrapper)})

    def test_c06_the_derivation_still_refuses_an_untracked_input_and_a_staged_change(self):
        """Label: mocked (as c05). After the copy, outside the copied set, so that the inventories stay equal: an
        untracked file, and a staged deletion of an uncopied path. The derivation's own source check refuses."""
        cases = {
            "an untracked input outside the copied set": (
                lambda workspace: write(workspace / ".claude/new_control_input.txt", b"untracked\n"),
                (SOURCE, UNTRACKED + ".claude/new_control_input.txt"), 15),
            "a staged deletion of an uncopied path": (
                lambda workspace: self.harness.git(workspace, "rm", "--quiet", "--cached", "--", UNCOPIED_FILE),
                (SOURCE, DIRTY + "D  " + UNCOPIED_FILE), 14),
        }
        for label, (change, refusal, count) in cases.items():
            with self.subTest(label):
                fixture = self.fixture(seven_tree())
                world = self.selection(fixture)
                output = world.evidence / "run"
                output.mkdir()
                workspace = self.prepare(fixture, output=output)
                change(workspace)
                selection = {"config_path": str(world.path), "config_sha256": world.sha256}
                with self.substituted(fixture.root), self.recording() as record:
                    with self.assertRaises(provider.CurrentHostBindingError) as caught:
                        check_local.bind_readback_workspace(selection, root=fixture.root, workspace=workspace, output=output,
                                                            source_before=fixture.record,
                                                            workspace_inventory=check_local.inventory(workspace))
                self.assertEqual((caught.exception.code, caught.exception.reason), refusal)
                expected = (provider_reads(fixture.root, fixture.commit) + provider_reads(workspace, fixture.commit)
                            + provider_reads(workspace, fixture.commit))[:count]
                self.assertEqual([row[1:] for row in record.starts], expected)
                self.assertEqual({row[0] for row in record.starts}, {str(self.wrapper)})

    def test_c07_a_qualifying_run_passes_its_preparation_with_the_derived_binding(self):
        """Label: mocked (as c05, and the plan has no step). tools.check_local.run with both selection arguments, on
        the seven-entry tree: the selection is verified, the workspace bound, and the run passes."""
        fixture = self.fixture(seven_tree())
        world = self.selection(fixture)
        output = world.evidence / "run"
        with self.substituted(fixture.root):
            code, summary, record = self.run_driver(fixture.root, output, readback_config=world.path,
                                                    readback_config_sha256=world.sha256)
        self.assertEqual((code, summary["status"]), (0, "passed"), summary.get("error"))
        selection = summary["readback_selection"]
        self.assertEqual((selection["status"], selection["run_kind"]), ("workspace_bound", "qualifying"))
        self.assertEqual(set(selection["derived"]), {"config_path", "config_sha256", "parent_config_sha256",
                                                     "workspace_binding_path", "workspace_binding_sha256"})
        self.assertNotIn("preparation_or_execution_error", selection)
        self.assertEqual(summary["git_binding"], {**self.binding, "bound": True, "source": "selection"})
        self.assertEqual(summary["workspace_git"]["tracked_worktree_status"], "\n".join(SEVEN_LINES))
        self.assertEqual(summary["steps"], [])
        self.assertTrue(summary["source_unchanged"])
        self.assertEqual({row[0] for row in record.starts}, {str(self.wrapper)})
        workspace = str(output / "workspace")
        refreshes = [row for row in record.starts if row[1:] == ["-c", "core.fsmonitor=false", "-C", workspace, *REFRESH]]
        self.assertEqual(len(refreshes), 1)
        derived_reads = provider_reads(workspace, fixture.commit)
        rows = [row[1:] for row in record.starts]
        self.assertTrue(any(rows[index:index + 5] == derived_reads for index in range(len(rows))))


# ---------------------------------------------------------------------------
# The derived route still refuses every change inside the copied set and every other form (real Git)
# ---------------------------------------------------------------------------

class DerivedRouteRefusalControls(ControlCase):

    def refuse(self, change, line, *, tree=None, reason=None, reads=4, extra_lines=()):
        """Prepare the full fixture, apply change to the workspace, and expect the derived check to refuse at line."""
        fixture = self.fixture(full_tree() if tree is None else tree)
        workspace = self.prepare(fixture)
        change(workspace)
        status = self.harness.status(workspace)
        if line is not None:
            self.assertIn(line, status)
        for other in extra_lines:
            self.assertIn(other, status)
        outcome = self.verify(self.source(fixture, workspace), copied=fixture.record)
        self.assert_refused(outcome, SOURCE, DIRTY + line if reason is None else reason, root=workspace,
                            commit=fixture.commit, reads=reads)
        return fixture, workspace

    def test_c10_a_modified_copied_file_is_refused(self):
        """Label: real. docs/notes.md, a copied file outside the 0.2.0 source set, gets other bytes."""
        self.refuse(lambda workspace: write(workspace / NOTES, b"changed by the control\n"), " M " + NOTES)

    def test_c11_a_deleted_copied_file_is_refused(self):
        """Label: real. A copied file outside the 0.2.0 source set is deleted: docs/notes.md, README.md, and the file
        that the uncopied link names."""
        for path in (NOTES, "README.md", ".agents/skills/alpha/SKILL.md"):
            with self.subTest(path=path):
                self.refuse(lambda workspace: (workspace / path).unlink(), " D " + path)

    def test_c12_a_same_size_change_with_the_old_modification_time_is_refused_after_the_refresh(self):
        """Label: real. FZ-02: more than a second after the driver's refresh, docs/notes.md gets other bytes of the
        same size, and its access and modification times are set back."""
        def same_size(workspace):
            path = workspace / NOTES
            before = path.stat()
            time.sleep(1.2)
            path.write_bytes(b"#" * before.st_size)
            os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
            self.assertEqual((path.stat().st_size, path.stat().st_mtime_ns), (before.st_size, before.st_mtime_ns))
        self.refuse(same_size, " M " + NOTES)

    def test_c13_a_retyped_copied_file_is_refused(self):
        """Label: real. docs/notes.md is replaced by a symbolic link."""
        self.refuse(lambda workspace: link(workspace / NOTES, "../README.md"), " T " + NOTES)

    def test_c14_a_staged_change_is_refused(self):
        """Label: real. Changes staged in the workspace's index, inside and outside the copied set."""
        def staged_new(name):
            def change(workspace):
                write(workspace / name, b"staged by the control\n")
                self.harness.git(workspace, "add", "--force", "--", name)
            return change

        def staged_modification(workspace):
            write(workspace / NOTES, b"staged modification\n")
            self.harness.git(workspace, "add", "--", NOTES)

        def staged_and_modified(workspace):
            staged_modification(workspace)
            write(workspace / NOTES, b"modified again after staging\n")
        cases = {
            "a staged deletion of an uncopied path": (
                lambda workspace: self.harness.git(workspace, "rm", "--quiet", "--cached", "--", UNCOPIED_FILE),
                "D  " + UNCOPIED_FILE),
            "a staged deletion of a copied file": (
                lambda workspace: self.harness.git(workspace, "rm", "--quiet", "--cached", "--", NOTES), "D  " + NOTES),
            "a staged modification of a copied file": (staged_modification, "M  " + NOTES),
            "a staged and then modified copied file": (staged_and_modified, "MM " + NOTES),
            "a staged new file inside the copied set": (staged_new("tools/staged_input.py"), "A  tools/staged_input.py"),
            "a staged new file outside the copied set": (staged_new("outside/staged_input.txt"), "A  outside/staged_input.txt"),
        }
        for label, (change, line) in cases.items():
            with self.subTest(label):
                self.refuse(change, line)

    def test_c15_a_rename_line_is_refused(self):
        """Label: real. Staged renames: of a copied file, of an uncopied path present again with the commit's bytes,
        and of a copied file that matches the generated-product pattern."""
        def restored_then_moved(workspace):
            write(workspace / UNCOPIED_FILE, full_tree()[UNCOPIED_FILE][1])
            self.harness.git(workspace, "mv", "--", UNCOPIED_FILE, ".claude/moved.txt")
        cases = {
            "a copied file": (lambda workspace: self.harness.git(workspace, "mv", "--", NOTES, "docs/renamed.md"),
                              "R  docs/notes.md -> docs/renamed.md"),
            "an uncopied path": (restored_then_moved, "R  .claude/.gitignore -> .claude/moved.txt"),
            "a generated product": (
                lambda workspace: self.harness.git(workspace, "mv", "--", GENERATED_PRODUCT, "examples/visual/b.glb"),
                "R  examples/visual/a.glb -> examples/visual/b.glb"),
        }
        for label, (change, line) in cases.items():
            with self.subTest(label):
                self.refuse(change, line)

    def test_c16_an_uncopied_path_whose_name_git_quotes_is_refused(self):
        """Label: real. A tracked path outside the copied set whose name holds a double quote or a non-ASCII letter;
        Git quotes it, and the line refuses."""
        cases = {'.claude/quote"mark.txt': ' D ".claude/quote\\"mark.txt"',
                 ".claude/naïve.txt": ' D ".claude/na\\303\\257ve.txt"'}
        for name, line in cases.items():
            with self.subTest(line=line):
                self.refuse(lambda workspace: None, line, tree=full_tree(**{name: (FILE, b"outside the copied set\n", 0o644)}))

    def test_c17_an_uncopied_path_that_is_present_but_changed_is_refused(self):
        """Label: real. An uncopied path present in the workspace in any form other than its commit's, and an
        intent-to-add entry outside the copied set."""
        def intent_to_add(workspace):
            write(workspace / "outside/intent_to_add.txt", b"intent to add\n")
            self.harness.git(workspace, "add", "--intent-to-add", "--", "outside/intent_to_add.txt")
        cases = {
            "the file with other bytes": (lambda workspace: write(workspace / UNCOPIED_FILE, b"other bytes\n"),
                                          " M " + UNCOPIED_FILE),
            "the link as a regular file": (lambda workspace: write(workspace / UNCOPIED_LINK, b"a regular file\n"),
                                           " T " + UNCOPIED_LINK),
            "the link with another target": (lambda workspace: link(workspace / UNCOPIED_LINK, "../../README.md"),
                                             " M " + UNCOPIED_LINK),
            "the executable file with another mode": (
                lambda workspace: write(workspace / ".claude/hooks/check.sh", OTHER_UNCOPIED[".claude/hooks/check.sh"][1], 0o644),
                " M .claude/hooks/check.sh"),
            "a root file outside ROOT_FILES with other bytes": (lambda workspace: write(workspace / "Makefile", b"other\n"),
                                                                " M Makefile"),
            "a file under an ignored directory with other bytes": (
                lambda workspace: write(workspace / "tools/build/generated.py", b"print('other')\n"),
                " M tools/build/generated.py"),
            "an intent-to-add entry outside the copied set": (intent_to_add, " A outside/intent_to_add.txt"),
        }
        for label, (change, line) in cases.items():
            with self.subTest(label):
                self.refuse(change, line)

    def test_c18_an_uncopied_path_replaced_by_a_directory_holding_a_file_is_refused(self):
        """Label: real. Makefile is a directory holding inner.txt: its deletion line is admitted, and the untracked
        file in it refuses."""
        self.refuse(lambda workspace: write(workspace / "Makefile/inner.txt", b"inside a directory\n"), " D Makefile",
                    reason=UNTRACKED + "Makefile/inner.txt", reads=5)

    def test_c19_an_untracked_input_inside_the_copied_set_is_refused(self):
        """Label: real. An untracked file inside the copied set but outside the 0.2.0 source set's trees."""
        for name in ("tools/new_control_input.py", "docs/new_control_input.md", ".agents/new_control_input.md", ".lfsconfig"):
            with self.subTest(name=name):
                self.assertTrue(check_local.copied_source_path(name))
                self.refuse(lambda workspace: write(workspace / name, b"untracked input\n"), None,
                            reason=UNTRACKED + name, reads=5)

    def test_c20_an_untracked_input_outside_the_copied_set_is_refused(self):
        """Label: real. An untracked file outside the copied set, which neither the copy nor the commit supplies."""
        for name in (".claude/new_control_input.txt", "outside/new_control_input.txt", "Makefile.local",
                     "tools/build/new_control_input.py"):
            with self.subTest(name=name):
                self.assertFalse(check_local.copied_source_path(name))
                self.refuse(lambda workspace: write(workspace / name, b"untracked input\n"), None,
                            reason=UNTRACKED + name, reads=5)

    def test_c21_the_source_sets_binding_still_refuses_before_any_git_read(self):
        """Label: real. In the derived workspace: a missing source role, a missing or an added file in a source tree,
        and a changed provider or probe. The binding refuses before the first Git read."""
        cases = {
            "a missing source role": (lambda workspace: (workspace / "pyproject.toml").unlink(),
                                      lambda workspace: PATH_MISSING + str(workspace / "pyproject.toml")),
            "a missing file of a source tree": (lambda workspace: (workspace / "ontokin/control_fixture.txt").unlink(),
                                                lambda workspace: INVENTORY_DIFFERS),
            "an added file in a source tree": (lambda workspace: write(workspace / "tests/new_control_input.py", b"# new\n"),
                                               lambda workspace: INVENTORY_DIFFERS),
            "a changed provider": (lambda workspace: write(workspace / provider.PROVIDER, b"# changed provider\n"),
                                   lambda workspace: LOCKED_DIFFERS + str(workspace / provider.PROVIDER)),
            "a changed probe": (lambda workspace: write(workspace / provider.PROBE, b"// changed probe\n"),
                                lambda workspace: LOCKED_DIFFERS + str(workspace / provider.PROBE)),
        }
        for label, (change, reason) in cases.items():
            with self.subTest(label):
                fixture = self.fixture(full_tree())
                workspace = self.prepare(fixture)
                change(workspace)
                outcome = self.verify(self.source(fixture, workspace), copied=fixture.record)
                self.assert_refused(outcome, SOURCE, reason(workspace), root=workspace, commit=fixture.commit, reads=0)

    def test_c22_another_checkout_an_unbound_git_and_another_commit_or_tree_are_refused(self):
        """Label: real. MC19's other cases on the derived route, with the record given."""
        fixture = self.fixture(full_tree())
        workspace = self.prepare(fixture)
        cases = {
            "another checkout": (dict(own_root=True), self.source(fixture, workspace), OTHER_CHECKOUT, 0),
            "no Git binding": (dict(git=None), self.source(fixture, workspace), UNBOUND, 0),
            "another commit": ({}, self.source(fixture, workspace, commit="0" * 40), IDENTITY, 2),
            "another tree": ({}, self.source(fixture, workspace, tree="0" * 40), IDENTITY, 3),
        }
        for label, (options, source, reason, reads) in cases.items():
            with self.subTest(label):
                outcome = self.verify(source, copied=fixture.record, **options)
                self.assert_refused(outcome, SOURCE, reason, root=workspace, commit=source["commit"], reads=reads)

    def test_c23_a_symbolic_link_inside_the_copied_set_is_refused_by_the_driver(self):
        """Label: real. A tracked link tools/linked.py: the driver's inventory and copy refuse it, so no workspace
        exists for the provider."""
        tree = full_tree(**{"tools/linked.py": (LINK, "../README.md")})
        root = self.fresh("checkout") / "source"
        old = time.time() - 600
        for rel, spec in sorted(tree.items()):
            (write(root / rel, spec[1], spec[2], mtime=old) if spec[0] == FILE else link(root / rel, spec[1], mtime=old))
        self.harness.git(root, "-c", "init.defaultBranch=control", "init", "--quiet", "--template=")
        self.harness.git(root, "add", "--all", "--force")
        self.harness.git(root, "-c", "user.name=derived-route control fixture", "-c", "user.email=fixture@example.invalid",
                         "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "a link inside the copied set")
        self.assertEqual(self.harness.status(root), [])
        self.assertTrue(check_local.copied_source_path("tools/linked.py"))
        source_git = check_local.git_metadata(root)
        output = self.fresh("evidence")
        with self.recording() as record:
            with self.assertRaises(ValueError) as inventory_refusal:
                check_local.inventory(root)
            with self.assertRaises(ValueError) as copy_refusal:
                check_local.prepare_workspace(root, output, False, source_git=source_git)
        self.assertEqual(str(inventory_refusal.exception), INVENTORY_LINK + str(root / "tools/linked.py"))
        self.assertEqual(str(copy_refusal.exception), COPY_LINK + str(root / "tools/linked.py"))
        self.assertEqual(record.starts, [])
        self.assertFalse(os.path.lexists(output / "workspace/.git"))

    def test_c24_a_source_tree_file_that_the_copy_leaves_out_is_refused_as_missing_source(self):
        """Label: real. A tracked file of a 0.2.0 source tree whose path has an ignored() component: it belongs to the
        source set, so the original route accepts the clean checkout, but the copy leaves it out. Its deletion line
        lies outside the copied set, and the source set's binding refuses before any Git read."""
        for path in ("ontokin/.env", "prototypes/static_tray_v01/build/helper.py"):
            with self.subTest(path=path):
                fixture = self.fixture(full_tree(**{path: (FILE, b"inside a source tree, outside the copied set\n", 0o644)}))
                self.assertIn(path, fixture.document["files"])
                self.assertFalse(check_local.copied_source_path(path))
                original = self.verify(self.source(fixture), derived=False, copied=None)
                self.assert_accepted(original, fixture, fixture.root)
                workspace = self.prepare(fixture)
                self.assertFalse(os.path.lexists(workspace / path))
                self.assertIn(" D " + path, self.harness.status(workspace))
                outcome = self.verify(self.source(fixture, workspace), copied=fixture.record)
                self.assert_refused(outcome, SOURCE, INVENTORY_DIFFERS, root=workspace, commit=fixture.commit, reads=0)


# ---------------------------------------------------------------------------
# The original route still refuses every line (real Git)
# ---------------------------------------------------------------------------

class OriginalRouteControls(ControlCase):

    def assert_original_refusal(self, fixture, line):
        self.assertIn(line, self.harness.status(fixture.root))
        for copied in (fixture.record, None):
            with self.subTest(record="given" if copied is not None else "none"):
                outcome = self.verify(self.source(fixture), derived=False, copied=copied)
                self.assert_refused(outcome, SOURCE, DIRTY + line, root=fixture.root, commit=fixture.commit, reads=4)

    def test_c30_an_uncopied_file_deleted_in_the_original_checkout_is_refused(self):
        """Label: real. The original checkout of the seven-entry tree lacks .claude/.gitignore."""
        fixture = self.fixture(seven_tree())
        (fixture.root / UNCOPIED_FILE).unlink()
        self.assert_original_refusal(fixture, " D " + UNCOPIED_FILE)

    def test_c31_an_uncopied_link_deleted_in_the_original_checkout_is_refused(self):
        """Label: real. The original checkout of the seven-entry tree lacks the link .claude/skills/communication."""
        fixture = self.fixture(seven_tree())
        (fixture.root / ".claude/skills/communication").unlink()
        self.assert_original_refusal(fixture, " D .claude/skills/communication")

    def test_c32_an_original_checkout_without_any_uncopied_path_is_refused(self):
        """Label: real. The original checkout of the full fixture lacks every uncopied path, as a workspace does."""
        fixture = self.fixture(full_tree())
        for path in full_uncopied():
            remove(fixture.root / path)
        self.assertEqual(self.harness.status(fixture.root), deletions(full_uncopied()))
        self.assert_original_refusal(fixture, " D " + UNCOPIED_FILE)

    def test_c33_the_derived_workspace_read_as_an_original_is_refused(self):
        """Label: real. The driver's workspace of the seven-entry tree, checked with derived=False."""
        fixture = self.fixture(seven_tree())
        workspace = self.prepare(fixture)
        for copied in (fixture.record, None):
            with self.subTest(record="given" if copied is not None else "none"):
                outcome = self.verify(self.source(fixture, workspace), derived=False, copied=copied)
                self.assert_refused(outcome, SOURCE, DIRTY + SEVEN_LINES[0], root=workspace, commit=fixture.commit, reads=4)

    def test_c34_a_qualifying_run_whose_original_checkout_lacks_an_uncopied_path_fails_preparation(self):
        """Label: mocked (as c05; the plan has one step, which must never start). MC21's outcome: the original
        selection refuses in the driver's preparation, before any copy and any step."""
        fixture = self.fixture(seven_tree())
        world = self.selection(fixture)
        (fixture.root / UNCOPIED_FILE).unlink()
        output = world.evidence / "run"
        step = check_local.Step("control-unit", (sys.executable, "-I", "-S", "-B", "-c", "raise SystemExit(7)"))
        with self.substituted(fixture.root):
            code, summary, record = self.run_driver(fixture.root, output, plan=[step], readback_config=world.path,
                                                    readback_config_sha256=world.sha256)
        self.assertEqual((code, summary["status"]), (1, "failed"))
        self.assertEqual(summary["error"], DIRTY + " D " + UNCOPIED_FILE)
        selection = summary["readback_selection"]
        self.assertEqual((selection["status"], selection["run_kind"], selection["preparation_or_execution_error"]),
                         ("preparation_pending", "qualifying", DIRTY + " D " + UNCOPIED_FILE))
        self.assertEqual((summary["steps"], summary["not_executed_steps"]), ([], ["control-unit"]))
        self.assertNotIn("workspace_git", summary)
        self.assertFalse(os.path.lexists(output / "workspace"))
        self.assertEqual([row[1:] for row in record.starts], provider_reads(fixture.root, fixture.commit)[:4])
        self.assertEqual({row[0] for row in record.starts}, {str(self.wrapper)})

    def test_c35_generated_example_changes_still_refuse_on_the_original_route(self):
        """Label: real. Unchanged: in an original checkout a changed generated example and an untracked generated
        product refuse."""
        fixture = self.fixture(full_tree())
        write(fixture.root / GENERATED, b"regenerated in the original checkout\n")
        self.assert_original_refusal(fixture, " M " + GENERATED)
        fixture = self.fixture(full_tree())
        write(fixture.root / "examples/visual/scene.glb", b"glTF untracked product\n")
        outcome = self.verify(self.source(fixture), derived=False, copied=None)
        self.assert_refused(outcome, SOURCE, UNTRACKED + "examples/visual/scene.glb", root=fixture.root,
                            commit=fixture.commit, reads=5)


# ---------------------------------------------------------------------------
# The generated-example exclusion still holds on the derived route (real Git)
# ---------------------------------------------------------------------------

class GeneratedExampleControls(ControlCase):

    CHANGES = {
        "a changed generated example": (lambda case, workspace: write(workspace / GENERATED, b"regenerated\n"),
                                        [" M " + GENERATED], []),
        "a deleted generated example": (lambda case, workspace: (workspace / GENERATED).unlink(), [" D " + GENERATED], []),
        "a staged generated example": (lambda case, workspace: (write(workspace / GENERATED, b"regenerated and staged\n"),
                                                                case.harness.git(workspace, "add", "--", GENERATED)),
                                       ["M  " + GENERATED], []),
        "untracked generated products": (
            lambda case, workspace: [write(workspace / name, b"generated product\n") for name in (
                "examples/visual/scene.glb", "examples/agent/workflow.json", "examples/construction/program.bundle.json")],
            [], ["examples/agent/workflow.json", "examples/construction/program.bundle.json", "examples/visual/scene.glb"]),
    }

    def accept(self, changes):
        fixture = self.fixture(full_tree())
        workspace = self.prepare(fixture)
        lines, untracked = list(deletions(full_uncopied())), []
        for change, added, names in changes:
            change(self, workspace)
            lines += added
            untracked += names
        self.assertEqual(sorted(self.harness.status(workspace)), sorted(lines))
        self.assertEqual(sorted(self.harness.untracked(workspace)), sorted(untracked))
        self.assert_accepted(self.verify(self.source(fixture, workspace), copied=fixture.record), fixture, workspace)

    def test_c40_each_change_of_a_generated_example_is_accepted_beside_the_uncopied_paths(self):
        """Label: real. Unchanged rule A: each change, alone, in the full fixture's derived workspace."""
        for label, change in self.CHANGES.items():
            with self.subTest(label):
                self.accept([change])

    def test_c41_all_generated_example_changes_together_are_accepted(self):
        """Label: real. The changed example, the untracked products, and the uncopied paths in one workspace."""
        self.accept([self.CHANGES["a changed generated example"], self.CHANGES["untracked generated products"]])


# ---------------------------------------------------------------------------
# Exact porcelain lines (simulated: a /bin/sh stand-in answers the five reads from files)
# ---------------------------------------------------------------------------

class ExactStatusLineControls(ControlCase):

    BIND = False
    COMMIT, TREE = "a1" * 20, "b2" * 20

    def setUp(self):
        super().setUp()
        tree = base_tree()
        tree["tests/control_fixture.txt"] = (FILE, b"synthetic source tree file\n", 0o644)
        self.root = self.fresh("lines") / "workspace"
        for rel, spec in sorted(tree.items()):
            write(self.root / rel, spec[1], spec[2])
        files = {}
        for rel in source_set(tree):
            data = (self.root / rel).read_bytes()
            files[rel] = {"sha256": digest(data), "size_bytes": len(data), "mode": "0o644"}
        self.document = {"schema": SOURCE_SCHEMA, "files": files}
        inventory = descriptor(write(self.fresh("inventory") / "source.json", canonical(self.document), 0o644))
        self.source_record = {"root": str(self.root), "commit": self.COMMIT, "tree": self.TREE, "inventory": inventory}
        self.record = check_local.inventory(self.root)
        self.answers = self.fresh("answers")
        self.standin_log = self.base / "standin.log"
        standin = write(self.base / "bin/git-standin", standin_script(self.standin_log, self.root, self.COMMIT, self.answers), 0o755)
        self.standin = {"path": str(standin), "sha256": file_sha256(standin)}
        for name, value in (("toplevel", str(self.root) + "\n"), ("commit", self.COMMIT + "\n"), ("tree", self.TREE + "\n")):
            (self.answers / name).write_text(value, encoding="ascii")

    def verdict(self, status_lines=(), untracked=(), *, derived=True, copied="record"):
        (self.answers / "status").write_bytes("".join(line + "\n" for line in status_lines).encode("utf-8"))
        (self.answers / "untracked").write_bytes("".join(name + "\0" for name in untracked).encode("utf-8"))
        if self.standin_log.exists():
            self.standin_log.unlink()
        copied = self.record if copied == "record" else copied
        with self.recording() as record:
            try:
                result, error = provider._verify_source(self.source_record, git=dict(self.standin), derived=derived,
                                                        own_root=False, copied=copied), None
            except provider.CurrentHostBindingError as exc:
                result, error = None, exc
        log = self.standin_log.read_text(encoding="utf-8").splitlines() if self.standin_log.exists() else []
        outcome = SimpleNamespace(result=result, error=error, starts=record.starts, log=log)
        self.evidence(route="derived" if derived else "original", record=type(copied).__name__,
                      status=list(status_lines), untracked=list(untracked), outcome=self.described(outcome),
                      git_reads=len(record.starts))
        return outcome

    def expect(self, outcome, verdict, reads):
        if verdict == "accepted":
            self.assertIsNone(outcome.error, outcome.error.as_dict() if outcome.error is not None else None)
            self.assertEqual(outcome.result, self.document)
        else:
            self.assertIsNone(outcome.result, "accepted")
            self.assertIsInstance(outcome.error, provider.CurrentHostBindingError)
            self.assertEqual((outcome.error.code, outcome.error.reason), verdict)
        self.assert_reads(outcome, self.root, self.COMMIT, reads, program=self.standin["path"])

    def test_c50_the_deletion_of_a_path_outside_the_copied_set_is_admitted(self):
        """Label: simulated (Git boundary). ' D P' for P outside the copied set by the driver's definition."""
        outside = [UNCOPIED_FILE, UNCOPIED_LINK, *OTHER_UNCOPIED, "ontokin/.env", "tests/__pycache__/cached.cpython-312.pyc",
                   "LICENSE/inner.txt", ".claude/two words.txt", "Docs/other.md"]
        for path in outside:
            with self.subTest(path=path):
                self.assertFalse(check_local.copied_source_path(path))
                self.expect(self.verdict([" D " + path]), "accepted", 5)
        with self.subTest("the real tree's seven lines together"):
            self.expect(self.verdict(SEVEN_LINES), "accepted", 5)

    def test_c51_every_other_status_form_of_an_uncopied_path_is_refused(self):
        """Label: simulated (Git boundary). Staged, unstaged other than a deletion, unmerged, untracked or ignored forms."""
        for xy in ("D ", " M", "M ", "MM", "MD", " T", "T ", "TM", "A ", " A", "AM", "AD", "DD", "AU", "UD", "UA", "DU",
                   "AA", "UU", "??", "!!"):
            line = xy + " " + UNCOPIED_FILE
            with self.subTest(line=line):
                self.expect(self.verdict([line]), (SOURCE, DIRTY + line), 4)

    def test_c52_the_deletion_of_a_path_inside_the_copied_set_is_refused(self):
        """Label: simulated (Git boundary). ' D P' for P inside the copied set, a link and a submodule path among them,
        and a case variant of an ignored directory name, which the predicate does not ignore."""
        inside = ["README.md", "pyproject.toml", ".gitignore", ".gitattributes", ".lfsconfig", NOTES,
                  "tests/control_fixture.txt", "tools/linked.py", "tools/sub", ".agents/skills/alpha/SKILL.md",
                  "TRDs/INDEX.md", ".github/workflows/check.yml", "tools/Build/x.py", "tests", provider.PROVIDER]
        for path in inside:
            with self.subTest(path=path):
                self.assertTrue(check_local.copied_source_path(path))
                self.expect(self.verdict([" D " + path]), (SOURCE, DIRTY + " D " + path), 4)

    def test_c53_rename_and_copy_lines_are_refused(self):
        """Label: simulated (Git boundary). Any line naming two paths, generated products included."""
        for line in ("R  .claude/a -> .claude/b", "C  .claude/a -> .claude/b", "RM .claude/a -> .claude/b",
                     "CM .claude/a -> .claude/b", " R .claude/a -> .claude/b", "R  docs/notes.md -> .claude/b",
                     "R  .claude/a -> docs/b.md", " D .claude/a -> b",
                     "R  examples/visual/a.glb -> examples/visual/b.glb", " D examples/visual/a.glb -> examples/visual/b.glb"):
            with self.subTest(line=line):
                self.expect(self.verdict([line]), (SOURCE, DIRTY + line), 4)

    def test_c54_quoted_names_are_refused(self):
        """Label: simulated (Git boundary). Git's C-quoted names, outside the copied set and for generated products."""
        for line in (' D ".claude/two words.txt"', ' D ".claude/na\\303\\257ve.txt"', ' D ".claude/quote\\"mark.txt"',
                     ' M "examples/visual/two words.glb"', ' D "examples/visual/two words.glb"'):
            with self.subTest(line=line):
                self.expect(self.verdict([line]), (SOURCE, DIRTY + line), 4)

    def test_c55_unsafe_names_are_refused(self):
        """Label: simulated (Git boundary). An empty, '.' or '..' component, or no name."""
        for line in (" D ../escape", " D ./outside", " D outside//notes", " D /outside/notes", " D outside/", " D ",
                     " D .claude/../README.md", " D .claude/./x", " D ."):
            with self.subTest(line=line):
                self.expect(self.verdict([line]), (SOURCE, DIRTY + line), 4)

    def test_c56_a_case_variant_of_a_recorded_copied_file_is_refused(self):
        """Label: simulated (Git boundary). The record holds docs/notes.md, README.md, tests/control_fixture.txt and
        .agents/skills/alpha/SKILL.md; a deletion of one of them up to case refuses, another name is admitted."""
        recorded = {item["path"] for item in self.record["files"]}
        self.assertTrue({NOTES, "README.md", "tests/control_fixture.txt", ".agents/skills/alpha/SKILL.md"} <= recorded)
        for line in (" D Docs/notes.md", " D DOCS/NOTES.MD", " D readme.md", " D README.MD",
                     " D Tests/control_fixture.txt", " D .AGENTS/skills/alpha/SKILL.md"):
            with self.subTest(line=line):
                self.assertFalse(check_local.copied_source_path(line[3:]))
                self.expect(self.verdict([line]), (SOURCE, DIRTY + line), 4)
        self.expect(self.verdict([" D Docs/other.md"]), "accepted", 5)

    def test_c57_a_derived_check_without_a_well_formed_record_admits_no_deletion(self):
        """Label: simulated (Git boundary). No record: the deletion refuses at its line. A malformed record refuses
        before any Git start."""
        self.expect(self.verdict([" D " + UNCOPIED_FILE], copied=None), (SOURCE, DIRTY + " D " + UNCOPIED_FILE), 4)
        for record in ([], {}, {"files": None}, {"files": "README.md"}, {"files": [{"path": 1}]},
                       {"files": [["README.md"]]}, {"files": [{}]}, "text", {"files": [{"path": "README.md"}, 3]}):
            with self.subTest(record=record):
                self.expect(self.verdict([" D " + UNCOPIED_FILE], copied=record), (WORKSPACE, MALFORMED), 0)

    def test_c58_the_original_route_refuses_every_line_with_or_without_a_record(self):
        """Label: simulated (Git boundary). derived=False: deletions outside the copied set and generated examples."""
        for line in (" D " + UNCOPIED_FILE, " D " + UNCOPIED_LINK, " D Makefile", " D tools/build/generated.py",
                     " M " + GENERATED, " D " + GENERATED):
            for copied in ("record", None):
                with self.subTest(line=line, record=copied):
                    self.expect(self.verdict([line], derived=False, copied=copied), (SOURCE, DIRTY + line), 4)

    def test_c59_generated_examples_and_untracked_names_keep_their_rules(self):
        """Label: simulated (Git boundary). Rule A needs no record; untracked names refuse, inside and outside the
        copied set, except a generated product on the derived route."""
        for line in (" M " + GENERATED, "M  " + GENERATED, " D examples/agent/workflow.json",
                     "MM examples/construction/main.ok", " D examples/visual/scene.glb"):
            with self.subTest(generated=line):
                self.expect(self.verdict([line], copied=None), "accepted", 5)
        for name in ("tools/new_control_input.py", "docs/new_control_input.md", ".claude/new_control_input.txt",
                     "outside/new_control_input.txt", "Makefile.local", ".lfsconfig"):
            with self.subTest(untracked=name):
                self.expect(self.verdict(untracked=[name]), (SOURCE, UNTRACKED + name), 5)
        for name in ("examples/visual/fresh.glb", "examples/agent/fresh.export.json"):
            with self.subTest(generated_untracked=name):
                self.expect(self.verdict(untracked=[name]), "accepted", 5)
                self.expect(self.verdict(untracked=[name], derived=False), (SOURCE, UNTRACKED + name), 5)


# ---------------------------------------------------------------------------
# FZ-02: the workspace index refresh (real Git)
# ---------------------------------------------------------------------------

class WorkspaceIndexControls(ControlCase):

    def normalized(self, rows, replacements):
        result = []
        for row in rows:
            text = []
            for item in row:
                for old, new in replacements:
                    item = item.replace(old, new)
                text.append(item)
            result.append(text)
        return result

    def test_c60_the_preparation_makes_exactly_one_more_git_start_the_refresh(self):
        """Label: real (the comparison substitutes refresh_workspace_index with a no-op). The added start is
        update-index -q --refresh in the workspace, last in the preparation, after the storage reads and before any
        status read of the workspace, with a 120 s allowance."""
        fixture = self.fixture(full_tree())
        sequences, allowances = {}, {}
        for refresh in (True, False):
            output = self.fresh("evidence")
            with self.recording() as record:
                self.prepare(fixture, refresh=refresh, output=output)
            self.assertEqual({row[0] for row in record.starts}, {str(self.wrapper)})
            self.assert_no_forbidden_program(record.starts)
            sequences[refresh] = self.normalized(record.starts, [(str(output), "<output>"), (str(self.wrapper), "<git>")])
            allowances[refresh] = [run["timeout"] for run in record.runs if run["argv"][-3:] == REFRESH]
        refresh_start = ["<git>", "-c", "core.fsmonitor=false", "-C", "<output>/workspace", *REFRESH]
        self.assertEqual(sequences[True][:-1], sequences[False])
        self.assertEqual(sequences[True][-1], refresh_start)
        self.assertEqual(allowances, {True: [120], False: []})
        self.assertFalse([row for row in sequences[True] if "<output>/workspace" in row and "status" in row])

    def test_c61_the_refresh_records_stat_data_for_the_copied_entries_only_and_changes_no_entry(self):
        """Label: real (the comparison substitutes refresh_workspace_index with a no-op). The workspace's index file,
        read without Git."""
        fixture = self.fixture(full_tree())
        refreshed = self.prepare(fixture)
        plain = self.prepare(fixture, refresh=False)
        tree = self.harness.tree(fixture.root, fixture.commit)
        _, after = index_entries(refreshed / ".git/index")
        _, before = index_entries(plain / ".git/index")
        uncopied = set(full_uncopied())
        self.assertEqual(set(after), set(tree))
        self.assertEqual(set(before), set(tree))
        for path, (mode, oid) in tree.items():
            with self.subTest(path=path):
                self.assertEqual((after[path]["mode"], after[path]["oid"], after[path]["stage"]), (mode, oid, 0))
                self.assertEqual((before[path]["mode"], before[path]["oid"], before[path]["stage"]), (mode, oid, 0))
                self.assertEqual(before[path]["stat"], ZERO_STAT)
                if path in uncopied:
                    self.assertEqual(after[path]["stat"], ZERO_STAT)
                else:
                    info = os.lstat(refreshed / path)
                    ctime_s, _, mtime_s, _, _, ino, _, _, size = after[path]["stat"]
                    self.assertNotEqual(ctime_s, 0)
                    self.assertEqual((mtime_s, ino, size),
                                     (int(info.st_mtime) & 0xFFFFFFFF, info.st_ino & 0xFFFFFFFF, info.st_size & 0xFFFFFFFF))

    def test_c62_status_lines_and_the_derived_outcome_are_the_same_with_and_without_the_refresh(self):
        """Label: real (the comparison substitutes refresh_workspace_index with a no-op)."""
        fixture = self.fixture(full_tree())
        for refresh in (True, False):
            with self.subTest(refresh=refresh):
                workspace = self.prepare(fixture, refresh=refresh)
                self.assertEqual(self.harness.status(workspace), deletions(full_uncopied()))
                self.assert_accepted(self.verify(self.source(fixture, workspace), copied=fixture.record), fixture, workspace)
                write(workspace / NOTES, b"changed after the preparation\n")
                outcome = self.verify(self.source(fixture, workspace), copied=fixture.record)
                self.assert_refused(outcome, SOURCE, DIRTY + " M " + NOTES, root=workspace, commit=fixture.commit, reads=4)

    def test_c63_an_ordinary_runs_summary_keeps_its_fields_and_values(self):
        """Label: real (the plan has no step, the platform metadata leaf is mocked, and the comparison substitutes
        refresh_workspace_index with a no-op). The PATH Git is the logging wrapper. A clean seven-entry tree, and the
        same tree with an uncommitted change and a staged new file in the original checkout."""
        path_git = write(self.fresh("path-bin") / "git", wrapper_script(self.log, self.harness.git_path), 0o755)

        def clean(fixture):
            return "", [], "\n".join(SEVEN_LINES), []

        def dirty(fixture):
            write(fixture.root / NOTES, b"uncommitted change in the original checkout\n")
            write(fixture.root / "docs/staged.md", b"staged in the original checkout\n")
            self.harness.git(fixture.root, "add", "--", "docs/staged.md")
            return (" M docs/notes.md\nA  docs/staged.md", [], "\n".join(SEVEN_LINES + [" M docs/notes.md"]),
                    ["docs/staged.md"])
        for label, prepare in (("a clean original checkout", clean), ("a dirty original checkout", dirty)):
            with self.subTest(label):
                fixture = self.fixture(seven_tree())
                original_status, original_untracked, workspace_status, workspace_untracked = prepare(fixture)
                runs = {}
                for refresh in (True, False):
                    output = self.base / ("run-%s-%d" % (refresh, self.counter))
                    self.counter += 1
                    code, summary, record = self.run_driver(fixture.root, output, refresh=refresh, path_git=path_git)
                    self.assertEqual({row[0] for row in record.starts}, {str(path_git)})
                    self.assert_no_forbidden_program(record.starts)
                    runs[refresh] = (code, summary, self.normalized(record.starts, [(str(output), "<output>")]))
                for refresh, (code, summary, _) in runs.items():
                    self.assertEqual((code, summary["status"], summary["exit_code"]), (0, "passed", 0), summary.get("error"))
                    self.assertEqual(set(summary), SUMMARY_KEYS)
                    self.assertEqual(summary["readback_selection"], ORDINARY)
                    self.assertEqual(summary["git"], {"available": True, "local_head": fixture.commit,
                                                      "local_tree": fixture.tree, "tracked_worktree_status": original_status,
                                                      "untracked_source_files": original_untracked,
                                                      "head_is_base_revision": True,
                                                      "source_inventory_includes_untracked_files": True,
                                                      "remote_head_verified": False})
                    self.assertEqual(summary["workspace_git"], {
                        "available": True, "local_head": fixture.commit, "local_tree": fixture.tree,
                        "tracked_worktree_status": workspace_status, "untracked_source_files": workspace_untracked,
                        "head_is_base_revision": True, "source_inventory_includes_untracked_files": True,
                        "remote_head_verified": False, "index_basis": "source_commit_tree",
                        "copied_worktree_changes_preserved": True, "source_staging_preserved": False})
                    self.assertEqual(set(summary["workspace_git"]), WORKSPACE_GIT_KEYS)
                    self.assertEqual((summary["workspace_storage"]["lfs_files"], summary["workspace_storage"]["network_transfers"]),
                                     ([], False))
                    self.assertEqual((summary["source_unchanged"], summary["git_revision_unchanged"]), (True, True))
                    self.assertEqual((summary["steps"], summary["not_executed_steps"], summary["pending_external_cases"]),
                                     ([], [], []))
                    self.assertEqual(summary["git_binding"], {"path": str(path_git), "sha256": file_sha256(path_git),
                                                              "bound": False, "source": "PATH"})
                with_refresh, without = runs[True][1], runs[False][1]
                self.assertEqual({key: value for key, value in with_refresh.items() if key not in TIMES},
                                 {key: value for key, value in without.items() if key not in TIMES})
                starts, baseline = runs[True][2], runs[False][2]
                # The workspace's first read after its preparation: git_metadata(workspace) for workspace_git.
                first_read = baseline.index([str(path_git), "-c", "core.fsmonitor=false", "-C", "<output>/workspace",
                                             "rev-parse", "--show-toplevel"])
                self.assertEqual(baseline[first_read - 1][-4:-1], ["ls-tree", "-r", "-z"], "the storage step's last read")
                self.assertFalse([row for row in baseline[:first_read] if "<output>/workspace" in row and "status" in row])
                refresh_start = [str(path_git), "-c", "core.fsmonitor=false", "-C", "<output>/workspace", *REFRESH]
                self.assertEqual(starts, baseline[:first_read] + [refresh_start] + baseline[first_read:])

    def test_c64_a_failed_refresh_fails_the_run_before_any_step(self):
        """Label: simulated (the PATH Git's refresh start exits 128; every other start runs the real Git). An ordinary
        run whose one planned step must never start."""
        path_git = write(self.fresh("path-bin") / "git", wrapper_script(self.log, self.harness.git_path, fail_refresh=True), 0o755)
        fixture = self.fixture(seven_tree())
        output = self.base / "run-failed-refresh"
        step = check_local.Step("control-unit", (sys.executable, "-I", "-S", "-B", "-c", "raise SystemExit(7)"))
        code, summary, record = self.run_driver(fixture.root, output, plan=[step], path_git=path_git)
        self.assertEqual((code, summary["status"], summary["exit_code"]), (1, "failed", 1))
        self.assertTrue(summary["error"].startswith(REFRESH_FAILED), summary["error"])
        self.assertIn("returned non-zero exit status 128", summary["error"])
        self.assertEqual(summary["readback_selection"], ORDINARY)
        self.assertEqual((summary["steps"], summary["not_executed_steps"]), ([], ["control-unit"]))
        self.assertNotIn("workspace_git", summary)
        self.assertEqual({row[0] for row in record.starts}, {str(path_git)})
        self.assertEqual(record.starts[-1][1:], ["-c", "core.fsmonitor=false", "-C", str(output / "workspace"), *REFRESH])

    def test_c65_a_copied_file_that_differs_from_the_commit_before_the_copy_stays_unrefreshed_and_refuses(self):
        """Label: real. The original checkout has an uncommitted change of docs/notes.md when the driver copies it: the
        refresh leaves that entry without stat data, status reports it, and the derived check refuses it."""
        fixture = self.fixture(full_tree())
        write(fixture.root / NOTES, b"changed in the original checkout before the copy\n")
        output = self.fresh("evidence")
        workspace = check_local.prepare_workspace(fixture.root, output, False)
        _, entries = index_entries(workspace / ".git/index")
        self.assertEqual(entries[NOTES]["stat"], ZERO_STAT)
        self.assertNotEqual(entries["README.md"]["stat"], ZERO_STAT)
        self.assertIn(" M " + NOTES, self.harness.status(workspace))
        outcome = self.verify(self.source(fixture, workspace), copied=check_local.inventory(fixture.root))
        self.assert_refused(outcome, SOURCE, DIRTY + " M " + NOTES, root=workspace, commit=fixture.commit, reads=4)


if __name__ == "__main__":
    unittest.main()
