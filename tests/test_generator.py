import os
from pathlib import Path

import pytest

from directory_tree.generator import (
    _format_size,
    export_markdown,
    generate_tree,
    should_ignore,
)


def _entry_names(tree):
    """Return each entry label, without the root heading or tree connectors."""
    return [line.split("── ")[-1] for line in tree.splitlines()[1:]]


def _has_entry(tree, name):
    return name in _entry_names(tree)


def _symlink(link, target):
    try:
        link.symlink_to(target, target_is_directory=target.is_dir())
    except OSError as exc:
        pytest.skip(f"symlinks are not available: {exc}")


def _deny_listing(directory):
    """Make ``directory`` unlistable, or skip when the OS will not enforce it."""
    directory.chmod(0)
    try:
        list(directory.iterdir())
    except OSError:
        return
    directory.chmod(0o755)
    pytest.skip("directory permissions are not enforced")


def test_generate_tree(tmp_path):
    """Test directory tree generation."""
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


def test_branch_connectors_and_sort_order(tmp_path):
    (tmp_path / "dir").mkdir()
    (tmp_path / "dir" / "nested.txt").write_text("n")
    (tmp_path / "B.txt").write_text("B")
    (tmp_path / "a.txt").write_text("a")

    tree = generate_tree(str(tmp_path), ignore_patterns=[])
    assert tree == (
        f"{tmp_path.name}/\n├── dir\n│   └── nested.txt\n├── B.txt\n└── a.txt"
    )


def test_max_depth_levels(tmp_path):
    (tmp_path / "a" / "b").mkdir(parents=True)
    (tmp_path / "a" / "b" / "c.txt").write_text("c")
    name = tmp_path.name

    assert generate_tree(str(tmp_path), max_depth=0, ignore_patterns=[]) == f"{name}/"
    assert generate_tree(str(tmp_path), max_depth=1, ignore_patterns=[]) == (
        f"{name}/\n└── a"
    )
    assert generate_tree(str(tmp_path), max_depth=2, ignore_patterns=[]) == (
        f"{name}/\n└── a\n    └── b"
    )
    assert "c.txt" in generate_tree(str(tmp_path), max_depth=3, ignore_patterns=[])


def test_max_depth_rejects_invalid_values(tmp_path):
    with pytest.raises(ValueError):
        generate_tree(str(tmp_path), max_depth=-1)
    with pytest.raises(TypeError):
        generate_tree(str(tmp_path), max_depth=1.5)
    with pytest.raises(TypeError):
        generate_tree(str(tmp_path), max_depth=True)


def test_dirs_only(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "f.txt").write_text("x")
    (tmp_path / "top.txt").write_text("x")
    (tmp_path / "empty").mkdir()

    tree = generate_tree(str(tmp_path), ignore_patterns=[], show_files=False)
    assert tree == f"{tmp_path.name}/\n├── empty\n└── sub"


def test_default_ignore_matches_names_not_substrings(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("c")
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "workflows").mkdir()
    (tmp_path / ".gitignore").write_text("*\n")
    (tmp_path / ".venv").mkdir()
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "pkg").mkdir()
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "my.gitconfig").write_text("x")
    (tmp_path / "not__pycache__x").mkdir()
    (tmp_path / "src").mkdir()

    tree = generate_tree(str(tmp_path))
    assert not _has_entry(tree, ".git")
    assert not _has_entry(tree, "config")
    assert not _has_entry(tree, ".venv")
    assert not _has_entry(tree, "node_modules")
    assert not _has_entry(tree, "pkg")
    assert not _has_entry(tree, "__pycache__")
    assert _has_entry(tree, ".github")
    assert _has_entry(tree, "workflows")
    assert _has_entry(tree, ".gitignore")
    assert _has_entry(tree, "my.gitconfig")
    assert _has_entry(tree, "not__pycache__x")
    assert _has_entry(tree, "src")


def test_ignore_glob_and_replacement(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "debug.log").write_text("d")
    (tmp_path / "notes.txt").write_text("n")
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "app.log").write_text("a")

    tree = generate_tree(str(tmp_path), ignore_patterns=["*.log"])
    assert _has_entry(tree, ".git")
    assert "debug.log" not in tree
    assert "app.log" not in tree
    assert "notes.txt" in tree
    assert _has_entry(tree, "logs")

    assert should_ignore(Path("a.pyc"), ["*.pyc"])
    assert not should_ignore(Path("a.py"), ["*.pyc"])
    assert not should_ignore(Path(".github"), [".git"])


def test_empty_ignore_list_disables_defaults(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "node_modules").mkdir()
    tree = generate_tree(str(tmp_path), ignore_patterns=[])
    assert _has_entry(tree, ".git")
    assert _has_entry(tree, "node_modules")


def test_root_is_listed_even_when_its_name_is_ignored(tmp_path):
    git = tmp_path / ".git"
    git.mkdir()
    (git / "config").write_text("x")
    tree = generate_tree(str(git))
    assert tree.splitlines()[0] == ".git/"
    assert "config" in tree


def test_current_directory_uses_real_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.txt").write_text("x")
    tree = generate_tree(".")
    assert tree.splitlines()[0] == f"{tmp_path.name}/"
    assert "a.txt" in tree


def test_filesystem_root_heading():
    assert generate_tree("/", max_depth=0) == "/"


def test_expanduser(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / "note.txt").write_text("n")
    tree = generate_tree("~")
    assert tree.splitlines()[0] == f"{tmp_path.name}/"
    assert "note.txt" in tree


