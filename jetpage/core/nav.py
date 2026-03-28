import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class NavNode:
    """A node in the navigation tree, representing either a single page or a section.

    Attributes:
        title: The display title for the node.
        slug: The URL-friendly identifier for the node.
        is_section: Whether this node contains child nodes.
        document_id: Optional ID of the document this node belongs to.
        children: A list of child NavNodes if this is a section.
    """

    title: str
    slug: str
    is_section: bool
    document_id: str | None = None
    children: list["NavNode"] = field(default_factory=list)


@dataclass
class GitSource:
    """Configuration for syncing documentation from a Git repository.

    Attributes:
        url: The URL of the Git repository.
        path: Optional subpath within the repository where docs are located.
        tag: Optional branch, tag, or commit hash to sync.
    """

    url: str
    path: str | None = None
    tag: str | None = None


@dataclass
class Document:
    """A documentation set, which can be local or synced from a remote source.

    Attributes:
        id: Unique identifier for the document.
        title: Display title for the document.
        description: Brief description of the document's content.
        root: Relative path to the document's root directory.
        color: Primary brand color for the document.
        git: Optional Git source configuration for remote syncing.
        effective_root: The actual path on disk where documents are stored.
    """

    id: str
    title: str
    description: str
    root: str
    color: str
    git: GitSource | None = None
    effective_root: Path | None = None


@dataclass
class NavTree:
    """The complete navigation structure for the site.

    Attributes:
        site: Global site configuration.
        documents: List of all available documentation sets.
        nodes: Top-level navigation nodes.
    """

    site: dict
    documents: list[Document]
    nodes: list[NavNode]

    def find_document(self, doc_id: str) -> Document | None:
        return next((d for d in self.documents if d.id == doc_id), None)


def load_nav_tree(content_dir: Path) -> NavTree:
    """Read all _meta.json files and assemble the full navigation tree.

    Args:
        content_dir: The base directory where documentation content is stored.

    Returns:
        A complete NavTree structure containing site config and all documents.
    """
    meta_path = content_dir / "_meta.json"
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)

    site = meta.get("site", {})

    documents = []
    for d in meta.get("documents", []):
        git_data = d.get("git")
        git_source = None
        if git_data:
            git_source = GitSource(
                url=git_data.get("url"),
                path=git_data.get("path"),
                tag=git_data.get("tag"),
            )

        documents.append(
            Document(
                id=d["id"],
                title=d["title"],
                description=d.get("description", ""),
                root=d["root"],
                color=d.get("color", "#4A90D9"),
                git=git_source,
            )
        )

    # Step 1: Integrate sync and calculate effective_root
    from jetpage.core.sync import sync_git_docs

    sync_git_docs(documents, content_dir)

    for doc in documents:
        if doc.git:
            # Effective root is the directory containing the content within the clone
            doc.effective_root = content_dir / ".jetpage" / "external" / doc.id / (doc.git.path or "")
        else:
            # For local docs, effective_root is the document's specific root folder
            doc.effective_root = content_dir / doc.root

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
            doc_id = entry.get("document")
            doc = next((d for d in documents if d.id == doc_id), None) if doc_id else None

            if doc and entry["slug"].startswith(doc.root):
                # If it belongs to a document and follows its prefix, find the section's directory within that document
                rel_path = entry["slug"].removeprefix(doc.root).lstrip("/")
                effective_section_root = doc.effective_root / rel_path
            else:
                # Fallback for pages not explicitly tied to a document root prefix, or no document
                effective_section_root = content_dir / entry["slug"]

            children = _load_section(effective_section_root, entry["slug"], doc_id)
            nodes.append(
                NavNode(
                    title=entry["title"],
                    slug=entry["slug"],
                    is_section=True,
                    document_id=doc_id,
                    children=children,
                )
            )

    return NavTree(site=site, documents=documents, nodes=nodes)


def _load_section(effective_root: Path, section_slug: str, document_id: str | None) -> list[NavNode]:
    """Load navigation nodes for a specific section from its _meta.json.

    Args:
        effective_root: The actual path on disk where this section's content is located.
        section_slug: The site-wide identifier for the section.
        document_id: Optional ID of the document this section belongs to.

    Returns:
        A list of NavNodes representing the pages and items in this section.
    """
    meta_path = effective_root / "_meta.json"
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
