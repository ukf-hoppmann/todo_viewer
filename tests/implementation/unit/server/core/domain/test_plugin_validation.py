from dataclasses import dataclass

from viewer.core.domain.operations import HttpBinding, Operation
from viewer.core.domain.plugin import ElementKind, Migration, load_order, schema_problems, validate_plugins


@dataclass
class Nothing:
    pass


@dataclass(frozen=True)
class FakePlugin:
    id: str
    requires: tuple[str, ...] = ()
    operations: tuple[Operation, ...] = ()
    migrations: tuple[Migration, ...] = ()
    element_kinds: tuple[ElementKind, ...] = ()


def op(name: str, http: HttpBinding | None = None, mcp: bool = True) -> Operation:
    return Operation(name, "x", "read", Nothing, Nothing, lambda s, i: Nothing(), http, mcp)


def test_valid_list_has_no_problems() -> None:
    plugins = [FakePlugin("a"), FakePlugin("b", ("a",), (op("list", HttpBinding("GET", "/items")),))]
    assert validate_plugins(plugins) == []


def test_unknown_requires_is_reported() -> None:
    problems = validate_plugins([FakePlugin("a", ("missing",))])
    assert problems == ["Plugin 'a' verlangt unbekanntes Plugin 'missing'"]


def test_cycle_is_reported() -> None:
    problems = validate_plugins([FakePlugin("a", ("b",)), FakePlugin("b", ("a",))])
    assert any(p.startswith("Zyklus in requires:") and "a -> b -> a" in p for p in problems)


def test_self_requires_is_reported() -> None:
    assert validate_plugins([FakePlugin("a", ("a",))]) == ["Plugin 'a' verlangt sich selbst"]


def test_duplicate_ids_and_reserved_and_format() -> None:
    problems = validate_plugins([FakePlugin("a"), FakePlugin("a"), FakePlugin("core"), FakePlugin("Bad_Id")])
    assert "Plugin-ID 'a' kommt 2-mal vor" in problems
    assert "Plugin-ID 'core' ist für den Core reserviert" in problems
    assert "Plugin-ID 'Bad_Id' ist nicht kebab-case" in problems


def test_duplicate_route_is_reported_even_with_different_param_names() -> None:
    plugins = [
        FakePlugin(
            "a",
            operations=(
                op("one", HttpBinding("GET", "/items/{uid}")),
                op("two", HttpBinding("GET", "/items/{id}")),
            ),
        )
    ]
    problems = validate_plugins(plugins)
    assert problems == ["Doppelte Route GET /api/a/items/{}: 'a.one' und 'a.two'"]


def test_same_path_with_other_method_is_fine() -> None:
    plugins = [FakePlugin("a", operations=(op("one", HttpBinding("GET", "/x")), op("two", HttpBinding("PUT", "/x"))))]
    assert validate_plugins(plugins) == []


def test_duplicate_operation_and_tool_names() -> None:
    plugins = [
        FakePlugin("a", operations=(op("go"), op("go"))),
        FakePlugin("b-c", operations=(op("x"),)),
        FakePlugin("b", operations=(op("c_x"),)),
    ]
    problems = validate_plugins(plugins)
    assert "Operation 'a.go' ist doppelt" in problems
    assert "Doppeltes MCP-Tool 'a_go': 'a.go' und 'a.go'" in problems
    assert "Doppeltes MCP-Tool 'b_c_x': 'b-c.x' und 'b.c_x'" in problems


def test_non_mcp_operations_do_not_clash_on_tools() -> None:
    plugins = [FakePlugin("a", operations=(op("go"),)), FakePlugin("b", operations=(op("go", mcp=False),))]
    assert validate_plugins(plugins) == []


def test_operation_name_must_be_snake_case() -> None:
    problems = validate_plugins([FakePlugin("a", operations=(op("BadName"),))])
    assert problems == ["Operation 'a.BadName' ist nicht snake_case"]


def test_load_order_puts_required_plugins_first() -> None:
    plugins = [FakePlugin("c", ("b",)), FakePlugin("b", ("a",)), FakePlugin("a")]
    assert load_order(plugins) == ["a", "b", "c"]


def test_migration_versions_must_start_at_one_and_have_no_gaps() -> None:
    def mig(*versions: int) -> tuple[Migration, ...]:
        return tuple(Migration(v, lambda c: None) for v in versions)

    assert validate_plugins([FakePlugin("a", migrations=mig(1, 2, 3))]) == []
    for bad in [(2,), (1, 3), (1, 1), (2, 1)]:
        problems = validate_plugins([FakePlugin("a", migrations=mig(*bad))])
        assert len(problems) == 1 and problems[0].startswith("Migrationen von 'a' müssen lückenlos")


def test_overlapping_table_prefixes_are_reported() -> None:
    problems = validate_plugins([FakePlugin("a"), FakePlugin("a-b")])
    assert problems == ["Tabellen-Präfix 'a_' von 'a' überlappt 'a_b_' von 'a-b'"]


def test_schema_problems_checks_prefix_and_foreign_keys() -> None:
    ok = schema_problems(
        "backlog",
        {"backlog_items"},
        {"backlog_items": {"workspace_elements", "core_x", "backlog_areas"}},
        {"backlog", "core", "workspace"},
    )
    assert ok == []
    problems = schema_problems("notes", {"notes_x", "other_y"}, {"notes_x": {"backlog_items"}}, {"notes", "core"})
    assert problems[0] == "Tabelle 'other_y' von 'notes' trägt nicht das Präfix 'notes_'"
    assert problems[1].startswith("Fremdschlüssel von 'notes_x' auf 'backlog_items'")
    assert len(problems) == 2


def test_plugins_with_element_kinds_must_require_workspace() -> None:
    kinds = (ElementKind("note", "NOTE"),)
    assert validate_plugins([FakePlugin("workspace", element_kinds=kinds)]) == []
    assert validate_plugins([FakePlugin("workspace"), FakePlugin("notes", ("workspace",), element_kinds=kinds)]) == []
    assert validate_plugins([FakePlugin("notes", element_kinds=kinds)]) == [
        "Plugin 'notes' meldet Elementtypen an und muss 'workspace' in requires nennen"
    ]
