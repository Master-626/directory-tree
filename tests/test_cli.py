import subprocess
import sys
from importlib.metadata import version

from click.testing import CliRunner

from directory_tree import __version__
from directory_tree.cli import main


def _run(args):
    return CliRunner().invoke(main, args)


def test_package_version_matches_metadata():
    assert version("directory-tree") == __version__


def test_cli_version():
    result = _run(["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_help_lists_scan_options():
    result = _run(["tree", "--help"])
    assert result.exit_code == 0
    for option in ("--size", "--ignore", "--no-ignore", "--dirs-only", "--max-depth"):
        assert option in result.output

    export_help = _run(["export", "--help"])
    assert export_help.exit_code == 0
    assert "--size" in export_help.output
    assert "--output" in export_help.output


def test_cli_tree_shape(tmp_path):
    (tmp_path / "a.txt").write_text("hi")
    result = _run(["tree", "-d", str(tmp_path), "--max-depth", "1"])
    assert result.exit_code == 0
    assert result.output.splitlines()[0] == f"{tmp_path.name}/"
    assert "a.txt" in result.output


def test_cli_current_directory_label(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.txt").write_text("x")
    result = _run(["tree"])
    assert result.exit_code == 0
    assert result.output.splitlines()[0] == f"{tmp_path.name}/"


def test_cli_default_ignore_keeps_github(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".github").mkdir()
    (tmp_path / "a.txt").write_text("x")
    result = _run(["tree", "-d", str(tmp_path)])
    assert result.exit_code == 0
    assert ".github" in result.output
    assert not any(line.endswith(".git") for line in result.output.splitlines())
    assert "a.txt" in result.output


def test_cli_ignore_replaces_defaults(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("x")
    (tmp_path / "a.txt").write_text("x")
    (tmp_path / "b.log").write_text("x")
    result = _run(["tree", "-d", str(tmp_path), "--ignore", "*.log"])
    assert result.exit_code == 0
    assert ".git" in result.output
    assert "config" in result.output
    assert "a.txt" in result.output
    assert "b.log" not in result.output


def test_cli_no_ignore(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "a.txt").write_text("x")
    result = _run(["tree", "-d", str(tmp_path), "--no-ignore"])
    assert result.exit_code == 0
    assert ".git" in result.output
    assert "node_modules" in result.output
    assert "a.txt" in result.output


def test_cli_no_ignore_conflicts_with_ignore(tmp_path):
    result = _run(["tree", "-d", str(tmp_path), "--no-ignore", "--ignore", ".git"])
    assert result.exit_code != 0
    assert "cannot be combined" in result.output


def test_cli_dirs_only(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.txt").write_text("x")
    result = _run(["tree", "-d", str(tmp_path), "--dirs-only"])
    assert result.exit_code == 0
    assert "sub" in result.output
    assert "a.txt" not in result.output


def test_cli_size(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"abcd")
    result = _run(["tree", "-d", str(tmp_path), "--size"])
    assert result.exit_code == 0
    assert "a.txt (4 B)" in result.output


def test_cli_expands_user(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / "note.txt").write_text("n")
    result = _run(["tree", "-d", "~"])
    assert result.exit_code == 0
    assert "note.txt" in result.output


def test_cli_missing_directory(tmp_path):
    result = _run(["tree", "-d", str(tmp_path / "nope")])
    assert result.exit_code != 0
    assert "Directory not found" in result.output


def test_cli_file_root(tmp_path):
    file = tmp_path / "a.txt"
    file.write_text("x")
    result = _run(["tree", "-d", str(file)])
    assert result.exit_code != 0
    assert "Not a directory" in result.output


def test_cli_rejects_negative_depth(tmp_path):
    result = _run(["tree", "-d", str(tmp_path), "--max-depth", "-1"])
    assert result.exit_code != 0


def test_cli_export(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"z" * 1024)
    output = tmp_path / "out.md"
    result = _run(
        [
            "export",
            "-d",
            str(tmp_path),
            "-o",
            str(output),
            "--title",
            "Proj",
            "--size",
            "--no-ignore",
        ]
    )
    assert result.exit_code == 0, result.output
    assert "Exported to" in result.output
    text = output.read_text(encoding="utf-8")
    assert text.startswith("# Proj\n")
    assert "a.txt (1.0 KB)" in text
    assert text.endswith("```\n")


def test_cli_export_missing_parent(tmp_path):
    output = tmp_path / "missing" / "tree.md"
    result = _run(["export", "-d", str(tmp_path), "-o", str(output)])
    assert result.exit_code != 0
    assert "Output directory not found" in result.output


def test_module_entrypoint(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "directory_tree.cli",
            "tree",
            "-d",
            str(tmp_path),
            "--max-depth",
            "1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "a.txt" in result.stdout
