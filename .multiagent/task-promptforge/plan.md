# PromptForge Implementation Plan (Phases 2–7)

## Stack Summary

Python 3.11+, Typer/Rich CLI, LiteLLM for the single LLM call per session (httpx transport), TOML config,
pytest + respx for tests. All dataclasses in `models.py` files are already correct — do not touch them.

---

## Slices

### Slice 1 — Config providers + manager (Phase 2)
Files: `src/promptforge/config/providers.py`, `src/promptforge/config/manager.py`

- `providers.py`: Define `PROVIDERS: list[Provider]` — 6 providers (OpenAI, Anthropic, Google, Mistral, Groq, Copilot). Each `Model` has a non-empty `litellm_string`. Copilot: use `"openai/gpt-4o"` with `base_url="https://api.githubcopilot.com"` per context.md constraint 10; encode that base_url as a module constant `COPILOT_BASE_URL`.
- `manager.py`: `ConfigManager` — `CONFIG_PATH = Path.home() / ".config/promptforge/config.toml"`. Methods: `load() -> AppConfig` (raises `ConfigError` if missing/malformed), `save(config: AppConfig) -> None` (tomli-w write + `os.chmod(0o600)` guarded by `sys.platform != "win32"`), `validate_key(config: AppConfig) -> bool` (1-token LiteLLM call; raises on non-auth exceptions, returns False on AuthenticationError).
- Tests: `tests/unit/config/test_providers.py`, `tests/unit/config/test_manager.py` — use `tmp_path` for all disk I/O; mock LiteLLM http call with respx for `validate_key`.

### Slice 2 — Configure wizard in cli.py (Phase 2)
Files: `src/promptforge/cli.py` (configure command only)

- Replace `_not_implemented("configure")` with full wizard: numbered provider list → model list → masked key input → `ConfigManager.validate_key()` (max 3 attempts, exit 2 on exhaustion) → `ConfigManager.save()`. All output via `typer.echo(..., err=True)`. Exit 0 on success, 1 on user cancel, 2 on 3 failed validations.
- Tests: `tests/integration/test_configure_command.py` — mock respx for validation, `tmp_path` for config write, assert file permissions = 0o600.

### Slice 3 — All 7 detectors (Phase 3)
Files: `src/promptforge/analyzer/detectors/` — 7 files:
`missing_context.py`, `audience.py`, `output_format.py`, `scope.py`, `input_schema.py`, `action_verb.py`, `examples.py`

- Each detector is a module-level function. Six use `detect(raw_prompt: str) -> list[Issue]`. `examples.py` uses `detect(raw_prompt: str, analysis_report: AnalysisReport) -> list[Issue]`.
- Implement algorithms exactly per §8.1. `output_format.py` first (its keyword list is shared by `examples.py` logic via `analysis_report.has_output_format_issue`, not direct import).
- Tests: `tests/unit/analyzer/detectors/` — 7 test files, ≥3 cases each. `test_missing_context.py` must include mid-prompt pronoun no-fire cases. `test_examples.py` must test both `has_output_format_issue=True` and `False`.

### Slice 4 — Analyzer engine (Phase 3)
Files: `src/promptforge/analyzer/engine.py`

- `class Analyzer`: `DETECTOR_REGISTRY` list, `analyze(raw_prompt: str) -> AnalysisReport`. Runs pure detectors, sets `has_output_format_issue` after `OutputFormatDetector`, calls `ExampleDetector` last with partially-built report. Catches per-detector exceptions → WARNING log, skip detector. Computes `detected_intent`/`detected_domain` via keyword scan (§8.1). Populates `issue_count_by_severity`.
- Tests: `tests/unit/analyzer/test_engine.py` — all detectors called, exception in one detector doesn't abort, empty prompt, intent/domain heuristics.

### Slice 5 — Question engine + templates (Phase 4)
Files: `src/promptforge/questions/templates.py`, `src/promptforge/questions/engine.py`

- `templates.py`: `TEMPLATES: dict[str, ClarifyingQuestion]` — 7 entries per §8.2. Note: `source_issue_ids` and `is_required` fields from `ClarifyingQuestion` model must be populated; templates without fragments use static text; fragment templates use `"{fragment}"` placeholder.
- `engine.py`: `class QuestionEngine`: `generate(report: AnalysisReport) -> list[ClarifyingQuestion]`. Sort HIGH→MEDIUM→LOW, deduplicate by `question_id`, fill `{fragment}` from `issue.fragment`, cap at 7.
- Tests: `tests/unit/questions/test_engine.py`, `tests/unit/questions/test_templates.py`.

### Slice 6 — Interviewer + ContextAssembler (Phase 4)
Files: `src/promptforge/interviewer/terminal.py`, `src/promptforge/assembler/context.py`

