from pathlib import Path

import pytest

from jetpage.core.nav import load_nav_tree

CONTENT_DIR = Path(__file__).parent.parent / "content"


@pytest.fixture(scope="session")
def content_dir() -> Path:
    return CONTENT_DIR


@pytest.fixture(scope="session")
def nav_tree(content_dir):
    return load_nav_tree(content_dir)
