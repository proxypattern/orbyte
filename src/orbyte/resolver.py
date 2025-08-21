from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from .validation import assert_valid_identifier, normalize_locale

# locale token like: en, es, en-US, zh-Hant, pt-BR, etc.
_LOCALE_TOKEN = r"[A-Za-z]{2,3}(?:[-_][A-Za-z0-9]{2,8})*"
# filename stem with optional locale suffix: welcome.en, invoice.en-US, etc.
_LOCALE_SUFFIX_RE = re.compile(rf"^(?P<base>.+?)\.(?P<loc>{_LOCALE_TOKEN})$")

_EXCLUDED_DIRS = {".git", ".hg", ".svn", "__pycache__", ".venv", "venv"}


@dataclass(frozen=True)
class Resolution:
    identifier: str
    locale: str
    candidates: Tuple[Path, ...]
    chosen: Optional[Path]


class PromptResolver:
    """Resolve identifier + locale to a concrete template file.

    Naming convention:
      identifier[.locale].j2

    Fallback order:
      1) identifier.<locale>.j2
      2) identifier.<default_locale>.j2
      3) identifier.j2
    """

    def __init__(self, search_paths: Iterable[str], default_locale: str = "en") -> None:
        self.search_paths: List[Path] = [Path(p) for p in search_paths]
        self.default_locale = default_locale

    def resolve(self, identifier: str, locale: str | None = None) -> Resolution:
        assert_valid_identifier(identifier)
        loc = normalize_locale(locale, self.default_locale)

        names: List[str] = []
        names.append(f"{identifier}.{loc}.j2")
        if loc != self.default_locale:
            names.append(f"{identifier}.{self.default_locale}.j2")
        names.append(f"{identifier}.j2")

        candidates: List[Path] = []
        chosen: Optional[Path] = None
        for base in self.search_paths:
            for name in names:
                p = base / name
                candidates.append(p)
                if p.exists():
                    chosen = p
                    return Resolution(identifier, loc, tuple(candidates), chosen)
        return Resolution(identifier, loc, tuple(candidates), chosen)

    def list_identifiers(self, *, recursive: bool = True) -> List[str]:
        """
        List unique base identifiers found across search paths.

        - Returns identifiers with POSIX-style paths (e.g., "emails/welcome").
        - Strips locale suffix from the *filename* only (e.g., "welcome.en" -> "welcome").
        - If `recursive=False`, only looks in the top directory of each search path.
        """
        seen: set[str] = set()

        for base in self.search_paths:
            if not base.exists():
                continue

            it = base.rglob("*.j2") if recursive else base.glob("*.j2")
            for p in it:
                rel = p.relative_to(base)

                # skip hidden/excluded dirs
                parts = rel.parts[:-1]  # parent dirs only
                if any(part in _EXCLUDED_DIRS or part.startswith(".") for part in parts):
                    continue

                # remove .j2 and locale suffix from the *filename*
                stem = p.stem
                m = _LOCALE_SUFFIX_RE.match(stem)
                base_name = m.group("base") if m else stem

                # rebuild the identifier using parent dirs + base_name (POSIX separators)
                parent = rel.parent
                ident_path = (
                    (parent / base_name) if str(parent) != "." else Path(base_name)
                )
                seen.add(ident_path.as_posix())

        return sorted(seen)
