from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping, Optional

from jinja2 import UndefinedError

from .env import create_env
from .exceptions import MissingVariableError, TemplateLookupError
from .resolver import PromptResolver

from .validation import assert_valid_paths, assert_mapping, OrbyteConfigError


class Orbyte:
    """
    Filesystem-first prompt renderer with locale fallback.

    Parameters
    ----------
    prompts_paths : Iterable[str]
        One or more directories to search for templates.
    default_locale : str
        Default locale used in the fallback chain.
    translations : optional
        A babel.support.Translations instance (if using gettext/i18n).
    sandbox : bool
        Use Jinja2 SandboxedEnvironment (for untrusted templates).
    bytecode_cache_dir : Optional[str]
        Directory for Jinja2 bytecode cache (perf in prod).
    extra_filters : Optional[Mapping[str, object]]
        Custom Jinja2 filters to install into the environment.
    """

    def __init__(
        self,
        prompts_paths: Iterable[str],
        default_locale: str = "en",
        *,
        translations=None,
        sandbox: bool = False,
        bytecode_cache_dir: Optional[str] = None,
        extra_filters: Optional[Mapping[str, object]] = None,
    ) -> None:
        self.search_paths = [Path(p) for p in prompts_paths]
        assert_valid_paths(prompts_paths)

        self.resolver = PromptResolver(prompts_paths, default_locale=default_locale)
        self.env = create_env(
            prompts_paths,
            translations=translations,
            sandbox=sandbox,
            bytecode_cache_dir=bytecode_cache_dir,
            extra_filters=extra_filters,
        )
        self.default_locale = default_locale

    def _to_loader_name(self, absolute_path: Path) -> str:
        abs_path = absolute_path.resolve()
        for base in self.search_paths:
            try:
                rel = abs_path.relative_to(base.resolve())
                return rel.as_posix()
            except ValueError:
                continue
        raise TemplateLookupError(
            f"Chosen template '{abs_path}' is outside configured search paths: "
            + ", ".join(str(b) for b in self.search_paths)
        )

    def render(
        self,
        identifier: str,
        variables: Mapping[str, object] | None = None,
        locale: Optional[str] = None,
    ) -> str:
        assert_mapping("variables", variables)

        res = self.resolver.resolve(identifier, locale=locale)
        if res.chosen is None:
            raise TemplateLookupError(
                f"Template not found. Tried: {', '.join(str(c) for c in res.candidates)}"
            )

        try:
            name_for_loader = self._to_loader_name(res.chosen)
            template = self.env.get_template(name_for_loader)
            return template.render(**(variables or {}))
        except UndefinedError as e:
            raise MissingVariableError(str(e)) from e

    def explain(self, identifier: str, locale: Optional[str] = None) -> dict:
        res = self.resolver.resolve(identifier, locale=locale)
        return {
            "identifier": res.identifier,
            "locale": res.locale,
            "candidates": [str(c) for c in res.candidates],
            "chosen": str(res.chosen) if res.chosen else None,
        }

    def list_identifiers(self, *, recursive: bool = True) -> list[str]:
        return self.resolver.list_identifiers(recursive=recursive)

    @staticmethod
    def parse_vars(value: str) -> dict:
        v = (value or "").strip()
        if not v:
            return {}
        if v.startswith("@"):
            path = v[1:]
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except FileNotFoundError as e:
                raise OrbyteConfigError(f"Vars file not found: {path}") from e
            except json.JSONDecodeError as e:
                raise OrbyteConfigError(
                    f"Vars file is not valid JSON: {path} (line {e.lineno})"
                ) from e
        try:
            return json.loads(v)
        except json.JSONDecodeError as e:
            raise OrbyteConfigError(
                f"--vars must be valid JSON or @file.json (line {e.lineno})"
            ) from e
