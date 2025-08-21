import pytest
from pathlib import Path

from orbyte.core import Orbyte
from orbyte.validation import (
    OrbyteConfigError,
    assert_valid_identifier,
    normalize_locale,
    assert_valid_paths,
    assert_mapping,
)
from orbyte.resolver import PromptResolver


def test_identifier_validation_blocks_traversal(tmp_path: Path):
    base = tmp_path / "prompts"
    base.mkdir()
    (base / "safe.j2").write_text("ok", encoding="utf-8")
    r = PromptResolver([str(base)])
    with pytest.raises(OrbyteConfigError):
        r.resolve("../etc/passwd")


def test_identifier_validation_blocks_extension(tmp_path: Path):
    base = tmp_path / "prompts"
    base.mkdir()
    r = PromptResolver([str(base)])
    with pytest.raises(OrbyteConfigError):
        r.resolve("welcome.j2")


def test_locale_validation(tmp_path: Path):
    base = tmp_path / "prompts"
    base.mkdir()
    (base / "hello.en.j2").write_text("Hi", encoding="utf-8")
    r = PromptResolver([str(base)])
    # invalid locale
    with pytest.raises(OrbyteConfigError):
        r.resolve("hello", locale="english")


def test_prompts_path_validation(tmp_path: Path):
    bad = tmp_path / "nope"
    with pytest.raises(OrbyteConfigError):
        Orbyte([str(bad)])


def test_vars_parse_errors(tmp_path: Path):
    from orbyte.core import Orbyte

    base = tmp_path / "prompts"
    base.mkdir()
    (base / "h.j2").write_text("x", encoding="utf-8")
    ob = Orbyte([str(base)])
    with pytest.raises(OrbyteConfigError):
        ob.parse_vars('{"a":')  # bad json
    vars_file = tmp_path / "vars.json"
    vars_file.write_text('{"a": ]}', encoding="utf-8")
    with pytest.raises(OrbyteConfigError):
        ob.parse_vars(f"@{vars_file}")


def test_identifier_validation_empty_and_non_string():
    with pytest.raises(OrbyteConfigError):
        assert_valid_identifier("")  # empty string
    with pytest.raises(OrbyteConfigError):
        assert_valid_identifier(None)  # type: ignore[arg-type]
    with pytest.raises(OrbyteConfigError):
        assert_valid_identifier(123)  # type: ignore[arg-type]


def test_identifier_validation_blocks_absolute_path(tmp_path: Path):
    # absolute path should be rejected
    abs_ident = str((tmp_path / "welcome").resolve())
    with pytest.raises(OrbyteConfigError):
        assert_valid_identifier(abs_ident)


def test_identifier_validation_blocks_invalid_chars():
    # spaces or $ should fail the allowed pattern
    with pytest.raises(OrbyteConfigError):
        assert_valid_identifier("welcome template")
    with pytest.raises(OrbyteConfigError):
        assert_valid_identifier("welcome$prod")


def test_normalize_locale_underscore_to_hyphen_and_empty_raises():
    # underscore normalized to hyphen
    assert normalize_locale("en_US", default_locale="en") == "en-US"
    # when both are empty -> error (covers "Locale cannot be empty.")
    with pytest.raises(OrbyteConfigError):
        normalize_locale(None, default_locale="")


def test_assert_valid_paths_raises_when_path_is_file(tmp_path: Path):
    f = tmp_path / "not_a_dir.txt"
    f.write_text("x", encoding="utf-8")
    with pytest.raises(OrbyteConfigError) as e:
        assert_valid_paths([str(f)])
    assert "not a directory" in str(e.value)


def test_assert_mapping_accepts_none_and_rejects_non_mapping():
    # None is allowed (no-op)
    assert_mapping("vars", None)
    # But non-mapping should raise
    with pytest.raises(OrbyteConfigError):
        assert_mapping("vars", ["not", "a", "mapping"])  # type: ignore[arg-type]
