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
        tag = doc.git.tag  # None or string

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
