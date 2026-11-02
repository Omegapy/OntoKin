"""Exact reviewed Agent-only input overlay; never a generic manifest override."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from keyed_membership_evidence import FROZEN_MANIFEST_SHA256, canonical, inventory, read, sha


# This exact proposal remains closed until root supplies independently reviewed,
# published and read-back adoption identity. No CLI switch bypasses this gate.
EXPECTED_AMENDMENT_SHA256 = "d53ae7f40659686d0874ced5d342deaa1a1421fd6ce17b9e6dd02b1b68510a54"
EXPECTED_EFFECTIVE_MANIFEST_SHA256 = "c3bebcb33f03340b1d92ae48172c5c5d83d45f87e38a6934d75fd7ce7e327546"
ADOPTED_PUBLICATION_COMMIT = "d162ec2cb8e032c24d2e7897eac642fe1fbe7ab0"


class AgentAmendment:
    def __init__(self, freeze, directory):
        if ADOPTED_PUBLICATION_COMMIT is None:
            raise ValueError("The exact Agent amendment has not yet passed independent adoption/readback.")
        self.directory = Path(directory).resolve()
        self.path = self.directory / "AMENDMENT.json"
        if sha(self.path.read_bytes()) != EXPECTED_AMENDMENT_SHA256:
            raise ValueError("Agent amendment is not the independently reviewed exact proposal.")
        self.record = read(self.path)
        self.before = inventory(self.directory)
        for field in ("static_review_basis", "content_diff"):
            artifact = self.record[field]
            if sha((self.directory / artifact["path"]).read_bytes()) != artifact["sha256"]:
                raise ValueError("Agent amendment's sealed review artifact differs: " + field)
        if self.record["original_input_manifest_sha256"] != FROZEN_MANIFEST_SHA256:
            raise ValueError("Agent amendment identifies a different original freeze.")
        self.root = self.directory / "effective-freeze"
        raw_manifest = (self.root / "INPUTS-MANIFEST.json").read_bytes()
        if sha(raw_manifest) != EXPECTED_EFFECTIVE_MANIFEST_SHA256 or self.record["effective_input_manifest_sha256"] != EXPECTED_EFFECTIVE_MANIFEST_SHA256:
            raise ValueError("Agent effective manifest differs from adopted bytes.")
        self.manifest = json.loads(raw_manifest)
        self.files = inventory(self.root, exclude=("INPUTS-MANIFEST.json",))
        if self.files != self.manifest["files"] or sha(canonical(self.files)) != self.record["effective_input_inventory_sha256"]:
            raise ValueError("Agent effective file inventory differs.")
        original_files = {row["path"]: row for row in freeze.before}
        if set(original_files) != {row["path"] for row in self.files}:
            raise ValueError("Agent overlay cannot add or remove frozen files.")
        changed = [row["path"] for row in self.files if row != original_files[row["path"]]]
        if changed != ["agent/request-workflows.json"]:
            raise ValueError("Agent overlay attempted a semantic or unrelated file change.")
        change = self.record["changed_file"]
        before = (freeze.root / change["path"]).read_bytes()
        after = (self.root / change["path"]).read_bytes()
        if sha(before) != change["original_sha256"] or sha(after) != change["replacement_sha256"]:
            raise ValueError("Original/replacement workflow byte precondition differs.")
        patch_path = self.directory / self.record["patch"]["path"]
        if sha(patch_path.read_bytes()) != self.record["patch"]["sha256"]:
            raise ValueError("Exact test/replace patch identity differs.")
        patched = copy.deepcopy(json.loads(before))
        operations = read(patch_path)
        if len(operations) != 14:
            raise ValueError("Agent overlay must contain exactly seven tests and seven replacements.")
        for index, operation in enumerate(operations):
            if operation["op"] != ("test" if index % 2 == 0 else "replace"):
                raise ValueError("Agent overlay test/replace order differs.")
            parts = operation["path"].split("/")[1:]
            if parts[-3:] != ["patches", "0", "element_id"]:
                raise ValueError("Agent overlay target is not the frozen source scope field.")
            target = patched
            for part in parts[:-1]:
                target = target[int(part)] if isinstance(target, list) else target[part]
            if operation["op"] == "test":
                if target[parts[-1]] != operation["value"] or operation["value"] != ["sparse-panels", "demo", "first"]:
                    raise ValueError("Original occurrence-scope patch precondition differs.")
            else:
                if operation["value"] != ["sources", "entry"] or target["source_id"] != "entry":
                    raise ValueError("Replacement is not the exact inherited source-file scope.")
                target[parts[-1]] = operation["value"]
        if patched != json.loads(after):
            raise ValueError("Agent replacement changed a non-authorized JSON field.")
        self.contract = patched

    def lineage(self):
        return {"amendment_sha256": EXPECTED_AMENDMENT_SHA256,
                "effective_input_manifest_sha256": EXPECTED_EFFECTIVE_MANIFEST_SHA256,
                "effective_input_inventory_sha256": self.record["effective_input_inventory_sha256"],
                "original_input_manifest_sha256": FROZEN_MANIFEST_SHA256,
                "adopted_publication_commit": ADOPTED_PUBLICATION_COMMIT}

    def assert_unchanged(self):
        if self.before != inventory(self.directory):
            raise ValueError("An original Agent amendment artifact changed during independent reading.")
        if sha(self.path.read_bytes()) != EXPECTED_AMENDMENT_SHA256 or self.files != inventory(self.root, exclude=("INPUTS-MANIFEST.json",)):
            raise ValueError("Exact Agent amendment changed during independent reading.")
        if sha((self.root / "INPUTS-MANIFEST.json").read_bytes()) != EXPECTED_EFFECTIVE_MANIFEST_SHA256:
            raise ValueError("Effective manifest changed during independent reading.")
