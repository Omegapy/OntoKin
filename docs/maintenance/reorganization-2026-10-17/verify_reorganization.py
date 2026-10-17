#!/usr/bin/env python3
"""Verify this documentation migration offline using only Python's standard library.

Run from any directory. The adjacent source-map.json records the original files,
their Git object identities, exact editorial substitutions, and section hashes.
The script reconstructs every original, checks the complete baseline Git tree,
checks the active requirement registries, and follows local documentation links.
It does not execute or establish conformance of an OntoKin implementation.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import re
import sys
import unicodedata
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = Path(__file__).with_name("source-map.json")
EXPECTED_SOURCE_COUNT = 29
SUBSTANTIVE_NAMES = {
    "OntoKin_001_Project_Vision_and_Architecture.md",
    "OntoKin_002_Language_Foundations_and_Minimal_Specification.md",
    "OntoKin_003_Compilation_and_Runtime_Architecture.md",
    "OntoKin_PRD_v0.md",
    "OntoKin_Modeling_Motion_and_Object_Structure.md",
    "OntoKin_Core_Object_Motion_and_Physics_Semantics.md",
}
PRD_FAMILIES = {
    "LNG": 21, "AGT": 18, "OBJ": 18, "GEO": 12, "PHY": 21,
    "MEC": 12, "BIO": 15, "ANM": 20, "MAT": 15, "ENV": 11,
    "FLD": 13, "EXP": 16, "VAL": 11, "NFR": 14, "DOC": 9,
}
SHOULD_IDS = {
    "LNG-017", "AGT-015", "OBJ-016", "GEO-012", "MEC-012",
    "BIO-015", "ANM-017", "MAT-013", "ENV-011", "FLD-013",
    "EXP-015", "NFR-013", "DOC-008",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_object(kind: str, data: bytes) -> str:
    return hashlib.sha1(f"{kind} {len(data)}\0".encode() + data).hexdigest()


def without_code(text: str, inline: bool = False) -> str:
    """Mask YAML and fenced code, preserving newlines for useful diagnostics."""
    lines = text.splitlines(keepends=True)
    masked = []
    fence = None
    frontmatter = bool(lines and lines[0].strip() == "---")
    for index, line in enumerate(lines):
        if frontmatter:
            masked.append("\n" if line.endswith("\n") else "")
            if index and line.strip() in {"---", "..."}:
                frontmatter = False
            continue
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\r\n"))
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= fence[1] and not marker[2].strip():
                fence = None
            masked.append("\n" if line.endswith("\n") else "")
        elif marker:
            fence = (marker[1][0], len(marker[1]))
            masked.append("\n" if line.endswith("\n") else "")
        else:
            masked.append(line)
    result = "".join(masked)
    if inline:
        # A code span must close with the same number of backticks.
        result = re.sub(
            r"(?<!`)(`+)(?!`)([\s\S]*?)(?<!`)\1(?!`)",
            lambda match: "".join("\n" if c == "\n" else " " for c in match[0]),
            result,
        )
    return result


def heading_text(value: str) -> str:
    value = re.sub(r"^ {0,3}#{1,6}(?:[ \t]+|$)", "", value.strip())
    return re.sub(r"[ \t]+#+[ \t]*$", "", value).strip()


def github_slug(value: str) -> str:
    """Approximate GitHub heading IDs for this repository's Markdown vocabulary."""
    value = re.sub(r"<[^>]*>", "", value)
    value = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"\[([^\]]*)\]\[[^\]]*\]", r"\1", value)
    value = html.unescape(value).lower()
    value = "".join(
        character for character in value
        if character in "-_" or character.isspace()
        or unicodedata.category(character)[0] not in "PSC"
    )
    return re.sub(r"\s", "-", value)


