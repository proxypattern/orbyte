import pytest
from pathlib import Path

from orbyte.core import Orbyte
from orbyte.validation import OrbyteConfigError
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
