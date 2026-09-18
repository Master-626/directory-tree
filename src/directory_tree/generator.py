"""
Core directory tree generation logic.
"""

from pathlib import Path
from typing import List, Optional


def should_ignore(path: Path, ignore_patterns: List[str]) -> bool:
    """Check if path matches any ignore pattern."""
    for pattern in ignore_patterns:
        if pattern in path.name:
            return True
    return False


def generate_tree(
    root_path: str,
    max_depth: Optional[int] = None,
    ignore_patterns: Optional[List[str]] = None,
    show_files: bool = True,
) -> str:
    """Generate a directory tree string."""
    if ignore_patterns is None:
        ignore_patterns = [".git", "__pycache__", ".venv", "node_modules"]

    root = Path(root_path)
    lines = [f"{root.name}/"]

    def _walk(dir_path: Path, prefix: str, depth: int):
        if max_depth is not None and depth > max_depth:
            return

        entries = sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name))

        # Filter ignored
        entries = [e for e in entries if not should_ignore(e, ignore_patterns)]

        if not show_files:
            entries = [e for e in entries if e.is_dir()]

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "

            lines.append(f"{prefix}{connector}{entry.name}")

            if entry.is_dir():
                extension = "    " if is_last else "│   "
                _walk(entry, prefix + extension, depth + 1)

    _walk(root, "", 1)
    return "\n".join(lines)


def export_markdown(tree: str, output_path: str, title: str = "Directory Structure"):
    """Export directory tree to Markdown file."""
    content = f"# {title}\n\n```\n{tree}\n```\n"
    Path(output_path).write_text(content, encoding="utf-8")
