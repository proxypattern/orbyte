from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from .validation import assert_valid_identifier, normalize_locale


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

    def list_identifiers(self) -> List[str]:
        """List unique base identifiers found across search paths."""
        seen = set()
        for base in self.search_paths:
            if not base.exists():
                continue
            for p in base.rglob("*.j2"):
                # Strip .j2 and possible .<locale> suffix
                stem = p.name[:-3]  # remove .j2
                parts = stem.split(".")
                if len(parts) >= 2 and len(parts[-1]) <= 10:
                    # treat last segment as potential locale (like en, es, en-US)
                    base_id = ".".join(parts[:-1])
                else:
                    base_id = stem
                seen.add(base_id)
        return sorted(seen)
