from pathlib import Path

from sitegen.content.image_processor import embed_images


def load_page(path: Path | str) -> str:
    """Read and return the raw markdown content of a page file.

    Relative image references are converted to base64 data URIs so that they
    render correctly in both the Flet viewer (ft.Markdown) and the Playwright
    PDF export path without requiring a static file server.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    return embed_images(text, path)
