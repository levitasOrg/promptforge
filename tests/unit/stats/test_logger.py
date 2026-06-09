import json
import pytest
from pathlib import Path
from promptforge.stats.logger import UsageLogger
from promptforge.stats.models import UsageRecord, RatingRecord

def make_usage_record(session_id="sess-1", **kwargs):
    defaults = dict(
        session_id=session_id,
        timestamp="2025-06-08T12:00:00Z",
        command="run",
        mode="standard",
        original_token_estimate=100,
        optimized_token_estimate=60,
        tool_input_tokens=50,
        tool_output_tokens=80,
        tool_total_tokens=130,
        provider="anthropic",
        model="claude-haiku-3-5",
        issues_detected=3,
        questions_asked=3,
        questions_answered=3,
        reduction_pct=40.0,
    )
    defaults.update(kwargs)
    return UsageRecord(**defaults)

def test_record_writes_session_line(tmp_path):
    log = UsageLogger(tmp_path / "usage.jsonl")
    rec = make_usage_record()
    log.record(rec)
    lines = (tmp_path / "usage.jsonl").read_text().strip().split("\n")
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["session_id"] == "sess-1"
    assert data["record_type"] == "session"

def test_record_rating_writes_rating_line(tmp_path):
    log = UsageLogger(tmp_path / "usage.jsonl")
    log.record_rating("sess-1", 1)
    lines = (tmp_path / "usage.jsonl").read_text().strip().split("\n")
    data = json.loads(lines[0])
    assert data["record_type"] == "rating"
    assert data["rating"] == 1

def test_load_all_merges_session_and_rating(tmp_path):
    log = UsageLogger(tmp_path / "usage.jsonl")
    rec = make_usage_record("sess-1")
    log.record(rec)
    log.record_rating("sess-1", 1)
    records = log.load_all()
    assert len(records) == 1
    assert records[0].rating == 1

def test_load_all_skips_malformed_line(tmp_path, caplog):
    import logging
    logfile = tmp_path / "usage.jsonl"
    logfile.write_text('{"bad json\n{"record_type": "session", "session_id": "s1", "timestamp": "2025-06-08T12:00:00Z", "command": "run", "mode": "standard", "original_token_estimate": 10, "optimized_token_estimate": 8, "tool_input_tokens": 5, "tool_output_tokens": 5, "tool_total_tokens": 10, "provider": "anthropic", "model": "m", "issues_detected": 0, "questions_asked": 0, "questions_answered": 0, "reduction_pct": 0.0}\n')
    log = UsageLogger(logfile)
    with caplog.at_level(logging.WARNING):
        records = log.load_all()
    assert len(records) == 1
    assert any("malformed" in r.message.lower() or "Skipping" in r.message for r in caplog.records)

def test_export_writes_json_array(tmp_path):
    log = UsageLogger(tmp_path / "usage.jsonl")
    log.record(make_usage_record("s1"))
    log.record(make_usage_record("s2"))
    out = tmp_path / "out.json"
    log.export(out)
    data = json.loads(out.read_text())
    assert isinstance(data, list)
    assert len(data) == 2

def test_reset_with_skip_confirmation_deletes_file(tmp_path):
    log = UsageLogger(tmp_path / "usage.jsonl")
    log.record(make_usage_record())
    assert log.log_path.exists()
    log.reset(skip_confirmation=True)
    assert not log.log_path.exists()

def test_load_all_empty_file_returns_empty(tmp_path):
    log = UsageLogger(tmp_path / "missing.jsonl")
    assert log.load_all() == []
