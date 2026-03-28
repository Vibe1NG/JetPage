"""Build a table of contents structure from a Document's navigation tree.

Used both by the PDF exporter (to generate PDF outline/bookmarks) and
potentially by a future printed TOC page.
"""

from dataclasses import dataclass, field

from jetpage.core.document import get_pages_for_document
from jetpage.core.nav import Document, NavTree


@dataclass
class TocEntry:
    title: str
    slug: str
    page_index: int = 0  # 0-based PDF page index; set after stitching
    children: list["TocEntry"] = field(default_factory=list)


def build_toc(doc: Document, nav_tree: NavTree) -> list[TocEntry]:
    """Return one TocEntry per page in the document, in navigation order."""
    pages = get_pages_for_document(doc, nav_tree)
    return [TocEntry(title=page.title, slug=page.slug, page_index=i) for i, page in enumerate(pages)]
