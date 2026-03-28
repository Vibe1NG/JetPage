"""Breadcrumb and prev/next navigation controls."""

import flet as ft

from jetpage.core.navigation import PageLink

# Design tokens
_SECONDARY = "#0057c0"
_SECONDARY_DARK = "#6daeff"

# surface_container_high — raised card bg for prev/next
_CARD_BG_LIGHT = "#ebe7e7"
_CARD_BG_DARK = "#2b2b2b"

_ON_SURFACE_VAR_LIGHT = "#414754"
_ON_SURFACE_VAR_DARK = "#b0b8c8"
_ON_SURFACE_LIGHT = "#1c1b1b"
_ON_SURFACE_DARK = "#e5e2e1"


def build_breadcrumb(crumbs: list[PageLink], on_navigate, dark: bool = False) -> ft.Control:
    secondary = _SECONDARY_DARK if dark else _SECONDARY
    label_color = _ON_SURFACE_VAR_DARK if dark else _ON_SURFACE_VAR_LIGHT
    sep_color = _ON_SURFACE_VAR_DARK if dark else "#9ca3af"

    if not crumbs:
        return ft.Container(height=0)

    controls = []
    for i, crumb in enumerate(crumbs):
        if i > 0:
            controls.append(ft.Text("/", color=sep_color, size=12))
        is_last = i == len(crumbs) - 1
        controls.append(
            ft.TextButton(
                content=ft.Text(
                    crumb.title,
                    size=12,
                    color=label_color if is_last else secondary,
                    weight=ft.FontWeight.NORMAL,
                ),
                style=ft.ButtonStyle(
                    padding=ft.padding.symmetric(horizontal=4, vertical=0),
                    overlay_color=ft.Colors.with_opacity(0.06, secondary),
                ),
                on_click=(lambda _, s=crumb.slug: on_navigate(s)) if not is_last else None,
                disabled=is_last,
            )
        )
    return ft.Container(
        content=ft.Row(controls=controls, spacing=0),
        padding=ft.padding.only(bottom=8),
    )


def build_prev_next_bar(
    prev: PageLink | None,
    next_: PageLink | None,
    on_navigate,
    dark: bool = False,
) -> ft.Control:
    card_bg = _CARD_BG_DARK if dark else _CARD_BG_LIGHT
    text_color = _ON_SURFACE_DARK if dark else _ON_SURFACE_LIGHT
    label_color = _ON_SURFACE_VAR_DARK if dark else _ON_SURFACE_VAR_LIGHT

    controls = []
    if prev:
        controls.append(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("← Previous", size=11, color=label_color),
                        ft.Text(
                            prev.title,
                            size=13,
                            weight=ft.FontWeight.W_500,
                            color=text_color,
                        ),
                    ],
                    spacing=2,
                    tight=True,
                ),
                bgcolor=card_bg,
                border_radius=8,
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
                on_click=lambda _, s=prev.slug: on_navigate(s),
                ink=True,
            )
        )
    if prev and next_:
        controls.append(ft.Container(expand=True))
    if next_:
        controls.append(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Next →",
                            size=11,
                            color=label_color,
                            text_align=ft.TextAlign.RIGHT,
                        ),
                        ft.Text(
                            next_.title,
                            size=13,
                            weight=ft.FontWeight.W_500,
                            color=text_color,
                            text_align=ft.TextAlign.RIGHT,
                        ),
                    ],
                    spacing=2,
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.END,
                ),
                bgcolor=card_bg,
                border_radius=8,
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
                on_click=lambda _, s=next_.slug: on_navigate(s),
                ink=True,
            )
        )
    if not controls:
        return ft.Container(height=0)
    return ft.Container(
        content=ft.Row(controls=controls, expand=True),
        padding=ft.padding.only(top=32),
    )
