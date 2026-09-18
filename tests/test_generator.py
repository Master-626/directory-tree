import pytest
from pathlib import Path
from directory_tree.generator import generate_tree, export_markdown


def test_generate_tree(tmp_path):
    """Test directory tree generation."""
    # Create test structure
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir2").mkdir()
    (tmp_path / "dir1" / "file1.txt").write_text("test")

    tree = generate_tree(str(tmp_path))
    assert "dir1" in tree
    assert "dir2" in tree
    assert "file1.txt" in tree


def test_max_depth(tmp_path):
    """Test max depth limit."""
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "b").mkdir()
    (tmp_path / "a" / "b" / "c").mkdir()

    tree = generate_tree(str(tmp_path), max_depth=1)
    assert "a" in tree
    assert "b" not in tree


def test_export_markdown(tmp_path):
    """Test Markdown export."""
    tree = generate_tree(str(tmp_path))
    output = tmp_path / "tree.md"
    export_markdown(tree, str(output))
    assert output.exists()
    content = output.read_text()
    assert "```" in content
