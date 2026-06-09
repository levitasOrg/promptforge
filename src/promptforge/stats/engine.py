from math import ceil
from statistics import mean
from promptforge.stats.models import UsageRecord


class StatsEngine:
    def compute_summary(self, records: list[UsageRecord]) -> dict:
        if not records:
            return {
                "total_sessions": 0,
                "total_original_tokens": 0,
                "total_optimized_tokens": 0,
                "total_tool_cost": 0,
                "avg_reduction_pct": 0.0,
                "sessions_rated": 0,
                "positive_ratings": 0,
                "negative_ratings": 0,
            }
        total_sessions = len(records)
        total_original = sum(r.original_token_estimate for r in records)
        total_optimized = sum(r.optimized_token_estimate for r in records)
        total_tool_cost = sum(r.tool_total_tokens for r in records)

        reductions = [r.reduction_pct for r in records if r.original_token_estimate > 0]
        avg_reduction = mean(reductions) if reductions else 0.0

        rated = [r for r in records if r.rating is not None]
        positive = sum(1 for r in rated if r.rating == 1)
        negative = sum(1 for r in rated if r.rating == -1)

        return {
            "total_sessions": total_sessions,
            "total_original_tokens": total_original,
            "total_optimized_tokens": total_optimized,
            "total_tool_cost": total_tool_cost,
            "avg_reduction_pct": avg_reduction,
            "sessions_rated": len(rated),
            "positive_ratings": positive,
            "negative_ratings": negative,
        }

    def compute_savings(self, records: list[UsageRecord], reuse_n: int) -> dict:
        gross = sum(
            (r.original_token_estimate - r.optimized_token_estimate) * reuse_n
            for r in records
        )
        total_tool_cost = sum(r.tool_total_tokens for r in records)
        net = gross - total_tool_cost

        baseline = sum(r.original_token_estimate for r in records) * reuse_n
        with_tool = (
            sum(r.optimized_token_estimate for r in records) * reuse_n + total_tool_cost
        )
        reduction_pct = (baseline - with_tool) / baseline * 100 if baseline > 0 else 0.0

        return {
            "reuse_n": reuse_n,
            "baseline_tokens": baseline,
            "with_tool_tokens": with_tool,
            "net_saving": net,
            "reduction_pct": reduction_pct,
        }

    def filter_last(self, records: list[UsageRecord], n: int) -> list[UsageRecord]:
        return records[-n:] if n < len(records) else records

    def compute_break_even(self, record: UsageRecord) -> int | None:
        diff = record.original_token_estimate - record.optimized_token_estimate
        if diff <= 0:
            return None
        return ceil(record.tool_total_tokens / diff)
