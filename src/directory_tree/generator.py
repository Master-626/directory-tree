"""Core directory tree generation logic."""

import fnmatch
from pathlib import Path
from typing import FrozenSet, Optional, Sequence, Tuple

# Names skipped when the caller does not pass ignore_patterns.
# Matched as exact names, so ".git" does not hide ".github".
DEFAULT_IGNORE_PATTERNS = (".git", "__pycache__", ".venv", "node_modules")

Inode = Tuple[int, int]


def should_ignore(path: Path, ignore_patterns: Sequence[str]) -> bool:
    """Return True if ``path.name`` matches any glob ignore pattern.

    Patterns use :mod:`fnmatch` syntax and are compared to the entry name
    only, case-sensitively. ``.git`` matches ``.git`` and does not match
    ``.github`` or ``.gitignore``.
    """
    name = path.name
    for pattern in ignore_patterns:
        if fnmatch.fnmatchcase(name, pattern):
            return True
    return False


def _format_size(num_bytes: int) -> str:
    """Format a byte count with 1024-based units (B, KB, MB, ...)."""
    size = float(num_bytes)
    units = ("B", "KB", "MB", "GB", "TB", "PB")
    for unit in units[:-1]:
        if size < 1024:
            if unit == "B":
                return f"{int(size)} B"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} {units[-1]}"


def _inode(path: Path) -> Optional[Inode]:
    try:
        stat_result = path.stat()
    except OSError:
        return None
    return stat_result.st_dev, stat_result.st_ino


def _root_heading(root: Path) -> str:
    """Return the root line, including its trailing slash.

    ``Path(".").name`` is empty, which used to render as ``/``. Use the
    resolved directory name in that case. The filesystem root stays ``/``.
    """
    name = root.name or root.resolve().name
    if not name:
        return root.anchor or "/"
    return f"{name}/"


def _size_suffix(entry: Path) -> str:
    try:
        size = entry.stat().st_size
    except OSError:
        return " (?)"
    return f" ({_format_size(size)})"


def generate_tree(
    root_path: str,
    max_depth: Optional[int] = None,
    ignore_patterns: Optional[Sequence[str]] = None,
    show_files: bool = True,
    show_sizes: bool = False,
) -> str:
    """Generate a directory tree string.

    ``max_depth`` counts levels below the root. ``1`` shows the root's
    immediate children, and ``0`` shows only the root line. ``None`` walks
    the whole tree.

    ``ignore_patterns`` are case-sensitive globs matched against each entry
    name. ``None`` uses :data:`DEFAULT_IGNORE_PATTERNS`. Pass an empty
    sequence to disable ignoring. Patterns replace that default; they are
    not added to it.

    ``show_sizes`` appends a human-readable size to each regular file.
    A symlink that points at an ancestor is marked ``[cycle]`` and is not
    followed. A nested directory that cannot be read stays in the tree with
    an ``[error: ...]`` child. If the root itself cannot be listed, the
    error is raised.

    Raises:
        FileNotFoundError: ``root_path`` does not exist.
        NotADirectoryError: ``root_path`` is not a directory.
        ValueError: ``max_depth`` is negative.
        TypeError: ``max_depth`` is not an integer or ``None``.
        OSError: the root directory cannot be listed.
    """
    if max_depth is not None and (
        isinstance(max_depth, bool) or not isinstance(max_depth, int)
    ):
        raise TypeError("max_depth must be an integer or None")
    if max_depth is not None and max_depth < 0:
        raise ValueError("max_depth must be zero or a positive integer")

    if ignore_patterns is None:
        ignore_patterns = DEFAULT_IGNORE_PATTERNS

    root = Path(root_path).expanduser()
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    lines = [_root_heading(root)]

    def _walk(
        dir_path: Path,
        prefix: str,
        depth: int,
        ancestors: FrozenSet[Inode],
    ) -> None:
        if max_depth is not None and depth > max_depth:
            return

        ident = _inode(dir_path)
        if ident is not None:
            if ident in ancestors:
                return
            ancestors = ancestors | {ident}

        try:
            entries = list(dir_path.iterdir())
        except OSError as exc:
            if depth == 1:
                raise
            reason = exc.strerror or exc.__class__.__name__
            lines.append(f"{prefix}└── [error: {reason}]")
            return

        visible = [
            entry for entry in entries if not should_ignore(entry, ignore_patterns)
        ]
        if not show_files:
            visible = [entry for entry in visible if entry.is_dir()]
        visible.sort(key=lambda entry: (entry.is_file(), entry.name))

        for index, entry in enumerate(visible):
            is_last = index == len(visible) - 1
            connector = "└── " if is_last else "├── "
            cycle = False
            if entry.is_dir():
                child_ident = _inode(entry)
                cycle = child_ident is not None and child_ident in ancestors

            label = entry.name
            if show_sizes and entry.is_file():
                label += _size_suffix(entry)
            if cycle:
                label += " [cycle]"
            lines.append(f"{prefix}{connector}{label}")

            if entry.is_dir() and not cycle:
                extension = "    " if is_last else "│   "
                _walk(entry, prefix + extension, depth + 1, ancestors)

    _walk(root, "", 1, frozenset())
    return "\n".join(lines)


def export_markdown(
    tree: str,
    output_path: str,
    title: str = "Directory Structure",
) -> None:
    """Write ``tree`` to a Markdown file as a fenced code block.

    The fence is lengthened when ``tree`` already contains a three-backtick
    fence, so a name that includes ``` does not close the block early. The
    parent directory of ``output_path`` must already exist.
    """
    path = Path(output_path)
    parent = path.parent
    if not parent.exists():
        raise FileNotFoundError(f"Output directory not found: {parent}")

    fence = "```"
    while fence in tree:
        fence += "`"
    content = f"# {title}\n\n{fence}\n{tree}\n{fence}\n"
    path.write_text(content, encoding="utf-8")
