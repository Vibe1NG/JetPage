"""Simple full-text search over the content directory.

Scans all leaf-page Markdown files for the query string and returns ranked
results with a short excerpt. No indexing — suitable for small doc sites.
"""

from dataclasses import dataclass
from pathlib import Path

from jetpage.core.nav import NavNode, NavTree
from jetpage.core.page_resolver import resolve

_MIN_QUERY_LEN = 2
_EXCERPT_WIDTH = 120


@dataclass
class SearchResult:
    title: str
    slug: str
    excerpt: str


def search(query: str, content_dir: Path, nav_tree: NavTree) -> list[SearchResult]:
    """Return pages whose content contains *query* (case-insensitive)."""
    query = query.strip()
    if len(query) < _MIN_QUERY_LEN:
        return []

    query_lower = query.lower()
    results: list[SearchResult] = []

    for node in _all_leaf_pages(nav_tree):
        path = resolve(node.slug, content_dir)
        if path is None:
            continue
        content = path.read_text(encoding="utf-8")
        if query_lower in content.lower():
            results.append(
                SearchResult(
                    title=node.title,
                    slug=node.slug,
                    excerpt=_excerpt(content, query_lower),
                )
            )

    return results


def _all_leaf_pages(nav_tree: NavTree) -> list[NavNode]:
    pages: list[NavNode] = []
    for node in nav_tree.nodes:
        if not node.is_section:
            pages.append(node)
        pages.extend(node.children)
    return pages


def _excerpt(content: str, query: str) -> str:
    idx = content.lower().find(query)
    if idx == -1:
        return content[:_EXCERPT_WIDTH].strip() + "…"
    start = max(0, idx - _EXCERPT_WIDTH // 2)
    end = min(len(content), idx + len(query) + _EXCERPT_WIDTH // 2)
    snippet = content[start:end].strip()
    if start > 0:
        snippet = "…" + snippet
    if end < len(content):
        snippet += "…"
    return snippet
