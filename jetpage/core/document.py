"""Document-level helpers: page enumeration and slug-to-document lookup."""

from jetpage.core.nav import Document, NavNode, NavTree


def get_pages_for_document(doc: Document, nav_tree: NavTree) -> list[NavNode]:
    """Return all leaf pages belonging to a document, in navigation order."""
    pages: list[NavNode] = []
    for node in nav_tree.nodes:
        if node.is_section and node.document_id == doc.id:
            pages.extend(node.children)
    return pages


def get_document_for_slug(slug: str, nav_tree: NavTree) -> Document | None:
    """Return the Document that owns the given page slug, or None."""
    for node in nav_tree.nodes:
        if node.is_section:
            # Match section root slug (e.g. "getting-started") or any child page
            if node.slug == slug and node.document_id:
                return nav_tree.find_document(node.document_id)
            for child in node.children:
                if child.slug == slug and child.document_id:
                    return nav_tree.find_document(child.document_id)
    return None
