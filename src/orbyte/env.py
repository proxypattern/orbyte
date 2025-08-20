from __future__ import annotations

from typing import Iterable, Mapping, Optional, Union
from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    select_autoescape,
)

try:
    # Available in jinja2; import lazily to avoid hard dependency on sandbox unless used
    from jinja2.sandbox import SandboxedEnvironment
except Exception:  # pragma: no cover
    SandboxedEnvironment = None  # type: ignore[assignment]

try:
    from jinja2 import FileSystemBytecodeCache
except Exception:  # pragma: no cover
    FileSystemBytecodeCache = None  # type: ignore[misc]

try:
    from babel.support import Translations  # optional
except Exception:  # pragma: no cover
    Translations = object  # type: ignore[assignment]


def create_env(
    templates_paths: Union[str, Iterable[str]],
    *,
    translations: Optional[Translations] = None,
    sandbox: bool = False,
    bytecode_cache_dir: Optional[str] = None,
    extra_filters: Optional[Mapping[str, object]] = None,
) -> Environment:
    """
    Create a Jinja2 Environment for prompt rendering.

    - Supports one or many search paths.
    - StrictUndefined: fail on missing vars (safer for prompts).
    - Autoescape only for html/xml; plain .j2 remains raw.
    - Optional gettext/i18n if `translations` is provided.
    - Optional sandbox (for untrusted templates).
    - Optional bytecode cache for faster production loads.
    - Optional injection of custom filters.
    """
    if isinstance(templates_paths, str):
        paths = [templates_paths]
    else:
        paths = list(templates_paths)

    # Choose environment class
    env_cls = Environment
    if sandbox:
        if SandboxedEnvironment is None:
            raise RuntimeError(
                "SandboxedEnvironment not available in this Jinja2 install."
            )
        env_cls = SandboxedEnvironment  # type: ignore[assignment]

    # Optional bytecode cache
    bcc = None
    if bytecode_cache_dir and FileSystemBytecodeCache is not None:
        bcc = FileSystemBytecodeCache(directory=bytecode_cache_dir)

    env = env_cls(
        loader=FileSystemLoader(paths),
        autoescape=select_autoescape(
            enabled_extensions=("html", "htm", "xml"),
            default_for_string=False,
        ),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        auto_reload=True,
        bytecode_cache=bcc,
    )

    # Optional i18n via gettext
    if translations is not None and translations is not object:
        env.add_extension("jinja2.ext.i18n")
        env.install_gettext_translations(translations)

    # Optional extra filters
    if extra_filters:
        env.filters.update(extra_filters)

    return env
