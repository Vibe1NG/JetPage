from jetpage.core.nav import NavTree


def test_load_nav_tree_returns_nav_tree(nav_tree):
    assert isinstance(nav_tree, NavTree)


def test_site_title(nav_tree):
    assert nav_tree.site["title"] == "JetPage Docs"


def test_documents_loaded(nav_tree):
    assert len(nav_tree.documents) == 4
    doc_ids = {d.id for d in nav_tree.documents}
    assert "user-guide" in doc_ids
    assert "reference" in doc_ids
    assert "how-i-made-this" in doc_ids
    assert "api-reference" in doc_ids


def test_nav_sections_present(nav_tree):
    sections = [n for n in nav_tree.nodes if n.is_section]
    assert len(sections) == 5


def test_section_children_populated(nav_tree):
    gs = next(n for n in nav_tree.nodes if n.slug == "getting-started")
    assert len(gs.children) == 3
    assert gs.children[0].slug == "getting-started/index"
    assert gs.children[1].slug == "getting-started/installation"


def test_section_children_inherit_document_id(nav_tree):
    gs = next(n for n in nav_tree.nodes if n.slug == "getting-started")
    for child in gs.children:
        assert child.document_id == "user-guide"


def test_find_document(nav_tree):
    doc = nav_tree.find_document("reference")
    assert doc is not None
    assert doc.title == "Reference"


def test_find_document_missing_returns_none(nav_tree):
    assert nav_tree.find_document("nonexistent") is None


def test_toolbar_loaded(nav_tree):
    assert len(nav_tree.toolbar) == 2
    assert nav_tree.toolbar[0].type == "document"
    assert nav_tree.toolbar[0].document_id == "user-guide"
    assert nav_tree.toolbar[1].type == "library"
    assert nav_tree.toolbar[1].title == "Reference Library"
    assert len(nav_tree.toolbar[1].items) == 3
    # Check nested library
    nested = nav_tree.toolbar[1].items[2]
    assert nested.type == "library"
    assert nested.title == "Technical Specs"
    assert len(nested.items) == 1
    assert nested.items[0].type == "document"
    assert nested.items[0].document_id == "api-reference"
