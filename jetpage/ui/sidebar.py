import flet as ft

from jetpage.core.nav import NavNode, NavTree

_SIDEBAR_WIDTH = 240


def build_sidebar(
    nav_tree: NavTree,
    active_slug: str,
    on_navigate,
    dark: bool = False,
    active_doc_id: str | None = None,
) -> ft.Container:
    """Build the navigation sidebar for the given nav tree and active page."""
    colors = _dark_colors() if dark else _light_colors()
    items: list[ft.Control] = []

    for node in nav_tree.nodes:
        if node.is_section:
            if active_doc_id and node.document_id != active_doc_id:
                continue
            items.append(_section_header(node, colors))
            for child in node.children:
                items.append(_page_item(child.title, child.slug, active_slug, on_navigate, colors, indent=True))
        else:
            items.append(_page_item(node.title, node.slug, active_slug, on_navigate, colors, indent=False))

    return ft.Container(
        content=ft.Column(
            controls=items,
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        ),
        width=_SIDEBAR_WIDTH,
        bgcolor=colors["sidebar_bg"],
        padding=ft.padding.only(left=8, right=8, top=12, bottom=12),
    )


def _light_colors() -> dict:
    return {
        "sidebar_bg": "#f6f3f2",
        "section_label": "#6b7280",
        "active_text": "#0057c0",
        "active_bg": ft.Colors.with_opacity(0.08, "#0057c0"),
        "default_text": "#1c1b1b",
        "hover_bg": ft.Colors.with_opacity(0.04, "#1c1b1b"),
    }


def _dark_colors() -> dict:
    return {
        "sidebar_bg": "#252525",
        "section_label": "#8b929e",
        "active_text": "#6daeff",
        "active_bg": ft.Colors.with_opacity(0.12, "#6daeff"),
        "default_text": "#e5e2e1",
        "hover_bg": ft.Colors.with_opacity(0.06, "#ffffff"),
    }


def _section_header(node: NavNode, colors: dict) -> ft.Control:
    return ft.Container(
        content=ft.Text(
            node.title.upper(),
            size=11,
            weight=ft.FontWeight.W_600,
            color=colors["section_label"],
        ),
        padding=ft.padding.only(left=8, right=8, top=20, bottom=4),
    )


def _page_item(
    title: str,
    slug: str,
    active_slug: str,
    on_navigate,
    colors: dict,
    indent: bool,
) -> ft.Control:
    is_active = active_slug == slug
    return ft.Container(
        content=ft.Text(
            title,
            size=13,
            color=colors["active_text"] if is_active else colors["default_text"],
            weight=ft.FontWeight.W_500 if is_active else ft.FontWeight.NORMAL,
        ),
        padding=ft.padding.only(left=8 + (12 if indent else 0), right=8, top=7, bottom=7),
        bgcolor=colors["active_bg"] if is_active else None,
        border_radius=6,
        on_click=lambda e, s=slug: on_navigate(s),
        ink=True,
    )
