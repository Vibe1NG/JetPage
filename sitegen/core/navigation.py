"""Prev/next page navigation and breadcrumb helpers."""

from dataclasses import dataclass

from sitegen.core.nav import NavNode, NavTree


@dataclass
class PageLink:
    title: str
    slug: str


def _flat_pages(nav_tree: NavTree) -> list[NavNode]:
    """Return all non-section nav nodes in order."""
    pages = []
    for node in nav_tree.nodes:
        if node.is_section:
            for child in node.children:
                pages.append(child)
        else:
            pages.append(node)
    return pages


def get_prev_next(slug: str, nav_tree: NavTree) -> tuple[PageLink | None, PageLink | None]:
    """Return (prev, next) PageLink for the given slug, or None if at boundary."""
    pages = _flat_pages(nav_tree)
    for i, node in enumerate(pages):
        if node.slug == slug:
            prev = PageLink(pages[i - 1].title, pages[i - 1].slug) if i > 0 else None
            next_ = PageLink(pages[i + 1].title, pages[i + 1].slug) if i < len(pages) - 1 else None
            return prev, next_
    return None, None


def get_breadcrumb(slug: str, nav_tree: NavTree) -> list[PageLink]:
    """Return breadcrumb links for the given slug."""
    crumbs = []
    for node in nav_tree.nodes:
        if node.is_section:
            for child in node.children:
                if child.slug == slug:
                    crumbs.append(PageLink(node.title, node.slug))
                    if child.slug != node.slug + "/index":
                        crumbs.append(PageLink(child.title, child.slug))
                    return crumbs
        elif node.slug == slug:
            crumbs.append(PageLink(node.title, node.slug))
            return crumbs
    return crumbs
