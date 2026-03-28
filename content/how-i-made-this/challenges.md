# Challenges & Solutions

Building JetPage surfaced several non-obvious problems. Here are the five most
significant, and how they were resolved.

## 1. Flet 0.82.2 API Breaking Changes

Flet's API evolved significantly between versions, and the public documentation
does not always reflect the exact version in use. Several breakages were
encountered:

- **`ft.Colors` vs `ft.colors`** — the capitalised form is required in 0.82.2;
  the lower-case alias was removed.
- **`ft.Tab(label=...)`** — the `text=` parameter was renamed to `label=`.
- **`ft.TextButton(content=ft.Text(...))`** — the convenience `text=` shorthand
  was removed; a `content=` widget must be provided explicitly.
- **`page.show_dialog(dialog)`** / **`page.pop_dialog()`** — the newer
  `page.open()` / `page.close()` API is not present in 0.82.2.
- **`page.launch_url` is async** — calling it from a background thread requires
  wrapping in a closure and dispatching via `page.run_task(async_fn)`.

Each of these was identified by inspecting the Flet source at the installed
version and correcting the call sites.

## 2. LaTeX Rendering — No `page.run_javascript`

The original plan was to inject MathJax into the page via JavaScript. Flet
0.82.2 has no `page.run_javascript` method and no `ft.Html` widget that could
host a full browser context. The solution was to use Flet's own `ft.Markdown`
widget, which accepts a `latex_scale_factor` parameter and renders LaTeX math
natively via its underlying Flutter engine. For the PDF export path (which uses
Playwright), a custom `protect_latex` / `restore_latex` pipeline wraps math
expressions so python-markdown does not corrupt them before they reach
Playwright's MathJax-enabled page.

## 3. PDF Generation — Playwright Captures HTML, Not the Flet Canvas

Playwright cannot capture the Flutter canvas that Flet renders into — it would
only see the surrounding `<flet-app>` shell. The solution was to bypass Flet
entirely for PDF generation: each page is re-rendered as a clean, standalone
HTML document using the python-markdown pipeline and a handcrafted CSS template,
then Playwright's `page.pdf()` prints it. This produces a text-searchable PDF
(with real selectable text, not a screenshot) and strips the UI chrome (sidebar,
top bar, TOC panel) so the PDF contains only content.

## 4. Thread Safety for PDF Export

PDF generation is slow — it launches a headless browser and renders multiple
pages. Running it on the Flet event loop would freeze the UI. The export is
dispatched to a `threading.Thread`. Inside that thread, `asyncio.run()` creates
a fresh event loop for the `async_playwright` context. This is safe because
`asyncio.run()` is designed to be called from non-async contexts; it blocks the
calling thread until the coroutine finishes and then tears down the loop. No
shared state is accessed without the GIL, so no explicit locking is needed.

## 5. `toc_tokens` Nesting in python-markdown

The `toc` extension's `toc_tokens` attribute is a nested list of dicts with
keys `level`, `id`, `name`, and `children`. The nesting depth matches heading
levels, but only headings actually present in the document appear — so a page
that skips from `h1` to `h3` produces a tree where `h3` nodes are children of
the `h1`. The `toc_panel.py` renderer recurses through the tree and indents
entries proportionally to their level, rather than assuming a fixed two-level
structure.

## Getting Started

Ready to try JetPage yourself? See the [Getting Started guide](/getting-started)
to install and run it.
