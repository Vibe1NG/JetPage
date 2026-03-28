"""Custom code block widget with copy-to-clipboard button."""

from typing import Any

import flet as ft

# Design tokens
_LIGHT_BG = "#e5e2e1"  # surface_container_highest — "pops" off the surface page
_DARK_BG = "#2b2b2b"  # inverse_surface-ish — high contrast in dark mode
_LABEL_LIGHT = "#6b7280"
_LABEL_DARK = "#8b929e"


def build_code_block(language: str, code: str, page: ft.Page, dark: bool = False) -> ft.Control:
    bg_color = _DARK_BG if dark else _LIGHT_BG
    label_color = _LABEL_DARK if dark else _LABEL_LIGHT

    def _copy(_e: Any) -> None:
        async def _do_copy(text: str = code) -> None:
            await ft.Clipboard().set(text)

        page.run_task(_do_copy)

    copy_icon = ft.IconButton(
        icon=ft.Icons.CONTENT_COPY,
        icon_size=16,
        icon_color=label_color,
        tooltip="Copy",
        style=ft.ButtonStyle(padding=ft.padding.all(4)),
        on_click=_copy,
    )

    header_controls: list[ft.Control] = []
    if language:
        header_controls.append(ft.Text(language, size=11, color=label_color, font_family="monospace"))
    header_controls.append(ft.Container(expand=True))
    header_controls.append(copy_icon)

    # Render the code as ft.Markdown to preserve Flet's built-in syntax highlighting
    fence = f"```{language}\n{code.rstrip()}\n```"
    code_md = ft.Markdown(
        value=fence,
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
        code_theme=ft.MarkdownCodeTheme.GITHUB if not dark else ft.MarkdownCodeTheme.MONOKAI,
        selectable=True,
    )

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(controls=header_controls, spacing=4),
                code_md,
            ],
            spacing=0,
            tight=True,
        ),
        bgcolor=bg_color,
        border_radius=8,
        padding=ft.padding.only(left=12, right=8, top=8, bottom=8),
        margin=ft.margin.symmetric(vertical=8),
    )
