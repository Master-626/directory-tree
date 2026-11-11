# Directory Tree

## 概述

`directory-tree` 把目录打印成树状文本，也可以导出成 Markdown。可以限制层级、按文件名 glob 忽略条目、只显示文件夹，并在文件后标出大小。默认跳过 `.git`、`__pycache__`、`.venv` 和 `node_modules`；`.git` 不会误伤 `.github`。指回上级的符号链接标成 `[cycle]`，读不了的子目录就地标错，不会让整棵树失败。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![CI](https://github.com/Master-626/directory-tree/actions/workflows/ci.yml/badge.svg)](https://github.com/Master-626/directory-tree/actions/workflows/ci.yml)

Generate a directory tree for the terminal or a Markdown file. Limit how deep the walk goes, skip names with glob patterns, and optionally print each file's size.

```text
project/
├── src
│   └── app.py (120 B)
├── .github
│   └── workflows
└── README.md (1.1 KB)
```

## Installation

```bash
git clone https://github.com/Master-626/directory-tree.git
cd directory-tree
python -m pip install .
```

That installs two commands, `directory-tree` and `dirtree`. If the install location is not on your `PATH`, run the module instead:

```bash
python -m directory_tree.cli tree -d .
```

For development, including tests and Ruff:

```bash
python -m pip install -e ".[dev]"
```

Python 3.8 and newer is supported. The only runtime dependency is Click.

## Usage

### Command line

```bash
# Current directory
directory-tree tree

# Two levels under another directory, directories only
directory-tree tree -d ~/projects --max-depth 2 --dirs-only

# Replace the default ignores with globs
directory-tree tree -d . --ignore '*.pyc' --ignore 'tmp*'

# Show every entry, with file sizes
directory-tree tree -d . --no-ignore --size

# Markdown export
directory-tree export -d . -o tree.md --title "Project structure" --size
```

`~` is expanded in the directory argument, including when the shell does not expand it for you.

### Options

`tree` and `export` accept the same scan options. `export` also writes a file.

| Option | Description |
| --- | --- |
| `-d`, `--directory` | Directory to scan. Default: `.` |
| `--max-depth N` | Levels below the root. `1` shows immediate children. `0` prints only the root line. |
| `--dirs-only` | List directories and skip files. |
| `--ignore GLOB` | Glob matched against each entry's name. Replaces the default ignores. Repeat the flag to add more patterns. |
| `--no-ignore` | Ignore nothing. Cannot be combined with `--ignore`. |
| `--size` | Append a 1024-based size to each file, such as `1.5 KB`. |
| `-o`, `--output` | Markdown output path (`export` only). Default: `tree.md`. |
| `--title` | Heading written above the Markdown fence (`export` only). |

Default ignore patterns, used when neither `--ignore` nor `--no-ignore` is set:

`.git`, `__pycache__`, `.venv`, `node_modules`

Patterns are case-sensitive and match the name only, not a parent path. `.git` matches a directory named `.git` and does not match `.github`, `.gitignore`, or `my.gitconfig`. Use `*.pyc` or `temp*` when you want a wildcard.

Directories are listed before files. Names are sorted case-sensitively, so `B.txt` comes before `a.txt`.

### Python API

```python
from directory_tree import DEFAULT_IGNORE_PATTERNS, export_markdown, generate_tree

tree = generate_tree("~/projects", max_depth=2)
print(tree)

# Keep the defaults and also skip bytecode files.
tree = generate_tree(
    ".",
    ignore_patterns=[*DEFAULT_IGNORE_PATTERNS, "*.pyc"],
    show_sizes=True,
)
export_markdown(tree, "tree.md", title="Project structure")
```

`generate_tree` returns the tree as one string. `ignore_patterns=None` applies the defaults; `ignore_patterns=[]` shows every name. `show_files=False` is the same filter as `--dirs-only`.

`export_markdown` writes a fenced code block. The parent directory of the output file must already exist. If the tree itself contains triple backticks, the fence is made longer so the block stays intact.

A symlink that points back at a directory already being walked is printed with a `[cycle]` suffix and is not followed. Other directory symlinks are followed, so a link to a sibling is listed again. A nested directory that cannot be read is kept in the tree with an `[error: ...]` line. If the root itself cannot be read, or is missing, or is a file, `generate_tree` raises.

## Running tests

```bash
python -m pip install -e ".[dev]"
pytest
ruff check src tests
```

GitHub Actions runs Ruff on Python 3.12 and pytest on Python 3.8 through 3.13.

## License

MIT License. Copyright (c) 2026 Xu Jiaqi.