class HTMLReferences(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.anchors = set()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if not value:
                continue
            if key == "id" or (tag == "a" and key == "name"):
                self.anchors.add(value)
            if key in {"href", "src"}:
                self.links.append((value, self.getpos()[0]))

    handle_startendtag = handle_starttag


def anchors_for(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    is_markdown = path.suffix.lower() in {".md", ".markdown"}
    text = without_code(text) if is_markdown else text
    parser = HTMLReferences()
    parser.feed(text)
    anchors = set(parser.anchors)
    if is_markdown:
        used = set()
        lines = text.splitlines()
        for index, line in enumerate(lines):
            match = re.match(r"^ {0,3}(#{1,6})(?:[ \t]+|$)(.*)$", line)
            label = heading_text(line) if match else None
            if not match and index and re.match(r"^ {0,3}(?:=+|-+)\s*$", line):
                previous = lines[index - 1].strip()
                if previous and previous[0] not in "|>#-*+":
                    label = previous
            if label is None:
                continue
            base = github_slug(label)
            slug = base
            suffix = 0
            while slug in used:
                suffix += 1
                slug = f"{base}-{suffix}"
            used.add(slug)
            anchors.add(slug)
    # GitHub prefixes sanitized user-defined HTML anchors in rendered markup.
    anchors.update("user-content-" + anchor for anchor in tuple(anchors))
    return anchors


def reference_label(value: str) -> str:
    return " ".join(value.split()).casefold()


def markdown_links(text: str):
    """Yield URLs from inline, reference, and HTML links outside code examples."""
    text = without_code(text, inline=True)
    definitions = {}
    for match in re.finditer(r"^ {0,3}\[([^\]\n]+)\]:\s*(?:<([^>\n]+)>|(\S+))", text, re.M):
        destination = match[2] or match[3]
        definitions[reference_label(match[1])] = destination
        yield destination, text.count("\n", 0, match.start()) + 1, None
    # Definition lines were already checked; do not treat their labels as uses.
    body = re.sub(r"^ {0,3}\[[^\]\n]+\]:[^\n]*", "", text, flags=re.M)
    index = 0
    while index < len(body):
        if body[index] != "[" or (index and body[index - 1] == "\\"):
            index += 1
            continue
        start = index
        end = start + 1
        depth = 1
        while end < len(body) and depth:
            if body[end] == "\\":
                end += 2
                continue
            if body[end] == "[":
                depth += 1
            elif body[end] == "]":
                depth -= 1
            end += 1
        if depth:
            index += 1
            continue
        label = body[start + 1:end - 1]
        line = body.count("\n", 0, start) + 1
        if end < len(body) and body[end] == "(":
            position = end + 1
            while position < len(body) and body[position].isspace():
                position += 1
            if position < len(body) and body[position] == "<":
                close = body.find(">", position + 1)
                if close != -1:
                    yield body[position + 1:close], line, None
                    index = close + 1
                    continue
            destination_start = position
            nested = 0
            while position < len(body):
                character = body[position]
                if character == "\\":
                    position += 2
                    continue
                if character == "(":
                    nested += 1
                elif character == ")":
                    if not nested:
                        break
                    nested -= 1
                elif character.isspace() and not nested:
                    break
                position += 1
            yield body[destination_start:position], line, None
            index = max(position, end + 1)
        elif end < len(body) and body[end] == "[":
            close = body.find("]", end + 1)
            if close != -1:
                key = reference_label(body[end + 1:close] or label)
                yield definitions.get(key, ""), line, None if key in definitions else key
                index = close + 1
            else:
                index = end
        else:
            key = reference_label(label)
            if key in definitions:
                yield definitions[key], line, None
            index = end
    parser = HTMLReferences()
    parser.feed(text)
    for destination, line in parser.links:
        yield destination, line, None


class Verification:
    def __init__(self):
        self.failures = []
        self.summary = {
            "status": "failed", "scope": "documentation preservation and local navigation",
            "sources": [], "sections_verified": 0, "registries": {},
            "links": {"documents": 0, "local_links": 0, "anchors": 0, "external_skipped": 0},
        }
        self.anchor_cache = {}

    def fail(self, check, detail, **context):
        self.failures.append({"check": check, "detail": detail, **context})

    def path(self, value):
        if not isinstance(value, str) or not value or PurePosixPath(value).is_absolute():
            raise ValueError(f"Expected a relative repository path: {value!r}")
        path = (ROOT / value).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError(f"Path escapes repository: {value!r}")
        return path

    def anchors(self, path):
        if path not in self.anchor_cache:
            self.anchor_cache[path] = anchors_for(path)
        return self.anchor_cache[path]

    def verify_sections(self, source, original):
        sections = source.get("sections", [])
        markdown = source["source_path"].lower().endswith((".md", ".markdown"))
        if not sections and not markdown:
            return
        lines = original.splitlines(keepends=True)
        if markdown:
            visible = without_code(original.decode("utf-8"))
            heading_starts = [
                number for number, line in enumerate(visible.splitlines(), 1)
                if re.match(r"^ {0,3}#{1,6}(?:[ \t]+|$)", line)
            ]
            expected_starts = list(heading_starts)
            if lines and (not heading_starts or heading_starts[0] != 1):
                expected_starts.insert(0, 1)
            if [section["start_line"] for section in sections] != expected_starts:
                self.fail("section_heading_coverage", "Section map must include every Markdown heading and any preamble.", source=source["source_id"])
        cursor = 1
        for number, section in enumerate(sections, 1):
            context = {"source": source["source_id"], "section": number}
            start, end = section["start_line"], section["end_line"]
            if not isinstance(start, int) or not isinstance(end, int) or start != cursor or end < start or end > len(lines):
                self.fail("section_coverage", "Sections must cover original lines once, in order, without gaps.", **context)
                return
            content = b"".join(lines[start - 1:end])
            if digest(content) != section["sha256"]:
                self.fail("section_sha256", "Reconstructed section differs from its original hash.", **context)
            else:
                self.summary["sections_verified"] += 1
            if section.get("level", 0):
                first = lines[start - 1].decode("utf-8").rstrip("\r\n")
                match = re.match(r"^ {0,3}(#{1,6})(?:[ \t]+|$)", first)
                if not match or len(match[1]) != section["level"] or heading_text(first) != heading_text(section["heading"]):
                    self.fail("section_heading", "Heading text or level does not match the source section.", **context)
            if section.get("destination_anchor"):
                anchor = unquote(section["destination_anchor"].lstrip("#"))
                if anchor not in self.anchors(self.path(source["destination"])):
                    self.fail("section_destination_anchor", f"Missing destination anchor: {anchor}", **context)
            cursor = end + 1
        if cursor != len(lines) + 1:
            self.fail("section_coverage", "Section map omits part of the original file.", source=source["source_id"])

    def check_rows(self, key, pattern, original, active, expected_ids, original_is_verified):
        original_rows = re.findall(pattern, original, re.M)
        active_rows = re.findall(pattern, active, re.M)
        # The patterns capture each complete row/heading and its identity.
        original_map = {identity: row for row, identity in original_rows}
        active_map = {identity: row for row, identity in active_rows}
        if len(original_rows) != len(original_map) or len(active_rows) != len(active_map):
            self.fail("registry_duplicates", "Registry repeats an identifier.", registry=key)
        if set(original_map) != expected_ids or set(active_map) != expected_ids:
            self.fail("registry_ids", "Registry does not contain the exact expected ID set.", registry=key,
                      missing=sorted(expected_ids - set(active_map)), extra=sorted(set(active_map) - expected_ids))
        if active_map != original_map:
            changed = sorted(identity for identity in set(active_map) | set(original_map)
                             if active_map.get(identity) != original_map.get(identity))
            self.fail("registry_content", "Active registry rows differ from the reconstructed original.", registry=key, changed=changed)
        if not original_is_verified:
            self.fail("registry_baseline", "Original row equality cannot be established because source reconstruction failed its content hashes.", registry=key)
        self.summary["registries"][key] = {"count": len(active_rows), "exact_rows_preserved": original_is_verified and active_map == original_map}
        return active_rows

    def verify_registries(self, source, original, active, original_is_verified):
        name = PurePosixPath(source["source_path"]).name
        if name not in SUBSTANTIVE_NAMES:
            return
        if source.get("extraction"):
            self.fail("active_substantive_document", "A substantive document must remain active, not only in a quoted archive.", source=source["source_id"])
        old, new = original.decode("utf-8"), active.decode("utf-8")

        def check_rows(key, pattern, expected_ids):
            return self.check_rows(key, pattern, old, new, expected_ids, original_is_verified)

        for field in ("document_id", "version", "status", "review_state", "implementation_status"):
            pattern = rf"^{field}:.*$"
            if re.findall(pattern, old, re.M) != re.findall(pattern, new, re.M):
                self.fail("document_status", f"Active document changed {field}.", source=source["source_id"])
        if name == "OntoKin_PRD_v0.md":
            ids = {f"{family}-{number:03d}" for family, count in PRD_FAMILIES.items() for number in range(1, count + 1)}
            rows = check_rows("PRD_requirements", r"^(\| ([A-Z]{3}-\d{3}) \| (?:MUST|SHOULD) \|.*)$", ids)
            priorities = Counter(re.match(r"\| [^|]+ \| (MUST|SHOULD) \|", row)[1] for row, _ in rows)
            actual_should = {identity for row, identity in rows if " | SHOULD | " in row}
            if priorities != {"MUST": 213, "SHOULD": 13} or actual_should != SHOULD_IDS:
                self.fail("PRD_priorities", "Expected 213 MUST and the original 13 SHOULD requirements.")
            self.summary["registries"]["PRD_requirements"]["priorities"] = dict(priorities)
            check_rows("PRD_acceptance", r"^(\| (AC-\d{2}):.*)$", {f"AC-{n:02d}" for n in range(1, 23)})
            check_rows("PRD_owner_intentions", r"^(\| (U\d{2}) \|.*)$", {f"U{n:02d}" for n in range(1, 17)})
        elif name == "OntoKin_Modeling_Motion_and_Object_Structure.md":
            check_rows("CAP_requirements", r"^(\| (CAP-\d{2}) \|.*)$", {f"CAP-{n:02d}" for n in range(1, 19)})
        elif name == "OntoKin_Core_Object_Motion_and_Physics_Semantics.md":
            check_rows("SEM_rules", r"^(### (SEM-\d{2})\. .*)$", {f"SEM-{n:02d}" for n in range(1, 29)})
            check_rows("SEM_behavior_checks", r"^(\| (SC-\d{2}) \|.*)$", {f"SC-{n:02d}" for n in range(1, 25)})

    def verify_source(self, source):
        source_id = source["source_id"]
        before_failures = len(self.failures)
        destination = self.path(source["destination"])
        active = destination.read_bytes()
        reconstructed = active
        extraction = source.get("extraction")
        if extraction:
            start = extraction["start_marker"].encode("utf-8")
            end = extraction["end_marker"].encode("utf-8")
            if not start or not end or active.count(start) != 1 or active.count(end) != 1:
                raise ValueError("Archive extraction markers must each occur exactly once.")
            after_start = active.split(start, 1)[1]
            if end not in after_start:
                raise ValueError("Archive end marker occurs before its start marker.")
            reconstructed = after_start.split(end, 1)[0]
        for transform in reversed(source.get("transforms", [])):
            old = transform["before"].encode("utf-8")
            new = transform["after"].encode("utf-8")
            count = transform["occurrences"]
            if not old or not new or not isinstance(count, int) or count < 1:
                raise ValueError("Transforms require nonempty strings and a positive exact occurrence count.")
            if reconstructed.count(new) != count:
                raise ValueError(f"Reverse transform expected {count} occurrences, found {reconstructed.count(new)}: {transform['after']!r}")
            reconstructed = reconstructed.replace(new, old)
        checks = {
            "original_bytes": len(reconstructed),
            "original_sha256": digest(reconstructed),
            "original_git_blob": git_object("blob", reconstructed),
        }
        for key, actual in checks.items():
            if actual != source[key]:
                self.fail(key, "Reconstructed content differs from the original record.", source=source_id, expected=source[key], actual=actual)
        self.verify_sections(source, reconstructed)
        self.verify_registries(source, reconstructed, active, all(actual == source[key] for key, actual in checks.items()))
        self.summary["sources"].append({
            "source_id": source_id, "destination": source["destination"],
            "bytes": len(reconstructed), "verified": len(self.failures) == before_failures,
        })

    def verify_baseline_tree(self, manifest):
        tree = {}
        baseline_sources = [source for source in manifest["sources"] if source["source_commit"] == manifest["baseline_commit"]]
        for source in baseline_sources:
            parts = PurePosixPath(source["source_path"]).parts
            if not parts or any(part in {"", ".", "..", "/"} for part in parts):
                raise ValueError("Invalid original source path in baseline tree.")
            branch = tree
            for part in parts[:-1]:
                branch = branch.setdefault(part, {})
                if not isinstance(branch, dict):
                    raise ValueError("Baseline tree contains a file/directory conflict.")
            if parts[-1] in branch:
                raise ValueError("Duplicate original path in baseline tree.")
            mode = str(source.get("original_mode", "100644"))
            if mode not in {"100644", "100755", "120000"}:
                raise ValueError(f"Unsupported Git file mode: {mode}")
            branch[parts[-1]] = (mode, source["original_git_blob"])

        def tree_hash(branch):
            records = []
            for name, value in branch.items():
                if isinstance(value, dict):
                    mode, identity = "40000", tree_hash(value)
                    sort_key = (name + "/").encode("utf-8")
                else:
                    mode, identity = value
                    sort_key = name.encode("utf-8")
                record = mode.encode() + b" " + name.encode("utf-8") + b"\0" + bytes.fromhex(identity)
                records.append((sort_key, record))
            return git_object("tree", b"".join(record for _, record in sorted(records)))

        actual = tree_hash(tree)
        self.summary["baseline_tree"] = {"expected": manifest["baseline_tree"], "reconstructed": actual, "source_files": len(baseline_sources)}
        if actual != manifest["baseline_tree"]:
            self.fail("baseline_tree", "Listed baseline files do not reconstruct the complete original Git tree.")

    def check_link(self, source_path, destination, line):
        destination = html.unescape(re.sub(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\]\\^_`{|}~])", r"\1", destination)).strip()
        if not destination:
            return
        if destination.startswith("//") or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", destination):
            self.summary["links"]["external_skipped"] += 1
            return
        parsed = urlsplit(destination)
        relative = unquote(parsed.path)
        target = ((ROOT / relative.lstrip("/")) if relative.startswith("/") else (source_path.parent / relative)).resolve() if relative else source_path
        context = {"file": source_path.relative_to(ROOT).as_posix(), "line": line, "target": destination}
        self.summary["links"]["local_links"] += 1
        if not target.is_relative_to(ROOT) or not target.exists():
            self.fail("local_link", "Local target does not exist inside the repository.", **context)
            return
        if not parsed.fragment:
            return
        self.summary["links"]["anchors"] += 1
        if target.is_dir():
            target = next((target / name for name in ("README.md", "readme.md", "index.md", "index.html") if (target / name).is_file()), target)
        if target.is_dir() or target.suffix.lower() not in {".md", ".markdown", ".html", ".htm", ".svg"}:
            self.fail("local_anchor", "Target has no supported document anchor representation.", **context)
        elif unquote(parsed.fragment) not in self.anchors(target):
            self.fail("local_anchor", "Target anchor does not exist.", **context)

    def verify_links(self):
        excluded = {".git", ".venv", "venv", "node_modules", "__pycache__"}
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".md", ".markdown", ".html", ".htm"}:
                continue
            if any(part in excluded or part.startswith(".") for part in path.relative_to(ROOT).parts):
                continue
            self.summary["links"]["documents"] += 1
            try:
                text = path.read_text(encoding="utf-8")
                if path.suffix.lower() in {".md", ".markdown"}:
                    references = markdown_links(text)
                else:
                    parser = HTMLReferences()
                    parser.feed(text)
                    references = ((target, line, None) for target, line in parser.links)
                for target, line, unresolved in references:
                    if unresolved is not None:
                        self.fail("reference_link", f"Undefined explicit reference: {unresolved}", file=path.relative_to(ROOT).as_posix(), line=line)
                    else:
                        self.check_link(path, target, line)
            except (OSError, UnicodeError, ValueError) as error:
                self.fail("link_document", str(error), file=path.relative_to(ROOT).as_posix())

    def run(self):
        try:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
            sources = manifest["sources"]
            self.summary["baseline_commit"] = manifest["baseline_commit"]
            self.summary["repository"] = manifest["repository"]
            self.summary["source_count"] = len(sources)
            if len(sources) != EXPECTED_SOURCE_COUNT:
                self.fail("source_count", f"Expected {EXPECTED_SOURCE_COUNT} original files; found {len(sources)}.")
            identities = [source["source_id"] for source in sources]
            if len(set(identities)) != len(identities):
                self.fail("source_ids", "Source identities must be unique.")
            substantive = [PurePosixPath(source["source_path"]).name for source in sources if PurePosixPath(source["source_path"]).name in SUBSTANTIVE_NAMES]
            self.summary["active_substantive_documents"] = len(substantive)
            if Counter(substantive) != Counter({name: 1 for name in SUBSTANTIVE_NAMES}):
                self.fail("substantive_sources", "Each of the six original substantive documents must be present exactly once.")
            for source in sources:
                try:
                    self.verify_source(source)
                except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
                    self.fail("source_record", str(error), source=source.get("source_id", "unknown"))
            try:
                self.verify_baseline_tree(manifest)
            except (ValueError, KeyError, TypeError) as error:
                self.fail("baseline_tree", str(error))
            self.verify_links()
        except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
            self.fail("manifest", str(error))
        self.summary["sources_verified"] = sum(source["verified"] for source in self.summary["sources"])
        self.summary["failures"] = self.failures
        self.summary["status"] = "passed" if not self.failures else "failed"
        return self.summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, help="Also write the JSON result to this path.")
    args = parser.parse_args()
    summary = Verification().run()
    if args.json_output:
        try:
            args.json_output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except OSError as error:
            summary["status"] = "failed"
            summary["failures"].append({"check": "json_output", "detail": str(error)})
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
