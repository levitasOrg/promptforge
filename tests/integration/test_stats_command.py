from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from promptforge.cli import app
from promptforge.stats.models import UsageRecord

runner = CliRunner()

def make_record(session_id="s1", original=100, optimized=60, tool_total=50, rating=None):
    return UsageRecord(
        session_id=session_id,
        timestamp="2025-06-08T12:00:00Z",
        command="run",
        mode="standard",
        original_token_estimate=original,
        optimized_token_estimate=optimized,
        tool_input_tokens=25,
        tool_output_tokens=25,
        tool_total_tokens=tool_total,
        provider="anthropic",
        model="claude-haiku-3-5",
        issues_detected=2,
        questions_asked=2,
        questions_answered=2,
        reduction_pct=40.0,
        rating=rating,
    )

def test_stats_summary_no_sessions():
    with patch("promptforge.stats.logger.UsageLogger.load_all", return_value=[]):
        result = runner.invoke(app, ["stats"])
    assert result.exit_code == 0

def test_stats_summary_with_sessions():
    records = [make_record("s1"), make_record("s2")]
    with patch("promptforge.stats.logger.UsageLogger.load_all", return_value=records):
        result = runner.invoke(app, ["stats"])
    assert result.exit_code == 0
    assert "2" in result.output  # 2 sessions

def test_stats_detailed_flag():
    records = [make_record("s1"), make_record("s2")]
    with patch("promptforge.stats.logger.UsageLogger.load_all", return_value=records):
        result = runner.invoke(app, ["stats", "--detailed"])
    assert result.exit_code == 0
    assert "2025-06-08" in result.output

def test_stats_reuse_shows_projection():
    records = [make_record("s1")]
    with patch("promptforge.stats.logger.UsageLogger.load_all", return_value=records):
        result = runner.invoke(app, ["stats", "--reuse", "10"])
    assert result.exit_code == 0
    assert "10" in result.output

def test_stats_reset_with_yes():
    with patch("promptforge.stats.logger.UsageLogger.reset") as mock_reset:
        result = runner.invoke(app, ["stats", "--reset", "--yes"])
    assert result.exit_code == 0
    mock_reset.assert_called_once_with(skip_confirmation=True)

def test_stats_export(tmp_path):
    records = [make_record("s1")]
    out_file = str(tmp_path / "out.json")
    with (
        patch("promptforge.stats.logger.UsageLogger.load_all", return_value=records),
        patch("promptforge.stats.logger.UsageLogger.export") as mock_export,
    ):
        result = runner.invoke(app, ["stats", "--export", out_file])
    assert result.exit_code == 0
    mock_export.assert_called_once()
