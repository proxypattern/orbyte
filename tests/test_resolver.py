from pathlib import Path
from typing import List, Optional

import pytest

from orbyte.resolver import PromptResolver, Resolution
from orbyte.validation import OrbyteConfigError


def write_template(
    base: Path, identifier: str, content: str, locale: Optional[str] = None
):
    """Helper to create template files."""
    name = f"{identifier}.{locale}.j2" if locale else f"{identifier}.j2"
    (base / name).write_text(content, encoding="utf-8")


@pytest.fixture()
def tmp_prompts_dir(tmp_path: Path) -> Path:
    d = tmp_path / "prompts"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture()
def resolver_single_path(tmp_prompts_dir: Path) -> PromptResolver:
    return PromptResolver([str(tmp_prompts_dir)], default_locale="en")


@pytest.fixture()
def resolver_multi_path(tmp_path: Path) -> tuple[PromptResolver, List[Path]]:
    paths = []
    for i in range(2):
        p = tmp_path / f"prompts{i}"
        p.mkdir()
        paths.append(p)
    resolver = PromptResolver([str(p) for p in paths], default_locale="en")
    return resolver, paths


def test_resolve_exact_locale_match(
    resolver_single_path: PromptResolver, tmp_prompts_dir: Path
):
    write_template(tmp_prompts_dir, "greeting", "Hello!", locale="en")
    write_template(tmp_prompts_dir, "greeting", "Hola!", locale="es")

    result = resolver_single_path.resolve("greeting", locale="es")

    assert result.identifier == "greeting"
    assert result.locale == "es"
    assert result.chosen is not None
    assert result.chosen.name == "greeting.es.j2"


def test_resolve_fallback_to_default_locale(
    resolver_single_path: PromptResolver, tmp_prompts_dir: Path
):
    write_template(tmp_prompts_dir, "greeting", "Hello!", locale="en")

    result = resolver_single_path.resolve("greeting", locale="fr")

    assert result.identifier == "greeting"
    assert result.locale == "fr"
    assert result.chosen is not None
    assert result.chosen.name == "greeting.en.j2"


def test_resolve_fallback_to_plain_identifier(
    resolver_single_path: PromptResolver, tmp_prompts_dir: Path
):
    write_template(tmp_prompts_dir, "greeting", "Hello!")

    result = resolver_single_path.resolve("greeting", locale="fr")

    assert result.identifier == "greeting"
    assert result.locale == "fr"
    assert result.chosen is not None
    assert result.chosen.name == "greeting.j2"


def test_resolve_no_match_found(resolver_single_path: PromptResolver):
    result = resolver_single_path.resolve("nonexistent", locale="en")

    assert result.identifier == "nonexistent"
    assert result.locale == "en"
    assert result.chosen is None
    assert len(result.candidates) > 0


def test_resolve_default_locale_when_none_provided(
    resolver_single_path: PromptResolver, tmp_prompts_dir: Path
):
    write_template(tmp_prompts_dir, "greeting", "Hello!", locale="en")

    result = resolver_single_path.resolve("greeting", locale=None)

    assert result.identifier == "greeting"
    assert result.locale == "en"
    assert result.chosen is not None


def test_resolve_multi_search_paths(resolver_multi_path, tmp_path: Path):
    resolver, paths = resolver_multi_path

    # Put template in second path
    write_template(paths[1], "greeting", "Hello from path 2!")

    result = resolver.resolve("greeting", locale="en")

    assert result.chosen is not None
    assert "prompts1" in str(result.chosen)


def test_resolve_priority_first_path_wins(resolver_multi_path, tmp_path: Path):
    resolver, paths = resolver_multi_path

    # Put templates in both paths
    write_template(paths[0], "greeting", "Hello from path 1!", locale="en")
    write_template(paths[1], "greeting", "Hello from path 2!", locale="en")

    result = resolver.resolve("greeting", locale="en")

    assert result.chosen is not None
    assert "prompts0" in str(result.chosen)


def test_resolve_invalid_identifier(resolver_single_path: PromptResolver):
    with pytest.raises(OrbyteConfigError, match="must not be absolute"):
        resolver_single_path.resolve("/absolute/path")


def test_resolve_identifier_with_parent_traversal(resolver_single_path: PromptResolver):
    with pytest.raises(OrbyteConfigError, match="must not contain"):
        resolver_single_path.resolve("../escape")


