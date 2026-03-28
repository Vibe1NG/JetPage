import os

import flet as ft

from jetpage.config import HOST, PORT
from jetpage.export.pdf_server import pdf_server
from jetpage.ui.app_shell import build_app


def main() -> None:
    pdf_server.start()

    # Get assets directory relative to this script
    assets_path = os.path.join(os.path.dirname(__file__), "assets")

    ft.app(
        target=build_app,
        host=HOST,
        port=PORT,
        view=ft.AppView.WEB_BROWSER,
        assets_dir=assets_path,
    )


if __name__ == "__main__":
    main()
