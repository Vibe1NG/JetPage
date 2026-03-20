"""In-page table of contents panel."""

import flet as ft

_PANEL_WIDTH     = 200
_INDENT_PER_LEVEL = 10


def build_toc_panel(toc_tokens: list[dict], dark: bool = False, on_anchor_click=None) -> ft.Container | None:
    """Build the in-page TOC panel from toc_tokens.

    Returns None if there are no sub-headings worth showing (h2+).
    """
    header_color  = "#8b929e" if dark else "#6b7280"
    item_color    = "#c5c9d4" if dark else "#414754"   # on_surface_variant
    active_color  = "#6daeff" if dark else "#0057c0"   # secondary

    items: list[ft.Control] = []
    _collect(toc_tokens, items, min_level=2, item_color=item_color,
             active_color=active_color, on_anchor_click=on_anchor_click)

    if not items:
        return None

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "On this page",
                    size=11,
                    weight=ft.FontWeight.W_600,
                    color=header_color,
                ),
                ft.Container(height=8),
                *items,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        ),
        width=_PANEL_WIDTH,
        padding=ft.padding.only(left=16, right=8, top=20, bottom=16),
    )


def _collect(
    tokens: list[dict],
    items: list[ft.Control],
    min_level: int,
    item_color,
    active_color,
    on_anchor_click=None,
) -> None:
    for token in tokens:
        level = token.get("level", 1)
        if level >= min_level:
            indent = (level - min_level) * _INDENT_PER_LEVEL
            anchor_id = token.get("id", "")
            clickable = bool(on_anchor_click and anchor_id)
            items.append(
                ft.Container(
                    content=ft.Text(
                        token.get("name", ""),
                        size=13,
                        color=active_color if (level == min_level) else item_color,
                        no_wrap=True,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    padding=ft.padding.only(left=indent, top=5, bottom=5),
                    on_click=(lambda _, a=anchor_id: on_anchor_click(a)) if clickable else None,
                    ink=clickable,
                )
            )
        _collect(token.get("children", []), items, min_level, item_color,
                 active_color, on_anchor_click)
