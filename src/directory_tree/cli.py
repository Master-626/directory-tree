"""CLI interface for directory-tree."""

import click

from . import __version__
from .generator import export_markdown, generate_tree

_DIRECTORY_HELP = "Directory to scan."
_DEPTH_HELP = "Levels below the root to include. 0 shows only the root line."
_DIRS_HELP = "Show directories only."
_IGNORE_HELP = "Name glob that replaces the default ignores. Can be repeated."
_NO_IGNORE_HELP = "Ignore nothing, including the default patterns."
_SIZE_HELP = "Show a human-readable size next to each file."


def _ignore_patterns(ignore, no_ignore):
    if no_ignore and ignore:
        raise click.UsageError("--no-ignore cannot be combined with --ignore.")
    if no_ignore:
        return []
    if ignore:
        return list(ignore)
    return None


def _generate(directory, max_depth, dirs_only, ignore, no_ignore, show_sizes):
    ignore_patterns = _ignore_patterns(ignore, no_ignore)
    try:
        return generate_tree(
            directory,
            max_depth=max_depth,
            ignore_patterns=ignore_patterns,
            show_files=not dirs_only,
            show_sizes=show_sizes,
        )
    except (FileNotFoundError, NotADirectoryError, PermissionError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc


@click.group()
@click.version_option(__version__, prog_name="directory-tree")
def main():
    """Directory Tree - Generate directory trees."""


@main.command()
@click.option("-d", "--directory", default=".", help=_DIRECTORY_HELP)
@click.option("--max-depth", type=click.IntRange(min=0), metavar="N", help=_DEPTH_HELP)
@click.option("--dirs-only", is_flag=True, help=_DIRS_HELP)
@click.option("--ignore", multiple=True, metavar="GLOB", help=_IGNORE_HELP)
@click.option("--no-ignore", is_flag=True, help=_NO_IGNORE_HELP)
@click.option("--size", is_flag=True, help=_SIZE_HELP)
def tree(directory, max_depth, dirs_only, ignore, no_ignore, size):
    """Generate a directory tree."""
    click.echo(_generate(directory, max_depth, dirs_only, ignore, no_ignore, size))


@main.command()
@click.option("-d", "--directory", default=".", help=_DIRECTORY_HELP)
@click.option("-o", "--output", default="tree.md", help="Output Markdown file.")
@click.option("--title", default="Directory Structure", help="Markdown title.")
@click.option("--max-depth", type=click.IntRange(min=0), metavar="N", help=_DEPTH_HELP)
@click.option("--dirs-only", is_flag=True, help=_DIRS_HELP)
@click.option("--ignore", multiple=True, metavar="GLOB", help=_IGNORE_HELP)
@click.option("--no-ignore", is_flag=True, help=_NO_IGNORE_HELP)
@click.option("--size", is_flag=True, help=_SIZE_HELP)
def export(directory, output, title, max_depth, dirs_only, ignore, no_ignore, size):
    """Export a directory tree to Markdown."""
    tree_str = _generate(directory, max_depth, dirs_only, ignore, no_ignore, size)
    try:
        export_markdown(tree_str, output, title=title)
    except OSError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"✅ Exported to: {output}")


if __name__ == "__main__":
    main()
