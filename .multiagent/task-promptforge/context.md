# Task: PromptForge Phases 2–7 Implementation

## Original Request
Implement PromptForge v4 from plan-promptforge-v4.md. The full plan is at /Users/gmv/claude/plan-promptforge-v4.md.

## Roster
Architect + Engineer × multiple + QA + Reviewer

## Current State
- Phase 1 (skeleton) is COMPLETE — all __init__.py files, dataclasses in models.py, stub cli.py, pyproject.toml, system_prompt.txt all exist
- Branch: feat/implement-phases-2-7
- Repo root: /Users/gmv/claude/promptforge/

## Existing models (already correct per plan):
- src/promptforge/analyzer/models.py — Issue, IssueSeverity, AnalysisReport (with has_output_format_issue)
- src/promptforge/questions/models.py — ClarifyingQuestion, UserAnswer
- src/promptforge/assembler/models.py — PromptContext
- src/promptforge/synthesizer/models.py — OptimizedPrompt (with session_id, repo_slug, injected_files)
- src/promptforge/config/models.py — AppConfig, Provider, Model
- src/promptforge/stats/models.py — UsageRecord, RatingRecord
- src/promptforge/synthesizer/system_prompt.txt — exists

## What needs implementing (Phases 2–7):
- Phase 2: config/manager.py, config/providers.py, configure wizard in cli.py
- Phase 3: analyzer/detectors/ (6 detectors), analyzer/engine.py
- Phase 4: questions/engine.py, questions/templates.py, interviewer/terminal.py, assembler/context.py
- Phase 5: synthesizer/engine.py (MetaPromptBuilder + LiteLLM), stats/logger.py, renderer/display.py, wire cli.py
- Phase 6: CLI hardening, error handling, integration tests
- Phase 7: stats/engine.py, stats/display.py, stats/pricing.py, promptforge stats command, README

## Key constraints from plan:
1. stdout = OptimizedPrompt.text ONLY; all UI/errors go to stderr
2. Exactly ONE LiteLLM call per session, in synthesizer/engine.py only
3. Mock LLM at HTTP level using respx (not litellm.completion directly)
4. File permissions: os.chmod(config_path, 0o600) on write (if sys.platform != "win32")
5. Clipboard and rating collection are always non-fatal
6. UsageLogger writes TWO records: session record (before Renderer), rating record (after rating)
7. Synthesizer must NOT import UsageLogger
8. Rating collection requires BOTH sys.stdin.isatty() AND sys.stderr.isatty()
9. Input precedence in run: --file > positional > stdin
10. Copilot: use "openai/gpt-4o" with base_url="https://api.githubcopilot.com" (openai-compatible endpoint)
