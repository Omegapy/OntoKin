"""W1 (C271-P36, gate MR) static start scanner. Reads source files only; imports nothing it scans.

Run only as: python3 -I -S -B scan_starts.py WORKTREE OUTFILE [RELDIR ...]

For every .py file under the given directories (relative to WORKTREE), it parses the AST and records:
  - calls and references that resolve (through the file's import aliases) to process-start APIs,
    PATH lookups, platform helpers that can shell out, ctypes, bytecode writers, dynamic loaders,
    environment/cwd mutations and signal/kill calls;
  - unresolved attribute calls whose final name is a start-like name (Popen, check_output, ...);
  - mock.patch / patch.object / patch.dict targets;
  - for each start call, the literal shape of its first argument and its keywords.
The output is JSON with one record per site. Paths in the output are relative to WORKTREE.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import sys

START = {
    "subprocess": {"Popen", "run", "call", "check_call", "check_output", "getoutput", "getstatusoutput"},
    "os": {"system", "popen", "execl", "execle", "execlp", "execlpe", "execv", "execve", "execvp", "execvpe",
           "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe",
           "posix_spawn", "posix_spawnp", "fork", "forkpty", "startfile"},
    "pty": {"spawn", "fork"},
    "asyncio": {"create_subprocess_exec", "create_subprocess_shell"},
    "concurrent.futures": {"ProcessPoolExecutor"},
}
WHOLE_MODULES = {"multiprocessing", "webbrowser", "ctypes", "ctypes.util", "venv", "py_compile", "compileall",
                 "runpy", "pty", "platform", "_posixsubprocess", "posix", "zipimport"}
OTHER = {
    "shutil": {"which"},
    "uuid": {"uuid1", "getnode"},
    "importlib": {"import_module", "__import__", "reload", "invalidate_caches"},
    "importlib.util": {"spec_from_file_location", "module_from_spec", "cache_from_source", "find_spec"},
    "importlib.machinery": {"SourceFileLoader", "SourcelessFileLoader", "ExtensionFileLoader"},
    "os": {"chdir", "putenv", "unsetenv", "kill", "killpg", "setsid", "umask", "fchdir", "nice"},
    "time": {"tzset"},
    "locale": {"setlocale"},
    "signal": {"signal", "alarm", "setitimer", "pthread_kill"},
    "sys": {"setrecursionlimit", "settrace", "setprofile"},
    "builtins": {"exec", "eval", "compile", "__import__"},
}
START_LIKE_ATTRS = {"Popen", "check_output", "check_call", "getoutput", "getstatusoutput", "posix_spawn",
                    "posix_spawnp", "spawnv", "spawnve", "execv", "execve", "execvp", "execvpe", "forkpty",
                    "create_subprocess_exec", "create_subprocess_shell", "subprocess_exec", "subprocess_shell",
                    "system", "popen", "fork", "ProcessPoolExecutor", "Process", "Pool"}
ENV_MUTATORS = {"update", "pop", "setdefault", "clear", "popitem", "__setitem__", "__delitem__"}
PROGRAM_WORDS = {"git", "node", "nodejs", "npm", "npx", "uname", "file", "ldd", "codesign", "otool", "sh", "bash",
                 "zsh", "env", "xcrun", "xcode-select", "lipo", "nm", "strip", "install_name_tool", "sysctl",
                 "sw_vers", "ditto", "tar", "unzip", "zip", "chromium", "open", "osascript", "plutil", "security",
                 "spctl", "xattr", "hdiutil", "python", "python3", "pip", "pip3", "uv", "git-lfs", "lfs", "make",
                 "cc", "gcc", "clang", "ld", "objdump", "readelf", "ldconfig", "patchelf", "docker", "podman",
                 "sudo", "chmod", "chown", "cp", "mv", "rm", "ln", "mkdir", "touch", "cat", "true", "false",
                 "sleep", "kill", "ps", "pgrep", "pkill", "launchctl", "date", "id", "whoami", "hostname",
                 "mdls", "mdfind", "defaults", "diskutil", "stat", "shasum", "sha256sum", "openssl", "curl",
                 "wget", "jq", "perl", "ruby", "deno", "bun", "glslangValidator", "gltf_validator", "blender",
                 "playwright", "tsc", "esbuild", "vite", "yarn", "pnpm", "corepack", "which", "command", "type"}


def dotted(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    if isinstance(node, ast.Call):
        inner = dotted(node.func)
        if inner:
            parts.append(inner + "()")
            return ".".join(reversed(parts))
    return None


def shape(node, depth=0):
    """A short literal description of an argv expression."""
    if depth > 3:
        return "..."
    if isinstance(node, ast.Constant):
        return repr(node.value)[:120]
    if isinstance(node, (ast.List, ast.Tuple)):
        inner = [shape(e, depth + 1) for e in node.elts[:14]]
        if len(node.elts) > 14:
            inner.append("...")
        return ("[" if isinstance(node, ast.List) else "(") + ", ".join(inner) + ("]" if isinstance(node, ast.List) else ")")
    if isinstance(node, ast.Starred):
        return "*" + shape(node.value, depth + 1)
    if isinstance(node, ast.JoinedStr):
        return "f-string"
    if isinstance(node, ast.BinOp):
        return shape(node.left, depth + 1) + " " + type(node.op).__name__ + " " + shape(node.right, depth + 1)
    d = dotted(node)
    if d:
        return d
    if isinstance(node, ast.Call):
        return (dotted(node.func) or "call") + "(...)"
    if isinstance(node, ast.Subscript):
        return shape(node.value, depth + 1) + "[...]"
    return type(node).__name__


class Scanner(ast.NodeVisitor):
    def __init__(self, path, module_package):
        self.path = path
        self.aliases = {}          # local name -> dotted module or module.attr
        self.records = []
        self.scope = []
        self.package = module_package
        self.patch_targets = []
        self.program_strings = []
        self.call_funcs = set()

    # ---- imports
    def visit_Import(self, node):
        for alias in node.names:
            if alias.asname:
                self.aliases[alias.asname] = alias.name
            else:
                top = alias.name.split(".")[0]
                self.aliases[top] = top
        self.records.append(self.rec(node, "import", ",".join(a.name for a in node.names)))
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ""
        if node.level:
            module = "." * node.level + module
        for alias in node.names:
            self.aliases[alias.asname or alias.name] = (module + "." + alias.name) if module else alias.name
        self.records.append(self.rec(node, "import-from", module + ":" + ",".join(a.name for a in node.names)))
        self.generic_visit(node)

    # ---- scopes
    def visit_FunctionDef(self, node):
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def rec(self, node, kind, name, **extra):
        return {"file": self.path, "line": getattr(node, "lineno", 0), "kind": kind, "name": name,
                "scope": ".".join(self.scope) or "<module>", **extra}

    def resolve(self, node):
        d = dotted(node)
        if d is None:
            return None, None
        head, _, rest = d.partition(".")
        if head in self.aliases:
            base = self.aliases[head]
            full = base + ("." + rest if rest else "")
        else:
            full = d
        return d, full

    def classify(self, full):
        if full is None:
            return None
        for module, names in START.items():
            if full.startswith(module + "."):
                attr = full[len(module) + 1:]
                if attr in names:
                    return "start"
        for module in WHOLE_MODULES:
            if full == module or full.startswith(module + "."):
                return "module:" + module
        for module, names in OTHER.items():
            if full.startswith(module + "."):
                attr = full[len(module) + 1:]
                if attr in names:
                    return "other:" + module
        if full in {"exec", "eval", "compile", "__import__"}:
            return "other:builtins"
        if full.startswith("os.environ") or full == "os.environ":
            return "environ"
        if full in {"sys.dont_write_bytecode"} or full.endswith(".dont_write_bytecode"):
            return "bytecode-flag"
        return None

    def visit_Call(self, node):
        self.call_funcs.add(id(node.func))
        d, full = self.resolve(node.func)
        cls = self.classify(full)
        extra = {}
        if cls == "start" or (cls and cls.startswith("module:")) or (cls and cls.startswith("other:")):
            if node.args:
                extra["arg0"] = shape(node.args[0])
            if len(node.args) > 1:
                extra["args_rest"] = [shape(a) for a in node.args[1:6]]
            kws = {}
            for kw in node.keywords:
                kws[kw.arg or "**"] = shape(kw.value)
            if kws:
                extra["keywords"] = kws
            self.records.append(self.rec(node, "call:" + cls, full, written=d, **extra))
        elif cls == "environ":
            self.records.append(self.rec(node, "call:environ", full, written=d,
                                         arg0=shape(node.args[0]) if node.args else None))
        elif full and isinstance(node.func, ast.Attribute) and node.func.attr in START_LIKE_ATTRS:
            extra = {}
            if node.args:
                extra["arg0"] = shape(node.args[0])
            kws = {kw.arg or "**": shape(kw.value) for kw in node.keywords}
            if kws:
                extra["keywords"] = kws
            self.records.append(self.rec(node, "call:unresolved-start-like", full, written=d, **extra))
        # mock patch targets
        if full and (full.endswith("patch") or full.endswith("patch.object") or full.endswith("patch.dict")
                     or full.endswith("patch.multiple")):
            target = [shape(a) for a in node.args[:3]]
            self.records.append(self.rec(node, "patch", full, target=target,
                                         keywords={kw.arg or "**": shape(kw.value) for kw in node.keywords}))
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load) and id(node) not in self.call_funcs and node.id in self.aliases:
            full = self.aliases[node.id]
            cls = self.classify(full)
            if cls == "start":
                self.records.append(self.rec(node, "ref:start", full, written=node.id))
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.ctx, ast.Load) and id(node) not in self.call_funcs:
            d, full = self.resolve(node)
            cls = self.classify(full)
            if cls == "start" or cls == "module:multiprocessing" or (full or "").startswith("subprocess.Popen"):
                self.records.append(self.rec(node, "ref:" + cls if cls else "ref", full, written=d))
        elif isinstance(node.ctx, ast.Store):
            d, full = self.resolve(node)
            if full and (full.endswith("dont_write_bytecode") or full.startswith("os.environ")):
                self.records.append(self.rec(node, "store", full, written=d))
        self.generic_visit(node)

    def visit_Subscript(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            d, full = self.resolve(node.value)
            if full == "os.environ":
                self.records.append(self.rec(node, "environ-" + type(node.ctx).__name__.lower(), full,
                                             key=shape(node.slice)))
        self.generic_visit(node)

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            v = node.value
            if v in PROGRAM_WORDS or v.startswith("/usr/bin/") or v.startswith("/bin/") or v.startswith("/usr/sbin/") \
                    or v.startswith("/sbin/") or v.startswith("/opt/") or v.startswith("/usr/local/") \
                    or v.startswith("/Library/") or v.startswith("/Applications/"):
                self.program_strings.append({"file": self.path, "line": node.lineno, "value": v[:160],
                                             "scope": ".".join(self.scope) or "<module>"})
        self.generic_visit(node)


def main():
    worktree, outfile, *dirs = sys.argv[1:]
    files = []
    for rel in dirs:
        base = os.path.join(worktree, rel)
        if os.path.isfile(base):
            files.append(rel)
            continue
        for parent, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if d not in {"__pycache__", "node_modules", ".git"})
            for f in sorted(filenames):
                if f.endswith(".py"):
                    files.append(os.path.relpath(os.path.join(parent, f), worktree))
    out = {"files": [], "sites": [], "program_strings": [], "errors": []}
    for rel in files:
        full = os.path.join(worktree, rel)
        with open(full, "rb") as stream:
            raw = stream.read()
        out["files"].append({"file": rel, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
        try:
            tree = ast.parse(raw, filename=rel)
        except SyntaxError as error:
            out["errors"].append({"file": rel, "error": str(error)})
            continue
        scanner = Scanner(rel, None)
        scanner.visit(tree)
        out["sites"].extend(r for r in scanner.records if not r["kind"].startswith("import"))
        out["program_strings"].extend(scanner.program_strings)
    with open(outfile, "x", encoding="utf-8") as stream:
        json.dump(out, stream, indent=1, sort_keys=True)
        stream.write("\n")
    kinds = {}
    for s in out["sites"]:
        kinds[s["kind"]] = kinds.get(s["kind"], 0) + 1
    print(json.dumps({"files": len(out["files"]), "sites": len(out["sites"]), "kinds": kinds,
                      "program_strings": len(out["program_strings"]), "errors": len(out["errors"])}, indent=1))


if __name__ == "__main__":
    main()
