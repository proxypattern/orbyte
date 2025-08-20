from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Mapping


class OrbyteConfigError(ValueError):
    """Raised when Orbyte is misconfigured (paths/locales/identifiers)."""


_IDENTIFIER_RE = re.compile(r"^[\w\-/\.]+$")  # letters, digits, _, -, /, .
_LOCALE_RE = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")  # en, en-US, zh-Hant


def assert_valid_identifier(identifier: str) -> None:
    """
    Rules:
      - not absolute
      - no parent traversal ('..')
      - no trailing .j2 (users pass logical names)
      - allowed chars only
    """
    if not identifier or not isinstance(identifier, str):
        raise OrbyteConfigError("Identifier must be a non-empty string.")
    p = Path(identifier)
    if p.is_absolute():
        raise OrbyteConfigError(f"Identifier '{identifier}' must not be absolute.")
    if any(part == ".." for part in p.parts):
        raise OrbyteConfigError(f"Identifier '{identifier}' must not contain '..'.")
    if identifier.endswith(".j2"):
        raise OrbyteConfigError("Identifier must not include the '.j2' extension.")
    if not _IDENTIFIER_RE.match(identifier):
        raise OrbyteConfigError(
            "Identifier contains unsupported characters. Allowed: letters, digits, _, -, /, ."
        )


def normalize_locale(locale: str | None, default_locale: str) -> str:
    """
    - None -> default
    - '_' to '-' (en_US -> en-US)
    - validate pattern.
    """
    loc = (locale or default_locale or "").strip()
    if not loc:
        raise OrbyteConfigError("Locale cannot be empty.")
    loc = loc.replace("_", "-")
    if not _LOCALE_RE.match(loc):
        raise OrbyteConfigError(
            f"Locale '{loc}' is invalid. Expected like 'en' or 'en-US'."
        )
    return loc


def assert_valid_paths(paths: Iterable[str]) -> None:
    for p in paths:
        q = Path(p)
        if not q.exists():
            raise OrbyteConfigError(f"Prompts path does not exist: {p}")
        if not q.is_dir():
            raise OrbyteConfigError(f"Prompts path is not a directory: {p}")


def assert_mapping(name: str, value: Mapping | None) -> None:
    if value is None:
        return
    if not isinstance(value, Mapping):
        raise OrbyteConfigError(f"{name} must be a mapping/dict.")
