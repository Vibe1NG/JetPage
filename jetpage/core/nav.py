import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class NavNode:
    title: str
    slug: str
    is_section: bool
    document_id: str | None = None
    children: list["NavNode"] = field(default_factory=list)


@dataclass
class Document:
    id: str
    title: str
    description: str
    root: str
    color: str


@dataclass
class NavTree:
    site: dict
    documents: list[Document]
    nodes: list[NavNode]

    def find_document(self, doc_id: str) -> Document | None:
        return next((d for d in self.documents if d.id == doc_id), None)


def load_nav_tree(content_dir: Path) -> NavTree:
    """Read all _meta.json files and assemble the full navigation tree."""
    meta_path = content_dir / "_meta.json"
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)

    site = meta.get("site", {})

    documents = [
        Document(
            id=d["id"],
            title=d["title"],
            description=d.get("description", ""),
            root=d["root"],
            color=d.get("color", "#4A90D9"),
        )
        for d in meta.get("documents", [])
    ]

    nodes: list[NavNode] = []
    for entry in meta.get("nav", []):
        if entry["type"] == "page":
            nodes.append(
                NavNode(
                    title=entry["title"],
                    slug=entry["slug"],
                    is_section=False,
                )
            )
        elif entry["type"] == "section":
            children = _load_section(content_dir, entry["slug"], entry.get("document"))
            nodes.append(
                NavNode(
                    title=entry["title"],
                    slug=entry["slug"],
                    is_section=True,
                    document_id=entry.get("document"),
                    children=children,
                )
            )

    return NavTree(site=site, documents=documents, nodes=nodes)


def _load_section(content_dir: Path, section_slug: str, document_id: str | None) -> list[NavNode]:
    meta_path = content_dir / section_slug / "_meta.json"
    if not meta_path.exists():
        return []

    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)

    return [
        NavNode(
            title=item["title"],
            slug=f"{section_slug}/{item['slug']}",
            is_section=False,
            document_id=document_id,
        )
        for item in meta.get("order", [])
    ]
