import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from jetpage.core.nav import Document, GitSource
from jetpage.core.sync import sync_git_docs
import jetpage.core.sync


def test_sync_git_docs_clones_new_repo(tmp_path):
    jetpage.core.sync._SYNCED = False

    content_dir = tmp_path / "docs"
    content_dir.mkdir()

    docs = [
        Document(
            id="ext",
            title="External",
            description="",
            root="ext",
            color="",
            git=GitSource(url="https://github.com/org/repo.git"),
        )
    ]

    with patch("subprocess.run") as mock_run:
        sync_git_docs(docs, content_dir)

        # Verify clone was called
        expected_target = content_dir / ".jetpage" / "external" / "ext"
        mock_run.assert_any_call(
            ["git", "clone", "--depth", "1", "https://github.com/org/repo.git", str(expected_target)],
            check=True,
            timeout=60,
        )


def test_sync_git_docs_updates_existing_repo(tmp_path):
    jetpage.core.sync._SYNCED = False

    content_dir = tmp_path / "docs"
    external_dir = content_dir / ".jetpage" / "external" / "ext"
    external_dir.mkdir(parents=True)

    docs = [
        Document(
            id="ext",
            title="External",
            description="",
            root="ext",
            color="",
            git=GitSource(url="https://github.com/org/repo.git"),
        )
    ]

    with patch("subprocess.run") as mock_run:
        sync_git_docs(docs, content_dir)

        # Verify fetch and reset were called
        mock_run.assert_any_call(["git", "fetch", "--depth", "1", "origin"], cwd=external_dir, check=True, timeout=60)
        mock_run.assert_any_call(["git", "reset", "--hard", "FETCH_HEAD"], cwd=external_dir, check=True, timeout=60)


def test_sync_git_docs_cleans_up_stale_files_and_dirs(tmp_path):
    jetpage.core.sync._SYNCED = False

    content_dir = tmp_path / "docs"
    external_dir = content_dir / ".jetpage" / "external"
    external_dir.mkdir(parents=True)
    (external_dir / "stale_dir").mkdir()
    (external_dir / "stale_file.txt").write_text("dummy content")
    (external_dir / "active").mkdir()

    docs = [
        Document(
            id="active",
            title="Active",
            description="",
            root="active",
            color="",
            git=GitSource(url="https://github.com/org/repo.git"),
        )
    ]

    with patch("subprocess.run"):
        sync_git_docs(docs, content_dir)

    assert not (external_dir / "stale_dir").exists()
    assert not (external_dir / "stale_file.txt").exists()
    assert (external_dir / "active").exists()


def test_sync_git_docs_global_guard(tmp_path):
    jetpage.core.sync._SYNCED = False

    content_dir = tmp_path / "docs"
    content_dir.mkdir()

    docs = [
        Document(
            id="ext",
            title="External",
            description="",
            root="ext",
            color="",
            git=GitSource(url="https://github.com/org/repo.git"),
        )
    ]

    with patch("subprocess.run") as mock_run:
        sync_git_docs(docs, content_dir)
        assert mock_run.call_count == 1

        # Second call should be a no-op due to _SYNCED
        sync_git_docs(docs, content_dir)
        assert mock_run.call_count == 1
