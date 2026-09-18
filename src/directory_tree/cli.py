"""
CLI interface for directory-tree.
"""

import click
from .generator import generate_tree, export_markdown


@click.group()
@click.version_option()
def main():
    """Directory Tree - Generate beautiful directory trees."""
    pass


@main.command()
@click.option("-d", "--directory", default=".", help="Directory to scan")
@click.option("--max-depth", type=int, help="Maximum depth to traverse")
@click.option("--dirs-only", is_flag=True, help="Show directories only")
@click.option("--ignore", multiple=True, help="Ignore patterns (can be used multiple times)")
def tree(directory, max_depth, dirs_only, ignore):
    """Generate directory tree."""
    ignore_list = list(ignore) if ignore else None
    tree_str = generate_tree(
        directory,
        max_depth=max_depth,
        ignore_patterns=ignore_list,
        show_files=not dirs_only,
    )
    click.echo(tree_str)


@main.command()
@click.option("-d", "--directory", default=".", help="Directory to scan")
@click.option("-o", "--output", default="tree.md", help="Output Markdown file")
@click.option("--title", default="Directory Structure", help="Markdown title")
@click.option("--max-depth", type=int, help="Maximum depth")
def export(directory, output, title, max_depth):
    """Export directory tree to Markdown."""
    tree_str = generate_tree(directory, max_depth=max_depth)
    export_markdown(tree_str, output, title=title)
    click.echo(f"✅ Exported to: {output}")


if __name__ == "__main__":
    main()
