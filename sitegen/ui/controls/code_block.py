"""Custom code block widget with copy-to-clipboard button."""

import flet as ft


def build_code_block(language: str, code: str, page: ft.Page, dark: bool = False) -> ft.Control:
    bg = ft.Colors.GREY_900 if dark else ft.Colors.GREY_100
    border_color = ft.Colors.GREY_700 if dark else ft.Colors.GREY_300
    text_color = ft.Colors.GREY_100 if dark else ft.Colors.GREY_900
    label_color = ft.Colors.GREY_500

    def _copy(_e: ft.ControlEvent) -> None:
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

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(controls=header_controls, spacing=4),
                ft.Divider(height=1, color=border_color),
                ft.Text(
                    code.rstrip("\n"),
                    font_family="monospace",
                    size=12,
                    color=text_color,
                    selectable=True,
                    no_wrap=False,
                ),
            ],
            spacing=4,
            tight=True,
        ),
        bgcolor=bg,
        border=ft.border.all(1, border_color),
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        margin=ft.margin.symmetric(vertical=8),
    )
