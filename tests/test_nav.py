from jetpage.core.nav import NavTree


def test_load_nav_tree_returns_nav_tree(nav_tree):
    assert isinstance(nav_tree, NavTree)


def test_site_title(nav_tree):
    assert nav_tree.site["title"] == "JetPage Docs"


def test_documents_loaded(nav_tree):
    assert len(nav_tree.documents) == 3
    doc_ids = {d.id for d in nav_tree.documents}
    assert "user-guide" in doc_ids
    assert "reference" in doc_ids
    assert "how-i-made-this" in doc_ids


def test_nav_contains_home_page(nav_tree):
    home = next((n for n in nav_tree.nodes if n.slug == "index"), None)
    assert home is not None
    assert not home.is_section


def test_nav_sections_present(nav_tree):
    sections = [n for n in nav_tree.nodes if n.is_section]
    assert len(sections) == 4


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
