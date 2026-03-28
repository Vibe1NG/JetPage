# Design Spec: Git Documentation Syncing

This specification outlines the implementation of a feature that allows JetPage to pull documentation from external Git repositories and serve them as if they were local content.

## 1. Problem Definition
Currently, JetPage only supports content located within the local `content/` directory. For many projects, documentation is hosted alongside the source code in separate repositories. Manually copying this content or using submodules is cumbersome.

## 2. Proposed Solution
Add an optional `git` configuration for each document in `content/_meta.json`. JetPage will automatically sync (clone/pull) these repositories on startup into a local cache directory (`content/.jetpage/external/`) and serve the content from there.

## 3. Data Model Changes

### 3.1 `_meta.json` Schema
The root `content/_meta.json`'s `documents` array will support an optional `git` object:

```json
{
  "documents": [
    {
      "id": "my-external-docs",
      "title": "My External Docs",
      "root": "my-external-docs",
      "git": {
        "url": "https://github.com/user/repo.git",
        "path": "docs",
        "tag": "v1.0.0"
      }
    }
  ]
}
```

- `url`: The public Git repository URL.
- `path`: (Optional) A subdirectory within the repository to use as the content root.
- `tag`: (Optional) A specific tag or branch to checkout. Defaults to the repository's default branch if omitted.

### 3.2 `Document` Dataclass
Update `jetpage/core/nav.py`:

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

The `effective_root` will be calculated during `load_nav_tree` and point to either the standard `CONTENT_DIR / root` or the synced Git path.

## 4. Sync Logic (`jetpage/core/sync.py`)

A new module will handle the synchronization logic using the `git` CLI (via `subprocess`).

### 4.1 `sync_git_docs(documents: list[Document], content_dir: Path)`
1. Iterate through `documents`.
2. For each document with `git` source:
   - Target path: `content_dir / ".jetpage" / "external" / doc.id`
   - If path doesn't exist: `git clone --depth 1 --branch <tag or default> <url> <target_path>`
   - If path exists: `git fetch --depth 1 origin <tag or default> && git reset --hard FETCH_HEAD`
3. Implement a basic timeout (e.g., 30s) for Git commands.
4. Log successes and warnings.

### 4.2 Sync Timing
To avoid redundant syncs for every user session (since `build_app` runs per visitor), the sync logic will be called once in `jetpage/main.py` before the Flet app starts, or guarded by a global "already synced" flag in `jetpage/core/sync.py`.

## 5. Path Redirection

### 5.1 `NavTree` Construction
In `jetpage/core/nav.py`, `load_nav_tree` will:
1. Parse the root `_meta.json`.
2. Calculate the `effective_root` for each document:
   - Standard: `CONTENT_DIR / root`
   - Git: `CONTENT_DIR / ".jetpage" / "external" / doc_id / doc.git.path`
3. `_load_section` will use the `effective_root` of the associated document.

### 5.2 `page_resolver.resolve`
Update `resolve(slug, content_dir)` to allow passing the `effective_root` directly. The caller in `app_shell.py` will look up the document for the current slug, and pass its `effective_root` to `resolve`.


### 5.3 Asset Resolution
Since `jetpage/content/image_processor.py` embeds relative image paths as base64 data URIs based on the `page_path`, assets within the cloned Git repository will work automatically as long as they are referenced relatively in the markdown files.

## 6. Implementation Plan Highlights
1. Create `jetpage/core/sync.py`.
2. Update `Document` model in `jetpage/core/nav.py`.
3. Integrate `sync_git_docs` into `load_nav_tree`.
   - Implement `git fetch --depth 1 && git reset --hard origin/HEAD` for stability.
   - Implement stale cache cleanup (remove dirs in `.jetpage/external/` not present in current `_meta.json`).
4. Update `_load_section` and `resolve` logic to support dynamic roots.
5. Add `.jetpage/` to `.gitignore` (if not already there).

## 7. Security & Limitations
- **Public Only:** No support for private repositories (no SSH keys or tokens) in the first iteration.
- **Git Required:** The host must have the `git` binary installed.
- **No Periodic Refresh:** Sync only happens on startup.

## 8. Error Handling
- If `git clone/pull` fails, log an error and use the existing local cache if available.
- If no cache exists and sync fails, the document will show a "Page Not Found" or a custom error message.
