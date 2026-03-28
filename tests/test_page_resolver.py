from jetpage.core.page_resolver import resolve


def test_resolve_index(content_dir):
    result = resolve("index", content_dir)
    assert result is not None
    assert result.name == "index.md"


def test_resolve_leading_slash_stripped(content_dir):
    assert resolve("/index", content_dir) == resolve("index", content_dir)


def test_resolve_empty_slug_falls_back_to_index(content_dir):
    result = resolve("", content_dir)
    assert result is not None
    assert result.name == "index.md"


def test_resolve_section_returns_index(content_dir):
    result = resolve("getting-started", content_dir)
    assert result is not None
    assert result.name == "index.md"
    assert "getting-started" in str(result)


def test_resolve_nested_page(content_dir):
    result = resolve("getting-started/installation", content_dir)
    assert result is not None
    assert result.name == "installation.md"


def test_resolve_missing_returns_none(content_dir):
    assert resolve("does/not/exist", content_dir) is None


def test_resolve_returns_path_that_exists(content_dir):
    for slug in ["index", "getting-started/installation", "reference/meta-json"]:
        result = resolve(slug, content_dir)
        assert result is not None and result.exists(), f"Expected {slug} to resolve to an existing file"
