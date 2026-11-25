#!/usr/bin/env python3
"""Read and validate OntoKin's repository-owned workflow records for local and browser sessions.

This offline helper checks recorded structure and local references. It does not
authenticate evidence, contact GitHub, establish merge state, or grant authority.
Only ``new-task`` writes files; it creates an unselected local draft.

The registry and CURRENT have two schemas. Schema 1 has one browser entry point and embedded
handoff receipts; it stays valid for earlier records. Schema 2 names an entry point and read
set for each execution mode and links retained history instead of embedding it. The mapping is
in docs/engineering/local-migration-20261124/SCHEMA-MAPPING.md.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import ipaddress
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Any
from urllib.parse import urlsplit


REGISTRY = "docs/workflow/registry.json"
LIMIT = 2_000_000
IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
TASK_STATES = {"draft", "ready", "in_progress", "blocked", "review", "done", "retired", "cancelled"}
CLOSED_STATES = {"done", "retired", "cancelled"}
MODES = {"local", "browser"}
EMBEDDED_RECEIPTS = ("historical_handoff", "latest_handoff", "previous_handoff", "older_handoffs",
                     "latest_recovery", "previous_recovery", "older_recoveries")
NOTICE = "Local structural check only; live GitHub state and the truth of cited evidence require separate verification."


class Invalid(ValueError):
    """An actionable workflow-data diagnostic."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Invalid(message)


def mapping(value: Any, label: str) -> dict:
    require(isinstance(value, dict), f"{label}: expected an object")
    return value


def sequence(value: Any, label: str, nonempty: bool = False) -> list:
    require(isinstance(value, list), f"{label}: expected an array")
    require(not nonempty or bool(value), f"{label}: must not be empty")
    return value


def text(value: Any, label: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), f"{label}: expected nonempty text")
    return value


def choice(value: Any, values: set[str], label: str) -> str:
    require(isinstance(value, str) and value in values, f"{label}: expected one of {', '.join(sorted(values))}")
    return value


def identifier(value: Any, label: str) -> str:
    require(isinstance(value, str) and bool(IDENTIFIER.fullmatch(value)), f"{label}: invalid identifier")
    return value


def sha(value: Any, label: str, optional: bool = False) -> None:
    require((optional and value is None) or (isinstance(value, str) and bool(SHA.fullmatch(value))),
            f"{label}: expected {'null or ' if optional else ''}40 lowercase hexadecimal characters")


def timestamp(value: Any, label: str) -> None:
    raw = text(value, label)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise Invalid(f"{label}: invalid ISO timestamp") from exc
    require(parsed.utcoffset() is not None and parsed.utcoffset().total_seconds() == 0,
            f"{label}: expected an explicit UTC timestamp")


def https(value: Any, label: str) -> str:
    raw = text(value, label)
    require(not any(c.isspace() or ord(c) < 32 for c in raw) and "\\" not in raw,
            f"{label}: invalid URL characters")
    try:
        parsed = urlsplit(raw)
        parsed.port
    except ValueError as exc:
        raise Invalid(f"{label}: malformed URL") from exc
    require(parsed.scheme == "https" and bool(parsed.hostname) and parsed.username is None
            and parsed.password is None, f"{label}: expected an HTTPS URL without credentials")
    host = parsed.hostname
    try:
        ipaddress.ip_address(host)
    except ValueError:
        try:
            hostname = host.encode("idna").decode("ascii")
        except UnicodeError as exc:
            raise Invalid(f"{label}: invalid hostname") from exc
        require(len(hostname) <= 253 and all(re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", part)
                                            for part in hostname.rstrip(".").split(".")),
                f"{label}: invalid hostname")
    return raw


