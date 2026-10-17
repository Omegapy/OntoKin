"""Lexer and recursive-descent parser for the published core EBNF.

Nodes retain original-source UTF-8 byte spans. Parsing does not load Python
code, resolve names, execute actions, or infer physical units.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from .diagnostics import OntoKinError


@dataclass
class Node:
    kind: str
    start: int
    end: int
    data: dict[str, Any] = field(default_factory=dict)

    def __getattr__(self, name: str) -> Any:
        data = self.__dict__.get("data", {})
        if name in data:
            return data[name]
        raise AttributeError(name)

    def __getitem__(self, name: str) -> Any:
        return self.data[name]


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    start: int
    end: int


RESERVED = frozenset("""ontokin module profile requires class extends public private
param derive override method fn let return part site joint follow scene object
action at sequence start pause resume stop release using incoming assert if then
else and or not true false Quantity""".split())
_NUMBER = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_INTEGER = re.compile(r"(?:0|[1-9][0-9]*)\Z")
MAX_SOURCE_BYTES = 2_000_000
MAX_TOKENS = 200_000


def lex(text: str) -> list[Token]:
    offsets = [0]
    for c in text:
        offsets.append(offsets[-1] + len(c.encode("utf-8", errors="surrogatepass")))
    if offsets[-1] > MAX_SOURCE_BYTES:
        raise OntoKinError("OKL-E-RESOURCE", "Source exceeds the 2 MB reference budget.",
                           category="resource_limit", phase="lexical")
    tokens: list[Token] = []
    i = 0

    def fail(message: str, a: int, b: int) -> None:
        raise OntoKinError("OKL-E-LEXICAL", message,
                           Node("span", offsets[a], offsets[b]), phase="lexical")

    def add(kind: str, value: str, a: int, b: int) -> None:
        tokens.append(Token(kind, value, offsets[a], offsets[b]))

    while i < len(text):
        if len(tokens) >= MAX_TOKENS:
            raise OntoKinError("OKL-E-RESOURCE", "Token budget exceeded.",
                               category="resource_limit", phase="lexical")
        c = text[i]
        if c in " \t\r\n":
            i += 1
            continue
        if text.startswith("//", i):
            i += 2
            while i < len(text) and text[i] not in "\r\n":
                if 0xD800 <= ord(text[i]) <= 0xDFFF:
                    fail("Source contains an invalid Unicode scalar value.", i, i + 1)
                i += 1
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end == -1:
                fail("Unterminated block comment.", i, len(text))
            for pos in range(i, end + 2):
                if 0xD800 <= ord(text[pos]) <= 0xDFFF:
                    fail("Source contains an invalid Unicode scalar value.", pos, pos + 1)
            i = end + 2
            continue
        if c == '"':
            start = i
            i += 1
            chars: list[str] = []
            while i < len(text) and text[i] != '"':
                c = text[i]
                if c == "\\":
                    if i + 1 >= len(text):
                        fail("Unterminated string escape.", start, len(text))
                    escapes = {'"': '"', "\\": "\\", "n": "\n", "r": "\r", "t": "\t"}
                    if text[i + 1] not in escapes:
                        fail("Unsupported string escape; use \\\" , \\\\ , \\n, \\r, or \\t.", i, i + 2)
                    chars.append(escapes[text[i + 1]])
                    i += 2
                else:
                    if ord(c) <= 0x1F or 0x7F <= ord(c) <= 0x9F or 0xD800 <= ord(c) <= 0xDFFF:
                        fail("Raw control characters and invalid Unicode scalars are forbidden in strings.", i, i + 1)
                    chars.append(c)
                    i += 1
            if i == len(text):
                fail("Unterminated string literal.", start, i)
            i += 1
            add("STRING", "".join(chars), start, i)
            continue
        if "0" <= c <= "9":
            start = i
            if c == "0" and i + 1 < len(text) and text[i + 1].isdigit():
                fail("Leading zeroes are not allowed in numeric literals.", i, i + 2)
            match = _NUMBER.match(text, i)
            assert match is not None
            i = match.end()
            if i < len(text) and (text[i].isalnum() or text[i] == "_"):
                fail("Malformed numeric literal.", start, i + 1)
            add("NUMBER", match.group(), start, i)
            continue
        match = _IDENT.match(text, i)
        if match:
            value = match.group()
            add(value if value in RESERVED else "IDENT", value, i, match.end())
            i = match.end()
            continue
        if text[i:i + 2] in {"->", "<=", ">=", "==", "!="}:
            add(text[i:i + 2], text[i:i + 2], i, i + 2)
            i += 2
            continue
        if c in "{}();:@,.[]<>+-*/^=":
            if c == "." and i + 1 < len(text) and text[i + 1].isdigit():
                fail("A numeric literal needs a digit before its decimal point.", i, i + 2)
            add(c, c, i, i + 1)
            i += 1
            continue
        fail("Unexpected character in source.", i, i + 1)
    tokens.append(Token("EOF", "", offsets[-1], offsets[-1]))
    return tokens


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.index = 0

    @property
    def token(self) -> Token:
        return self.tokens[self.index]

    def take(self, kind: str) -> Token:
        token = self.token
        if token.kind != kind:
            found = "end of source" if token.kind == "EOF" else repr(token.value)
            raise OntoKinError("OKL-E-SYNTAX", f"Expected {kind!r}; found {found}.",
                               token, phase="syntax", details={"expected": kind, "found": token.kind})
        self.index += 1
        return token

    def accept(self, kind: str) -> Token | None:
        return self.take(kind) if self.token.kind == kind else None

    def node(self, kind: str, start: Token | Node, **data: Any) -> Node:
        return Node(kind, start.start, self.tokens[self.index - 1].end, data)

    def identity(self) -> str:
        self.take("@")
        return self.take("STRING").value

    def program(self) -> Node:
        start = self.take("ontokin")
        version = self.take("STRING").value
        self.take(";")
        self.take("module")
        name = self.take("IDENT").value
        key = self.identity()
        self.take(";")
        self.take("profile")
        profile = self.take("STRING").value
        self.take(";")
        requires = []
        while self.token.kind == "requires":
            token = self.take("requires")
            value = self.take("STRING").value
            self.take(";")
            requires.append(self.node("capability", token, value=value))
        classes, functions, definitions = [], [], []
        while self.token.kind in {"class", "fn"}:
            item = self.class_decl() if self.token.kind == "class" else self.function_decl()
            (classes if item.kind == "class" else functions).append(item)
            definitions.append(item)
        scene = self.scene()
        self.take("EOF")
        return self.node("program", start, version=version, module_name=name,
                         module_key=key, profile=profile, requires=requires,
                         classes=classes, functions=functions, definitions=definitions, scene=scene)

    def class_decl(self) -> Node:
        start = self.take("class")
        name = self.take("IDENT").value
        key = self.identity()
        base = self.take("IDENT").value if self.accept("extends") else None
        self.take("{")
        members = []
        while self.token.kind != "}":
            members.append(self.member(in_scene=False))
        self.take("}")
        return self.node("class", start, name=name, key=key, base=base, members=members)

    def parameters(self) -> list[Node]:
        self.take("(")
        params = []
        if self.token.kind != ")":
            while True:
                start = self.take("IDENT")
                self.take(":")
                type_ = self.type_decl()
                params.append(self.node("parameter", start, name=start.value, type=type_))
                if not self.accept(","):
                    break
        self.take(")")
        return params

    def type_decl(self) -> Node:
        start = self.token
        args, unit = [], None
        if self.accept("Quantity"):
            name = "Quantity"
            self.take("[")
            unit = self.unit_expr()
            self.take("]")
        else:
            name = self.take("IDENT").value
            if self.accept("<"):
                args.append(self.type_decl())
                while self.accept(","):
                    args.append(self.type_decl())
                self.take(">")
        return self.node("type", start, name=name, args=args, unit=unit)

    def function_decl(self, visibility: str = "public", override: bool = False,
                      start: Token | None = None) -> Node:
        keyword = self.token
        self.take("fn" if keyword.kind == "fn" else "method")
        name = self.take("IDENT").value
        key = self.identity()
        params = self.parameters()
        self.take("->")
        return_type = self.type_decl()
        self.take("{")
        locals_ = []
        while self.token.kind == "let":
            token = self.take("let")
            local_name = self.take("IDENT").value
            self.take(":")
            local_type = self.type_decl()
            self.take("=")
            value = self.expression()
            self.take(";")
            locals_.append(self.node("let", token, name=local_name, type=local_type, value=value))
        self.take("return")
        result = self.expression()
        self.take(";")
        self.take("}")
        return self.node("function" if keyword.kind == "fn" else "method", start or keyword,
                         name=name, key=key, visibility=visibility, override=override,
                         params=params, return_type=return_type, locals=locals_, result=result)

    def member(self, in_scene: bool) -> Node:
        start = self.token
        visibility = None
        if self.token.kind in {"public", "private"}:
            visibility = self.take(self.token.kind).value
        if self.token.kind in {"joint", "follow"}:
            return self.declaration(self.token.kind, visibility, start)
        if in_scene and visibility is None:
            if self.token.kind == "object":
                return self.declaration("object", None, start)
            if self.token.kind == "action":
                self.take("action")
                name = self.take("IDENT").value
                key = self.identity()
                self.take("=")
                value = self.expression()
                self.take(";")
                return self.node("action", start, name=name, key=key, value=value)
            if self.token.kind == "at":
                return self.event_block()
        if not in_scene and visibility is not None:
            if self.token.kind in {"param", "derive"}:
                kind = self.take(self.token.kind).value
                name = self.take("IDENT").value
                key = self.identity()
                self.take(":")
                type_ = self.type_decl()
                self.take("=")
                value = self.expression()
                self.take(";")
                return self.node(kind, start, name=name, key=key, visibility=visibility,
                                 type=type_, value=value)
            if self.token.kind in {"part", "site"}:
                return self.declaration(self.token.kind, visibility, start)
            override = bool(self.accept("override"))
            return self.function_decl(visibility, override, start)
        if visibility is not None:
            self.take("joint")  # Emit a syntax diagnostic for a misplaced modifier.
        if not in_scene and self.accept("override"):
            name = self.take("IDENT").value
            self.take("=")
            value = self.expression()
            self.take(";")
            return self.node("override_default", start, name=name, value=value)
        if self.accept("assert"):
            condition = self.expression()
            self.take(",")
            message = self.take("STRING").value
            self.take(";")
            return self.node("assert", start, condition=condition, message=message)
        return self.assignment()

    def path(self) -> list[str]:
        parts = [self.take("IDENT").value]
        while self.accept("."):
            parts.append(self.take("IDENT").value)
        return parts

    def assignment(self) -> Node:
        start = self.token
        path = self.path()
        self.take("=")
        value = self.expression()
        self.take(";")
        return self.node("assign", start, path=path, value=value)

    def declaration(self, kind: str, visibility: str | None, start: Token) -> Node:
        self.take(kind)
        name = self.take("IDENT").value
        key = self.identity()
        class_name = joint_type = None
        if kind in {"object", "part", "joint"}:
            self.take(":")
            value = self.take("IDENT").value
            if kind == "joint":
                joint_type = value
            else:
                class_name = value
        self.take("{")
        assignments = []
        while self.token.kind != "}":
            assignments.append(self.assignment())
        self.take("}")
        return self.node(kind, start, name=name, key=key, visibility=visibility,
                         class_name=class_name, joint_type=joint_type, assignments=assignments)

    def scene(self) -> Node:
        start = self.take("scene")
        name = self.take("IDENT").value
        key = self.identity()
        self.take("{")
        members = []
        while self.token.kind != "}":
            members.append(self.member(in_scene=True))
        self.take("}")
        return self.node("scene", start, name=name, key=key, members=members)

    def event_block(self) -> Node:
        start = self.take("at")
        time = self.expression()
        self.take("sequence")
        self.take("{")
        events = []
        while self.token.kind != "}":
            token = self.token
            if self.token.kind in {"start", "pause", "resume", "stop"}:
                kind = self.take(self.token.kind).value
                name = self.take("IDENT").value
                self.take(";")
                events.append(self.node(kind, token, name=name))
            else:
                self.take("release")
                path = self.path()
                self.take("using")
                self.take("incoming")
                self.take(";")
                events.append(self.node("release", token, path=path))
        self.take("}")
        return self.node("event_block", start, time=time, events=events)

    def expression(self) -> Node:
        if self.token.kind == "if":
            start = self.take("if")
            condition = self.expression()
            self.take("then")
            then = self.expression()
            self.take("else")
            otherwise = self.expression()
            return self.node("conditional", start, condition=condition, then=then, otherwise=otherwise)
        return self.binary(0)

    _LEVELS = ({"or"}, {"and"}, {"==", "!="}, {"<", "<=", ">", ">="},
               {"+", "-"}, {"*", "/"})

    def binary(self, level: int) -> Node:
        if level == len(self._LEVELS):
            return self.unary()
        left = self.binary(level + 1)
        while self.token.kind in self._LEVELS[level]:
            op = self.take(self.token.kind).value
            right = self.binary(level + 1)
            left = self.node("binary", left, op=op, left=left, right=right)
            if level in {2, 3}:
                break
        return left

    def unary(self) -> Node:
        if self.token.kind in {"-", "not"}:
            start = self.take(self.token.kind)
            return self.node("unary", start, op=start.value, value=self.unary())
        return self.postfix()

    def postfix(self) -> Node:
        value = self.primary()
        while self.token.kind in {".", "("}:
            if self.accept("."):
                name = self.take("IDENT").value
                value = self.node("member", value, target=value, name=name)
            else:
                self.take("(")
                args = []
                if self.token.kind != ")":
                    args.append(self.expression())
                    while self.accept(","):
                        args.append(self.expression())
                self.take(")")
                value = self.node("call", value, callee=value, args=args)
        return value

    def primary(self) -> Node:
        token = self.token
        if self.accept("NUMBER"):
            unit = None
            if self.accept("["):
                unit = self.unit_expr()
                self.take("]")
            return self.node("number", token, text=token.value, unit=unit)
        if self.accept("STRING"):
            return self.node("string", token, value=token.value)
        if token.kind in {"true", "false"}:
            self.take(token.kind)
            return self.node("bool", token, value=token.kind == "true")
        if self.accept("IDENT"):
            return self.node("name", token, name=token.value)
        if self.accept("("):
            value = self.expression()
            self.take(")")
            # Retain the expression shape while extending its diagnostic span.
            return Node(value.kind, token.start, self.tokens[self.index - 1].end, value.data)
        self.take("IDENT")
        raise AssertionError("unreachable")

    def unit_expr(self) -> str:
        result = self.unit_factor()
        while self.token.kind in {"*", "/"}:
            result += self.take(self.token.kind).value + self.unit_factor()
        return result

    def unit_factor(self) -> str:
        result = self.take("IDENT").value
        if self.accept("^"):
            result += "^"
            if self.accept("-"):
                result += "-"
            token = self.take("NUMBER")
            if not _INTEGER.fullmatch(token.value):
                raise OntoKinError("OKL-E-SYNTAX", "A unit exponent must be an integer token.",
                                   token, phase="syntax")
            result += token.value
        return result


def parse(source: str, filename: str = "<input>") -> Node:
    """Parse a complete source bundle, with bounded parser stack usage."""
    try:
        result = Parser(lex(source)).program()
        result.data["filename"] = filename
        return result
    except RecursionError:
        raise OntoKinError("OKL-E-RESOURCE", "Parser nesting budget exceeded.",
                           category="resource_limit", phase="syntax") from None
