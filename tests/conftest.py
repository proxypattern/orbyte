# tests/conftest.py
from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Callable, Optional

import pytest
from typer.testing import CliRunner

from orbyte.resolver import PromptResolver


# ---- Global safety: avoid env leakage across tests --------------------------
@pytest.fixture(autouse=True)
def _clear_orbyte_env(monkeypatch: pytest.MonkeyPatch):
    """Ensure tests don't leak ORBYTE_PROMPTS_PATH across each other."""
    monkeypatch.delenv("ORBYTE_PROMPTS_PATH", raising=False)


# ---- Common paths & helpers --------------------------------------------------
@pytest.fixture()
def tmp_prompts_dir(tmp_path: Path) -> Path:
    """A fresh prompts directory for each test."""
    d = tmp_path / "prompts"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture()
def write_template() -> Callable[[Path, str, str, Optional[str]], Path]:
    """
    Helper to write a template file. Usage:
      write_template(base, "welcome", "Hello {{ name }}!", locale="en")
      write_template(base / "emails", "invite", "Hi!", None)
    """

    def _write(
        base: Path, identifier: str, content: str, locale: Optional[str] = None
    ) -> Path:
        base.mkdir(parents=True, exist_ok=True)
        name = f"{identifier}.{locale}.j2" if locale else f"{identifier}.j2"
        path = base / name
        path.write_text(content, encoding="utf-8")
        return path

    return _write


@pytest.fixture()
def resolver_single_path(tmp_prompts_dir: Path) -> PromptResolver:
    """A resolver over a single temporary prompts path."""
    return PromptResolver([str(tmp_prompts_dir)], default_locale="en")


# ---- CLI helper fixtures -----------------------------------------------------
@pytest.fixture()
def runner() -> CliRunner:
    """Shared Typer/Click CLI runner."""
    return CliRunner()


# ---- Optional: dummy Babel for gettext tests --------------------------------
@pytest.fixture()
def install_dummy_babel(monkeypatch: pytest.MonkeyPatch):
    """
    Make `from babel.support import Translations` importable without installing Babel.
    Provides Translations.load() returning an object with gettext/ngettext.
    """
    babel_mod = types.ModuleType("babel")
    support_mod = types.ModuleType("babel.support")

    class DummyTranslations:
        @classmethod
        def load(cls, *_args, **_kwargs):
            return cls()

        def gettext(self, s):  # pragma: no cover (behavior is trivial)
            return s

        def ngettext(self, s, p, n):  # pragma: no cover
            return s if n == 1 else p

    support_mod.Translations = DummyTranslations  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "babel", babel_mod)
    monkeypatch.setitem(sys.modules, "babel.support", support_mod)
    return DummyTranslations
