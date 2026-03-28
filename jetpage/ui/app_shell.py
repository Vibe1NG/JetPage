import logging
import threading
from typing import Any

import flet as ft

from jetpage.config import CONTENT_DIR
from jetpage.content import cache as page_cache
from jetpage.core.document import get_document_for_slug
from jetpage.core.nav import load_nav_tree
from jetpage.core.navigation import get_breadcrumb, get_prev_next
from jetpage.core.page_resolver import resolve
from jetpage.core.search import search
from jetpage.export.pdf_exporter import export_document
from jetpage.export.pdf_server import pdf_server
from jetpage.ui.controls.nav_controls import build_breadcrumb, build_prev_next_bar
from jetpage.ui.controls.toc_panel import build_toc_panel
from jetpage.ui.sidebar import build_sidebar

logger = logging.getLogger(__name__)


_SURFACE = "#fcf9f8"
_SURFACE_DARK = "#1c1b1b"
_PANEL_WIDTH = 200  # TOC panel width (matches toc_panel._PANEL_WIDTH)


def build_app(page: ft.Page) -> None:
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = _SURFACE

    nav_tree = load_nav_tree(CONTENT_DIR)
    page.title = nav_tree.site.get("title", "JetPage")
    _docs = nav_tree.documents

    _state = {"dark": False, "slug": "index", "tab_index": 0}

    # Design token palettes
    _LIGHT = {
        "topbar_bg": "#fcf9f8",
        "topbar_text": "#1c1b1b",
        "topbar_icon": "#1c1b1b",
        "tab_active": "#0057c0",
        "tab_inactive": "#414754",
        "spinner": "#0057c0",
        "shadow": ft.Colors.with_opacity(0.07, "#1c1b1b"),
    }
    _DARK = {
        "topbar_bg": "#1c1b1b",
        "topbar_text": "#e5e2e1",
        "topbar_icon": "#e5e2e1",
        "tab_active": "#6daeff",
        "tab_inactive": "#b0b8c8",
        "spinner": "#6daeff",
        "shadow": ft.Colors.with_opacity(0.25, "#000000"),
    }

    def _tok() -> dict:
        return _DARK if _state["dark"] else _LIGHT

    # --- Content area ---
    content_col = ft.Column(controls=[], tight=True)
    breadcrumb_container = ft.Container()
    prev_next_container = ft.Container()
    content_scroll_col = ft.Column(
        controls=[breadcrumb_container, content_col, prev_next_container],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    content_area = ft.Container(
        content=content_scroll_col,
        alignment=ft.Alignment(-1, -1),
        padding=ft.padding.all(32),
        bgcolor=_SURFACE,
        expand=True,
    )

    # --- Sidebar ---
    sidebar_container = ft.Container(width=240, alignment=ft.Alignment(-1, -1))

    # --- TOC panel ---
    toc_container = ft.Container(width=0, alignment=ft.Alignment(-1, -1))

    def _icon_btn_style() -> ft.ButtonStyle:
        return ft.ButtonStyle(
            overlay_color=ft.Colors.with_opacity(0.06, _tok()["topbar_icon"]),
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.all(8),
        )

    # --- Top-bar controls ---
    download_btn = ft.IconButton(
        icon=ft.Icons.DOWNLOAD_OUTLINED,
        icon_color=_tok()["topbar_icon"],
        tooltip="Download as PDF",
        style=_icon_btn_style(),
        visible=False,
        on_click=None,
    )
    export_spinner = ft.ProgressRing(width=20, height=20, stroke_width=2, color=_tok()["spinner"], visible=False)
    search_btn = ft.IconButton(
        icon=ft.Icons.SEARCH,
        icon_color=_tok()["topbar_icon"],
        tooltip="Search",
        style=_icon_btn_style(),
        on_click=None,
    )
    dark_btn = ft.IconButton(
        icon=ft.Icons.DARK_MODE_OUTLINED,
        icon_color=_tok()["topbar_icon"],
        tooltip="Toggle dark mode",
        style=_icon_btn_style(),
        on_click=None,
    )

    def _tab_style(active: bool) -> ft.ButtonStyle:
        tok = _tok()
        return ft.ButtonStyle(
            color=tok["tab_active"] if active else tok["tab_inactive"],
            bgcolor=ft.Colors.TRANSPARENT,
            overlay_color=ft.Colors.with_opacity(0.06, tok["tab_active"]),
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            shape=ft.RoundedRectangleBorder(radius=6),
        )

    def _make_tab_buttons() -> list[ft.Control]:
        return [
            ft.TextButton(
                content=ft.Text(
                    doc.title,
                    weight=ft.FontWeight.W_500 if i == _state["tab_index"] else ft.FontWeight.NORMAL,
                ),
                style=_tab_style(i == _state["tab_index"]),
                on_click=lambda _, idx=i: on_tab_click(idx),
            )
            for i, doc in enumerate(_docs)
        ]

    doc_tab_row = ft.Row(controls=_make_tab_buttons(), spacing=2)

    _logo_text = ft.Text(
        nav_tree.site.get("title", "JetPage"),
        size=17,
        weight=ft.FontWeight.BOLD,
        color=_tok()["topbar_text"],
    )

    top_bar = ft.Container(
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Image(src="/jetpage-logo.svg", height=20),
                        ft.Container(width=6),
                        _logo_text,
                    ],
                    spacing=0,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(width=24),
                doc_tab_row if _docs else ft.Container(),
                ft.Container(expand=True),
                export_spinner,
                download_btn,
                search_btn,
                dark_btn,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=_tok()["topbar_bg"],
        padding=ft.padding.symmetric(horizontal=24, vertical=10),
        shadow=ft.BoxShadow(
            blur_radius=16,
            color=_tok()["shadow"],
            offset=ft.Offset(0, 2),
        ),
    )

    body = ft.Row(
        controls=[
            sidebar_container,
            content_area,
            toc_container,
        ],
        spacing=0,
        expand=True,
    )

    page.add(ft.Column(controls=[top_bar, body], spacing=0, expand=True))

    # --- Helpers ---

    def _resolve_slug_to_path(slug: str):
        doc = get_document_for_slug(slug, nav_tree)
        if doc and doc.effective_root and slug.startswith(doc.root):
            rel_slug = slug.removeprefix(doc.root).lstrip("/") or "index"
            return resolve(rel_slug, doc.effective_root)
        return resolve(slug, CONTENT_DIR)

    def _show_snack(message: str, error: bool = False) -> None:
        page.open(ft.SnackBar(content=ft.Text(message), bgcolor=ft.Colors.RED_700 if error else None))  # type: ignore

    def navigate(slug: str) -> None:

        page.go(f"/{slug}")

    def _current_doc():
        idx = _state["tab_index"]
        return _docs[idx] if _docs and idx < len(_docs) else None

    def _rebuild_doc_tabs() -> None:
        doc_tab_row.controls = _make_tab_buttons()

    def _update_doc_tab(slug: str) -> None:
        if not _docs:
            return
        doc = get_document_for_slug(slug, nav_tree)
        if doc:
            try:
                _state["tab_index"] = _docs.index(doc)
                _rebuild_doc_tabs()
            except ValueError:
                pass

    def _rebuild_sidebar() -> None:
        doc = _current_doc()
        doc_id = doc.id if doc else None
        sidebar_container.content = build_sidebar(
            nav_tree, _state["slug"], navigate, dark=_state["dark"], active_doc_id=doc_id
        ).content

    def _rebuild_toc(toc_tokens: list[dict]) -> None:
        def _on_anchor(anchor_id: str) -> None:
            page.go(f"/{_state['slug']}#{anchor_id}")

        toc_panel = build_toc_panel(toc_tokens, dark=_state["dark"], on_anchor_click=_on_anchor)
        if toc_panel:
            toc_container.content = toc_panel
            toc_container.width = _PANEL_WIDTH
        else:
            toc_container.content = None
            toc_container.width = 0

    def _rebuild_nav_controls(slug: str) -> None:
        crumbs = get_breadcrumb(slug, nav_tree)
        prev, next_ = get_prev_next(slug, nav_tree)
        breadcrumb_container.content = build_breadcrumb(crumbs, navigate, dark=_state["dark"])
        prev_next_container.content = build_prev_next_bar(prev, next_, navigate, dark=_state["dark"])

    # --- Dark mode ---

    def _update_topbar_colors() -> None:
        tok = _tok()
        top_bar.bgcolor = tok["topbar_bg"]
        top_bar.shadow = ft.BoxShadow(
            blur_radius=16,
            color=tok["shadow"],
            offset=ft.Offset(0, 2),
        )
        # Update the logo text color
        _logo_text.color = tok["topbar_text"]
        btn_style = _icon_btn_style()
        download_btn.icon_color = tok["topbar_icon"]
        download_btn.style = btn_style
        search_btn.icon_color = tok["topbar_icon"]
        search_btn.style = btn_style
        dark_btn.icon_color = tok["topbar_icon"]
        dark_btn.style = btn_style
        export_spinner.color = tok["spinner"]
        doc_tab_row.controls = _make_tab_buttons()

    def on_dark_toggle(_e: Any) -> None:
        _state["dark"] = not _state["dark"]
        dark = _state["dark"]
        page.theme_mode = ft.ThemeMode.DARK if dark else ft.ThemeMode.LIGHT
        page.bgcolor = _SURFACE_DARK if dark else _SURFACE
        content_area.bgcolor = _SURFACE_DARK if dark else _SURFACE
        dark_btn.icon = ft.Icons.LIGHT_MODE_OUTLINED if dark else ft.Icons.DARK_MODE_OUTLINED
        _update_topbar_colors()
        _rebuild_sidebar()
        # Rebuild TOC and nav controls with cached tokens
        slug = _state["slug"]
        path = _resolve_slug_to_path(slug)

        if path:
            entry = page_cache.get_page(path)
            _rebuild_toc(entry.toc_tokens)
            content_col.controls = _build_content_controls(entry.raw, entry.toc_tokens)
        _rebuild_nav_controls(slug)
        page.update()

    dark_btn.on_click = on_dark_toggle

    # --- Search ---

    def on_search_click(_e: Any) -> None:
        query_field = ft.TextField(
            hint_text="Search documentation…",
            autofocus=True,
            # Soft-plate style: filled bg, bottom-only border, no outer box
            border=ft.InputBorder.UNDERLINE,
            filled=True,
            fill_color=ft.Colors.with_opacity(1.0, "#f6f3f2" if not _state["dark"] else "#252525"),
            focused_color="#0057c0" if not _state["dark"] else "#6daeff",
            prefix_icon=ft.Icons.SEARCH,
        )
        results_col = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO, height=300)

        on_surface = "#1c1b1b" if not _state["dark"] else "#e5e2e1"
        on_surface_var = "#414754" if not _state["dark"] else "#b0b8c8"

        def on_tile_click(slug: str) -> None:
            page.close(dialog)  # type: ignore
            navigate(slug)

        def on_query_change(e: ft.ControlEvent) -> None:
            val = getattr(e.control, "value", "")
            results = search(val, CONTENT_DIR, nav_tree)
            results_col.controls = [
                ft.ListTile(
                    title=ft.Text(r.title, weight=ft.FontWeight.W_500, color=on_surface),
                    subtitle=ft.Text(
                        r.excerpt,
                        size=12,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        color=on_surface_var,
                    ),
                    on_click=lambda _, s=r.slug: on_tile_click(s),
                )
                for r in results
            ] or [ft.Text("No results", color=on_surface_var, italic=True, size=13)]
            results_col.update()

        query_field.on_change = on_query_change  # type: ignore

        dialog = ft.AlertDialog(
            title=ft.Text("Search", size=16, weight=ft.FontWeight.W_600, color=on_surface),
            content=ft.Column(
                controls=[query_field, ft.Container(height=8), results_col],
                tight=True,
                width=500,
            ),
        )

        page.open(dialog)  # type: ignore

    search_btn.on_click = on_search_click

    # --- Document tabs ---

    def on_tab_click(idx: int) -> None:
        if 0 <= idx < len(_docs):
            navigate(_docs[idx].root)

    # --- PDF export ---

    def on_download_click(_e: Any) -> None:
        doc = _current_doc()
        if not doc:
            return
        download_btn.visible = False
        export_spinner.visible = True
        page.update()

        def run_export() -> None:
            try:
                pdf_bytes = export_document(doc, nav_tree)
                url = pdf_server.store(doc.id, pdf_bytes)

                async def _launch(u: str = url) -> None:
                    await page.launch_url(u)

                page.run_task(_launch)
            except Exception as exc:
                logger.exception("PDF export failed for doc '%s'", doc.id)
                _show_snack(f"Export failed: {exc}", error=True)
            finally:
                export_spinner.visible = False
                download_btn.visible = True
                page.update()

        threading.Thread(target=run_export, daemon=True).start()

    download_btn.on_click = on_download_click

    # --- Content building ---

    def _build_content_controls(raw_md: str, toc_tokens: list[dict] | None = None) -> list[ft.Control]:
        import re

        from jetpage.content.code_splitter import CodeSegment, TextSegment, split_code_blocks
        from jetpage.ui.controls.code_block import build_code_block

        # Build anchor-id lookup from toc_tokens: {heading_name -> id}
        _anchor_map: dict[str, str] = {}

        def _collect_ids(tokens: list[dict]) -> None:
            for t in tokens:
                _anchor_map[t.get("name", "").strip()] = t.get("id", "")
                _collect_ids(t.get("children", []))

        _collect_ids(toc_tokens or [])

        # Split at heading boundaries (lookahead keeps the heading line at the start of each part)
        _heading_split_re = re.compile(r"(?=^#{1,6}\s)", re.MULTILINE)
        _heading_line_re = re.compile(r"^#{1,6}\s+(.+)")

        def _make_md(text: str) -> ft.Markdown:
            return ft.Markdown(
                value=text,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                code_theme=ft.MarkdownCodeTheme.GITHUB,
                selectable=True,
                latex_scale_factor=1.2,
                on_tap_link=on_link_tap,  # type: ignore
            )

        segments = split_code_blocks(raw_md)
        controls: list[ft.Control] = []
        for seg in segments:
            if isinstance(seg, TextSegment):
                # Split further at heading boundaries so each heading gets its own scroll key
                parts = [p for p in _heading_split_re.split(seg.text) if p.strip()]
                if not parts:
                    parts = [seg.text]
                for part in parts:
                    md = _make_md(part)
                    m = _heading_line_re.match(part.strip())
                    if m:
                        heading_text = re.sub(r"[*_`#]", "", m.group(1)).strip()
                        anchor_id = _anchor_map.get(heading_text, "")
                        if anchor_id:
                            controls.append(ft.Container(content=md, key=ft.ScrollKey(anchor_id)))
                            continue
                    controls.append(md)
            elif isinstance(seg, CodeSegment):
                controls.append(build_code_block(seg.language, seg.code, page, dark=_state["dark"]))
        return controls

    # --- Link handling ---

    def on_link_tap(e: ft.ControlEvent) -> None:
        href = getattr(e, "data", "")
        if href and not href.startswith("http"):
            navigate(href.strip("/"))

    # --- Route loading ---

    def load_route(route: str) -> None:
        raw = route.strip("/") or "index"
        slug, _, anchor = raw.partition("#")
        slug = slug or "index"

        # Same page, only hash changed — scroll without re-rendering
        if slug == _state["slug"] and anchor:

            async def _scroll() -> None:
                await content_scroll_col.scroll_to(scroll_key=anchor, duration=300)

            page.run_task(_scroll)
            return

        _state["slug"] = slug

        try:
            path = _resolve_slug_to_path(slug)

            if path:
                entry = page_cache.get_page(path)
                content_col.controls = _build_content_controls(entry.raw, entry.toc_tokens)
                _rebuild_toc(entry.toc_tokens)
            else:
                content_col.controls = list[ft.Control](
                    [
                        ft.Markdown(
                            value=f"# Page Not Found\n\nThe page `{slug}` does not exist.",
                            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                            selectable=True,
                            on_tap_link=on_link_tap,  # type: ignore
                        )
                    ]
                )
                _rebuild_toc([])
        except Exception as exc:
            logger.exception("Error loading page %r", slug)
            content_col.controls = list[ft.Control](
                [
                    ft.Markdown(
                        value=f"# Error\n\nFailed to load `{slug}`:\n\n```\n{exc}\n```",
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                        selectable=True,
                        on_tap_link=on_link_tap,  # type: ignore
                    )
                ]
            )
            _rebuild_toc([])

        _update_doc_tab(slug)
        _rebuild_sidebar()
        _rebuild_nav_controls(slug)
        download_btn.visible = bool(_current_doc())
        page.update()

        if anchor:

            async def _scroll_after_load(a: str = anchor) -> None:
                import asyncio

                await asyncio.sleep(1.0)
                await content_scroll_col.scroll_to(scroll_key=a, duration=300)

            page.run_task(_scroll_after_load)

    page.on_route_change = lambda e: load_route(e.route)
    load_route(page.route or "/")
