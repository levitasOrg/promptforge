import datetime
import logging
import sys
from pathlib import Path

import typer
from rich.console import Console

from promptforge import __version__
from promptforge.config.models import AppConfig

app = typer.Typer(
    name="promptforge",
    help="Turn vague prompts into structured, token-efficient prompts.",
    invoke_without_command=True,
    no_args_is_help=False,
)
repo_app = typer.Typer(help="Index and query git repositories.", no_args_is_help=True)
app.add_typer(repo_app, name="repo")


@app.callback()
def _main(ctx: typer.Context) -> None:
    """Show welcome banner when called with no subcommand."""
    if ctx.invoked_subcommand is None:
        _show_welcome()
        raise typer.Exit(0)


def _show_welcome() -> None:
    import os

    from rich.padding import Padding
    from rich.panel import Panel
    from rich.rule import Rule
    from rich.table import Table
    from rich.text import Text

    console = Console(stderr=True)
    cwd = os.path.basename(os.getcwd()) or os.getcwd()

    # ── Header line (above the box, like "claude claude  Claude Code v2.x") ──
    header = Text()
    header.append("[+ promptforge promptforge]", style="bold cyan")
    console.print(header)
    console.print(Rule(f"[bold]PromptForge[/bold] [dim]v{__version__}[/dim]", style="cyan"))

    # ── Left column: branding ────────────────────────────────────────────────
    left = Text(justify="center")
    left.append("\nWelcome to\n\n", style="white")
    left.append("⚡PromptForge!\n", style="bold cyan")
    left.append("\n")
    left.append(
        "▀█████████▀\n"
        " ▀███████▀\n"
        "  ▀█████▀\n"
        "   ▀███▀\n"
        "    ▀█▀\n"
        "     ▀\n",
        style="cyan",
    )
    left.append(f"\nv{__version__}\n", style="dim")
    left.append(f"~/{cwd}\n", style="dim")

    # ── Right column: tips + what is ────────────────────────────────────────
    right = Text()
    right.append("\nTips for getting started\n", style="bold yellow")
    right.append("Configure your provider, then run on any vague prompt.\n\n", style="")
    right.append("  promptforge configure\n", style="cyan")
    right.append("    Pick a provider and validate your API key.\n\n", style="dim")
    right.append("  promptforge run \"help me fix the code\"\n", style="cyan")
    right.append("    Analyse → ask → synthesize (one LLM call).\n\n", style="dim")
    right.append("  promptforge correct my_prompt.txt\n", style="cyan")
    right.append("    Optimise an existing prompt file.\n\n", style="dim")
    right.append("  promptforge run \"...\" --diff\n", style="cyan")
    right.append("    Show before/after token comparison.\n\n", style="dim")
    right.append("  promptforge stats --reuse 10\n", style="cyan")
    right.append("    See savings at 10× prompt reuse.\n\n", style="dim")

    right.append("What's new\n", style="bold yellow")
    right.append("Rule-based vagueness detection across 7 dimensions.\n", style="dim")
    right.append("Single LLM call per session — no token waste.\n", style="dim")
    right.append("Auto-copies result to clipboard after every run.\n", style="dim")
    right.append("Ratings + token savings tracked in usage_log.jsonl.\n", style="dim")
    right.append("Providers: OpenAI · Anthropic · Gemini · Mistral · Groq · Copilot\n", style="dim")

    # ── Two-column grid ──────────────────────────────────────────────────────
    grid = Table.grid(expand=True, padding=(0, 1))
    grid.add_column(ratio=2, min_width=22)
    grid.add_column(ratio=5)
    grid.add_row(
        Padding(left, (0, 1)),
        Padding(right, (0, 1)),
    )

    console.print(Panel(grid, border_style="cyan", padding=(0, 0)))
    console.print()

_MAX_FILE_SIZE = 50 * 1024  # 50KB


class InputError(Exception):
    pass


def _not_implemented(command: str) -> None:
    typer.echo(f"[promptforge] '{command}' is not implemented yet.", err=True)
    raise typer.Exit(code=1)


def _setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.WARNING
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)