- `terminal.py`: `class Interviewer`. `conduct(questions: list[ClarifyingQuestion], batch: bool) -> list[UserAnswer]`. Interactive: Rich prompt per question to stderr, reads from stdin. Batch: prints all questions to stderr then reads answers sequentially. All prompts/output to stderr via `Console(stderr=True)`.
- `context.py`: `class ContextAssembler`. `assemble(raw_prompt: str, report: AnalysisReport, answers: list[UserAnswer]) -> PromptContext`. Maps answers by `question_id` to `PromptContext` fields. Null for skipped/missing.
- Tests: `tests/unit/assembler/test_context.py` — all fields, nulls for skipped, empty answer list. Interviewer unit tests mock stdin/Rich.

### Slice 7 — UsageLogger (Phase 5)
Files: `src/promptforge/stats/logger.py`

- `class UsageLogger(log_path: Path)`. Public methods: `record(usage_record: UsageRecord) -> None`, `record_rating(session_id: str, rating: int) -> None`, `load_all() -> list[UsageRecord]`, `reset(skip_confirmation: bool = False) -> None`, `export(output_path: Path) -> None`.
- `load_all()`: parse JSONL, build session dict, patch ratings in, skip malformed lines with WARNING.
- `reset()`: if not skip_confirmation and not `sys.stdin.isatty()` → print error and exit 1. Otherwise confirm then truncate file.
- Tests: `tests/unit/stats/test_logger.py` — two-record merge, malformed line skip, `load_all()` returns merged list, `reset` with `--yes` vs TTY check, `export` produces valid JSON array.

### Slice 8 — Synthesizer engine (Phase 5)
Files: `src/promptforge/synthesizer/engine.py`

- `class MetaPromptBuilder`. `build(context: PromptContext) -> list[dict]` — returns `[system_msg, user_msg]`. Loads `system_prompt.txt` via `importlib.resources.files("promptforge.synthesizer").joinpath("system_prompt.txt").read_text(encoding="utf-8")`. Omits null fields. Truncates `additional_context` then `scope_constraints` if estimated tokens > 1500.
- `class Synthesizer`. `synthesize(context: PromptContext, config: AppConfig) -> OptimizedPrompt`. Calls `litellm.completion(model=config.litellm_model_string, ...)`. Generates `session_id = str(uuid4())`. Does NOT import `UsageLogger`.
- Tests: `tests/unit/synthesizer/test_meta_prompt_builder.py` — null field omission, truncation. Synthesizer tests mock at httpx level via respx; assert `UsageLogger` not in imports via AST or grep.

### Slice 9 — Renderer (Phase 5)
Files: `src/promptforge/renderer/display.py`

- `class Renderer`. `render(optimized: OptimizedPrompt, raw_prompt: str, output_path: Path | None, no_clipboard: bool, show_diff: bool, usage_logger: UsageLogger) -> None`. Follows §8.4a order exactly: stdout write → Rich panel stderr → diff stderr → file write → clipboard → rating collection.
- Rating: TTY guard `sys.stdin.isatty() and sys.stderr.isatty()` before readchar. `try/except Exception` around readchar call. On y/n: `usage_logger.record_rating(session_id, rating)`.
- Tests: `tests/unit/` — mock pyperclip, readchar, sys.stdin.isatty/sys.stderr.isatty. Assert stdout = raw text only, rating path writes RatingRecord, skip path writes nothing.

### Slice 10 — Wire cli.py run/correct + integration tests (Phase 6)
Files: `src/promptforge/cli.py` (run + correct), `tests/integration/test_run_command.py`, `tests/integration/test_correct_command.py`

- `run`: resolve input by `--file > positional > stdin`. Guard: no config → "Run promptforge configure first." exit 1. File > 50KB → InputError exit 1. Full pipeline per §5.11: Analyzer → QuestionEngine → Interviewer (skip if `--no-questions`) → ContextAssembler → Synthesizer → `UsageLogger.record()` (non-fatal on error) → Renderer.
- LLM error handling per §9: catch each LiteLLM exception class, print hint to stderr, exit 2. Broad except → exit 99.
- `correct`: one-liner reads file, calls run pipeline.
- `--debug`: log full tracebacks, meta-prompt, raw LLM response, per-detector issues to stderr.
- Integration tests use respx for HTTP mock, `typer.testing.CliRunner` with `mix_stderr=False`. Assert stdout = raw text, each LLM error sub-type produces correct stderr hint + exit 2.

### Slice 11 — Stats engine + display + pricing + stats command (Phase 7)
Files: `src/promptforge/stats/engine.py`, `src/promptforge/stats/display.py`, `src/promptforge/stats/pricing.py`, `src/promptforge/cli.py` (stats command), `tests/integration/test_stats_command.py`

