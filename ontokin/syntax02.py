"""Source-aware entry point for explicitly versioned bundled source units.

The core parser remains the entry point for legacy programs. This parser reuses
its unchanged expression precedence and statements but has its own keyword set,
qualified names, keyed values, and explicitly typed member/key paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .bundle import SourceUnit
from .diagnostics import OntoKinError
from .syntax import MAX_TOKENS, RESERVED, Node, Parser, Token, lex


VERSION = "0.2"
PROFILE = "construction-0.1"
RESERVED_02 = RESERVED | frozenset("import from version digest parts for in keyed".split())


@dataclass(frozen=True)
class PathStep:
    kind: str
    value: str
    start: int
    end: int

    def __post_init__(self) -> None:
        if self.kind not in ("member", "key"):
            raise ValueError("A source path step must be a member or key.")


class Parser02(Parser):
    def __init__(self, tokens: list[Token], source_id: str,
                 check: Callable[[], None] | None = None, *,
                 expected_version: str = VERSION, expected_profile: str = PROFILE):
        super().__init__(tokens)
        self.source_id = source_id
        self.check = check
        self.expected_version = expected_version
        self.expected_profile = expected_profile

    def node(self, kind: str, start: Token | Node, **data: Any) -> Node:
        if self.check is not None:
            self.check()
        return Node(kind, start.start, self.tokens[self.index - 1].end,
                    data, source_id=self.source_id)

    def qualified_name(self) -> tuple[str, tuple[str, ...]]:
        names = [self.take("IDENT").value]
        if self.accept("."):
            names.append(self.take("IDENT").value)
        return ".".join(names), tuple(names)

    def program(self) -> Node:
        start = self.take("ontokin")
        version_node = self.take("STRING")
        self.take(";")
        if version_node.value != self.expected_version:
            raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED",
                               f"This source unit requires language {self.expected_version}.",
                               version_node, category="unsupported", phase="support", rule_ids=["CON-001"],
                               details={"expected_version": self.expected_version, "actual_version": version_node.value})
        self.take("module")
        name = self.take("IDENT").value
        key = self.identity()
        self.take(";")
        self.take("profile")
        profile_node = self.take("STRING")
        self.take(";")
        if profile_node.value != self.expected_profile:
            raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED",
                               f"This source unit requires {self.expected_profile}.",
                               profile_node, category="unsupported", phase="support", rule_ids=["CON-001"],
                               details={"expected_profile": self.expected_profile, "actual_profile": profile_node.value})
        requires = []
        while self.token.kind == "requires":
            token = self.take("requires")
            value = self.take("STRING").value
            self.take(";")
            requires.append(self.node("capability", token, value=value))
        execution = self.execution_declaration()
        imports = []
        while self.token.kind == "import":
            imports.append(self.import_decl())
        classes, functions, definitions = [], [], []
        while self.token.kind in {"public", "private", "class", "fn"}:
            declaration_start = self.token
            visibility = self.take(self.token.kind).value if self.token.kind in {"public", "private"} else "public"
            if self.token.kind == "class":
                item = self.class_decl(visibility, declaration_start)
            else:
                if self.token.kind != "fn":
                    self.take("fn")
                item = self.function_decl(visibility, start=declaration_start)
            (classes if item.kind == "class" else functions).append(item)
            definitions.append(item)
        scene = self.scene() if self.token.kind == "scene" else None
        self.take("EOF")
        result = self.node("program", start, version=version_node.value,
                         module_name=name, module_key=key, profile=profile_node.value,
                         version_node=version_node, profile_node=profile_node,
                         requires=requires, imports=imports, classes=classes,
                         functions=functions, definitions=definitions, scene=scene)
        if self.expected_version in {"0.7", "0.8", "0.9", "0.10", "0.11", "0.12", "0.13", "0.14", "0.15"}:
            result.data["execution"] = execution
        return result

    def execution_declaration(self):
        # The legacy grammar and node/work counts retain their exact behavior.
        # Only Parser07 overrides this contextual header extension point.
        return None

    def import_decl(self) -> Node:
        start = self.take("import")
        name = self.take("IDENT").value
        key = self.identity()
        self.take("from")
        package_node = self.take("STRING")
        self.take("version")
        version_node = self.take("STRING")
        self.take("digest")
        digest_node = self.take("STRING")
        self.take(";")
        return self.node("import", start, name=name, key=key,
                         package_id=package_node.value, version=version_node.value,
                         digest=digest_node.value, package_node=package_node,
                         version_node=version_node, digest_node=digest_node)

    def class_decl(self, visibility: str = "public", start: Token | None = None) -> Node:
        keyword = self.take("class")
        name = self.take("IDENT").value
        key = self.identity()
        base, base_parts = self.qualified_name() if self.accept("extends") else (None, None)
        self.take("{")
        members = []
        while self.token.kind != "}":
            members.append(self.member(in_scene=False))
        self.take("}")
        return self.node("class", start or keyword, name=name, key=key,
                         visibility=visibility, base=base, base_parts=base_parts, members=members)

    def type_decl(self) -> Node:
        start = self.token
        args, unit = [], None
        if self.accept("Quantity"):
            name, names = "Quantity", ("Quantity",)
            self.take("[")
            unit = self.unit_expr()
            self.take("]")
        else:
            name, names = self.qualified_name()
            if self.accept("<"):
                args.append(self.type_decl())
                while self.accept(","):
                    args.append(self.type_decl())
                self.take(">")
        return self.node("type", start, name=name, name_parts=names, args=args, unit=unit)

    def member(self, in_scene: bool) -> Node:
        if (not in_scene and self.token.kind in {"public", "private"}
                and self.tokens[self.index + 1].kind == "parts"):
            start = self.token
            visibility = self.take(self.token.kind).value
            self.take("parts")
            name = self.take("IDENT").value
            key = self.identity()
            self.take(":")
            class_name, class_name_parts = self.qualified_name()
            self.take("for")
            self.take("(")
            key_node = self.take("IDENT")
            self.take(",")
            value_node = self.take("IDENT")
            self.take(")")
            self.take("in")
            input_ = self.expression()
            self.take("{")
            assignments = []
            while self.token.kind != "}":
                assignments.append(self.assignment())
            self.take("}")
            return self.node("parts", start, name=name, key=key, visibility=visibility,
                             class_name=class_name, class_name_parts=class_name_parts,
                             key_name=key_node.value, value_name=value_node.value,
                             key_node=key_node, value_node=value_node, input=input_,
                             assignments=assignments)
        return super().member(in_scene)

    def declaration(self, kind: str, visibility: str | None, start: Token) -> Node:
        self.take(kind)
        name = self.take("IDENT").value
        key = self.identity()
        class_name = class_name_parts = joint_type = None
        if kind in {"object", "part", "joint"}:
            self.take(":")
            if kind == "joint":
                joint_type = self.take("IDENT").value
            else:
                class_name, class_name_parts = self.qualified_name()
        self.take("{")
        assignments = []
        while self.token.kind != "}":
            assignments.append(self.assignment())
        self.take("}")
        return self.node(kind, start, name=name, key=key, visibility=visibility,
                         class_name=class_name, class_name_parts=class_name_parts,
                         joint_type=joint_type, assignments=assignments)

    def path(self) -> tuple[PathStep, ...]:
        start = self.take("IDENT")
        steps = [PathStep("member", start.value, start.start, start.end)]
        while self.token.kind in {".", "["}:
            if self.accept("."):
                token = self.take("IDENT")
                steps.append(PathStep("member", token.value, token.start, token.end))
            else:
                self.take("[")
                token = self.take("STRING")
                self.take("]")
                steps.append(PathStep("key", token.value, token.start, token.end))
        return tuple(steps)

    def postfix(self) -> Node:
        value = self.primary()
        while self.token.kind in {".", "(", "["}:
            if self.accept("."):
                name = self.take("IDENT").value
                value = self.node("member", value, target=value, name=name)
            elif self.accept("["):
                index = self.expression()
                self.take("]")
                value = self.node("index", value, target=value, index=index)
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
        if self.token.kind == "keyed":
            start = self.take("keyed")
            self.take("<")
            element_type = self.type_decl()
            self.take(">")
            self.take("{")
            entries = []
            if self.token.kind != "}":
                while True:
                    key_node = self.take("STRING")
                    self.take(":")
                    value = self.expression()
                    entries.append(self.node("keyed_entry", key_node, key=key_node.value,
                                             key_node=key_node, value=value))
                    if not self.accept(","):
                        break
            self.take("}")
            return self.node("keyed", start, element_type=element_type, entries=entries)
        if self.token.kind == "(":
            start = self.take("(")
            value = self.expression()
            self.take(")")
            return self.node(value.kind, start, **value.data)
        return super().primary()


def parse_source_unit(unit: SourceUnit, *, check: Callable[[], None] | None = None) -> Node:
    """Parse a source unit without deciding whether its bundle role is valid."""
    if not isinstance(unit, SourceUnit):
        raise TypeError("parse_source_unit requires an immutable SourceUnit")
    callback_error: Exception | None = None

    def checkpoint() -> None:
        nonlocal callback_error
        if check is not None:
            try:
                check()
            except Exception as exc:
                callback_error = exc
                raise

    try:
        checkpoint()
        # A one-token lexer allowance lets the exact limit end in whitespace;
        # the legacy lex() default and its historical boundary remain unchanged.
        tokens = lex(unit.text, reserved=RESERVED_02, source_id=unit.source_id,
                     max_tokens=MAX_TOKENS + 1, check=checkpoint if check is not None else None)
        if len(tokens) - 1 > MAX_TOKENS:
            raise OntoKinError("OKL-E-RESOURCE", "The source unit exceeds the token budget.",
                               tokens[MAX_TOKENS], category="resource_limit", phase="lexical",
                               rule_ids=["CON-012"], details={"limit": MAX_TOKENS})
        # Keep the existing lexer/0.2/0.3 grammar unchanged. Only an explicit
        # 0.4 header selects the contextual impulse event statement.
        declared = (tokens[1].value if len(tokens) > 2 and tokens[0].kind == "ontokin"
                    and tokens[1].kind == "STRING" else None)
        callback = checkpoint if check is not None else None
        if declared == "0.15":
            from .syntax15 import Parser15
            result = Parser15(tokens, unit.source_id, callback).program()
        elif declared == "0.14":
            from .syntax14 import Parser14
            result = Parser14(tokens, unit.source_id, callback).program()
        elif declared == "0.13":
            from .syntax13 import Parser13
            result = Parser13(tokens, unit.source_id, callback).program()
        elif declared == "0.12":
            from .syntax12 import Parser12
            result = Parser12(tokens, unit.source_id, callback).program()
        elif declared == "0.11":
            from .syntax11 import Parser11
            result = Parser11(tokens, unit.source_id, callback).program()
        elif declared == "0.10":
            from .syntax10 import Parser10
            result = Parser10(tokens, unit.source_id, callback).program()
        elif declared == "0.9":
            from .syntax09 import Parser09
            result = Parser09(tokens, unit.source_id, callback).program()
        elif declared == "0.8":
            from .syntax08 import Parser08
            result = Parser08(tokens, unit.source_id, callback).program()
        elif declared == "0.7":
            from .syntax07 import Parser07
            result = Parser07(tokens, unit.source_id, callback).program()
        elif declared == "0.6":
            from .syntax06 import Parser06
            result = Parser06(tokens, unit.source_id, callback).program()
        elif declared == "0.5":
            from .syntax05 import Parser05
            result = Parser05(tokens, unit.source_id, callback).program()
        elif declared == "0.4":
            from .syntax04 import Parser04
            result = Parser04(tokens, unit.source_id, callback).program()
        else:
            version, profile = ("0.3", "surface-0.1") if declared == "0.3" else (VERSION, PROFILE)
            result = Parser02(tokens, unit.source_id, callback,
                              expected_version=version, expected_profile=profile).program()
        result.data["filename"] = unit.filename
        result.data["token_count"] = len(tokens) - 1
        checkpoint()
        return result
    except OntoKinError as exc:
        if exc is callback_error:
            raise
        if exc.diagnostic.node is None:
            exc.diagnostic.node = Node("span", 0, 0, source_id=unit.source_id)
        elif getattr(exc.diagnostic.node, "source_id", None) is None:
            # Parser error tokens are immutable, so replace only their span.
            node = exc.diagnostic.node
            exc.diagnostic.node = Node("span", node.start, node.end, source_id=unit.source_id)
        raise
    except RecursionError as exc:
        if exc is callback_error:
            raise
        raise OntoKinError("OKL-E-RESOURCE", "Parser nesting exceeds the construction budget.",
                           Node("span", 0, 0, source_id=unit.source_id), category="resource_limit",
                           phase="syntax", rule_ids=["CON-012"]) from None