class Project:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.errors: list[str] = []
        self.registry: dict = {}
        self.current: dict = {}
        self.memory: dict = {}
        self.knowledge: dict = {}
        self.modes: dict[str, dict] = {}
        self.tasks: dict[str, dict] = {}

    def path(self, value: Any, label: str, exists: bool = True, directory: bool = False) -> Path:
        raw = text(value, label)
        require("\\" not in raw and "\x00" not in raw and "?" not in raw and "#" not in raw,
                f"{label}: expected a repository-relative path")
        parts = PurePosixPath(raw)
        require(not parts.is_absolute() and not any(p in {".", ".."} for p in raw.split("/"))
                and "" not in raw.split("/") and ":" not in raw,
                f"{label}: unsafe repository-relative path")
        target = self.root.joinpath(*parts.parts)
        require(target.resolve().is_relative_to(self.root), f"{label}: path escapes repository")
        if exists:
            require(target.is_dir() if directory else target.is_file(), f"{label}: missing {'directory' if directory else 'file'} {raw}")
        return target

    def source(self, value: Any, label: str) -> None:
        raw = text(value, label)
        if raw.startswith("https://"):
            https(raw, label)
        else:
            self.path(raw.split("#", 1)[0], label)

    def sources(self, value: Any, label: str, nonempty: bool = True) -> list:
        items = sequence(value, label, nonempty)
        for i, item in enumerate(items):
            self.source(item, f"{label}[{i}]")
        return items

    def load(self, relative: str, versions: tuple[int, ...] = (1,)) -> dict:
        file = self.path(relative, relative)
        require(file.stat().st_size <= LIMIT, f"{relative}: exceeds {LIMIT}-byte input limit")
        def unique_object(pairs: list[tuple[str, Any]]) -> dict:
            result = {}
            for key, value in pairs:
                require(key not in result, f"{relative}: duplicate JSON key {key}")
                result[key] = value
            return result
        try:
            data = mapping(json.loads(file.read_text(encoding="utf-8"), object_pairs_hook=unique_object), relative)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise Invalid(f"{relative}: invalid UTF-8 JSON: {exc}") from exc
        require(type(data.get("schema_version")) is int and data["schema_version"] in versions,
                f"{relative}: unsupported schema_version; expected {' or '.join(map(str, versions))}")
        return data

    def group(self, value: Any, label: str, nonempty: bool = False) -> dict[str, dict]:
        result = {}
        for item in sequence(value, label, nonempty):
            item = mapping(item, label)
            key = identifier(item.get("id"), f"{label}.id")
            require(key not in result, f"{label}: duplicate id {key}")
            result[key] = item
        return result

    def validate_registry(self) -> None:
        r = self.registry = self.load(REGISTRY, (1, 2))
        require(r.get("repository") == "Omegapy/OntoKin", "registry.repository: expected Omegapy/OntoKin")
        if r["schema_version"] == 1:
            # Schema 1 predates local mode; its single entry point is the browser entry point.
            self.modes = {"browser": self.read_set(r, "registry")}
        else:
            for key in ("entrypoint", "required_reads"):
                require(key not in r, f"registry.{key}: schema 2 names it only inside modes")
            modes = mapping(r.get("modes"), "registry.modes")
            require(set(modes) == MODES, f"registry.modes: expected exactly {', '.join(sorted(MODES))}")
            for name in sorted(modes):
                self.modes[name] = self.read_set(mapping(modes[name], f"registry.modes.{name}"), f"registry.modes.{name}")
                text(modes[name].get("declared_by"), f"registry.modes.{name}.declared_by")
            require(len({entry["entrypoint"] for entry in self.modes.values()}) == len(self.modes),
                    "registry.modes: each mode needs its own entrypoint")
        self.path(r.get("task_root"), "registry.task_root", directory=True)
        for key in ("memory", "knowledge", "current"):
            self.path(r.get(key), f"registry.{key}")
        for key, skill in self.group(r.get("skills"), "registry.skills", True).items():
            file = self.path(skill.get("path"), f"skill {key}.path")
            text(skill.get("when"), f"skill {key}.when")
            require(file.stat().st_size <= LIMIT, f"skill {key}: exceeds input limit")
            lines = file.read_text(encoding="utf-8").splitlines()
            require(lines and lines[0] == "---" and "---" in lines[1:], f"skill {key}: missing frontmatter")
            front = lines[1:lines.index("---", 1)]
            fields = {}
            for line in front:
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                require(":" in line and not line.startswith((" ", "\t")),
                        f"skill {key}: use simple single-line name and description frontmatter")
                name, value = line.split(":", 1)
                require(name not in fields, f"skill {key}: duplicate frontmatter key {name}")
                fields[name] = value.strip().strip("\"'")
            require(fields.get("name") == key, f"skill {key}: frontmatter name mismatch")
            text(fields.get("description"), f"skill {key}.description")

    def read_set(self, entry: dict, label: str) -> dict:
        self.path(entry.get("entrypoint"), f"{label}.entrypoint")
        for path in sequence(entry.get("required_reads"), f"{label}.required_reads", True):
            self.path(path, f"{label}.required_reads")
        require(entry["entrypoint"] in entry["required_reads"], f"{label}.required_reads: must include entrypoint")
        return {"entrypoint": entry["entrypoint"], "required_reads": entry["required_reads"]}

    def validate_current(self) -> None:
        c = self.current = self.load(self.registry["current"], (1, 2))
        require(c.get("project") == self.registry["repository"], "current.project: repository mismatch")
        identifier(c.get("latest_task"), "current.latest_task")
        if c.get("active_task") is not None:
            identifier(c["active_task"], "current.active_task")
        sha(c.get("observed_main"), "current.observed_main")
        timestamp(c.get("snapshot_date"), "current.snapshot_date")
        n = mapping(c.get("next_action"), "current.next_action")
        choice(n.get("status"), {"awaiting_user_direction", "ready", "blocked"}, "current.next_action.status")
        text(n.get("summary"), "current.next_action.summary")
        text(n.get("suggested_task"), "current.next_action.suggested_task")
        self.sources(n.get("sources"), "current.next_action.sources")
        for item in sequence(c.get("boundaries"), "current.boundaries", True):
            text(item, "current.boundaries")
        if c["schema_version"] == 2:
            self.validate_pointers(c)
            return
        h = mapping(c.get("historical_handoff"), "current.historical_handoff")
        https(h.get("url"), "current.historical_handoff.url")
        require(isinstance(h.get("sha256"), str) and bool(SHA256.fullmatch(h["sha256"])),
                "current.historical_handoff.sha256: expected 64 lowercase hexadecimal characters")
        require(type(h.get("bytes")) is int and h["bytes"] > 0, "current.historical_handoff.bytes: expected positive integer")
        text(h.get("scope"), "current.historical_handoff.scope")

    def validate_pointers(self, c: dict) -> None:
        """Schema 2: the selected mode and checkpoint, unfinished scopes and links to retained history."""
        for key in EMBEDDED_RECEIPTS:
            require(key not in c, f"current.{key}: schema 2 keeps receipts in linked history")
        active, mode = c.get("active_task"), c.get("execution_mode")
        require(mode is None or mode in self.modes, f"current.execution_mode: expected null or one of {', '.join(sorted(self.modes))}")
        require(active is None or mode is not None, "current.execution_mode: an active task needs its recorded mode")
        checkpoint = mapping(c.get("checkpoint"), "current.checkpoint")
        for key in ("record", "session"):
            require(key in checkpoint, f"current.checkpoint.{key}: expected a path or null")
            if checkpoint[key] is not None:
                self.path(checkpoint[key], f"current.checkpoint.{key}")
        require(active is None or checkpoint["record"] == f"{self.registry['task_root']}/{active}/task.json",
                "current.checkpoint.record: must be the active task's record")
        names = set()
        for item in sequence(c.get("unfinished"), "current.unfinished"):
            item = mapping(item, "current.unfinished")
            name = identifier(item.get("task"), "current.unfinished.task")
            require(name not in names and name != active, f"current.unfinished: {name} is repeated or is the active task")
            names.add(name)
            choice(item.get("status"), TASK_STATES - CLOSED_STATES, f"current.unfinished {name}.status")
            choice(item.get("mode"), MODES, f"current.unfinished {name}.mode")
            text(item.get("branch"), f"current.unfinished {name}.branch")
            sha(item.get("observed_head"), f"current.unfinished {name}.observed_head")
            timestamp(item.get("observed_at"), f"current.unfinished {name}.observed_at")
            for key in ("pull_request", "scope_issue"):
                if item.get(key) is not None:
                    https(item[key], f"current.unfinished {name}.{key}")
            for gate in sequence(item.get("open_gates"), f"current.unfinished {name}.open_gates", True):
                text(gate, f"current.unfinished {name}.open_gates")
            self.source(item.get("record"), f"current.unfinished {name}.record")
        policy = mapping(c.get("delivery_policy"), "current.delivery_policy")
        require(set(policy) == set(self.modes), f"current.delivery_policy: expected exactly {', '.join(sorted(self.modes))}")
        for name, entry in policy.items():
            entry = mapping(entry, f"current.delivery_policy.{name}")
            self.source(entry.get("contract"), f"current.delivery_policy.{name}.contract")
            text(entry.get("completion_gate"), f"current.delivery_policy.{name}.completion_gate")
        for item in sequence(c.get("history"), "current.history", True):
            item = mapping(item, "current.history")
            file = self.path(item.get("path"), "current.history.path")
            digest = hashlib.sha256()
            with file.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            require(isinstance(item.get("sha256"), str) and item["sha256"] == digest.hexdigest(),
                    f"current.history {item['path']}: SHA-256 differs from the retained file")
            require(type(item.get("bytes")) is int and item["bytes"] == file.stat().st_size,
                    f"current.history {item['path']}: size differs from the retained file")
            sha(item.get("source_commit"), f"current.history {item['path']}.source_commit")
            for key in sequence(item.get("holds"), f"current.history {item['path']}.holds", True):
                text(key, f"current.history {item['path']}.holds")
            text(item.get("purpose"), f"current.history {item['path']}.purpose")

    def validate_task(self, task: dict, folder: str) -> None:
        name = identifier(task.get("id"), f"task {folder}.id")
        require(name == folder, f"task {folder}: id must match directory")
        state = choice(task.get("status"), TASK_STATES, f"task {name}.status")
        for key in ("title", "intent", "owner", "branch", "next_action"):
            text(task.get(key), f"task {name}.{key}")
        if "execution_mode" in task:
            choice(task["execution_mode"], MODES, f"task {name}.execution_mode")
        sha(task.get("base_sha"), f"task {name}.base_sha")
        # A draft can be cancelled or retired before planning ever starts.
        planned = state not in {"draft", "cancelled", "retired"}
        requirements = self.group(task.get("requirements"), f"task {name}.requirements", planned)
        for key, req in requirements.items():
            for field in ("description", "acceptance"):
                text(req.get(field), f"{name}/{key}.{field}")
            done = choice(req.get("status"), {"not_done", "done"}, f"{name}/{key}.status") == "done"
            self.sources(req.get("evidence"), f"{name}/{key}.evidence", done)
            require(state != "done" or done, f"task {name}: done with unfinished requirement {key}")
        plan = self.group(task.get("plan"), f"task {name}.plan", planned)
        covered = set()
        for key, step in plan.items():
            text(step.get("title"), f"{name}/{key}.title")
            done = choice(step.get("status"), {"not_done", "in_progress", "done"}, f"{name}/{key}.status") == "done"
            for req in sequence(step.get("requirements"), f"{name}/{key}.requirements", True):
                identifier(req, f"{name}/{key}.requirements")
                require(req in requirements, f"{name}/{key}: unknown requirement {req}")
                covered.add(req)
            for item in sequence(step.get("artifacts"), f"{name}/{key}.artifacts", True):
                self.path(item, f"{name}/{key}.artifacts", exists=done)
            for item in sequence(step.get("verification"), f"{name}/{key}.verification", True):
                text(item, f"{name}/{key}.verification")
            require(state != "done" or done, f"task {name}: done with unfinished plan step {key}")
        require(covered == set(requirements), f"task {name}: requirements missing from plan: {', '.join(sorted(set(requirements) - covered))}")
        required_checks = []
        seen_checks = set()
        for check in sequence(task.get("checks"), f"task {name}.checks"):
            check = mapping(check, f"task {name}.checks")
            label = text(check.get("name"), f"task {name}.check.name")
            require(label not in seen_checks, f"task {name}: duplicate check {label}")
            seen_checks.add(label)
            text(check.get("command"), f"check {label}.command")
            result = choice(check.get("result"), {"passed", "failed", "not_run"}, f"check {label}.result")
            require(type(check.get("required")) is bool, f"check {label}.required: expected Boolean")
            self.sources(check.get("evidence"), f"check {label}.evidence", result != "not_run")
            if check["required"]:
                required_checks.append(check)
        completion = mapping(task.get("completion"), f"task {name}.completion")
        for key in ("implementation_commit", "merge_commit"):
            sha(completion.get(key), f"task {name}.completion.{key}", optional=state != "done")
        if completion.get("pull_request") is not None:
            url = https(completion["pull_request"], f"task {name}.completion.pull_request")
            require(bool(re.fullmatch(r"https://github\.com/Omegapy/OntoKin/pull/[1-9][0-9]*", url)),
                    f"task {name}: pull_request must identify an OntoKin PR")
        disposition = choice(completion.get("branch_disposition"), {"active", "deleted", "deletion_pending", "retained"}, f"task {name}.completion.branch_disposition")
        self.sources(completion.get("evidence"), f"task {name}.completion.evidence", state == "done")
        if state == "done":
            require(bool(required_checks) and all(c["result"] == "passed" for c in required_checks),
                    f"task {name}: done requires passing recorded required checks")
            require(completion.get("pull_request") is not None, f"task {name}: done requires a pull_request")
            require(disposition in {"deleted", "deletion_pending"}, f"task {name}: done requires branch cleanup disposition")

    def validate_tasks(self) -> None:
        directory = self.path(self.registry["task_root"], "registry.task_root", directory=True)
        for child in sorted(directory.iterdir()):
            if not child.is_dir():
                continue
            identifier(child.name, "task directory")
            relative = f"{self.registry['task_root']}/{child.name}/task.json"
            task = self.load(relative)
            self.validate_task(task, child.name)
            self.tasks[child.name] = task
        for key in ("latest_task", "active_task"):
            value = self.current.get(key)
            require(value is None or (isinstance(value, str) and value in self.tasks),
                    f"current.{key}: task {value!r} is missing")
        active = self.current.get("active_task")
        if active:
            require(self.tasks[active]["status"] not in CLOSED_STATES,
                    "current.active_task: completed or retired tasks cannot be active")
            if self.current["schema_version"] == 2:
                require(self.tasks[active].get("execution_mode") == self.current.get("execution_mode"),
                        "current.execution_mode: differs from the active task's recorded mode")

    def validate_memory(self) -> None:
        self.memory = self.load(self.registry["memory"])
        records = self.group(self.memory.get("records"), "memory.records")
        for key, record in records.items():
            choice(record.get("kind"), {"decision", "lesson", "constraint", "open_question"}, f"memory {key}.kind")
            choice(record.get("status"), {"current", "historical", "proposed", "unresolved", "superseded"}, f"memory {key}.status")
            for field in ("summary", "scope", "recorded_at"):
                text(record.get(field), f"memory {key}.{field}")
            self.sources(record.get("sources"), f"memory {key}.sources")
            previous = record.get("supersedes")
            require(previous is None or (isinstance(previous, str) and previous in records and previous != key),
                    f"memory {key}.supersedes: must name another existing record or null")
        for key in records:
            seen = set()
            cursor = key
            while cursor is not None:
                require(cursor not in seen, f"memory {key}: supersedes cycle")
                seen.add(cursor)
                cursor = records[cursor].get("supersedes")

    def validate_knowledge(self) -> None:
        self.knowledge = self.load(self.registry["knowledge"])
        terms = self.group(self.knowledge.get("terms"), "knowledge.terms")
        capabilities = self.group(self.knowledge.get("capabilities"), "knowledge.capabilities")
        require(not set(terms) & set(capabilities), "knowledge: term and capability IDs must be distinct")
        for key, term in terms.items():
            for field in ("term", "definition", "status"):
                text(term.get(field), f"term {key}.{field}")
            self.sources(term.get("authority"), f"term {key}.authority")
        for key, capability in capabilities.items():
            for field in ("name", "description", "status", "limits"):
                text(capability.get(field), f"capability {key}.{field}")
            self.sources(capability.get("sources"), f"capability {key}.sources")
        ids = set(terms) | set(capabilities)
        seen = set()
        for relation in sequence(self.knowledge.get("relationships"), "knowledge.relationships"):
            relation = mapping(relation, "knowledge.relationships")
            for field in ("subject", "object"):
                key = identifier(relation.get(field), f"relationship.{field}")
                require(key in ids, f"relationship.{field}: unknown knowledge ID {key}")
            text(relation.get("relation"), "relationship.relation")
            self.source(relation.get("source"), "relationship.source")
            key = (relation["subject"], relation["relation"], relation["object"])
            require(key not in seen, "knowledge.relationships: duplicate relationship")
            seen.add(key)

    def validate(self) -> dict:
        try:
            self.validate_registry()
        except (Invalid, OSError, UnicodeError, RuntimeError) as exc:
            self.errors.append(str(exc))
            return self.report()
        for procedure in (self.validate_current, self.validate_tasks, self.validate_memory, self.validate_knowledge):
            try:
                procedure()
            except (Invalid, OSError, UnicodeError, RuntimeError) as exc:
                self.errors.append(str(exc))
        return self.report()

    def report(self) -> dict:
        return {"passed": not self.errors, "errors": self.errors, "tasks_checked": len(self.tasks), "notice": NOTICE}

    def local_git(self, top_only: bool = False) -> dict:
        def run(*args: str) -> str | None:
            try:
                output = subprocess.run(["git", "--no-optional-locks", "-c", "core.fsmonitor=false",
                                         "-C", str(self.root), *args], capture_output=True,
                                        text=True, timeout=5, check=True)
                return output.stdout.strip()
            except (OSError, subprocess.SubprocessError):
                return None
        head = run("rev-parse", "HEAD")
        if top_only and head and Path(run("rev-parse", "--show-toplevel") or "/").resolve() != self.root:
            head = None  # A surrounding repository is not this checkout.
        dirty = run("status", "--porcelain", "--untracked-files=normal") if head else None
        return {"head": head, "dirty": bool(dirty) if dirty is not None else None,
                "scope": "local checkout only; no remote fetch or live-state verification"}

    def brief(self) -> dict:
        def task_summary(task_id: str | None) -> dict | None:
            if task_id is None:
                return None
            task = self.tasks[task_id]
            return {"id": task_id, "title": task["title"], "status": task["status"],
                    "record": f"{self.registry['task_root']}/{task_id}/task.json",
                    "owner": task["owner"], "branch": task["branch"], "next_action": task["next_action"],
                    "requirements_done": sum(r["status"] == "done" for r in task["requirements"]),
                    "requirements_total": len(task["requirements"]), "completion": task["completion"]}
        # Schema 1 has one entry point; schema 2 reads the selected task's mode and guesses none.
        mode = self.current.get("execution_mode") or (next(iter(self.modes)) if len(self.modes) == 1 else None)
        return {"project": self.registry["repository"], "current": self.current, "modes": self.modes,
                "required_reads": self.modes[mode]["required_reads"] if mode else None, "skills": self.registry["skills"],
                "active_task": task_summary(self.current.get("active_task")),
                "latest_task": task_summary(self.current["latest_task"]), "local_git": self.local_git(), "notice": NOTICE}

    def lookup(self, query: str) -> dict:
        words = query.casefold().split()
        require(bool(words), "lookup: query must not be empty")
        matches = []
        for kind, records in (("memory", self.memory["records"]), ("term", self.knowledge["terms"]),
                              ("capability", self.knowledge["capabilities"])):
            for record in records:
                corpus = " ".join(str(record.get(k, "")) for k in
                                  ("id", "summary", "scope", "term", "definition", "name", "description", "limits")).casefold()
                if all(word in corpus for word in words):
                    matches.append({"kind": kind, "record": record})
        return {"query": query, "matches": matches, "method": "literal case-insensitive AND search; no inference", "notice": NOTICE}

    def starting_revision(self, base: str | None) -> tuple[str, str]:
        """A supplied commit or the observed local head; never the recorded CURRENT.observed_main.

        CURRENT records an earlier observation and can be older than the actual head. Nothing is
        fetched: a head observed on the remote is supplied with --base.
        """
        if base is not None:
            sha(base, "new-task.base")
            return base, "supplied with --base"
        head = self.local_git(top_only=True)["head"]
        require(head is not None and bool(SHA.fullmatch(head)),
                "new-task.base: the local Git head of this root was not observed; supply --base with the observed starting commit")
        return head, "observed local head of this checkout"

    def new_task(self, task_id: str, title: str, intent: str, base: str | None = None) -> dict:
        identifier(task_id, "new-task.id")
        text(title, "new-task.title")
        text(intent, "new-task.intent")
        relative = f"{self.registry['task_root']}/{task_id}"
        directory = self.path(relative, "new-task.directory", exists=False)
        require(not directory.exists() and not directory.is_symlink(), f"new-task: {task_id} already exists; refusing overwrite")
        revision, origin = self.starting_revision(base)
        recorded = self.current["observed_main"]
        observation = origin + ("" if revision == recorded else f"; CURRENT.observed_main records {recorded}")
        task = {"schema_version": 1, "id": task_id, "title": title, "intent": intent, "status": "draft",
                "owner": "unassigned", "branch": "unassigned", "base_sha": revision, "base_observation": observation,
                "requirements": [], "plan": [], "checks": [],
                "completion": {"implementation_commit": None, "merge_commit": None, "pull_request": None,
                               "branch_disposition": "active", "evidence": []},
                "next_action": "Reconcile live GitHub state; assign scope and owner, then complete requirements and plan before implementation."}
        def literal(value: str) -> str:
            # A longer fence keeps supplied Markdown, HTML and embedded fences inert.
            fence = "`" * max(3, max((len(run) for run in re.findall(r"`+", value)), default=0) + 1)
            return f"{fence}text\n{value}\n{fence}"
        requirements = (
            f"# {task_id} requirements: draft\n\n"
            "This local draft is not selected work and makes no implementation or verification claim. "
            "Reconcile live repository state and the current user request before completing it.\n\n"
            f"## Requested title\n\n{literal(title)}\n\n"
            f"## Supplied intent\n\n{literal(intent)}\n\n"
            "## Scope and constraints\n\nNot yet specified. Record inclusions, exclusions, sources and unresolved questions.\n\n"
            "## Requirements and acceptance\n\nNot yet specified. Assign stable requirement IDs and observable acceptance criteria. "
            "Keep the requirements in [task.json](task.json) consistent with this document.\n\n"
            "## Evidence\n\nNo implementation or verification evidence has been recorded for this draft.\n"
        )
        plan = (
            f"# {task_id} implementation plan: draft\n\n"
            "This local draft is not authorization to execute and makes no completion claim.\n\n"
            f"## Requested title\n\n{literal(title)}\n\n"
            "## Inputs\n\nRead the supplied intent and acceptance criteria in [REQUIREMENTS.md](REQUIREMENTS.md), "
            "the current repository instructions, and the actual GitHub state.\n\n"
            "## Work and ownership\n\nNot yet specified. Map every requirement to a bounded step, owner, dependencies and intended artifacts. "
            "Keep the plan in [task.json](task.json) consistent with this document.\n\n"
            "## Verification and integration\n\nNot yet specified. Name applicable checks, evidence, review, integration and branch cleanup requirements.\n\n"
            "## Next action\n\nComplete this plan and the requirements after scope selection. "
            "Do not mark any step or requirement complete without supporting evidence.\n"
        )
        directory.mkdir()
        # On a failed write, leave any partial record visible for recovery.
        documents = {"task.json": json.dumps(task, indent=2, ensure_ascii=False) + "\n",
                     "REQUIREMENTS.md": requirements, "PLAN.md": plan}
        for name, content in documents.items():
            with (directory / name).open("x", encoding="utf-8") as output:
                output.write(content)
        return {"created": f"{relative}/task.json", "created_files": [f"{relative}/{name}" for name in documents],
                "status": "draft", "selected": False, "base_sha": revision, "base_observation": observation,
                "notice": "Created a local draft only. CURRENT, GitHub, authorization and integration ownership are unchanged."}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="repository checkout root")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "brief", "lookup", "new-task"):
        command = commands.add_parser(name)
        command.add_argument("--json", action="store_true", help="emit machine-readable JSON")
        if name == "lookup":
            command.add_argument("query")
        if name == "new-task":
            command.add_argument("id")
            command.add_argument("--title", required=True)
            command.add_argument("--intent", required=True)
            command.add_argument("--base", help="observed starting commit; default: the local head of this checkout")
    args = parser.parse_args(argv)
    project = Project(args.root)
    result = project.validate()
    if result["passed"]:
        try:
            if args.command == "brief":
                result = project.brief()
            elif args.command == "lookup":
                result = project.lookup(args.query)
            elif args.command == "new-task":
                result = project.new_task(args.id, args.title, args.intent, args.base)
        except (Invalid, OSError, RuntimeError) as exc:
            result = {"passed": False, "errors": [str(exc)], "notice": NOTICE}
    failed = result.get("passed") is False
    if args.json or args.command in {"brief", "lookup"}:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif failed:
        print("Workflow check failed:")
        for error in result["errors"]:
            print(f"- {error}")
        print(result["notice"])
    elif args.command == "new-task":
        print("Created local draft files:")
        for path in result["created_files"]:
            print(f"- {path}")
        print(f"Base: {result['base_sha']} ({result['base_observation']})")
        print(result["notice"])
    else:
        print(f"Workflow structure passed ({result['tasks_checked']} tasks).\n{NOTICE}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
