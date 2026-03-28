from jetpage.core.document import get_document_for_slug, get_pages_for_document


def test_get_pages_for_document_user_guide(nav_tree):
    doc = nav_tree.find_document("user-guide")
    pages = get_pages_for_document(doc, nav_tree)
    assert len(pages) > 0
    slugs = [p.slug for p in pages]
    assert "getting-started/installation" in slugs
    assert "guides/content-authoring" in slugs


def test_get_pages_for_document_reference(nav_tree):
    doc = nav_tree.find_document("reference")
    pages = get_pages_for_document(doc, nav_tree)
    assert len(pages) == 2
    assert pages[0].slug == "reference/index"


def test_all_pages_belong_to_document(nav_tree):
    doc = nav_tree.find_document("user-guide")
    pages = get_pages_for_document(doc, nav_tree)
    assert all(p.document_id == "user-guide" for p in pages)


def test_get_document_for_slug_known(nav_tree):
    doc = get_document_for_slug("getting-started/installation", nav_tree)
    assert doc is not None
    assert doc.id == "user-guide"


def test_get_document_for_slug_reference(nav_tree):
    doc = get_document_for_slug("reference/meta-json", nav_tree)
    assert doc is not None
    assert doc.id == "reference"


def test_get_document_for_slug_unknown(nav_tree):
    assert get_document_for_slug("nonexistent", nav_tree) is None


def test_get_document_for_home_page_returns_none(nav_tree):
    # The home page (index) has no document
    assert get_document_for_slug("index", nav_tree) is None
