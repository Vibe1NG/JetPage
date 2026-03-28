from jetpage.core.search import search


def test_search_finds_matching_page(content_dir, nav_tree):
    results = search("Installation", content_dir, nav_tree)
    slugs = [r.slug for r in results]
    assert any("installation" in s for s in slugs)


def test_search_is_case_insensitive(content_dir, nav_tree):
    lower = search("poetry", content_dir, nav_tree)
    upper = search("POETRY", content_dir, nav_tree)
    assert {r.slug for r in lower} == {r.slug for r in upper}


def test_search_returns_excerpt(content_dir, nav_tree):
    results = search("Poetry", content_dir, nav_tree)
    assert all(r.excerpt for r in results)


def test_search_empty_query_returns_nothing(content_dir, nav_tree):
    assert search("", content_dir, nav_tree) == []


def test_search_short_query_returns_nothing(content_dir, nav_tree):
    assert search("x", content_dir, nav_tree) == []


def test_search_no_match_returns_empty(content_dir, nav_tree):
    assert search("xyzzy_no_match_12345", content_dir, nav_tree) == []
