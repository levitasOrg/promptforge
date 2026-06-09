import sys

import typer

from promptforge import __version__

app = typer.Typer(
    name="promptforge",
    help="Turn vague prompts into structured, token-efficient prompts.",
    no_args_is_help=True,
)
repo_app = typer.Typer(help="Index and query git repositories.", no_args_is_help=True)
app.add_typer(repo_app, name="repo")


def _not_implemented(command: str) -> None:
    typer.echo(f"[promptforge] '{command}' is not implemented yet.", err=True)
    raise typer.Exit(code=1)


@app.command()
def configure() -> None:
    """First-run setup wizard. Select provider, model, enter API key."""
    _not_implemented("configure")


@app.command()
def run(
    prompt: str | None = typer.Argument(None, help="Prompt text (or pipe via stdin / use --file)."),
    file: str | None = typer.Option(None, "--file", "-f", help="Read prompt from file."),
    diff: bool = typer.Option(False, "--diff", "-d", help="Show before/after diff (stderr)."),
    output: str | None = typer.Option(None, "--output", "-o", help="Also write optimized prompt to file."),
    batch: bool = typer.Option(False, "--batch", "-b", help="Print all questions at once."),
    no_questions: bool = typer.Option(False, "--no-questions", help="Skip clarifying questions entirely."),
    no_clipboard: bool = typer.Option(False, "--no-clipboard", "-n", help="Do not copy result to clipboard."),
    debug: bool = typer.Option(False, "--debug", help="Print full tracebacks and debug info to stderr."),
) -> None:
    """Analyze a vague prompt and synthesize an optimized one."""
    _not_implemented("run")


@app.command()
def correct(
    file: str = typer.Argument(..., help="Path to existing prompt file to correct."),
    diff: bool = typer.Option(False, "--diff", "-d"),
    output: str | None = typer.Option(None, "--output", "-o"),
    batch: bool = typer.Option(False, "--batch", "-b"),
    no_questions: bool = typer.Option(False, "--no-questions"),
    no_clipboard: bool = typer.Option(False, "--no-clipboard", "-n"),
    debug: bool = typer.Option(False, "--debug"),
) -> None:
    """Convenience alias for `run --file <file>`."""
    _not_implemented("correct")


@app.command()
def stats(
    detailed: bool = typer.Option(False, "--detailed"),
    reuse: int = typer.Option(1, "--reuse"),
    last: int | None = typer.Option(None, "--last"),
    reset: bool = typer.Option(False, "--reset"),
    yes: bool = typer.Option(False, "--yes"),
    export: str | None = typer.Option(None, "--export"),
) -> None:
    """Show token savings analytics from session history."""
    _not_implemented("stats")


@app.command()
def version() -> None:
    """Print the installed PromptForge version."""
    # NOTE: version is one of the few things that goes to stdout — it's the user's request.
    typer.echo(f"promptforge {__version__}")


@repo_app.command("add")
def repo_add(target: str = typer.Argument(...)) -> None:
    """Index a local or remote git repository."""
    _not_implemented("repo add")


@repo_app.command("ask")
def repo_ask(question: str = typer.Argument(...)) -> None:
    """Ask a repo-aware question."""
    _not_implemented("repo ask")


@repo_app.command("list")
def repo_list() -> None:
    """List all indexed repos."""
    _not_implemented("repo list")


@repo_app.command("refresh")
def repo_refresh(name: str = typer.Argument(...)) -> None:
    """Re-index an existing repo."""
    _not_implemented("repo refresh")


@repo_app.command("templates")
def repo_templates() -> None:
    """Show saved prompt templates."""
    _not_implemented("repo templates")


if __name__ == "__main__":
    sys.exit(app())
