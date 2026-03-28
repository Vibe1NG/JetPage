"""Convert relative image src references in markdown to base64 data URIs."""

import base64
import re
from pathlib import Path

_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def embed_images(markdown_text: str, page_path: Path) -> str:
    """Replace relative image paths with base64 data URIs."""

    def _replace(m: re.Match) -> str:
        alt, src = m.group(1), m.group(2)
        if src.startswith(("http://", "https://", "data:")):
            return m.group(0)
        img_path = (page_path.parent / src).resolve()
        if not img_path.exists():
            return m.group(0)
        ext = img_path.suffix.lower().lstrip(".")
        mime = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "svg": "image/svg+xml",
            "webp": "image/webp",
        }.get(ext, "image/png")
        data = base64.b64encode(img_path.read_bytes()).decode()
        return f"![{alt}](data:{mime};base64,{data})"

    return _IMG_RE.sub(_replace, markdown_text)
