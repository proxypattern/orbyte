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
    SandboxedEnvironment = None  # type: ignore # noqa

try:
    from jinja2 import FileSystemBytecodeCache
except Exception:  # pragma: no cover
    FileSystemBytecodeCache = None  # type: ignore # noqa

try:
    from babel.support import Translations  # type: ignore # optional
except ImportError:  # pragma: no cover
    Translations = object  # type: ignore # noqa


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
        # Different Jinja2 versions use different methods
        if hasattr(env, "install_gettext_translations"):
            env.install_gettext_translations(translations)  # type: ignore # noqa
        else:
            # Handle different Jinja2 versions
            try:
                env.install_gettext_callables(  # type: ignore # noqa
                    translations.ugettext, translations.ungettext, newstyle=True
                )
            except AttributeError:
                # For newer Jinja2 versions
                env.install_gettext_callables(  # type: ignore # noqa
                    translations.gettext, translations.ngettext, newstyle=True
                )

    # Optional extra filters
    if extra_filters:
        env.filters.update(extra_filters)

    return env
