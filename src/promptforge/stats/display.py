from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from promptforge.stats.engine import StatsEngine
from promptforge.stats.models import UsageRecord

_console = Console(stderr=True)


class StatsRenderer:
    def render_summary(self, records: list[UsageRecord], reuse_n: int = 1) -> None:
        engine = StatsEngine()
        summary = engine.compute_summary(records)
        savings = engine.compute_savings(records, reuse_n)

        lines = [
            f"  Sessions tracked:           {summary['total_sessions']}",
            f"  Total original tokens:   {summary['total_original_tokens']:,}",
            f"  Total optimised tokens:  {summary['total_optimized_tokens']:,}",
            f"  Total tool cost:         {summary['total_tool_cost']:,}",
            "",
            f"  Average prompt reduction:    {summary['avg_reduction_pct']:.0f}%",
            f"  Net saving at {reuse_n}× reuse:  {savings['net_saving']:+,} tokens",
            "",
            "  ── Feedback ────────────────────────────────────────────",
            f"  Sessions rated:  {summary['sessions_rated']} of {summary['total_sessions']}",
            f"  \U0001f44d Positive:     {summary['positive_ratings']}",
            f"  \U0001f44e Negative:     {summary['negative_ratings']}",
        ]
        _console.print(Panel("\n".join(lines), title="[bold]PromptForge — Token Savings Report[/bold]", border_style="blue"))
        _console.print("[dim]Token estimates use a word-count approximation (~1.33 tokens/word).[/dim]")

    def render_detailed(self, records: list[UsageRecord]) -> None:
        engine = StatsEngine()
        table = Table(title="Session Log", border_style="blue")
        table.add_column("Date")
        table.add_column("Original", justify="right")
        table.add_column("Optimised", justify="right")
        table.add_column("Tool cost", justify="right")
        table.add_column("Reduction", justify="right")
        table.add_column("Break-even", justify="right")

        for r in records:
            be = engine.compute_break_even(r)
            be_str = f"{be}×" if be is not None else "N/A (expanded)"
            date_str = r.timestamp[:10]
            table.add_row(
                date_str,
                f"{r.original_token_estimate}t",
                f"{r.optimized_token_estimate}t",
                f"{r.tool_total_tokens}t",
                f"{r.reduction_pct:.0f}%",
                be_str,
            )
        _console.print(table)

    def render_projection(self, records: list[UsageRecord], reuse_n: int) -> None:
        engine = StatsEngine()
        savings = engine.compute_savings(records, reuse_n)
        lines = [
            f"  Baseline (raw prompts × {reuse_n}):  {savings['baseline_tokens']:,} tokens",
            f"  With PromptForge (opt × {reuse_n} + tool cost): {savings['with_tool_tokens']:,} tokens",
            f"  Net saving vs baseline:     {savings['net_saving']:+,} tokens",
            f"  Reduction vs baseline:       {savings['reduction_pct']:.1f}%",
        ]
        _console.print(Panel(
            "\n".join(lines),
            title=f"[bold]Projection: {reuse_n}× reuse per prompt[/bold]",
            border_style="cyan",
        ))