- `pricing.py`: `PRICING: dict[str, tuple[float, float]]` — model → (input $/1M, output $/1M). Include dated disclaimer comment.
- `engine.py`: `class StatsEngine`. Pure computation functions: `compute_summary(records: list[UsageRecord]) -> dict`, `compute_savings(records, reuse_n: int) -> dict`, `filter_last(records, n: int) -> list[UsageRecord]`.
- `display.py`: `class StatsRenderer`. `render_summary(...)`, `render_detailed(...)`, `render_projection(...)` — all to stderr via Rich.
- `stats` command: load records from `UsageLogger.load_all()`, apply `--last` filter, branch on `--reset`/`--export`/`--detailed`/default. `--reset` without `--yes` in non-TTY → exit 1.
- Tests: summary, detailed, reuse projection, reset TTY guard, export.

### Slice 12 — README.md (Phase 7)
Files: `README.md`

- Write per §17 spec. Include Linux clipboard note, `pip-audit` mention, platform support note.

---

## Contracts (cross-module boundaries)

| Symbol | Signature | Returns |
|---|---|---|
| `ConfigManager.load` | `() -> AppConfig` | `AppConfig`; raises `ConfigError` |
| `ConfigManager.save` | `(config: AppConfig) -> None` | None; sets chmod 600 |
| `ConfigManager.validate_key` | `(config: AppConfig) -> bool` | `True` if valid |
| `ProviderRegistry.get_providers` | `() -> list[Provider]` | All 6 providers |
| `Analyzer.analyze` | `(raw_prompt: str) -> AnalysisReport` | `AnalysisReport` |
| `QuestionEngine.generate` | `(report: AnalysisReport) -> list[ClarifyingQuestion]` | Max 7 questions |
| `Interviewer.conduct` | `(questions: list[ClarifyingQuestion], batch: bool) -> list[UserAnswer]` | `list[UserAnswer]` |
| `ContextAssembler.assemble` | `(raw_prompt: str, report: AnalysisReport, answers: list[UserAnswer]) -> PromptContext` | `PromptContext` |
| `MetaPromptBuilder.build` | `(context: PromptContext) -> list[dict]` | `[system_msg, user_msg]` |
| `Synthesizer.synthesize` | `(context: PromptContext, config: AppConfig) -> OptimizedPrompt` | `OptimizedPrompt` with `session_id` |
| `UsageLogger.record` | `(usage_record: UsageRecord) -> None` | None |
| `UsageLogger.record_rating` | `(session_id: str, rating: int) -> None` | None |
| `UsageLogger.load_all` | `() -> list[UsageRecord]` | Merged records |
| `Renderer.render` | `(optimized: OptimizedPrompt, raw_prompt: str, output_path: Path | None, no_clipboard: bool, show_diff: bool, usage_logger: UsageLogger) -> None` | None |
| `StatsEngine.compute_summary` | `(records: list[UsageRecord]) -> dict` | Stats dict |

---

## Test Strategy

- **Slices 1–9 (unit)**: All disk I/O uses `tmp_path`. LiteLLM HTTP calls mocked with `respx`. `pyperclip` and `readchar` mocked with `pytest-mock`. TTY checks mocked via `mocker.patch("sys.stdin.isatty", return_value=...)`. `tests/fixtures.py` factory functions: `make_issue()`, `make_analysis_report()`, `make_prompt_context()`, `make_app_config()`, `make_usage_record()`, `make_optimized_prompt()`.
- **Slices 10–11 (integration)**: `typer.testing.CliRunner(mix_stderr=False)`. respx intercepts LiteLLM httpx calls. Assert `result.stdout == optimized_prompt_text` exactly. Assert each LLM exception → exit 2 + hint in stderr.
- **Never** mock `litellm.completion` at the function level — always respx at httpx layer.

---

## Risks / ESCALATE Flags

1. **ESCALATE — Copilot LiteLLM prefix**: context.md says use `"openai/gpt-4o"` + `base_url="https://api.githubcopilot.com"`. This may require passing `base_url` to `litellm.completion()` or setting an env var. `AppConfig` has no `litellm_base_url` field per the plan — engineer must decide: add field (schema change) or pass `base_url` conditionally in Synthesizer. This is an architectural decision. Surface before Slice 1 lands.

2. **Copilot base_url in AppConfig**: If field is added to `AppConfig`, `config.toml` schema and `ConfigManager` read/write must also change. Verify against Slice 1 before Slice 8 begins.

3. **respx + LiteLLM version pinning**: `httpx >=0.27,<0.29` must be pinned in dev deps. Verify `respx` intercepts LiteLLM's requests in the exact pinned version before Slice 8. Unblock early (can be tested in a scratch test in Slice 1).
