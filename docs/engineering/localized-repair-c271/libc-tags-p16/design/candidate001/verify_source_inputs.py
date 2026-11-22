"""Verify retained source/capture correspondence as inert data; no product imports."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import os
import struct
import sys
import tarfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--incoming", required=True)
    parser.add_argument("--selected", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    incoming = Path(args.incoming)
    selected = Path(args.selected)
    downloads = incoming / "recovery/session/source-provenance/downloads-attempt001"
    pins = {
        "glibc_2.41.orig.tar.xz": (20323540, "f24aa441021121a79266f0d75242706cab8843a47901fefe74527491807f1998"),
        "glibc_2.41-12+deb13u4.debian.tar.xz": (499524, "dda4153511bfd543502d18e5bc9323110996fe9c531f14ae3fad6eb17f027c7d"),
        "glibc_2.41-12+deb13u4.dsc": (7576, "0915324aa646bb99abfaa9aa6ecb734b30babd28454a3e51f3152912370fbd3e"),
    }
    assertions = []

    def require(condition, name):
        assertions.append({"name": name, "passed": bool(condition)})
        if not condition:
            raise AssertionError(name)

    archive_rows = []
    for name, expected in pins.items():
        data = (downloads / name).read_bytes()
        require((len(data), digest(data)) == expected, "archive pin: " + name)
        archive_rows.append({"path": str(downloads / name), "bytes": len(data), "sha256": digest(data)})
    dsc = (downloads / "glibc_2.41-12+deb13u4.dsc").read_text()
    for name in ("glibc_2.41.orig.tar.xz", "glibc_2.41-12+deb13u4.debian.tar.xz"):
        require(f" {pins[name][1]} {pins[name][0]} {name}" in dsc, "descriptor checksum: " + name)

    patterns = (b"DT_X86_64_", b"plt_rewrite", b"ELF_DYNAMIC_AFTER_RELOC")
    matched, selected_rows = [], []
    member_count = byte_count = 0
    with tarfile.open(downloads / "glibc_2.41.orig.tar.xz", "r:xz") as archive:
        for member in archive:
            if not member.isfile():
                continue
            data = archive.extractfile(member).read()
            member_count += 1
            byte_count += len(data)
            if any(pattern in data for pattern in patterns):
                matched.append({"member": member.name, "bytes": len(data), "sha256": digest(data),
                                "hits": [{"line": n, "text": line.decode("utf-8", "replace")}
                                         for n, line in enumerate(data.splitlines(), 1)
                                         if any(pattern in line for pattern in patterns)]})
            relative = member.name.removeprefix("glibc-2.41/")
            copy = selected / "upstream" / relative
            if copy.is_file():
                require(copy.read_bytes() == data, "selected source byte equality: " + relative)
                selected_rows.append({"path": str(copy), "member": member.name, "bytes": len(data), "sha256": digest(data)})
    local_selected = sorted(str(p.relative_to(selected / "upstream")) for p in (selected / "upstream").rglob("*") if p.is_file())
    require(sorted(row["member"].removeprefix("glibc-2.41/") for row in selected_rows) == local_selected,
            "complete selected source inventory")

    with tarfile.open(downloads / "glibc_2.41-12+deb13u4.debian.tar.xz", "r:xz") as archive:
        series = archive.extractfile("debian/patches/series").read()
        active = [line.strip().split()[0] for line in series.decode().splitlines()
                  if line.strip() and not line.lstrip().startswith("#")]
        patches = []
        for name in active:
            data = archive.extractfile("debian/patches/" + name).read()
            headers = []
            for n, line in enumerate(data.decode().splitlines(), 1):
                if line.startswith(("--- ", "+++ ")):
                    path = line[4:].split()[0]
                    normal = path.split("/", 1)[1] if "/" in path and path != "/dev/null" else None
                    if normal in local_selected:
                        headers.append({"line": n, "path": normal})
            patches.append({"patch": name, "bytes": len(data), "sha256": digest(data), "selected_path_headers": headers,
                            "symbol_hits": [{"line": n, "text": line.decode("utf-8", "replace")}
                                            for n, line in enumerate(data.splitlines(), 1)
                                            if any(pattern in line for pattern in patterns)]})
        patch = archive.extractfile("debian/patches/git-updates.diff").read()
        lines = patch.splitlines(keepends=True)
        for name, chosen_paths in (
            ("git-updates-tag-context.diff", ("sysdeps/x86/cpu-features.c", "sysdeps/x86_64/Makefile")),
            ("git-updates-versions-context.diff", ("sysdeps/x86_64/Versions",)),
        ):
            starts = [i for i, line in enumerate(lines) if line.startswith(b"diff --git ")]
            chunks = [b"".join(lines[i:j]) for i, j in zip(starts, starts[1:] + [len(lines)])
                      if any((" b/" + path).encode() in lines[i] for path in chosen_paths)]
            require((selected / name).read_bytes() == b"".join(chunks), "complete relevant patch sections: " + name)

    package_path = incoming / "recovery/session/package-retrieval/libc6_2.41-12+deb13u4_amd64.deb.inert"
    package = package_path.read_bytes()
    require((len(package), digest(package)) == (2846580, "967aa62605721081c3eb2a17650611a792aa802d76a6511d1840242623d204c9"), "binary package pin")
    require(package[:8] == b"!<arch>\n", "ar header")
    position, members = 8, {}
    while position < len(package):
        header = package[position:position + 60]
        require(len(header) == 60 and header[58:60] == b"`\n", "ar member header")
        name = header[:16].decode().strip().rstrip("/")
        size = int(header[48:58])
        position += 60
        require(name not in members, "unique ar member: " + name)
        members[name] = package[position:position + size]
        require(len(members[name]) == size, "ar member size: " + name)
        position += size + size % 2
    require(position == len(package), "ar final position")
    with tarfile.open(fileobj=io.BytesIO(members["control.tar.xz"]), mode="r:xz") as archive:
        control = archive.extractfile("./control").read()
    fields = dict(line.split(": ", 1) for line in control.decode().splitlines()
                  if line and not line.startswith(" ") and ": " in line)
    require({key: fields[key] for key in ("Package", "Source", "Version", "Architecture")} ==
            {"Package": "libc6", "Source": "glibc", "Version": "2.41-12+deb13u4", "Architecture": "amd64"}, "package/source association")
    with tarfile.open(fileobj=io.BytesIO(members["data.tar.xz"]), mode="r:xz") as archive:
        libc = archive.extractfile("./usr/lib/x86_64-linux-gnu/libc.so.6").read()
        loader = archive.extractfile("./usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2").read()
    capture = incoming / "recovery/session/h0-static-admission-attempt001/current-python-loaded-libc.elf.inert"
    loader_capture = incoming / "recovery/session/h0-static-admission-attempt001/bound-loader.elf.inert"
    require(libc == capture.read_bytes(), "captured libc equals exact package member")
    require(loader == loader_capture.read_bytes(), "captured loader equals exact package member")
    require(digest(libc) == "9792e3cbb541c8f44c7acf5f14f4022ea62998ecc787d326bed4d8b6547dfd92", "captured libc pin")
    require(digest(loader) == "c8438e4fde1934e61c88311633f00949ff645d5c04cdb8671fa3d78164d2f307", "captured loader pin")
    require(libc[:7] == b"\x7fELF\x02\x01\x01" and struct.unpack_from("<HH", libc, 16) == (3, 62), "captured libc architecture")
    phoff = struct.unpack_from("<Q", libc, 32)[0]
    phentsize, phnum = struct.unpack_from("<HH", libc, 54)
    ph = [struct.unpack_from("<IIQQQQQQ", libc, phoff + i * phentsize) for i in range(phnum)]
    dynamic = [row for row in ph if row[0] == 2]
    require(len(dynamic) == 1, "captured libc one dynamic table")
    tags = []
    for offset in range(dynamic[0][2], dynamic[0][2] + dynamic[0][5], 16):
        tag, value = struct.unpack_from("<qQ", libc, offset)
        if tag == 0:
            break
        if tag in (0x70000000, 0x70000001, 0x70000003):
            tags.append({"offset": offset, "tag": tag, "value": value})
    require([(row["tag"], row["value"]) for row in tags] ==
            [(0x70000000, 0x28000), (0x70000001, 0x3D0), (0x70000003, 0x10)], "retained exact tag tuple")
    result = {
        "schema": "ontokin.c271.p16-primary-source-audit/1", "worker": "/root/tag_design",
        "command": [sys.executable, "-I", "-B", str(Path(__file__).resolve()), *sys.argv[1:]],
        "script_sha256": digest(Path(__file__).read_bytes()),
        "environment": {"python_executable": sys.executable, "python_version": sys.version, "platform": sys.platform, "os_name": os.name},
        "archives": archive_rows, "regular_upstream_members_scanned": member_count, "upstream_bytes_scanned": byte_count,
        "scan_patterns": [pattern.decode() for pattern in patterns], "symbol_matches": matched,
        "selected_sources": selected_rows, "active_patch_count": len(active), "series_sha256": digest(series), "patches": patches,
        "package": {"path": str(package_path), "bytes": len(package), "sha256": digest(package)},
        "libc": {"capture": str(capture), "bytes": len(libc), "sha256": digest(libc), "selected_tags": tags},
        "loader": {"capture": str(loader_capture), "bytes": len(loader), "sha256": digest(loader)},
        "assertions": assertions, "all_passed": all(row["passed"] for row in assertions),
        "later_flags_predicate_evaluated": False, "product_module_imported": False, "product_parser_called": False,
        "target_execution": False, "current_host_input_opened": False,
        "limitations": ["Source-to-binary association rests on retained official HTTPS/package/source records, not a reproduced build or verified OpenPGP signature.",
                        "Automated full-byte symbol scans do not mean every upstream file was manually read.",
                        "Exact retained capture equality is not current-host equality or host qualification."],
    }
    with Path(args.output).open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"output": args.output, "assertions_passed": len(assertions), "upstream_members_scanned": member_count,
                      "active_patches": len(active), "selected_sources": len(selected_rows), "all_passed": result["all_passed"]}))


if __name__ == "__main__":
    main()