def test_resolve_identifier_with_j2_extension(resolver_single_path: PromptResolver):
    with pytest.raises(OrbyteConfigError, match="must not include the '.j2' extension"):
        resolver_single_path.resolve("template.j2")


def test_resolve_complex_identifier_path(
    resolver_single_path: PromptResolver, tmp_prompts_dir: Path
):
    # Create subdirectory structure
    subdir = tmp_prompts_dir / "emails"
    subdir.mkdir()
    write_template(subdir, "welcome", "Welcome {{ name }}!", locale="en")

    result = resolver_single_path.resolve("emails/welcome", locale="en")

    assert result.chosen is not None
    assert result.chosen.name == "welcome.en.j2"


def test_list_identifiers_empty_directory(resolver_single_path: PromptResolver):
    identifiers = resolver_single_path.list_identifiers()
    assert identifiers == []


def test_list_identifiers_various_templates(
    resolver_single_path: PromptResolver, tmp_prompts_dir: Path
):
    write_template(tmp_prompts_dir, "greeting", "Hello!")
    write_template(tmp_prompts_dir, "welcome", "Welcome!", locale="en")
    write_template(tmp_prompts_dir, "welcome", "Bienvenido!", locale="es")
    write_template(tmp_prompts_dir, "goodbye", "Goodbye!", locale="fr")

    identifiers = resolver_single_path.list_identifiers()

    assert sorted(identifiers) == ["goodbye", "greeting", "welcome"]


def test_list_identifiers_nested_structure(
    resolver_single_path, tmp_prompts_dir, write_template
):
    emails_dir = tmp_prompts_dir / "emails"
    write_template(emails_dir, "welcome", "Welcome email")
    write_template(emails_dir, "goodbye", "Goodbye email", locale="en")

    notifications_dir = tmp_prompts_dir / "notifications"
    write_template(notifications_dir, "alert", "Alert!")

    identifiers = resolver_single_path.list_identifiers()
    assert "emails/welcome" in identifiers
    assert "emails/goodbye" in identifiers
    assert "notifications/alert" in identifiers


def test_list_identifiers_multi_path(resolver_multi_path, tmp_path: Path):
    resolver, paths = resolver_multi_path

    write_template(paths[0], "common", "Common template")
    write_template(paths[1], "unique", "Unique template")
    write_template(paths[1], "common", "Another common template")  # duplicate name

    identifiers = resolver.list_identifiers()

    assert "common" in identifiers
    assert "unique" in identifiers
    assert len([i for i in identifiers if i == "common"]) == 1  # deduplicated


def test_resolution_dataclass_properties():
    candidates = (Path("a.j2"), Path("b.j2"))
    chosen = Path("a.j2")

    resolution = Resolution(
        identifier="test", locale="en", candidates=candidates, chosen=chosen
    )

    assert resolution.identifier == "test"
    assert resolution.locale == "en"
    assert resolution.candidates == candidates
    assert resolution.chosen == chosen


def test_normalize_locale_underscores(
    resolver_single_path: PromptResolver, tmp_prompts_dir: Path
):
    write_template(tmp_prompts_dir, "greeting", "Hello!", locale="en-US")

    # Should normalize en_US to en-US and find the template
    result = resolver_single_path.resolve("greeting", locale="en_US")

    assert result.locale == "en-US"


def test_resolver_with_different_default_locale():
    resolver = PromptResolver(["/tmp"], default_locale="es")

    result = resolver.resolve("test", locale=None)

    assert result.locale == "es"


def test_list_identifiers_recursive_vs_non_recursive(tmp_path: Path):
    base = tmp_path / "prompts"
    (base / "emails").mkdir(parents=True)
    (base / "emails" / "welcome.en.j2").write_text("x", encoding="utf-8")
    (base / "root.j2").write_text("y", encoding="utf-8")

    r = PromptResolver([str(base)])
    assert r.list_identifiers(recursive=False) == ["root"]
    assert r.list_identifiers(recursive=True) == ["emails/welcome", "root"]


def test_list_identifiers_non_recursive(
    resolver_single_path: PromptResolver, tmp_prompts_dir: Path
):
    (tmp_prompts_dir / "root.en.j2").write_text("x", encoding="utf-8")
    (tmp_prompts_dir / "nested").mkdir()
    (tmp_prompts_dir / "nested" / "child.j2").write_text("y", encoding="utf-8")

    # Only top-level identifiers
    identifiers = resolver_single_path.list_identifiers(recursive=False)
    assert identifiers == ["root"]
