import difflib
import logging
import sys
from pathlib import Path

import pyperclip
from rich.console import Console
from rich.panel import Panel

from promptforge.stats.logger import UsageLogger
from promptforge.synthesizer.models import OptimizedPrompt

logger = logging.getLogger(__name__)
_stderr_console = Console(stderr=True)


class Renderer:
    def render(
        self,
        optimized: OptimizedPrompt,
        raw_prompt: str,
        output_path: Path | None = None,
        no_clipboard: bool = False,
        show_diff: bool = False,
        usage_logger: UsageLogger | None = None,
    ) -> None:
        # Step 1: stdout — raw text only, no decoration
        sys.stdout.write(optimized.text)
        sys.stdout.write("\n")
        sys.stdout.flush()

        # Step 2: Rich panel to stderr
        _stderr_console.print(
            Panel(
                optimized.text,
                title="[bold green]Optimized Prompt[/bold green]",
                border_style="green",
            )
        )

        # Step 3: Diff (--diff)
        if show_diff:
            self._render_diff(raw_prompt, optimized.text)

        # Step 4: File output (--output)
        if output_path is not None:
            try:
                output_path.write_text(optimized.text, encoding="utf-8")
            except OSError as e:
                _stderr_console.print(f"[yellow]Could not write to {output_path}: {e}[/yellow]")

        # Step 5: Clipboard
        if not no_clipboard:
            try:
                pyperclip.copy(optimized.text)
                _stderr_console.print("✓ Copied to clipboard")
            except pyperclip.PyperclipException as e:
                logger.warning("Clipboard not available: %s", e)
                _stderr_console.print("⚠ Clipboard unavailable — use --output to save")

        # Step 6: Rating collection — TTY guard first
        if usage_logger is not None:
            self._collect_rating(optimized.session_id, usage_logger)

    def _render_diff(self, original: str, optimized: str) -> None:
        orig_lines = original.splitlines(keepends=True)
        opt_lines = optimized.splitlines(keepends=True)
        diff = list(difflib.unified_diff(orig_lines, opt_lines, fromfile="original", tofile="optimized"))

        orig_tokens = int(len(original.split()) * 1.33)
        opt_tokens = int(len(optimized.split()) * 1.33)
        pct = int((orig_tokens - opt_tokens) / orig_tokens * 100) if orig_tokens > 0 else 0

        _stderr_console.print(f"\n[dim]Original: ~{orig_tokens} tokens → Optimized: ~{opt_tokens} tokens ({pct}% reduction)[/dim]")
        for line in diff:
            if line.startswith("+"):
                _stderr_console.print(f"[green]{line}[/green]", end="")
            elif line.startswith("-"):
                _stderr_console.print(f"[red]{line}[/red]", end="")
            else:
                _stderr_console.print(f"[dim]{line}[/dim]", end="")

    def _collect_rating(self, session_id: str, usage_logger: UsageLogger) -> None:
        if not (sys.stdin.isatty() and sys.stderr.isatty()):
            return
        try:
            import readchar
            _stderr_console.print("\nWas this prompt helpful? [y=👍 / n=👎 / s=skip]: ", end="")
            key = readchar.readchar()
            _stderr_console.print()
            if key.lower() == "y":
                usage_logger.record_rating(session_id, 1)
                _stderr_console.print("✓ Feedback recorded.")
            elif key.lower() == "n":
                usage_logger.record_rating(session_id, -1)
                _stderr_console.print("✓ Feedback recorded.")
            # s or anything else: silent skip
        except Exception as e:
            logger.warning("Rating collection failed: %s. Skipping.", e)