def _run_pipeline(
    raw_prompt: str,
    diff: bool,
    output: str | None,
    batch: bool,
    no_questions: bool,
    no_clipboard: bool,
    debug: bool,
) -> None:
    import litellm

    _console = Console(stderr=True)

    # Load config
    from promptforge.config.manager import ConfigError, ConfigManager
    try:
        config = ConfigManager().load()
    except ConfigError:
        _console.print("✗ Config not found. Run promptforge configure first.")
        raise typer.Exit(1)

    # Analyze
    from promptforge.analyzer.engine import Analyzer
    report = Analyzer().analyze(raw_prompt)

    # Question pipeline
    questions = []
    answers = []
    if not no_questions:
        from promptforge.interviewer.terminal import Interviewer
        from promptforge.questions.engine import QuestionEngine
        questions = QuestionEngine().generate(report)
        answers = Interviewer().conduct(questions, batch=batch)

    # Assemble context
    from promptforge.assembler.context import ContextAssembler
    context = ContextAssembler().assemble(raw_prompt, report, answers)

    # Synthesize
    from promptforge.synthesizer.engine import Synthesizer
    try:
        optimized = Synthesizer().synthesize(context, config)
    except litellm.AuthenticationError:  # type: ignore[attr-defined]
        _console.print(f"✗ API key was rejected by {config.provider}.")
        _console.print("  Hint: Run `promptforge configure` to update your key.")
        raise typer.Exit(2)
    except litellm.RateLimitError:  # type: ignore[attr-defined]
        _console.print(f"✗ {config.provider} rate limit reached.")
        _console.print("  Hint: Wait a few minutes or check your provider's usage dashboard.")
        raise typer.Exit(2)
    except (litellm.Timeout, litellm.APIConnectionError):  # type: ignore[attr-defined]
        _console.print(f"✗ Could not reach {config.provider}.")
        _console.print("  Hint: Check your network connection and try again.")
        raise typer.Exit(2)
    except litellm.BadRequestError as e:  # type: ignore[attr-defined]
        _console.print(f"✗ {config.provider} rejected the request: {e}")
        _console.print("  Hint: This usually means a bad model name in config — run `promptforge configure` again.")
        raise typer.Exit(2)
    except litellm.ServiceUnavailableError:  # type: ignore[attr-defined]
        _console.print(f"✗ {config.provider} is temporarily unavailable.")
        _console.print("  Hint: Try again in a few minutes.")
        raise typer.Exit(2)
    except Exception as e:
        if debug:
            import traceback
            traceback.print_exc(file=sys.stderr)
        _console.print(f"✗ Unexpected error: {e}")
        _console.print("  Hint: Run with --debug for full traceback.")
        raise typer.Exit(99)

    # Usage logging
    from promptforge.stats.logger import UsageLogger
    from promptforge.stats.models import UsageRecord
    usage_logger = UsageLogger()
    try:
        orig_tokens = int(len(raw_prompt.split()) * 1.33)
        record = UsageRecord(
            session_id=optimized.session_id,
            timestamp=datetime.datetime.now(tz=datetime.UTC).isoformat(),
            command="run",
            mode="standard",
            original_token_estimate=orig_tokens,
            optimized_token_estimate=optimized.token_estimate,
            tool_input_tokens=0,
            tool_output_tokens=0,
            tool_total_tokens=0,
            provider=config.provider,
            model=config.model,
            issues_detected=len(report.issues),
            questions_asked=len(questions) if not no_questions else 0,
            questions_answered=sum(1 for a in answers if not a.skipped) if not no_questions else 0,
            reduction_pct=float(int(
                (orig_tokens - optimized.token_estimate)
                / max(orig_tokens, 1) * 100
            )),
        )
        usage_logger.record(record)
    except Exception as e:
        logging.getLogger(__name__).warning(
            "Usage log write failed: %s. Continuing without recording this session.", e
        )

    # Render
    from promptforge.renderer.display import Renderer
    output_path = Path(output) if output else None
    Renderer().render(
        optimized=optimized,
        raw_prompt=raw_prompt,
        output_path=output_path,
        no_clipboard=no_clipboard,
        show_diff=diff,
        usage_logger=usage_logger,
    )


