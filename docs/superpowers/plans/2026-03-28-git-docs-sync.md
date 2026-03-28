# Git Documentation Syncing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow JetPage to pull documentation from external Git repositories (optionally with a tag) and serve them as local content.

**Architecture:** Sync repositories into `content/.jetpage/external/<doc_id>` on startup using `git` CLI. Calculate an `effective_root` for each document and use it during page resolution and navigation loading.

**Tech Stack:** Python, `subprocess` (for Git), `pathlib`, Flet (existing).

---

### Task 1: Update Data Models

**Files:**
- Modify: `jetpage/core/nav.py`

- [ ] **Step 1: Update `GitSource` and `Document` dataclasses**

Add `tag` to `GitSource` and `effective_root` to `Document`.

```python
@dataclass
class GitSource:
    url: str
    path: str | None = None
    tag: str | None = None

@dataclass
class Document:
    id: str
    title: str
    description: str
    root: str
    color: str
    git: GitSource | None = None
    effective_root: Path | None = None
```

- [ ] **Step 2: Update `load_nav_tree` to parse `git` source and `tag`**

Update the logic in `load_nav_tree` to handle the optional `git` dictionary when creating the `documents` list.

- [ ] **Step 3: Commit**

```bash
git add jetpage/core/nav.py
git commit -m "feat: update Document model for Git support"
```

---

### Task 2: Create Sync Module

**Files:**
- Create: `jetpage/core/sync.py`
- Test: `tests/test_sync.py`

- [ ] **Step 1: Write failing test for sync logic**

Mock `subprocess.run` to verify `git clone` and `git fetch/reset` commands.

- [ ] **Step 2: Implement `sync_git_docs`**

```python
import subprocess
import logging
import shutil
from pathlib import Path
from jetpage.core.nav import Document

logger = logging.getLogger(__name__)

_SYNCED = False

def sync_git_docs(documents: list[Document], content_dir: Path) -> None:
    global _SYNCED
    if _SYNCED:
        return
        
    external_dir = content_dir / ".jetpage" / "external"
    external_dir.mkdir(parents=True, exist_ok=True)
    
    active_ids = {d.id for d in documents if d.git}
    
    # Cleanup stale
    if external_dir.exists():
        for d in external_dir.iterdir():
            if d.is_dir() and d.name not in active_ids:
                shutil.rmtree(d)

    for doc in documents:
        if not doc.git:
            continue
            
        target = external_dir / doc.id
        tag = doc.git.tag # None or string
        
        try:
            if not target.exists():
                # Clone
                cmd = ["git", "clone", "--depth", "1"]
                if tag:
                    cmd.extend(["--branch", tag])
                cmd.extend([doc.git.url, str(target)])
                subprocess.run(cmd, check=True, timeout=60)
            else:
                # Update
                fetch_cmd = ["git", "fetch", "--depth", "1", "origin"]
                if tag:
                    fetch_cmd.append(tag)
                subprocess.run(fetch_cmd, cwd=target, check=True, timeout=60)
                subprocess.run(["git", "reset", "--hard", "FETCH_HEAD"], cwd=target, check=True, timeout=60)
        except Exception as e:
            logger.error(f"Failed to sync {doc.id}: {e}")
            
    _SYNCED = True
```

- [ ] **Step 3: Run tests and verify**

- [ ] **Step 4: Commit**

```bash
git add jetpage/core/sync.py tests/test_sync.py
git commit -m "feat: add git sync logic with global guard"
```

---

### Task 3: Integrate Sync and Path Redirection

**Files:**
- Modify: `jetpage/core/nav.py`
- Modify: `jetpage/core/page_resolver.py`
- Modify: `jetpage/ui/app_shell.py`

- [ ] **Step 1: Integrate `sync_git_docs` into `load_nav_tree`**

In `jetpage/core/nav.py`, `load_nav_tree` must sync *after* parsing the `documents` list from `_meta.json` but *before* the `nav` loop begins.

```python
# In load_nav_tree(content_dir):
# ... parse documents list ...
from jetpage.core.sync import sync_git_docs
sync_git_docs(documents, content_dir)

# Now calculate effective_root for each doc
for doc in documents:
    if doc.git:
        # Effective root is the directory containing the content within the clone
        doc.effective_root = content_dir / ".jetpage" / "external" / doc.id / (doc.git.path or "")
    else:
        # For local docs, effective_root is the document's specific root folder
        doc.effective_root = content_dir / doc.root
# ... proceed with nav loop ...
```

- [ ] **Step 2: Update `_load_section` to use `effective_root`**

Update `_load_section` signature: `def _load_section(effective_root: Path, section_slug: str, document_id: str | None) -> list[NavNode]`.

In `load_nav_tree`, when calling `_load_section`, find the document by `entry.get("document")` and pass its `effective_root`.
Inside `_load_section`, it should look for `effective_root / "_meta.json"` (since `section_slug` is already part of the path if nested, but usually `_load_section` is called per-section).
*Wait, let's look at `nav.py` again:* `meta_path = content_dir / section_slug / "_meta.json"`.
So if `effective_root` is the doc's root (e.g. `content/blog`), it should be `effective_root / "_meta.json"` if we are loading the root of that doc, OR if `section_slug` is the section name, it should be `effective_root / "_meta.json"` if the section *is* the doc root.

Actually, the current `nav.py` does: `meta_path = content_dir / section_slug / "_meta.json"`.
If `section_slug` is "getting-started", it looks in `content/getting-started/_meta.json`.
So if `effective_root` is `content/getting-started`, `_load_section` should just use `effective_root / "_meta.json"`.

- [ ] **Step 3: Update `page_resolver.py` and `app_shell.py`**

Update `resolve(slug: str, content_dir: Path)` to use the provided `content_dir` correctly.
In `app_shell.py`, `load_route` will find the `Document` for the `slug`.
If the document exists, calculate a relative slug: `rel_slug = slug.removeprefix(doc.root).lstrip("/") or "index"`.
Then call `resolve(rel_slug, doc.effective_root)`.

- [ ] **Step 4: Add `.jetpage/` to `.gitignore`**

- [ ] **Step 5: Final Verification**

Run the app with a sample external repo in `_meta.json`.

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "feat: integrate git sync and dynamic path resolution"
```
