from jetpage.content.extensions.math import protect_latex, restore_latex


def test_inline_math_removed_from_text():
    text, store = protect_latex("Value $x^2$ here")
    assert "$" not in text
    assert len(store) == 1


def test_block_math_removed_from_text():
    text, store = protect_latex("$$\nf(x)\n$$")
    assert "$$" not in text
    assert len(store) == 1


def test_inline_math_html_contains_mathjax_delimiters():
    _, store = protect_latex("$a + b$")
    html = next(iter(store.values()))
    assert r"\(a + b\)" in html
    assert 'class="math-inline"' in html


def test_block_math_html_contains_mathjax_delimiters():
    _, store = protect_latex("$$\nc = d\n$$")
    html = next(iter(store.values()))
    assert r"\[c = d\]" in html
    assert 'class="math-block"' in html


def test_block_processed_before_inline():
    # $$...$$ must not be captured as two adjacent $...$ inline spans
    _, store = protect_latex("$$block$$ and $inline$")
    assert len(store) == 2


def test_restore_inline():
    _, store = protect_latex("$x$")
    key = next(iter(store.keys()))
    result = restore_latex(key, store)
    assert r"\(x\)" in result


def test_restore_block_strips_paragraph_wrapper():
    _, store = protect_latex("$$y$$")
    key = next(iter(store.keys()))
    # Simulate python-markdown wrapping the placeholder in <p>
    result = restore_latex(f"<p>{key}</p>", store)
    assert "<p>" not in result
    assert 'class="math-block"' in result


def test_no_math_returns_unchanged():
    text, store = protect_latex("No math here")
    assert text == "No math here"
    assert store == {}


def test_multiple_inline_expressions():
    _, store = protect_latex("$a$ and $b$ and $c$")
    assert len(store) == 3
