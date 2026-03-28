# Architecture

JetPage is organised into four top-level packages under `jetpage/`:

## Module Structure

**`jetpage/core/`** — domain logic with no UI dependency.

- `nav.py` — loads `_meta.json` files and builds the `NavTree` (documents,
  sections, and leaf pages as `NavNode` objects).
- `document.py` — helpers for enumerating a document's pages and resolving
  which document owns a given slug.
- `page_resolver.py` — maps a URL slug to a filesystem path.
- `search.py` — full-text search across all content files.
- `navigation.py` — prev/next page and breadcrumb helpers.

**`jetpage/content/`** — Markdown processing pipeline.

- `loader.py` — reads raw Markdown from disk and embeds images as base64 data
  URIs so they survive both the Flet viewer and Playwright PDF rendering.
- `parser.py` — converts Markdown to HTML using python-markdown with Pygments
  syntax highlighting and a `toc` extension for heading anchors.
- `cache.py` — in-memory page cache keyed by `(path, mtime)`; picks up edits
  automatically in development without a full restart.
- `code_splitter.py` — splits a Markdown document into alternating text and
  fenced-code segments so the UI can render code blocks with a copy button.

**`jetpage/ui/`** — the Flet application shell and reusable controls.

- `app_shell.py` — the top-level `build_app` function; wires together the
  top bar, sidebar, content area, and TOC panel.
- `sidebar.py` — renders the navigation tree into clickable list tiles.
- `controls/toc_panel.py` — the in-page "On This Page" panel.
- `controls/nav_controls.py` — breadcrumb strip and prev/next bar.
- `controls/code_block.py` — syntax-coloured code block with copy button.

**`jetpage/export/`** — PDF generation.

- `pdf_exporter.py` — orchestrates Playwright-based HTML-to-PDF rendering,
  then uses pypdf to stitch pages and inject bookmarks plus a title page and
  table of contents.
- `toc_builder.py` — derives `TocEntry` objects from the navigation tree.
- `pdf_server.py` — a minimal in-process HTTP server for serving generated PDFs.

## Key Design Decisions

**Why Flet?** Flet wraps Flutter, giving access to a mature, cross-platform
widget toolkit from pure Python. It supports async patterns, dark mode via
`ThemeMode`, and native Markdown rendering with LaTeX support — all without a
browser target.

**Why python-markdown + Pygments?** python-markdown is extensible and has a
stable `toc` extension that exposes `toc_tokens`, which JetPage uses to build
the in-page TOC panel. Pygments provides accurate, theme-able syntax
highlighting for both the HTML export path and the PDF.

**Why Playwright for PDF?** Flet renders to a Flutter canvas; there is no
`page.run_javascript` or `ft.Html` widget to hook into directly. Instead,
JetPage re-renders each page as standalone HTML (using the same python-markdown
pipeline), then asks Playwright's headless Chromium to print it to PDF. The
result is a fully text-searchable PDF rather than a rasterised screenshot.
