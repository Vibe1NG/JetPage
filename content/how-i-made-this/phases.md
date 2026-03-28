# Build Phases

JetPage was assembled in seven discrete phases. Each phase added a slice of
functionality, was tested, and was merged before the next began. This
incremental approach kept each Claude response focused and manageable.

## Phase Summary

| Phase | Name | Key deliverables |
|-------|------|-----------------|
| 1 | Project skeleton | `pyproject.toml`, Poetry setup, `jetpage/main.py`, stub modules |
| 2 | Navigation tree | `_meta.json` loader, `NavTree`/`NavNode`/`Document` dataclasses, sidebar |
| 3 | Markdown rendering + BDD tests | `parser.py`, `cache.py`, `ft.Markdown` display, Behave feature files |
| 4 | Syntax highlighting + LaTeX math | Pygments via pymdownx, `latex_scale_factor`, math protection extension |
| 5 | Document model + TOC + 3-column layout | `document.py`, `toc_builder.py`, `toc_panel.py`, 3-column `app_shell.py` |
| 6 | PDF export | `pdf_exporter.py`, Playwright + pypdf, `pdf_server.py`, download button |
| 7 | Caching, search, dark mode, pytest | `cache.py` with mtime key, `search.py`, dark-mode toggle, pytest suite |

## Phase Details

**Phase 1 — Project Skeleton.** Claude generated the Poetry `pyproject.toml`
with all required dependencies (`flet`, `markdown`, `pymdown-extensions`,
`pygments`, `playwright`, `pypdf`, `behave`), created the package hierarchy
under `jetpage/`, and wired a minimal `main.py` that launches a blank Flet
window.

**Phase 2 — Navigation Tree.** The `_meta.json` convention was designed here:
a top-level file lists documents and nav entries; each section directory has its
own `_meta.json` with an ordered list of pages. `load_nav_tree` assembles these
into a `NavTree`. The sidebar renders clickable tiles and highlights the active
page.

**Phase 3 — Markdown Rendering + BDD Tests.** `parser.py` was introduced with
the python-markdown pipeline. The Flet `ft.Markdown` widget was wired to display
page content. Behave BDD tests (`features/`) were written first as
specifications, then the code was made to pass them — a lightweight TDD
approach.

**Phase 4 — Syntax Highlighting + LaTeX Math.** The `pymdownx.highlight` and
`pymdownx.superfences` extensions replaced the built-in fenced-code extension,
enabling Pygments-powered highlighting. A custom `protect_latex` / `restore_latex`
extension was written to prevent python-markdown from corrupting `$...$` and
`$$...$$` expressions before they reach Flet's native LaTeX renderer.

**Phase 5 — Document Model + TOC + 3-Column Layout.** The concept of
multi-document sets (user guide, reference, etc.) was formalised with
`Document` dataclasses and tab-bar switching. `toc_builder.py` derives a
flat list of `TocEntry` objects from the nav tree. `toc_panel.py` renders
an in-page "On This Page" panel that scrolls with the content. The layout
became a three-column `ft.Row`.

**Phase 6 — PDF Export.** Each page is re-rendered to standalone HTML using the
same python-markdown pipeline (bypassing Flet entirely), then Playwright's
headless Chromium prints it to PDF. `pypdf` stitches the per-page PDFs into a
single document and injects PDF outline bookmarks. A tiny `pdf_server.py` serves
the bytes over HTTP so the browser can display them. A title page and printed
table of contents were added in a later iteration.

**Phase 7 — Caching, Search, Dark Mode, pytest.** The in-memory cache was
extended with an mtime key so edits are picked up without restarting. Full-text
`search.py` scans all content files and returns ranked excerpts. The dark-mode
toggle flips Flet's `ThemeMode` and rebuilds the sidebar and content controls.
The Behave suite was supplemented with a `pytest` suite covering the core and
content modules.