@app.command()
def configure() -> None:
    """First-run setup wizard. Select provider, model, enter API key."""
    from promptforge.config.manager import ConfigManager
    from promptforge.config.providers import COPILOT_BASE_URL, ProviderRegistry

    console = Console(stderr=True)
    registry = ProviderRegistry()
    providers = registry.get_providers()

    # Step 1: Show provider list
    console.print("\n[bold]Select your LLM provider:[/bold]")
    for i, provider in enumerate(providers, 1):
        console.print(f"  {i}. {provider.display_name}")

    while True:
        choice = typer.prompt("Provider number", err=True)
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(providers):
                selected_provider = providers[idx]
                break
        except ValueError:
            pass
        console.print("[red]Invalid choice.[/red]")

    # Step 2: Show model list
    console.print(f"\n[bold]Select a model for {selected_provider.display_name}:[/bold]")
    for i, model in enumerate(selected_provider.models, 1):
        star = " ★" if model.is_recommended else ""
        console.print(f"  {i}. {model.display_name}{star}")

    while True:
        choice = typer.prompt("Model number", err=True)
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(selected_provider.models):
                selected_model = selected_provider.models[idx]
                break
        except ValueError:
            pass
        console.print("[red]Invalid choice.[/red]")

    # Step 3: API key input (hidden)
    key = typer.prompt(selected_provider.auth_label, hide_input=True, err=True)

    # Determine base_url for Copilot
    base_url = COPILOT_BASE_URL if selected_provider.id == "copilot" else None

    config = AppConfig(
        provider=selected_provider.id,
        model=selected_model.id,
        api_key=key,
        litellm_model_string=selected_model.litellm_string,
        litellm_base_url=base_url,
    )

    # Step 4: Validate key (max 3 attempts)
    manager = ConfigManager()
    for attempt in range(1, 4):
        console.print(f"\n[dim]Validating key (attempt {attempt}/3)...[/dim]")
        try:
            valid = manager.validate_key(config)
        except Exception as e:
            console.print(f"[red]Validation error: {e}[/red]")
            valid = False

        if valid:
            break
        console.print("[red]✗ Key rejected by provider. Check your key and try again.[/red]")
        if attempt < 3:
            key = typer.prompt(selected_provider.auth_label, hide_input=True, err=True)
            config = AppConfig(
                provider=selected_provider.id,
                model=selected_model.id,
                api_key=key,
                litellm_model_string=selected_model.litellm_string,
                litellm_base_url=base_url,
            )
    else:
        console.print("[red]✗ Failed after 3 attempts.[/red]")
        raise typer.Exit(2)

    # Step 5: Save
    manager.save(config)
    console.print(f"\n[green]✓ Key validated. Config saved to {manager.config_path}[/green]")


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
    _setup_logging(debug)
    _console = Console(stderr=True)

    # Read raw prompt: --file > positional > stdin
    raw_prompt: str | None = None
    if file is not None:
        p = Path(file)
        if not p.exists():
            _console.print(f"✗ File not found: {file}")
            raise typer.Exit(1)
        if p.stat().st_size > _MAX_FILE_SIZE:
            _console.print(f"✗ File too large (max 50KB): {file}")
            raise typer.Exit(1)
        raw_prompt = p.read_text(encoding="utf-8")
    elif prompt is not None:
        raw_prompt = prompt
    else:
        raw_prompt = sys.stdin.read()

    if not raw_prompt or not raw_prompt.strip():
        _console.print("✗ No prompt provided. Pass a prompt, use --file, or pipe via stdin.")
        raise typer.Exit(1)

    _run_pipeline(
        raw_prompt=raw_prompt,
        diff=diff,
        output=output,
        batch=batch,
        no_questions=no_questions,
        no_clipboard=no_clipboard,
        debug=debug,
    )


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
    _setup_logging(debug)
    _console = Console(stderr=True)

    p = Path(file)
    if not p.exists():
        _console.print(f"✗ File not found: {file}")
        raise typer.Exit(1)
    if p.stat().st_size > _MAX_FILE_SIZE:
        _console.print(f"✗ File too large (max 50KB): {file}")
        raise typer.Exit(1)
    raw_prompt = p.read_text(encoding="utf-8")

    if not raw_prompt or not raw_prompt.strip():
        _console.print("✗ File is empty.")
        raise typer.Exit(1)

    _run_pipeline(
        raw_prompt=raw_prompt,
        diff=diff,
        output=output,
        batch=batch,
        no_questions=no_questions,
        no_clipboard=no_clipboard,
        debug=debug,
    )


@app.command()
def stats(
    detailed: bool = typer.Option(False, "--detailed", help="Show per-session table."),
    reuse: int = typer.Option(1, "--reuse", help="Project savings at N× reuse per prompt."),
    last: int = typer.Option(0, "--last", help="Limit to last N sessions (0 = all)."),
    reset: bool = typer.Option(False, "--reset", help="Delete usage log after confirmation."),
    yes: bool = typer.Option(False, "--yes", help="Skip confirmation for --reset."),
    export: str | None = typer.Option(None, "--export", help="Write merged records as JSON array to file."),
) -> None:
    """Show token savings analytics from your session history."""
    from pathlib import Path

    from promptforge.stats.display import StatsRenderer
    from promptforge.stats.logger import UsageLogger

    usage_logger = UsageLogger()
    renderer = StatsRenderer()

    if reset:
        try:
            usage_logger.reset(skip_confirmation=yes)
        except SystemExit as e:
            Console(stderr=True).print(f"[red]{e}[/red]")
            raise typer.Exit(1)
        Console(stderr=True).print("[green]✓ Usage log reset.[/green]")
        return

    if export:
        usage_logger.export(Path(export))
        Console(stderr=True).print(f"[green]✓ Exported to {export}[/green]")
        return

    records = usage_logger.load_all()
    if last > 0:
        from promptforge.stats.engine import StatsEngine
        records = StatsEngine().filter_last(records, last)

    if detailed:
        renderer.render_detailed(records)

    renderer.render_summary(records, reuse_n=reuse)

    if reuse > 1:
        renderer.render_projection(records, reuse)


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
