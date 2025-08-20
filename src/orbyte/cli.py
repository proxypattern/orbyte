from __future__ import annotations

import json
import os
import runpy
from typing import Dict, List, Optional

import typer

from .core import Orbyte

from .validation import OrbyteConfigError, assert_valid_paths


app = typer.Typer(
    add_completion=False, help="Filesystem-first prompt templating with locale fallback."
)


def _resolve_paths(prompts_paths: Optional[List[str]]) -> List[str]:
    if prompts_paths and len(prompts_paths) > 0:
        paths = prompts_paths
    else:
        env = os.getenv("ORBYTE_PROMPTS_PATH", "")
        paths = [p for p in env.split(":") if p] or ["."]
    # Validate early for CLI
    assert_valid_paths(paths)
    return paths

def _load_filters(filters_path: Optional[str]) -> Optional[Dict[str, object]]:
    if not filters_path:
        return None
    if not os.path.exists(filters_path):
        raise OrbyteConfigError(f"Filters file not found: {filters_path}")
    ns = runpy.run_path(filters_path)
    if "FILTERS" in ns and isinstance(ns["FILTERS"], dict):
        return ns["FILTERS"]
    if "get_filters" in ns and callable(ns["get_filters"]):
        result = ns["get_filters"]()
        if not isinstance(result, dict):
            raise OrbyteConfigError("get_filters() in filters module must return a dict.")
        return result
    raise OrbyteConfigError(
        "Filters file must define FILTERS dict or get_filters() -> dict."
    )

def _load_translations(
    gettext_dir: Optional[str], locale: Optional[str], default_locale: str
):
    if not gettext_dir:
        return None
    if not os.path.isdir(gettext_dir):
        raise OrbyteConfigError(f"--gettext-dir must be a directory: {gettext_dir}")
    try:
        from babel.support import Translations
    except Exception as e:
        raise OrbyteConfigError("Babel is not installed. Use: pip install Babel") from e
    use_locale = (locale or default_locale).replace("_", "-")
    return Translations.load(gettext_dir, [use_locale])


def _build_orbyte(
    prompts_paths: List[str],
    default_locale: str,
    locale: Optional[str],
    sandbox: bool,
    bytecode_cache_dir: Optional[str],
    filters_path: Optional[str],
    gettext_dir: Optional[str],
) -> Orbyte:
    extra_filters = _load_filters(filters_path)
    translations = _load_translations(gettext_dir, locale, default_locale)
    return Orbyte(
        prompts_paths=prompts_paths,
        default_locale=default_locale,
        translations=translations,
        sandbox=sandbox,
        bytecode_cache_dir=bytecode_cache_dir,
        extra_filters=extra_filters,
    )


@app.command("list")
def list_cmd(
    prompts_path: List[str] = typer.Option(
        None,
        "--prompts-path",
        help="One or more paths to prompts directories (can repeat).",
    ),
    default_locale: str = typer.Option(
        "en",
        "--default-locale",
        help="Default locale for fallback resolution.",
    ),
    sandbox: bool = typer.Option(
        False,
        "--sandbox/--no-sandbox",
        help="Render with Jinja2 SandboxedEnvironment (for untrusted templates).",
    ),
    bytecode_cache_dir: Optional[str] = typer.Option(
        None, "--bytecode-cache-dir", help="Directory for Jinja2 bytecode cache."
    ),
    filters: Optional[str] = typer.Option(
        None,
        "--filters",
        help="Path to a Python file exporting FILTERS or get_filters().",
    ),
    gettext_dir: Optional[str] = typer.Option(
        None,
        "--gettext-dir",
        help="Directory containing gettext .mo files (Babel).",
    ),
):
    """List available identifiers."""
    paths = _resolve_paths(prompts_path)
    ob = _build_orbyte(
        paths, default_locale, None, sandbox, bytecode_cache_dir, filters, gettext_dir
    )
    for ident in ob.list_identifiers():
        typer.echo(ident)


@app.command()
def explain(
    identifier: str = typer.Argument(..., help="Template identifier (e.g., 'greeting')"),
    locale: Optional[str] = typer.Option(None, help="Locale (e.g., 'en', 'es')"),
    prompts_path: List[str] = typer.Option(
        None,
        "--prompts-path",
        help="One or more paths to prompts directories (can repeat).",
    ),
    default_locale: str = typer.Option(
        "en",
        "--default-locale",
        help="Default locale for fallback resolution.",
    ),
    sandbox: bool = typer.Option(
        False,
        "--sandbox/--no-sandbox",
        help="Render with Jinja2 SandboxedEnvironment (for untrusted templates).",
    ),
    bytecode_cache_dir: Optional[str] = typer.Option(
        None, "--bytecode-cache-dir", help="Directory for Jinja2 bytecode cache."
    ),
    filters: Optional[str] = typer.Option(
        None,
        "--filters",
        help="Path to a Python file exporting FILTERS or get_filters().",
    ),
    gettext_dir: Optional[str] = typer.Option(
        None,
        "--gettext-dir",
        help="Directory containing gettext .mo files (Babel).",
    ),
):
    """Explain which file will be used and show the fallback chain."""
    paths = _resolve_paths(prompts_path)
    ob = _build_orbyte(
        paths, default_locale, locale, sandbox, bytecode_cache_dir, filters, gettext_dir
    )
    info = ob.explain(identifier, locale=locale)
    typer.echo(json.dumps(info, indent=2))


@app.command()
def render(
    identifier: str = typer.Argument(..., help="Template identifier (e.g., 'greeting')"),
    vars: Optional[str] = typer.Option("{}", help="JSON string or @file.json"),
    locale: Optional[str] = typer.Option(None, help="Locale (e.g., 'en', 'es')"),
    prompts_path: List[str] = typer.Option(
        None,
        "--prompts-path",
        help="One or more paths to prompts directories (can repeat).",
    ),
    default_locale: str = typer.Option(
        "en",
        "--default-locale",
        help="Default locale for fallback resolution.",
    ),
    sandbox: bool = typer.Option(
        False,
        "--sandbox/--no-sandbox",
        help="Render with Jinja2 SandboxedEnvironment (for untrusted templates).",
    ),
    bytecode_cache_dir: Optional[str] = typer.Option(
        None, "--bytecode-cache-dir", help="Directory for Jinja2 bytecode cache."
    ),
    filters: Optional[str] = typer.Option(
        None,
        "--filters",
        help="Path to a Python file exporting FILTERS or get_filters().",
    ),
    gettext_dir: Optional[str] = typer.Option(
        None,
        "--gettext-dir",
        help="Directory containing gettext .mo files (Babel).",
    ),
):
    """Render a template."""
    paths = _resolve_paths(prompts_path)
    ob = _build_orbyte(
        paths, default_locale, locale, sandbox, bytecode_cache_dir, filters, gettext_dir
    )
    data = Orbyte.parse_vars(vars or "{}")
    output = ob.render(identifier, data, locale=locale)
    typer.echo(output)


def main():
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
