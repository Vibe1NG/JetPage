"""In-memory page cache keyed by (file path, mtime).

Avoids re-parsing unchanged files on every navigation event.
The cache is process-scoped; in DEV_MODE the mtime check picks up edits automatically.
"""

from dataclasses import dataclass
from pathlib import Path

from jetpage.content.parser import parse_with_toc


@dataclass(frozen=True)
class PageEntry:
    raw: str
    html: str
    toc_tokens: list[dict]


_cache: dict[tuple[str, float], PageEntry] = {}


def get_page(path: Path) -> PageEntry:
    """Return a PageEntry for the given path, reading from cache when the file is unchanged."""
    mtime = path.stat().st_mtime
    key = (str(path), mtime)
    if key not in _cache:
        raw = path.read_text(encoding="utf-8")
        html, toc_tokens = parse_with_toc(raw)
        _cache[key] = PageEntry(raw=raw, html=html, toc_tokens=toc_tokens)
    return _cache[key]


def clear() -> None:
    """Flush the entire cache (useful for testing or forced reload)."""
    _cache.clear()
