import logging
import threading

import flet as ft

from sitegen.config import CONTENT_DIR
from sitegen.content import cache as page_cache
from sitegen.core.document import get_document_for_slug
from sitegen.core.nav import load_nav_tree
from sitegen.core.navigation import get_breadcrumb, get_prev_next
from sitegen.core.page_resolver import resolve
from sitegen.core.search import search
from sitegen.export.pdf_exporter import export_document
from sitegen.export.pdf_server import pdf_server
from sitegen.ui.controls.nav_controls import build_breadcrumb, build_prev_next_bar
from sitegen.ui.controls.toc_panel import build_toc_panel
from sitegen.ui.sidebar import build_sidebar

logger = logging.getLogger(__name__)


def build_app(page: ft.Page) -> None:
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.WHITE

    nav_tree = load_nav_tree(CONTENT_DIR)
    page.title = nav_tree.site.get("title", "SiteGen")
    _docs = nav_tree.documents

    _state = {"dark": False, "slug": "index", "tab_index": 0}

    # --- Content area ---
    content_col = ft.Column(controls=[], tight=True)
    breadcrumb_container = ft.Container()
    prev_next_container = ft.Container()

    content_area = ft.Container(
        content=ft.Column(
            controls=[breadcrumb_container, content_col, prev_next_container],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        alignment=ft.Alignment(-1, -1),
        padding=ft.padding.all(32),
        expand=True,
    )

    # --- Sidebar ---
    sidebar_container = ft.Container(width=240, alignment=ft.Alignment(-1, -1))

    # --- TOC panel ---
    toc_container = ft.Container(width=0)

    # --- Top-bar controls ---
    download_btn = ft.IconButton(
        icon=ft.Icons.DOWNLOAD_OUTLINED,
        icon_color=ft.Colors.WHITE,
        tooltip="Download as PDF",
        visible=False,
        on_click=None,
    )
    export_spinner = ft.ProgressRing(width=20, height=20, stroke_width=2, color=ft.Colors.WHITE, visible=False)
    search_btn = ft.IconButton(
        icon=ft.Icons.SEARCH,
        icon_color=ft.Colors.WHITE,
        tooltip="Search",
        on_click=None,
    )
    dark_btn = ft.IconButton(
        icon=ft.Icons.DARK_MODE_OUTLINED,
        icon_color=ft.Colors.WHITE,
        tooltip="Toggle dark mode",
        on_click=None,
    )

    def _tab_style(active: bool) -> ft.ButtonStyle:
        return ft.ButtonStyle(
            color=ft.Colors.WHITE if active else ft.Colors.BLUE_200,
            bgcolor=ft.Colors.BLUE_900 if active else ft.Colors.TRANSPARENT,
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            shape=ft.RoundedRectangleBorder(radius=4),
        )

    def _make_tab_buttons() -> list[ft.Control]:
        return [
            ft.TextButton(
                content=ft.Text(doc.title),
                style=_tab_style(i == _state["tab_index"]),
                on_click=lambda _, idx=i: on_tab_click(idx),
            )
            for i, doc in enumerate(_docs)
        ]

    doc_tab_row = ft.Row(controls=_make_tab_buttons(), spacing=4)

    top_bar = ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(
                    nav_tree.site.get("title", "SiteGen"),
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
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
        bgcolor=ft.Colors.BLUE_700,
        padding=ft.padding.symmetric(horizontal=24, vertical=8),
    )

    body = ft.Row(
        controls=[
            sidebar_container,
            ft.VerticalDivider(width=1, color=ft.Colors.GREY_300),
            content_area,
            toc_container,
        ],
        spacing=0,
        expand=True,
    )

    page.add(ft.Column(controls=[top_bar, body], spacing=0, expand=True))

    # --- Helpers ---

    def _show_snack(message: str, error: bool = False) -> None:
        page.show_dialog(ft.SnackBar(content=ft.Text(message), bgcolor=ft.Colors.RED_700 if error else None))
        page.update()

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
        sidebar_container.content = build_sidebar(nav_tree, _state["slug"], navigate, dark=_state["dark"]).content

    def _rebuild_toc(toc_tokens: list[dict]) -> None:
        toc_panel = build_toc_panel(toc_tokens, dark=_state["dark"])
        if toc_panel:
            toc_container.content = ft.Column(
                controls=[
                    ft.VerticalDivider(width=1, color=ft.Colors.GREY_600 if _state["dark"] else ft.Colors.GREY_300),
                    toc_panel,
                ],
                spacing=0,
                expand=False,
            )
            toc_container.width = 201
        else:
            toc_container.content = None
            toc_container.width = 0

    def _rebuild_nav_controls(slug: str) -> None:
        crumbs = get_breadcrumb(slug, nav_tree)
        prev, next_ = get_prev_next(slug, nav_tree)
        breadcrumb_container.content = build_breadcrumb(crumbs, navigate, dark=_state["dark"])
        prev_next_container.content = build_prev_next_bar(prev, next_, navigate, dark=_state["dark"])

    # --- Dark mode ---

    def on_dark_toggle(_e: ft.ControlEvent) -> None:
        _state["dark"] = not _state["dark"]
        dark = _state["dark"]
        page.theme_mode = ft.ThemeMode.DARK if dark else ft.ThemeMode.LIGHT
        page.bgcolor = ft.Colors.GREY_900 if dark else ft.Colors.WHITE
        content_area.bgcolor = ft.Colors.GREY_900 if dark else ft.Colors.WHITE
        dark_btn.icon = ft.Icons.LIGHT_MODE_OUTLINED if dark else ft.Icons.DARK_MODE_OUTLINED
        _rebuild_sidebar()
        # Rebuild TOC and nav controls with cached tokens
        slug = _state["slug"]
        path = resolve(slug, CONTENT_DIR)
        if path:
            entry = page_cache.get_page(path)
            _rebuild_toc(entry.toc_tokens)
            content_col.controls = _build_content_controls(entry.raw)
        _rebuild_nav_controls(slug)
        page.update()

    dark_btn.on_click = on_dark_toggle

    # --- Search ---

    def on_search_click(_e: ft.ControlEvent) -> None:
        query_field = ft.TextField(
            hint_text="Search…",
            autofocus=True,
            border_radius=8,
            on_change=None,
        )
        results_col = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO, height=300)

        def on_query_change(e: ft.ControlEvent) -> None:
            results = search(e.control.value, CONTENT_DIR, nav_tree)
            results_col.controls = [
                ft.ListTile(
                    title=ft.Text(r.title, weight=ft.FontWeight.W_500),
                    subtitle=ft.Text(r.excerpt, size=12, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                    on_click=lambda _, s=r.slug: (dialog.open.__setattr__("open", False), navigate(s)),
                )
                for r in results
            ] or [ft.Text("No results", color=ft.Colors.GREY_500, italic=True)]
            results_col.update()

        query_field.on_change = on_query_change

        dialog = ft.AlertDialog(
            title=ft.Text("Search"),
            content=ft.Column(
                controls=[query_field, ft.Divider(), results_col],
                tight=True,
                width=500,
            ),
            on_dismiss=None,
        )

        def on_tile_click(slug: str) -> None:
            page.pop_dialog()
            navigate(slug)

        # Re-wire tile clicks now that dialog exists
        def on_query_change_v2(e: ft.ControlEvent) -> None:
            results = search(e.control.value, CONTENT_DIR, nav_tree)
            results_col.controls = [
                ft.ListTile(
                    title=ft.Text(r.title, weight=ft.FontWeight.W_500),
                    subtitle=ft.Text(r.excerpt, size=12, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                    on_click=lambda _, s=r.slug: on_tile_click(s),
                )
                for r in results
            ] or [ft.Text("No results", color=ft.Colors.GREY_500, italic=True)]
            results_col.update()

        query_field.on_change = on_query_change_v2
        page.show_dialog(dialog)

    search_btn.on_click = on_search_click

    # --- Document tabs ---

    def on_tab_click(idx: int) -> None:
        if 0 <= idx < len(_docs):
            navigate(_docs[idx].root)

    # --- PDF export ---

    def on_download_click(_e: ft.ControlEvent) -> None:
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

    def _build_content_controls(raw_md: str) -> list[ft.Control]:
        from sitegen.content.code_splitter import CodeSegment, TextSegment, split_code_blocks
        from sitegen.ui.controls.code_block import build_code_block

        segments = split_code_blocks(raw_md)
        controls: list[ft.Control] = []
        for seg in segments:
            if isinstance(seg, TextSegment):
                md = ft.Markdown(
                    value=seg.text,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                    code_theme=ft.MarkdownCodeTheme.GITHUB,
                    selectable=True,
                    latex_scale_factor=1.2,
                    on_tap_link=on_link_tap,
                )
                controls.append(md)
            elif isinstance(seg, CodeSegment):
                controls.append(build_code_block(seg.language, seg.code, page, dark=_state["dark"]))
        return controls

    # --- Link handling ---

    def on_link_tap(e: ft.ControlEvent) -> None:
        href = e.data
        if href and not href.startswith("http"):
            navigate(href.strip("/"))

    # --- Route loading ---

    def load_route(route: str) -> None:
        slug = route.strip("/") or "index"
        _state["slug"] = slug

        try:
            path = resolve(slug, CONTENT_DIR)
            if path:
                entry = page_cache.get_page(path)
                content_col.controls = _build_content_controls(entry.raw)
                _rebuild_toc(entry.toc_tokens)
            else:
                content_col.controls = [
                    ft.Markdown(
                        value=f"# Page Not Found\n\nThe page `{slug}` does not exist.",
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                        selectable=True,
                        on_tap_link=on_link_tap,
                    )
                ]
                _rebuild_toc([])
        except Exception as exc:
            logger.exception("Error loading page %r", slug)
            content_col.controls = [
                ft.Markdown(
                    value=f"# Error\n\nFailed to load `{slug}`:\n\n```\n{exc}\n```",
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                    selectable=True,
                    on_tap_link=on_link_tap,
                )
            ]
            _rebuild_toc([])

        _rebuild_sidebar()
        _update_doc_tab(slug)
        _rebuild_nav_controls(slug)
        download_btn.visible = bool(_current_doc())
        page.update()

    page.on_route_change = lambda e: load_route(e.route)
    load_route(page.route or "/")
