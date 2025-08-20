import pytest
from pathlib import Path
from orbyte.core import Orbyte, MissingVariableError, TemplateLookupError


def test_render_basic(tmp_path: Path):
    base = tmp_path / "prompts"
    base.mkdir()
    (base / "hello.j2").write_text("Hello {{ name }}!")
    ob = Orbyte([str(base)], default_locale="en")
    assert ob.render("hello", {"name": "Ada"}) == "Hello Ada!"


def test_missing_variable_raises(tmp_path: Path):
    base = tmp_path / "prompts"
    base.mkdir()
    (base / "hello.j2").write_text("Hello {{ name }}!")
    ob = Orbyte([str(base)])
    with pytest.raises(MissingVariableError):
        ob.render("hello", {})


def test_template_not_found(tmp_path: Path):
    base = tmp_path / "prompts"
    base.mkdir()
    ob = Orbyte([str(base)])
    with pytest.raises(TemplateLookupError):
        ob.render("missing", {"x": 1})
