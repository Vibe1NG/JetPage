"""Breadcrumb and prev/next navigation controls."""

import flet as ft

from sitegen.core.navigation import PageLink


def build_breadcrumb(crumbs: list[PageLink], on_navigate, dark: bool = False) -> ft.Control:
    text_color = ft.Colors.GREY_300 if dark else ft.Colors.GREY_600
    sep_color = ft.Colors.GREY_500 if dark else ft.Colors.GREY_400
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
                    color=text_color if is_last else ft.Colors.BLUE_400,
                ),
                style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=4, vertical=0)),
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
    btn_color = ft.Colors.GREY_800 if dark else ft.Colors.GREY_100
    text_color = ft.Colors.GREY_200 if dark else ft.Colors.GREY_800
    controls = []
    if prev:
        controls.append(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("← Previous", size=11, color=ft.Colors.GREY_500),
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
                bgcolor=btn_color,
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
                            color=ft.Colors.GREY_500,
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
                bgcolor=btn_color,
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
