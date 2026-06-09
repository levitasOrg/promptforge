"""Thin wrapper around the graphify CLI."""

import shutil
import subprocess
from pathlib import Path

INSTALL_HINT = (
    "graphify is not installed.\n"
    "Install it with:\n\n"
    "  pip install graphifyy && graphify install\n\n"
    "Then re-run your /repo command."
)


def is_installed() -> bool:
    return shutil.which("graphify") is not None


def index(repo_path: Path) -> Path:
    """
    Run `graphify <repo_path>` to build the knowledge graph.
    Returns the graphify-out/ directory.
    Streams graphify's output directly to the terminal.
    """
    result = subprocess.run(["graphify", str(repo_path)])
    if result.returncode != 0:
        raise RuntimeError(f"graphify exited with code {result.returncode}")
    output_dir = repo_path / "graphify-out"
    if not output_dir.exists():
        raise RuntimeError(
            f"graphify ran but no output found at {output_dir}.\n"
            "Make sure graphify completed successfully."
        )
    return output_dir


def query(repo_path: Path, question: str) -> str:
    """
    Run `graphify query "<question>"` from the repo directory.
    Returns the text output (relevant nodes + context snippets).
    """
    result = subprocess.run(
        ["graphify", "query", question],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"graphify query failed:\n{result.stderr.strip() or '(no error output)'}"
        )
    return result.stdout.strip()


def open_graph(graph_dir: Path) -> None:
    """Open graph.html in the default browser."""
    import webbrowser
    html = graph_dir / "graph.html"
    if not html.exists():
        raise FileNotFoundError(f"No graph.html found at {html}")
    webbrowser.open(f"file://{html.resolve()}")
