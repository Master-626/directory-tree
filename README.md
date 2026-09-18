# Directory Tree

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)

Generate beautiful directory tree with filtering and Markdown export.

## 🌟 Features

- 🌳 **Tree Generation** - Generate ASCII directory trees
- 📏 **Depth Control** - Limit traversal depth
- 🚫 **Filtering** - Ignore specific files/directories
- 📝 **Markdown Export** - Export to Markdown code blocks
- 🐍 **Python API** - Use as a library in your code

## 📦 Installation

```bash
git clone https://github.com/Master-626/directory-tree.git
cd directory-tree
pip install .
```

## 🚀 Usage

### Generate Directory Tree
```bash
# Current directory
directory-tree tree

# Specific directory
directory-tree tree -d ~/projects

# Max depth 2
directory-tree tree -d ~/projects --max-depth 2

# Directories only
directory-tree tree -d ~/projects --dirs-only

# Ignore patterns
directory-tree tree -d ~/projects --ignore .git --ignore __pycache__
```

### Export to Markdown
```bash
directory-tree export -d ~/projects -o tree.md --title "Project Structure"
```

## 🐍 Python API

```python
from directory_tree import generate_tree, export_markdown

# Generate tree
tree = generate_tree("~/projects", max_depth=3)
print(tree)

# Export to Markdown
export_markdown(tree, "output.md", title="My Project")
```

## 🧪 Testing

```bash
pip install -e ".[dev]"
pytest
```

## 📄 License

MIT License
