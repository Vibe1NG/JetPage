"""PDF export: render each page's HTML with Playwright, stitch with pypdf.

Pages are rendered from the output of our Markdown parser (not from the
live Flet app), so the PDF is clean text — no sidebar, no navigation chrome.
Cross-document internal links are stripped to plain text in the output CSS.

This module is designed to be called from a background thread; it uses
asyncio.run() internally so the caller does not need to manage an event loop.
"""

import asyncio
import io
import logging
from datetime import date as _date

import pypdf
from playwright.async_api import async_playwright
from pygments.formatters import HtmlFormatter

from sitegen.config import CONTENT_DIR
from sitegen.content.loader import load_page
from sitegen.content.parser import parse
from sitegen.core.document import get_pages_for_document
from sitegen.core.nav import Document, NavTree
from sitegen.core.page_resolver import resolve
from sitegen.export.toc_builder import TocEntry, build_toc

logger = logging.getLogger(__name__)

_PYGMENTS_CSS = HtmlFormatter(style="friendly").get_style_defs(".highlight")

_PAGE_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      font-family: Georgia, 'Times New Roman', serif;
      font-size: 11pt;
      line-height: 1.7;
      color: #1a1a1a;
      max-width: 680px;
      margin: 0 auto;
      padding: 0;
    }}
    h1, h2, h3, h4, h5, h6 {{
      font-family: system-ui, -apple-system, sans-serif;
      margin-top: 1.5em;
      margin-bottom: 0.4em;
      line-height: 1.3;
    }}
    h1 {{ font-size: 1.9em; border-bottom: 1px solid #ddd; padding-bottom: 0.25em; }}
    h2 {{ font-size: 1.4em; }}
    h3 {{ font-size: 1.15em; }}
    p {{ margin: 0.8em 0; }}
    pre {{
      background: #f6f8fa;
      padding: 14px 16px;
      border-radius: 6px;
      overflow-x: auto;
      font-size: 0.82em;
      line-height: 1.5;
    }}
    code {{
      font-family: 'Courier New', Courier, monospace;
      font-size: 0.88em;
      background: #f0f0f0;
      padding: 1px 4px;
      border-radius: 3px;
    }}
    pre code {{ background: none; padding: 0; font-size: inherit; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1em 0; font-size: 0.9em; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 12px; text-align: left; }}
    th {{ background: #f6f8fa; font-weight: bold; }}
    blockquote {{
      border-left: 4px solid #ddd;
      margin: 1em 0;
      padding: 0.5em 1em;
      color: #555;
    }}
    /* Strip internal links — they don't work in PDF */
    a[href^="/"], a[href^="."] {{
      color: inherit;
      text-decoration: none;
      pointer-events: none;
    }}
    /* Suppress permalink anchors added by the toc extension */
    a.headerlink {{ display: none; }}
    {pygments_css}
  </style>
</head>
<body>
{body}
</body>
</html>
"""

_TITLE_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: system-ui, -apple-system, sans-serif; margin: 0; padding: 0;
           display: flex; align-items: center; justify-content: center;
           min-height: 100vh; background: #fff; }}
    .title-page {{ text-align: center; max-width: 500px; }}
    .title {{ font-size: 2.4em; font-weight: 700; color: #1a1a1a; margin-bottom: 0.3em; }}
    .subtitle {{ font-size: 1.1em; color: #555; margin-bottom: 2em; }}
    .rule {{ border: none; border-top: 2px solid {color}; width: 80px; margin: 1.5em auto; }}
    .date {{ font-size: 0.9em; color: #888; }}
  </style>
</head>
<body>
  <div class="title-page">
    <div class="title">{title}</div>
    <div class="subtitle">{description}</div>
    <hr class="rule">
    <div class="date">{date}</div>
  </div>
</body>
</html>
"""

_TOC_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: system-ui, -apple-system, sans-serif; font-size: 11pt;
           color: #1a1a1a; max-width: 680px; margin: 0 auto; padding: 40px 0; }}
    h1 {{ font-size: 1.6em; border-bottom: 1px solid #ddd; padding-bottom: 0.3em; margin-bottom: 1em; }}
    .toc-entry {{ display: flex; align-items: baseline; margin: 0.4em 0; }}
    .toc-title {{ flex: 1; font-size: 0.95em; }}
    .toc-dots {{ flex: 1; border-bottom: 1px dotted #bbb; margin: 0 8px 4px 8px; }}
    .toc-page {{ font-size: 0.9em; color: #555; white-space: nowrap; }}
  </style>
</head>
<body>
  <h1>Table of Contents</h1>
  {entries}
</body>
</html>
"""


def _render_title_html(doc: Document) -> str:
    return _TITLE_TEMPLATE.format(
        title=doc.title,
        description=getattr(doc, "description", ""),
        color=getattr(doc, "color", "#4A90D9"),
        date=_date.today().strftime("%B %d, %Y"),
    )


def _render_toc_html(toc: list[TocEntry], page_offset: int = 2) -> str:
    rows = []
    for entry in toc:
        rows.append(
            f'<div class="toc-entry">'
            f'<span class="toc-title">{entry.title}</span>'
            f'<span class="toc-dots"></span>'
            f'<span class="toc-page">{entry.page_index + page_offset + 1}</span>'
            f"</div>"
        )
    return _TOC_TEMPLATE.format(entries="\n".join(rows))


def _render_page_html(slug: str) -> str | None:
    """Return a standalone HTML string for a content page, or None if missing."""
    path = resolve(slug, CONTENT_DIR)
    if path is None:
        logger.warning("PDF export: page not found for slug %r", slug)
        return None
    md = load_page(path)
    body = parse(md)
    return _PAGE_TEMPLATE.format(pygments_css=_PYGMENTS_CSS, body=body)


async def _html_to_pdf(browser, html: str) -> bytes:
    """Render an HTML string to PDF bytes using Playwright."""
    ctx = await browser.new_context()
    pw_page = await ctx.new_page()
    await pw_page.set_content(html, wait_until="load")
    pdf_bytes = await pw_page.pdf(
        format="A4",
        margin={"top": "25mm", "bottom": "25mm", "left": "20mm", "right": "20mm"},
        print_background=True,
    )
    await ctx.close()
    return pdf_bytes


async def _export_async(pages_slugs: list[str], extra_pages: list[str] | None = None) -> list[bytes]:
    """Capture each page as a PDF and return the list of PDF byte strings.

    extra_pages (HTML strings) are rendered first and prepended to the results.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        results: list[bytes] = []

        # Render extra (title + TOC) pages first
        for html in extra_pages or []:
            pdf_bytes = await _html_to_pdf(browser, html)
            results.append(pdf_bytes)

        # Render content pages
        for slug in pages_slugs:
            html = _render_page_html(slug)
            if html:
                pdf_bytes = await _html_to_pdf(browser, html)
                results.append(pdf_bytes)

        await browser.close()
    return results


def _stitch_pdfs(pdfs: list[bytes], toc: list[TocEntry], content_offset: int = 0) -> bytes:
    """Merge individual page PDFs into one and inject PDF outline bookmarks."""
    writer = pypdf.PdfWriter()

    for pdf_bytes in pdfs:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        for pdf_page in reader.pages:
            writer.add_page(pdf_page)

    # Inject document outline (bookmarks); offset by content_offset (title + toc pages)
    for entry in toc:
        adjusted_index = entry.page_index + content_offset
        if adjusted_index < len(writer.pages):
            writer.add_outline_item(entry.title, adjusted_index)

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def export_document(doc: Document, nav_tree: NavTree) -> bytes:
    """Generate and return a PDF for the given document.

    Blocking — intended to be called from a background thread so the Flet
    event loop is not blocked during the (potentially slow) Playwright capture.

    The generated PDF includes a title page and a table of contents page
    prepended before the content pages.
    """
    pages = get_pages_for_document(doc, nav_tree)
    toc = build_toc(doc, nav_tree)

    if not pages:
        raise ValueError(f"Document '{doc.id}' has no pages to export.")

    slugs = [p.slug for p in pages]
    logger.info("Exporting %d pages for document '%s'", len(slugs), doc.id)

    title_html = _render_title_html(doc)
    toc_html = _render_toc_html(toc, page_offset=2)

    pdfs = asyncio.run(_export_async(slugs, extra_pages=[title_html, toc_html]))

    if not pdfs:
        raise ValueError("No pages were successfully rendered.")

    return _stitch_pdfs(pdfs, toc, content_offset=2)
