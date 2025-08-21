from __future__ import annotations
from pathlib import Path
import pytest
from jinja2 import UndefinedError
from orbyte.env import create_env
import orbyte.env as env_mod


def test_create_env_accepts_string_and_iterable(tmp_path: Path):
    d1 = tmp_path / "p1"
    d1.mkdir()
    d2 = tmp_path / "p2"
    d2.mkdir()
    (d1 / "a.j2").write_text("A", encoding="utf-8")
    (d2 / "b.j2").write_text("B", encoding="utf-8")
    e1 = create_env(str(d1))
    assert e1.get_template("a.j2").render() == "A"
    e2 = create_env([str(d1), str(d2)])
    assert e2.get_template("a.j2").render() == "A"
    assert e2.get_template("b.j2").render() == "B"


def test_strict_undefined_raises(tmp_path: Path):
    e = create_env(str(tmp_path))
    t = e.from_string("Hello {{ missing_var }}")
    with pytest.raises(UndefinedError):
        t.render()


def test_autoescape_html_enabled_but_j2_not(tmp_path: Path):
    (tmp_path / "page.html").write_text("{{ x }}", encoding="utf-8")
    (tmp_path / "text.j2").write_text("{{ x }}", encoding="utf-8")
    e = create_env(str(tmp_path))
    assert e.get_template("page.html").render(x="<b>") == "&lt;b&gt;"
    assert e.get_template("text.j2").render(x="<b>") == "<b>"


def test_sandbox_environment_when_available(tmp_path: Path):
    SandboxedEnvironment = getattr(env_mod, "SandboxedEnvironment", None)
    if SandboxedEnvironment is None:
        pytest.skip("SandboxedEnvironment not available")
    e = create_env(str(tmp_path), sandbox=True)
    assert isinstance(e, SandboxedEnvironment)


def test_sandbox_raises_when_not_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(env_mod, "SandboxedEnvironment", None, raising=False)
    with pytest.raises(RuntimeError):
        create_env(str(tmp_path), sandbox=True)


def test_bytecode_cache_when_available(tmp_path: Path):
    FSBC = getattr(env_mod, "FileSystemBytecodeCache", None)
    if FSBC is None:
        pytest.skip("FileSystemBytecodeCache not available")
    cache_dir = tmp_path / ".bcc"
    e = create_env(str(tmp_path), bytecode_cache_dir=str(cache_dir))
    assert getattr(e, "bytecode_cache", None) is not None
    assert isinstance(e.bytecode_cache, FSBC)  # type: ignore[arg-type]


def test_extra_filters_are_installed_and_work(tmp_path: Path):
    e = create_env(str(tmp_path), extra_filters={"shout": lambda v: str(v).upper() + "!"})
    t = e.from_string("Hello {{ who|shout }}")
    assert t.render(who="ada") == "Hello ADA!"


def test_translations_install_and_apply(tmp_path: Path):
    class DummyTranslations:
        def gettext(self, s):
            return f"t:{s}"  # pragma: no cover

        def ngettext(self, s, p, n):
            return f"t:{s if n == 1 else p}"  # pragma: no cover

    e = create_env(str(tmp_path), translations=DummyTranslations())
    t1 = e.from_string("{% trans %}Hello{% endtrans %}")
    assert t1.render() == "t:Hello"
    t2 = e.from_string("{% trans count=2 %}item{% pluralize %}items{% endtrans %}")
    assert t2.render() == "t:items"
