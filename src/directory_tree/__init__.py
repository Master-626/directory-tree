"""directory-tree - Generate directory trees for the terminal and Markdown."""

from .generator import DEFAULT_IGNORE_PATTERNS, export_markdown, generate_tree

__version__ = "0.1.1"
__all__ = [
    "DEFAULT_IGNORE_PATTERNS",
    "export_markdown",
    "generate_tree",
]
