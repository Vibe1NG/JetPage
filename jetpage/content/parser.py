import markdown

from jetpage.content.extensions.math import protect_latex, restore_latex

_EXTENSIONS = [
    "pymdownx.highlight",  # Pygments syntax highlighting for code blocks
    "pymdownx.superfences",  # Replaces fenced_code; works with pymdownx.highlight
    "tables",
    "md_in_html",  # Pass raw HTML through; allow markdown inside HTML blocks
    "attr_list",
    "toc",  # Generates heading anchors (needed for in-page TOC)
]

_EXTENSION_CONFIGS: dict = {
    "pymdownx.highlight": {
        "use_pygments": True,
        "guess_lang": False,
        "pygments_lang_class": True,  # adds language-X class to <code> elements
    },
    "toc": {
        "permalink": True,
    },
}


def _make_md() -> markdown.Markdown:
    return markdown.Markdown(extensions=_EXTENSIONS, extension_configs=_EXTENSION_CONFIGS)


def parse(markdown_str: str) -> str:
    """Convert a Markdown string to an HTML string.

    LaTeX math ($...$ and $$...$$) is protected before parsing, then restored
    as MathJax-compatible HTML for PDF export. The web UI uses ft.Markdown's
    native LaTeX rendering instead.
    """
    html, _ = parse_with_toc(markdown_str)
    return html


def parse_with_toc(markdown_str: str) -> tuple[str, list[dict]]:
    """Convert Markdown to HTML and return (html, toc_tokens).

    toc_tokens is a nested list of dicts with keys: level, id, name, children.
    Used by the in-page TOC panel.
    """
    protected, store = protect_latex(markdown_str)
    md = _make_md()
    html = md.convert(protected)
    html = restore_latex(html, store)
    toc_tokens = getattr(md, "toc_tokens", [])
    return html, toc_tokens