def test_missing_directory(tmp_path):
    missing = tmp_path / "nope"
    with pytest.raises(FileNotFoundError, match="Directory not found"):
        generate_tree(str(missing))


def test_file_root(tmp_path):
    file = tmp_path / "a.txt"
    file.write_text("x")
    with pytest.raises(NotADirectoryError, match="Not a directory"):
        generate_tree(str(file))


def test_symlink_cycle_is_marked(tmp_path):
    (tmp_path / "file.txt").write_text("hi")
    _symlink(tmp_path / "loop", tmp_path)
    tree = generate_tree(str(tmp_path), ignore_patterns=[])
    assert tree == (f"{tmp_path.name}/\n├── loop [cycle]\n└── file.txt")


def test_mutual_directory_symlinks_stop(tmp_path):
    source = tmp_path / "a"
    other = tmp_path / "b"
    source.mkdir()
    other.mkdir()
    _symlink(source / "to_b", other)
    _symlink(other / "to_a", source)
    tree = generate_tree(str(tmp_path), ignore_patterns=[])
    assert tree == (
        f"{tmp_path.name}/\n"
        "├── a\n"
        "│   └── to_b\n"
        "│       └── to_a [cycle]\n"
        "└── b\n"
        "    └── to_a\n"
        "        └── to_b [cycle]"
    )


def test_symlink_to_sibling_is_followed(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    (real / "f.txt").write_text("z")
    _symlink(tmp_path / "link", real)
    tree = generate_tree(str(tmp_path), ignore_patterns=[])
    assert "[cycle]" not in tree
    assert tree.count("f.txt") == 2


def test_unreadable_child_does_not_abort(tmp_path):
    if getattr(os, "geteuid", lambda: 1)() == 0:
        pytest.skip("root ignores directory permissions")
    secret = tmp_path / "secret"
    secret.mkdir()
    (secret / "hidden.txt").write_text("nope")
    (tmp_path / "visible.txt").write_text("ok")
    _deny_listing(secret)
    try:
        tree = generate_tree(str(tmp_path), ignore_patterns=[])
    finally:
        secret.chmod(0o755)

    assert "visible.txt" in tree
    assert "hidden.txt" not in tree
    assert _has_entry(tree, "secret")
    assert any("[error:" in line for line in tree.splitlines())


def test_unreadable_root_raises(tmp_path):
    if getattr(os, "geteuid", lambda: 1)() == 0:
        pytest.skip("root ignores directory permissions")
    secret = tmp_path / "secret"
    secret.mkdir()
    (secret / "hidden.txt").write_text("nope")
    _deny_listing(secret)
    try:
        with pytest.raises(OSError):
            generate_tree(str(secret))
    finally:
        secret.chmod(0o755)


def test_show_sizes(tmp_path):
    (tmp_path / "empty.txt").write_bytes(b"")
    (tmp_path / "k.bin").write_bytes(b"x" * 1536)
    (tmp_path / "sub").mkdir()

    tree = generate_tree(str(tmp_path), ignore_patterns=[], show_sizes=True)
    assert "empty.txt (0 B)" in tree
    assert "k.bin (1.5 KB)" in tree
    assert "sub (" not in tree

    plain = generate_tree(str(tmp_path), ignore_patterns=[])
    assert "(0 B)" not in plain
    assert "(1.5 KB)" not in plain


def test_symlink_to_file_shows_target_size(tmp_path):
    target = tmp_path / "target.txt"
    target.write_bytes(b"abcd")
    _symlink(tmp_path / "link.txt", target)
    tree = generate_tree(str(tmp_path), ignore_patterns=[], show_sizes=True)
    assert "link.txt (4 B)" in tree
    assert "target.txt (4 B)" in tree


@pytest.mark.parametrize(
    ("num_bytes", "expected"),
    [
        (0, "0 B"),
        (1023, "1023 B"),
        (1024, "1.0 KB"),
        (1536, "1.5 KB"),
        (1024 * 1024, "1.0 MB"),
        (1024**5, "1.0 PB"),
        (1024**6, "1024.0 PB"),
    ],
)
def test_format_size(num_bytes, expected):
    assert _format_size(num_bytes) == expected


def test_unicode_names(tmp_path):
    folder = tmp_path / "文档"
    folder.mkdir()
    (folder / "说明.txt").write_text("你好", encoding="utf-8")
    tree = generate_tree(str(tmp_path), ignore_patterns=[])
    assert "文档" in tree
    assert "说明.txt" in tree


def test_export_markdown_contents(tmp_path):
    output = tmp_path / "tree.md"
    export_markdown("proj/\n└── a.txt", str(output), title="Demo")
    expected = "# Demo\n\n```\nproj/\n└── a.txt\n```\n"
    assert output.read_text(encoding="utf-8") == expected


def test_export_markdown_extends_fence(tmp_path):
    output = tmp_path / "out.md"
    export_markdown("```\nname/", str(output), title="Demo")
    assert output.read_text(encoding="utf-8") == "# Demo\n\n````\n```\nname/\n````\n"


def test_export_markdown_utf8(tmp_path):
    output = tmp_path / "tree.md"
    export_markdown("项目/\n└── 说明.txt", str(output), title="结构")
    text = output.read_text(encoding="utf-8")
    assert text.startswith("# 结构\n")
    assert "说明.txt" in text


def test_export_markdown_missing_parent(tmp_path):
    output = tmp_path / "missing" / "tree.md"
    with pytest.raises(FileNotFoundError, match="Output directory not found"):
        export_markdown("name/", str(output))
