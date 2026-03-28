"""
LaTeX math pre/post processing for the HTML parser output (used for PDF export).

Protects $...$ and $$...$$ expressions from being mangled by the Markdown
parser, then restores them as MathJax-compatible HTML spans/divs.

The web UI uses ft.Markdown's native latex_scale_factor support instead.
"""

import re

# Block math: $$...$$  (must be matched before inline to avoid false positives)
_BLOCK_RE = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)

# Inline math: $...$ — excludes $$ and avoids matching across newlines
_INLINE_RE = re.compile(r"(?<!\$)\$(?!\$)([^\$\n]+?)(?<!\$)\$(?!\$)")


def protect_latex(text: str) -> tuple[str, dict[str, str]]:
    """Replace LaTeX expressions with unique placeholders before markdown parsing.

    Returns the modified text and a dict mapping placeholder -> rendered HTML.
    """
    store: dict[str, str] = {}

    def _block(m: re.Match) -> str:
        key = f"SGSMATH{len(store):04d}X"
        store[key] = f'<div class="math-block">\\[{m.group(1).strip()}\\]</div>'
        # Surround with blank lines so the parser treats it as a block element
        return f"\n\n{key}\n\n"

    def _inline(m: re.Match) -> str:
        key = f"SGSIMATH{len(store):04d}X"
        store[key] = f'<span class="math-inline">\\({m.group(1)}\\)</span>'
        return key

    text = _BLOCK_RE.sub(_block, text)
    text = _INLINE_RE.sub(_inline, text)
    return text, store


def restore_latex(html: str, store: dict[str, str]) -> str:
    """Restore MathJax-compatible HTML from placeholders."""
    for key, math_html in store.items():
        # Block math: the placeholder may have been wrapped in <p> by the parser
        html = html.replace(f"<p>{key}</p>", math_html)
        # Inline math or unwrapped fallback
        html = html.replace(key, math_html)
    return html
