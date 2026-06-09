# PromptForge Implementation Review

## BLOCKER

**B1 — `cli.py:109` — Broad except exits 2, but plan §9 requires exit 99 for non-LLM exceptions.**
The final `except Exception` in `_run_pipeline` exits with code 2 (`raise typer.Exit(2)`). Per the plan (Slice 10), a broad/unexpected failure must exit 99. Exit 2 is reserved for known LLM exceptions. Fix: change `raise typer.Exit(2)` on line 109 to `raise typer.Exit(99)`.

**B2 — `stats/logger.py:57` — `UsageRecord(**data)` strips `record_type` before constructing. CONFIRMED SAFE.** `UsageRecord` has `record_type: str = "session"` (default) and `RatingRecord` has `record_type: str = "rating"`. The `asdict()` output includes `record_type`, so `load_all()` discriminates correctly. The strip `{k: v ... if k != "record_type"}` correctly prevents duplicate-kwarg errors. **PASS — not a blocker.**

**B3 — `renderer/display.py:88` — TTY guard is checked BEFORE the `readchar` import, but the import happens INSIDE the guarded block — correct. However, the import is inside `try/except Exception` which swallows `ImportError`.** If `readchar` is not installed, it silently skips with a misleading warning ("non-TTY?"). This is acceptable per "non-fatal" requirement, but the log message is misleading. NIT-level unless CI doesn't install readchar and tests pass incorrectly — in that case CONCERN.

## CONCERN

**C1 — `synthesizer/engine.py` — Does NOT import `UsageLogger`. PASS.**

**C2 — `renderer/display.py:29-31` — stdout = raw text only. PASS.** `sys.stdout.write(optimized.text)` with no Rich markup. Correct.

**C3 — `config/manager.py:67` — `os.chmod` is guarded by `sys.platform != "win32"`. PASS.**

**C4 — API key in logs — `cli.py` and `manager.py` log model/provider, not api_key. PASS.** No key appears in log calls.

**C5 — `renderer/display.py:88` — TTY guard `sys.stdin.isatty() and sys.stderr.isatty()` is checked BEFORE `readchar` call. PASS.**

**C6 — LLM error handling — cli.py handles: `AuthenticationError`, `RateLimitError`, `Timeout`, `APIConnectionError`, `BadRequestError`, `ServiceUnavailableError`. That is 6 types (Timeout + APIConnectionError caught together). PASS.** Broad `except` catches remainder → exit 2 (see B1).

**C7 — Two-record types written correctly. PASS.** Both `UsageRecord` and `RatingRecord` have `record_type` fields with correct defaults (`"session"` / `"rating"`). `asdict()` includes them. `load_all()` discriminates correctly and merges ratings into session records. Confirmed correct.

## NIT

**N1 — `renderer/display.py:103` — Warning says "non-TTY?" but we already checked TTY above.** More accurate: "readchar error or not installed".

**N2 — `logger.py:73` — `reset()` uses `raise SystemExit(...)` with a string message.** `sys.exit(1)` or `raise typer.Exit(1)` would be more idiomatic; the string will print as `str(e)` in the stats command handler which re-catches it.

**N3 — `cli.py:91` — `(litellm.Timeout, litellm.APIConnectionError)` caught together.** Plan §9 says "all 6 exception types" — combining two in a tuple is fine, but they produce the same hint. If distinct hints are required per exception, split them.

---

## Action Required Before Landing

1. Fix B1 (the only true blocker): `cli.py:109` — change `raise typer.Exit(2)` in the broad `except Exception` handler to `raise typer.Exit(99)`.
2. All other checks passed. No API key in logs, no UsageLogger import in synthesizer, TTY guard correct, chmod guarded, 6 LLM exception types handled, two-record types written and merged correctly.
