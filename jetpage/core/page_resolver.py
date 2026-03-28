from pathlib import Path


def resolve(slug: str, content_dir: Path) -> Path | None:
    """Map a URL slug to a .md file path, or None if not found.

    Resolution order:
      1. <slug>.md              (e.g. "index" -> content/index.md)
      2. <slug>/index.md        (e.g. "getting-started" -> content/getting-started/index.md)
    """
    slug = slug.strip("/") or "index"

    candidate = content_dir / f"{slug}.md"
    if candidate.exists():
        return candidate

    candidate = content_dir / slug / "index.md"
    if candidate.exists():
        return candidate

    return None
