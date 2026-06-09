"""Unit tests for Renderer."""
from unittest.mock import MagicMock, patch

import pyperclip

from promptforge.renderer.display import Renderer
from promptforge.synthesizer.models import OptimizedPrompt


def make_optimized(text="You are an expert. Do the task.") -> OptimizedPrompt:
    return OptimizedPrompt(
        text=text,
        token_estimate=10,
        sections={},
        model_used="anthropic/claude-haiku-3-5",
        session_id="test-session-id",
        repo_slug=None,
        injected_files=[],
    )


def make_mock_usage_logger():
    mock = MagicMock()
    mock.record_rating = MagicMock()
    return mock


def test_render_writes_raw_text_to_stdout(capsys):
    renderer = Renderer()
    optimized = make_optimized("Optimized prompt text.")
    with (
        patch("pyperclip.copy"),
        patch("sys.stdin.isatty", return_value=False),
        patch("sys.stderr.isatty", return_value=False),
    ):
        renderer.render(optimized, "original", no_clipboard=True, usage_logger=None)
    captured = capsys.readouterr()
    assert "Optimized prompt text." in captured.out


def test_render_clipboard_called_with_text(capsys):
    renderer = Renderer()
    optimized = make_optimized("clipboard content")
    with (
        patch("pyperclip.copy") as mock_copy,
        patch("sys.stdin.isatty", return_value=False),
    ):
        renderer.render(optimized, "orig", no_clipboard=False, usage_logger=None)
    mock_copy.assert_called_once_with("clipboard content")


def test_render_no_clipboard_skips_pyperclip(capsys):
    renderer = Renderer()
    optimized = make_optimized("some text")
    with patch("pyperclip.copy") as mock_copy:
        renderer.render(optimized, "orig", no_clipboard=True, usage_logger=None)
    mock_copy.assert_not_called()


def test_render_clipboard_exception_is_non_fatal(capsys):
    renderer = Renderer()
    optimized = make_optimized("text")
    with (
        patch("pyperclip.copy", side_effect=pyperclip.PyperclipException("no clipboard")),
        patch("sys.stdin.isatty", return_value=False),
    ):
        # Should not raise
        renderer.render(optimized, "orig", no_clipboard=False, usage_logger=None)


def test_render_output_file_written(tmp_path, capsys):
    renderer = Renderer()
    optimized = make_optimized("written content")
    out_file = tmp_path / "out.txt"
    with (
        patch("pyperclip.copy"),
        patch("sys.stdin.isatty", return_value=False),
    ):
        renderer.render(optimized, "orig", output_path=out_file, no_clipboard=True, usage_logger=None)
    assert out_file.read_text() == "written content"


def test_render_rating_skipped_when_non_tty(capsys):
    renderer = Renderer()
    optimized = make_optimized()
    mock_logger = make_mock_usage_logger()
    with (
        patch("pyperclip.copy"),
        patch("sys.stdin.isatty", return_value=False),
        patch("sys.stderr.isatty", return_value=True),
    ):
        renderer.render(optimized, "orig", no_clipboard=True, usage_logger=mock_logger)
    mock_logger.record_rating.assert_not_called()


def test_render_rating_y_writes_record(capsys):
    renderer = Renderer()
    optimized = make_optimized()
    mock_logger = make_mock_usage_logger()
    with (
        patch("pyperclip.copy"),
        patch("sys.stdin.isatty", return_value=True),
        patch("sys.stderr.isatty", return_value=True),
        patch("readchar.readchar", return_value="y"),
    ):
        renderer.render(optimized, "orig", no_clipboard=True, usage_logger=mock_logger)
    mock_logger.record_rating.assert_called_once_with("test-session-id", 1)


def test_render_rating_n_writes_negative_record(capsys):
    renderer = Renderer()
    optimized = make_optimized()
    mock_logger = make_mock_usage_logger()
    with (
        patch("pyperclip.copy"),
        patch("sys.stdin.isatty", return_value=True),
        patch("sys.stderr.isatty", return_value=True),
        patch("readchar.readchar", return_value="n"),
    ):
        renderer.render(optimized, "orig", no_clipboard=True, usage_logger=mock_logger)
    mock_logger.record_rating.assert_called_once_with("test-session-id", -1)


def test_render_rating_s_no_record_written(capsys):
    renderer = Renderer()
    optimized = make_optimized()
    mock_logger = make_mock_usage_logger()
    with (
        patch("pyperclip.copy"),
        patch("sys.stdin.isatty", return_value=True),
        patch("sys.stderr.isatty", return_value=True),
        patch("readchar.readchar", return_value="s"),
    ):
        renderer.render(optimized, "orig", no_clipboard=True, usage_logger=mock_logger)
    mock_logger.record_rating.assert_not_called()


def test_render_diff_displayed(capsys):
    renderer = Renderer()
    optimized = make_optimized("You are an expert. Refactor the code cleanly.")
    with (
        patch("pyperclip.copy"),
        patch("sys.stdin.isatty", return_value=False),
    ):
        renderer.render(optimized, "help me fix the code", no_clipboard=True, show_diff=True, usage_logger=None)
    # Diff was called — stdout still contains raw text
    captured = capsys.readouterr()
    assert "You are an expert." in captured.out


def test_render_readchar_exception_treated_as_skip(capsys):
    renderer = Renderer()
    optimized = make_optimized()
    mock_logger = make_mock_usage_logger()
    with (
        patch("pyperclip.copy"),
        patch("sys.stdin.isatty", return_value=True),
        patch("sys.stderr.isatty", return_value=True),
        patch("readchar.readchar", side_effect=OSError("not a tty")),
    ):
        renderer.render(optimized, "orig", no_clipboard=True, usage_logger=mock_logger)
    mock_logger.record_rating.assert_not_called()
