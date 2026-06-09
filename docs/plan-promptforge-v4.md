# Plan: PromptForge v4

> AI-powered CLI tool that transforms vague prompts into token-efficient, structured prompts
> ready for any LLM agent — using rule-based analysis and a single LLM call per session.

---

## § 1 — Project Overview

PromptForge is a Python CLI tool installed globally via `pip install promptforge` (or `pipx install promptforge`).
It accepts a vague, poorly formed prompt from the user, runs it through a rule-based analysis pipeline to detect
ambiguity, missing context, and unclear input/output expectations — then asks targeted clarifying questions in the
terminal. Once all context is gathered, it makes a single LLM API call to synthesize a final prompt that is
structured, unambiguous, token-efficient, and ready to be pasted into any AI agent or LLM interface.

The tool is designed for developers, prompt engineers, and power users who repeatedly write prompts to LLM agents
and want to stop burning tokens on vague retries. The core constraint is token economy: the tool itself costs one
small-model API call per session, and the output prompt must be leaner than the original input while being
dramatically more precise.

---

## § 2 — Goals & Non-Goals

### Goals

1. `pip install promptforge` and `pipx install promptforge` both work on macOS and Linux (including WSL). Native Windows is not a supported target.
2. `promptforge configure` launches an interactive wizard that lets the user select provider, model, and enter their API key — key is validated before saving.
3. `promptforge run` accepts a vague prompt (inline, piped, or from a file) and produces an optimized prompt.
4. Rule-based analysis detects at minimum: missing context, undefined audience, unclear output format, undefined scope, missing input/output examples, and ambiguous action verbs — without any LLM call.
5. Clarifying questions are generated from the rule analysis results and asked one-by-one interactively (default) or all-at-once via `--batch` flag.
6. Exactly one LLM API call is made per `run` session — at the final synthesis step only.
7. The output prompt includes: a role definition, explicit step-by-step instructions, defined input schema, defined output schema, constraints, and an example if applicable.
8. `--diff` flag shows a before/after comparison of original vs. optimized prompt.
9. Supported providers at launch: OpenAI (ChatGPT), Anthropic (Claude), Google Gemini, Mistral, Groq, and GitHub Copilot — with their respective model lists surfaced in the configure wizard.
10. Unit test coverage ≥ 85% on all rule-based modules; LLM calls mocked in all tests.
11. `promptforge correct <file>` is a convenience alias for `promptforge run --file <file>` — it accepts an existing prompt file and runs the same pipeline. Accepts all `run` flags.
12. `promptforge repo add <path|url>` indexes a local or remote git repository into a structured cache — supports both local paths and GitHub HTTPS URLs.
13. `promptforge repo ask "question"` generates a repo-aware optimized prompt using the indexed repo context — auto-injects relevant code snippets via `--inject-code` flag or describes structure by default.
14. Every repo-aware session stores the optimized prompt as a named template scoped to that repo — reusable in future sessions.
15. After every `run`, `correct`, or `repo ask` session, the user is prompted for a thumbs-up/thumbs-down rating with a single keypress (no Enter required). Ratings are stored in `usage_log.jsonl` and used to surface which prompt patterns work best per repo.
16. `promptforge stats` tracks both token savings (standard mode) and interaction reduction (repo mode) — showing estimated LLM turns saved alongside token counts.

### Non-Goals

- No web UI, API server, or GUI — CLI only.
- No local/offline LLM support (Ollama, llama.cpp) — out of scope for this version.
- No team/multi-user config sharing.
- No plugin system or custom rule authoring in this version.
- No streaming output from the LLM — wait for full response then display.
- No automatic deployment or CI/CD pipeline — developer runs tests locally.
- No indexing of binary files, images, or non-text assets in repos.
- No automatic repo re-index on file change (file watching) — user runs `promptforge repo refresh` manually.
- No native Windows support (macOS and Linux including WSL only). `os.chmod` for key file security is not meaningful on NTFS.

---

## § 3 — Technology Stack

| Layer | Technology | Why chosen |
|---|---|---|
| Language | Python 3.11+ | Required by user; modern typing, walrus operator, tomllib built-in |
| CLI framework | Typer 0.12+ | Auto-generates `--help`, type hints drive argument parsing, `rich` integration built-in |
| Terminal output | Rich 13+ | Panels, syntax highlighting, progress spinners, diff display — all in one library |
| LLM client | LiteLLM 1.40+ | Single interface for OpenAI, Anthropic, Gemini, Mistral, Groq, Copilot — one call pattern for all |
| Copilot access | LiteLLM Copilot provider (exact prefix TBD — see § 15) | Provider prefix and auth header format must be verified against the installed LiteLLM version *before* Phase 2 lands. Candidate prefixes: `github/`, `github_copilot/`, or a custom endpoint config. Do not assert one without testing. |
| HTTP client (LiteLLM transport) | `httpx >=0.27,<0.29` | Pinned in dev/test deps so `respx` mocking remains compatible with whatever httpx LiteLLM resolves |
| Clipboard | pyperclip 1.8+ | Cross-platform clipboard write (macOS, Linux); single function call |
| Single keypress input | readchar 4.0+ | Captures y/n/s for rating prompt without requiring Enter; cross-platform (termios on macOS/Linux) |
| Repo parsing — local | `pathlib` (stdlib) + `gitpython 3.1+` | Walk repo tree, read git metadata. **Added in Phase 8 only** — not required for Phases 1–7. |
| Repo parsing — remote | `PyGithub 2.0+` | GitHub REST API client — fetch repo tree, file contents, languages; handles auth token |
| Snippet relevance ranking | `rapidfuzz 3.0+` | Fuzzy string matching to rank which files/functions are most relevant to the user's question — no ML, fast |
| Config storage | TOML via `tomllib` (stdlib) + `tomli-w` for writing | Built-in read (Python 3.11+), minimal write dependency, human-readable config |
| Repo index storage | JSON files in `~/.config/promptforge/repos/<repo-slug>/` | One JSON index file per repo; human-readable, no database dependency |
| Rule engine | Pure Python — no NLP library | Regex + heuristics sufficient for vagueness detection |
| Testing | pytest 8+ | Industry standard, parametrize for table-driven tests, clean fixture model |
| HTTP mocking | respx 0.21+ | Mocks httpx requests — LiteLLM 1.40+ uses httpx as its HTTP client. `responses` only mocks the `requests` library and will not intercept LiteLLM calls |
| Other mocking | pytest-mock | Mock non-HTTP calls (pyperclip, readchar, os.chmod, filesystem) |
| Build/packaging | Hatch (hatchling backend) | Modern PEP 517/518 compliant, replaces setup.py |
| Linting | Ruff | Fastest Python linter, replaces flake8 + isort + pyupgrade in one tool |
| Type checking | mypy (strict mode) | Catches contract violations before runtime |
| Python version management | Requires Python 3.11+ — documented in README, no shim layer | Keep it simple; 3.11 is widely available |

---

## § 4 — Architecture

**Pattern: Layered Pipeline (Linear Command Architecture)**

A CLI tool with a linear data pipeline is not a web service — it does not need hexagonal ports, CQRS, or
microservices. The architecture is a single-process layered pipeline where each stage transforms data and
passes it to the next. Stages are independently testable because they take pure inputs and return pure outputs.

**Why not microservices or hexagonal:** Solo CLI tool, no concurrent users, no network boundary between
components. Adding abstraction layers here increases complexity with zero benefit.

**Why pipeline over event-driven:** Data flows in one direction — raw prompt in, optimized prompt out.
No fan-out, no async consumers, no retry queues needed.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLI Entry Point (Typer)                      │
│              promptforge run / correct / configure                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │ raw prompt string
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Analyzer (Rule Engine)                         │
│  • Runs all detectors against raw prompt                            │
│  • Returns: AnalysisReport(issues[], severity, detected_context)    │
│  • Zero LLM calls                                                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │ AnalysisReport
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Question Engine                                  │
│  • Maps each issue → targeted clarifying question                   │
│  • Returns: List[ClarifyingQuestion]                                │
│  • Zero LLM calls                                                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │ List[ClarifyingQuestion]
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Interviewer (Terminal I/O)                        │
│  • Interactive mode: ask one-by-one, collect answers                │
│  • Batch mode (--batch): print all, read answers in one pass        │
│  • Returns: List[UserAnswer]                                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │ List[UserAnswer]
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Context Assembler                                │
│  • Merges raw prompt + analysis + user answers                      │
│  • Builds structured PromptContext object                           │
│  • Zero LLM calls                                                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │ PromptContext
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Synthesizer (Single LLM Call)                    │
│  • Builds a tightly constrained meta-prompt from PromptContext      │
│  • Calls LiteLLM with user's configured provider + model            │
│  • Writes initial UsageRecord (rating=None) to usage_log.jsonl      │
│  • Returns: OptimizedPrompt                                         │
│  • THIS IS THE ONLY LLM CALL IN THE ENTIRE PIPELINE                │
└────────────────────────────┬────────────────────────────────────────┘
                             │ OptimizedPrompt
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Renderer (Rich terminal output)                  │
│  • Displays optimized prompt in a Rich panel (to stderr)            │
│  • Writes raw prompt text to stdout                                 │
│  • --diff: shows side-by-side original vs optimized (to stderr)     │
│  • --output <file>: writes raw text to file                         │
│  • Copies raw text to system clipboard (pyperclip)                  │
│  • Prompts for rating (readchar — single keypress)                  │
│  • Writes RatingRecord to usage_log.jsonl if rated                  │
└─────────────────────────────────────────────────────────────────────┘
```

**Stdout/stderr contract (enforced from Phase 1 — not retrofitted):**
- **stdout**: only `OptimizedPrompt.text` (the raw optimized prompt string, no decoration)
- **stderr**: all Rich panels, progress spinners, questions, error messages, warnings, debug output
- Rationale: `promptforge run "..." > prompt.txt` must write only clean prompt text to the file.
  All interactive UI remains visible in the terminal via stderr.

**Config layer** sits orthogonally — loaded at startup by every stage that needs provider/model/key.
It is never passed through the pipeline; each stage reads it directly from `ConfigManager`.

---

## § 5 — Module / Component Breakdown

### 5.1 `cli.py` — Entry Point
- **Responsibility:** Defines all Typer commands (`run`, `correct`, `configure`, `version`, `stats`, `repo`). Wires pipeline stages. Handles top-level exceptions and exits with correct codes.
- **Input:** Raw CLI arguments from terminal.
- **Output:** Exit code 0 (success) or non-zero (failure). `OptimizedPrompt.text` written to stdout.
- **Dependencies:** All pipeline modules, `ConfigManager`, `Renderer`.
- **Key classes:** None — pure Typer command functions.
- **Note on `correct`:** Implemented as a one-line wrapper that calls the `run` pipeline with `input_path` set. No separate pipeline logic.

### 5.2 `config/manager.py` — ConfigManager
- **Responsibility:** Reads, writes, and validates `~/.config/promptforge/config.toml`. Runs the interactive configure wizard. Validates API key against provider before saving.
- **Input:** User terminal input (wizard) or `config.toml` on disk.
- **Output:** `AppConfig` dataclass consumed by `Synthesizer`.
- **Dependencies:** `tomllib` (read), `tomli-w` (write), `LiteLLM` (key validation), `Rich` (wizard UI).
- **Key classes:** `AppConfig`, `ConfigManager`, `ProviderRegistry`.

### 5.3 `config/providers.py` — ProviderRegistry
- **Responsibility:** Holds the static registry of all **6** supported providers and their available models. Source of truth for the configure wizard dropdown.
- **Input:** None — static data.
- **Output:** `List[Provider]`, `List[Model]` for a given provider.
- **Dependencies:** None.
- **Key classes:** `Provider`, `Model`, `ProviderRegistry`.
- **Copilot routing (TBD — see § 15 open question):** GitHub Copilot is accessed via the user's GitHub PAT (with `copilot` scope). The exact LiteLLM provider prefix (`github/`, `github_copilot/`, or a custom endpoint config) must be verified against the installed LiteLLM version *before* Phase 2 ships. The wizard prompts for a GitHub PAT instead of an API key when Copilot is selected. If no built-in LiteLLM Copilot provider exists in the pinned version, fall back to a custom config with `base_url = "https://api.githubcopilot.com"` and explicit `Authorization: Bearer <PAT>` header injection — but only after confirming the LiteLLM version's capabilities.

### 5.4 `analyzer/engine.py` — Analyzer
- **Responsibility:** Runs all registered `Detector` instances against the raw prompt string. Aggregates results into a single `AnalysisReport`.
- **Input:** `raw_prompt: str`
- **Output:** `AnalysisReport`
- **Dependencies:** All detectors in `analyzer/detectors/`.
- **Key classes:** `Analyzer`, `AnalysisReport`, `Issue`, `IssueSeverity`.
- **Registry location:** `DETECTOR_REGISTRY: list[Detector]` is defined in `analyzer/engine.py`. The `detectors/__init__.py` is empty. New detectors are added to `DETECTOR_REGISTRY` in `engine.py` — no other change needed.
- **Detector signature:** Each detector implements `def detect(raw_prompt: str) -> list[Issue]`. All detectors are pure functions. The one exception to the pure-string input rule is `ExampleDetector`, which takes `(raw_prompt: str, analysis_report: AnalysisReport)` — see §5.5.

### 5.5 `analyzer/detectors/` — Detector modules (one file per detector)
- **Responsibility:** Each detector checks for exactly one type of vagueness or missing information. Returns `List[Issue]` or empty list.
- **Input:** `raw_prompt: str` (all detectors). `ExampleDetector` additionally takes `analysis_report: AnalysisReport` to avoid inter-detector dependencies via the engine.
- **Output:** `List[Issue]`
- **Dependencies:** None — pure functions, no imports beyond `re` and the local `models.py`.
- **Key classes (one per file):**
  - `MissingContextDetector` — detects pronouns used as the opening subject with no prior referent (narrow scope — see §8.1 for exact algorithm)
  - `AudienceDetector` — detects absence of target audience/role definition
  - `OutputFormatDetector` — detects no specified output format (list? JSON? paragraph? code?)
  - `ScopeDetector` — detects unbounded scope ("everything", "all", "complete")
  - `InputSchemaDetector` — detects no defined input structure when input is implied
  - `ActionVerbDetector` — detects weak/ambiguous verbs ("help", "do", "make", "handle")
  - `ExampleDetector` — detects absence of examples when complexity warrants one; takes `AnalysisReport` as second argument so it can check whether output format issues were detected without calling `OutputFormatDetector` again

### 5.6 `questions/engine.py` — QuestionEngine
- **Responsibility:** Maps each `Issue` from the `AnalysisReport` to a targeted `ClarifyingQuestion`. Deduplicates questions if multiple issues map to the same question. Prioritizes by severity.
- **Input:** `AnalysisReport`
- **Output:** `List[ClarifyingQuestion]`
- **Dependencies:** `analyzer/engine.py` (for Issue types).
- **Key classes:** `QuestionEngine`, `ClarifyingQuestion`, `QuestionTemplate`.

### 5.7 `interviewer/terminal.py` — Interviewer
- **Responsibility:** Presents clarifying questions to the user in the terminal. Interactive mode: one question at a time with Rich formatting. Batch mode: prints all questions, reads answers sequentially.
- **Input:** `List[ClarifyingQuestion]`, `mode: InterviewMode` (INTERACTIVE | BATCH)
- **Output:** `List[UserAnswer]`
- **Dependencies:** `Rich` (display), `QuestionEngine` (types).
- **Key classes:** `Interviewer`, `UserAnswer`, `InterviewMode`.
- **Batch vs no-questions distinction:** BATCH mode shows all questions (HIGH + MEDIUM + LOW, up to the 7-question cap) and reads answers sequentially without waiting for Enter between questions. `--no-questions` skips the entire Interviewer stage and synthesizes directly from the raw prompt. Both modes still run the Analyzer.

### 5.8 `assembler/context.py` — ContextAssembler
- **Responsibility:** Merges raw prompt, `AnalysisReport`, and `List[UserAnswer]` into a single `PromptContext` object that fully describes what the final prompt must contain.
- **Input:** `raw_prompt: str`, `AnalysisReport`, `List[UserAnswer]`
- **Output:** `PromptContext`
- **Dependencies:** Analyzer and Interviewer types.
- **Key classes:** `ContextAssembler`, `PromptContext`.

### 5.9 `synthesizer/engine.py` — Synthesizer
- **Responsibility:** Builds a compact meta-prompt from `PromptContext`, calls LiteLLM exactly once, parses the response into `OptimizedPrompt`. Generates the `session_id` (uuid4) and attaches it to the returned `OptimizedPrompt`. This is the only module that touches the network. **Synthesizer does not touch disk** — usage logging is orchestrated by `cli.py`, not by Synthesizer (see § 5.11).
- **Input:** `PromptContext`, `AppConfig`
- **Output:** `OptimizedPrompt` (with `session_id` populated)
- **Dependencies:** `LiteLLM`, `ConfigManager`, `ContextAssembler` types. **No `UsageLogger` dependency.**
- **Key classes:** `Synthesizer`, `OptimizedPrompt`, `MetaPromptBuilder`.

### 5.10 `renderer/display.py` — Renderer
- **Responsibility:** Renders `OptimizedPrompt` in a fixed order (see § 8.4a). Writes raw `OptimizedPrompt.text` to stdout. Displays Rich panel, optional diff, clipboard status to stderr. Handles `--output` file write. Collects post-session rating via `readchar` **only if both stdin and stderr are TTYs**. Writes `RatingRecord` to `usage_log.jsonl` if user rates.
- **Input:** `OptimizedPrompt`, `raw_prompt: str` (for diff), `output_path: Optional[Path]`, `no_clipboard: bool`
- **Output:** stdout (raw text) + stderr (Rich UI) + optional file write + clipboard copy + optional rating write.
- **Dependencies:** `Rich`, `pyperclip`, `readchar`, `OptimizedPrompt` type, `UsageLogger`.
- **Key classes:** `Renderer`.

### 5.11 `cli.py` — Orchestration of UsageLogger between Synthesizer and Renderer
- The CLI command function is responsible for the sequence:
  1. Call `Synthesizer.synthesize()` → returns `OptimizedPrompt` with `session_id`
  2. Build `UsageRecord` from `OptimizedPrompt` + context metadata
  3. Call `UsageLogger.record(usage_record)` — disk write happens here, not in Synthesizer
  4. Call `Renderer.render(optimized_prompt)` — Renderer collects rating, calls `UsageLogger.record_rating()` if user rated
- This keeps Synthesizer pure (testable without disk I/O) and makes the write boundary explicit in the pipeline.
- If `UsageLogger.record()` raises (e.g. disk full), the CLI logs a WARNING to stderr but does **not** exit non-zero — the API spend already happened and the user still gets their result. Renderer is invoked regardless.

---

## § 6 — Data Design

No database. All state is in-memory within a single CLI invocation. Config and usage log persist to disk.

### 6.1 Core Dataclasses

```python
# analyzer/models.py

@dataclass
class Issue:
    detector_id: str          # e.g. "output_format", "action_verb"
    severity: IssueSeverity   # HIGH | MEDIUM | LOW
    description: str          # human-readable: "No output format specified"
    fragment: str             # the exact text fragment that triggered this issue

class IssueSeverity(Enum):
    HIGH = "high"       # blocks meaningful optimization — must ask question
    MEDIUM = "medium"   # degrades quality — ask if not resolved by other answers
    LOW = "low"         # nice-to-have — ask only if HIGH/MEDIUM all resolved

@dataclass
class AnalysisReport:
    raw_prompt: str
    issues: list[Issue]
    detected_intent: str      # best-guess one-liner: "generate code", "summarize text", etc.
    detected_domain: str      # best-guess: "software engineering", "writing", "data analysis", etc.
    issue_count_by_severity: dict[str, int]
    has_output_format_issue: bool  # True if OutputFormatDetector fired; exposed for ExampleDetector
```

```python
# questions/models.py

@dataclass
class ClarifyingQuestion:
    question_id: str          # unique, stable: "q_output_format", "q_audience"
    question_text: str        # what is shown to the user in the terminal
    source_issue_ids: list[str]   # which Issue detector_ids this resolves
    is_required: bool         # True if source issue is HIGH severity

@dataclass
class UserAnswer:
    question_id: str
    answer_text: str          # raw text the user typed
    skipped: bool             # True if user hit Enter with no input
```

```python
# assembler/models.py

@dataclass
class PromptContext:
    raw_prompt: str
    detected_intent: str
    detected_domain: str
    role_definition: str | None       # from UserAnswer or inferred
    target_audience: str | None
    output_format: str | None         # "JSON", "markdown list", "Python function", etc.
    output_schema: str | None         # field-level detail if format is structured
    input_description: str | None
    scope_constraints: list[str]      # explicit limits derived from answers
    examples_requested: bool
    additional_context: str | None    # free-form from any catch-all answers
```

```python
# synthesizer/models.py

@dataclass
class OptimizedPrompt:
    text: str                 # the full optimized prompt ready to copy-paste
    token_estimate: int       # rough count: len(text.split()) * 1.33
    sections: dict[str, str]  # keyed sections: "role", "task", "input", "output", "constraints"
    model_used: str           # e.g. "anthropic/claude-haiku-3-5"
    session_id: str           # uuid4 generated by Synthesizer — links to UsageRecord
    repo_slug: str | None     # set if generated in repo mode; e.g. "my-org/my-repo"
    injected_files: list[str] # file paths whose snippets were injected; empty if describe-only
```

```python
# config/models.py

@dataclass
class AppConfig:
    provider: str             # "anthropic" | "openai" | "google" | "mistral" | "groq" | "copilot"
    model: str                # e.g. "claude-haiku-3-5", "gpt-4o-mini"
    api_key: str              # API key for most providers; GitHub PAT for Copilot
    litellm_model_string: str # fully prefixed identifier — exact Copilot prefix is TBD (see §5.3)
    # No litellm_base_url field — LiteLLM resolves endpoints from the provider prefix.
    # If Phase 2 verification reveals Copilot needs a custom base_url, add it then with a clear contract.

    @property
    def masked_key(self) -> str:
        # Returns first 8 chars + "[REDACTED]" — use only this in logs, never api_key directly.
        # Fail-safe: for keys <= 8 chars (shouldn't happen with real provider keys),
        # returns just "[REDACTED]" with no visible prefix.
        return self.api_key[:8] + "[REDACTED]" if len(self.api_key) > 8 else "[REDACTED]"

@dataclass
class Provider:
    id: str                   # "anthropic" | "openai" | "google" | "mistral" | "groq" | "copilot"
    display_name: str         # "Anthropic (Claude)" | "OpenAI (ChatGPT)" | "Google Gemini" | "Mistral" | "Groq" | "GitHub Copilot"
    models: list[Model]
    auth_label: str           # "API Key" for most; "GitHub Personal Access Token (copilot scope)" for Copilot
    # Note: no litellm_prefix field — Model.litellm_string contains the fully prefixed identifier.
    #       Provider doesn't need a prefix because nothing reads it.

@dataclass
class Model:
    id: str                   # "claude-haiku-3-5"
    display_name: str         # "Claude Haiku 3.5 (fastest, cheapest — recommended)"
    litellm_string: str       # fully prefixed identifier, e.g. "anthropic/claude-haiku-3-5"
                              # (Copilot's exact prefix is set by Phase 2 verification — see §5.3)
    is_recommended: bool      # shown with ★ in wizard
```

### 6.2 Config File Schema (`~/.config/promptforge/config.toml`)

```toml
[llm]
provider = "anthropic"
model = "claude-haiku-3-5"
api_key = "sk-ant-..."
litellm_model_string = "anthropic/claude-haiku-3-5"

[preferences]
default_mode = "interactive"   # "interactive" | "batch"
show_diff = false              # default for --diff flag
default_inject_code = false    # default for --inject-code flag in repo mode
```

For Copilot, `provider = "copilot"`, `api_key` holds a GitHub PAT (`ghp_...`), and `litellm_model_string`
is set by `ProviderRegistry` to whatever prefix was verified in Phase 2 (TBD — see §5.3 and §15).
The on-disk schema is identical across providers; only the values differ.

### 6.3 State Lifetime

| Data | Lifetime | Where |
|---|---|---|
| `AnalysisReport` | One CLI invocation | In-memory |
| `List[ClarifyingQuestion]` | One CLI invocation | In-memory |
| `List[UserAnswer]` | One CLI invocation | In-memory |
| `PromptContext` | One CLI invocation | In-memory |
| `OptimizedPrompt` | One CLI invocation | In-memory (+ file if --output, + stdout always) |
| `AppConfig` | Persistent | `~/.config/promptforge/config.toml` |
| `UsageRecord` (initial) | Written by `cli.py` after Synthesizer returns | `~/.config/promptforge/usage_log.jsonl` |
| `RatingRecord` | Written by Renderer after rating collection | `~/.config/promptforge/usage_log.jsonl` |

---

## § 7 — CLI API Design

### Command: `promptforge configure`

```
Purpose: First-run setup wizard. Select provider, model, enter API key, validate, save.

Flow:
  1. Display numbered list of all 6 providers
  2. User selects provider by number
  3. Display numbered list of models for that provider (recommended marked with ★)
  4. User selects model by number
  5. Prompt for API key (input hidden, like password)
     - If Copilot selected: label reads "GitHub Personal Access Token (copilot scope)"
  6. Validate key: make a minimal LiteLLM call (1-token completion)
     → Success: "✓ Key validated. Config saved to ~/.config/promptforge/config.toml"
     → Failure: "✗ Key rejected by provider. Check key and try again." (re-prompt)
  7. Write config.toml; immediately set file permissions to 600 (macOS/Linux only)

Flags: None
Exit codes: 0 (success), 1 (user cancelled), 2 (validation failed after 3 attempts)
```

### Command: `promptforge run`

```
Purpose: Analyze a vague prompt, ask clarifying questions, synthesize optimized prompt.

Usage:
  promptforge run "my vague prompt here"
  echo "my prompt" | promptforge run
  promptforge run --file prompt.txt
  promptforge run "prompt" --diff
  promptforge run "prompt" --output result.txt
  promptforge run "prompt" --batch

Arguments:
  prompt: str (positional, optional — see Input Precedence below for resolution order
                when multiple input sources are provided)

Flags:
  --file / -f PATH      Read raw prompt from file instead of argument/stdin
  --diff / -d           Show before/after comparison after output (stderr)
  --output / -o PATH    Write raw optimized prompt to file (in addition to stdout)
  --batch / -b          Non-interactive: print all questions at once, read answers sequentially.
                        Includes HIGH + MEDIUM + LOW questions (up to 7-question cap).
                        Use when piping input or scripting — all interaction happens in one pass.
  --no-questions        Skip clarifying questions entirely, synthesize directly from raw prompt.
                        Different from --batch: no questions are shown or answered at all.
  --no-clipboard / -n   Do not copy result to clipboard (useful in scripts/CI/piped output)

Stdout/stderr:
  stdout: OptimizedPrompt.text only (no decorations — safe to redirect: > file.txt or | pbpaste)
  stderr: all Rich panels, progress, questions, ratings, errors

Input precedence (when multiple sources are present):
  --file > positional argument > stdin
  If --file is set, ignore positional and stdin.
  If positional is set but no --file, ignore stdin.
  Stdin is only read when neither --file nor a positional argument is supplied.
  If multiple sources are present, the ignored sources do NOT cause an error — they are
  silently discarded. Document this in --help text.

Pipeline execution:
  1. Read raw prompt by precedence rule above
  2. Guard: if no config found → "Run promptforge configure first." → exit 1
  3. Run Analyzer → AnalysisReport
  4. If --no-questions → skip to step 6
  5. Run QuestionEngine + Interviewer → List[UserAnswer]
  6. Run ContextAssembler → PromptContext
  7. Run Synthesizer (LLM call) → OptimizedPrompt
       Synthesizer does NOT touch disk. It generates session_id and attaches it.
  8. cli.py orchestrates UsageLogger.record(usage_record) — see §5.11. If disk write fails,
       log WARNING and continue to step 9 (do not abort).
  9. Run Renderer in the fixed order from §8.4a:
     a. Write OptimizedPrompt.text to stdout
     b. Display Rich panel to stderr
     c. --diff: display comparison to stderr
     d. --output: write text to file
     e. Clipboard copy (unless --no-clipboard)
     f. Rating collection (per §8.6):
        - TTY guard FIRST: if not (stdin.isatty() and stderr.isatty()) → skip silently
        - Otherwise prompt and call readchar; on y/n call UsageLogger.record_rating()
 10. Exit 0

Errors: See §9 for the full taxonomy. Summary:
  - InputError (no prompt, file not found, file > 50KB) → exit 1
  - ConfigError (config missing or malformed) → exit 1
  - LLMError (per-exception-class hints from §9) → exit 2
  - ClipboardError, RenderError, RatingError → non-fatal, exit 0

Exit codes: 0 (success), 1 (usage error), 2 (LLM error), 99 (unexpected internal error)
```

### Command: `promptforge correct`

```
Purpose: Convenience alias for `promptforge run --file <file>`.
         Treats the file content as the "vague prompt" to be corrected.
         Exists for discoverability — users with existing prompt files think "correct this file"
         before they think "run with --file".

Usage:
  promptforge correct prompt.txt
  promptforge correct prompt.txt --diff --output corrected.txt

Arguments:
  file: PATH (required positional)

Flags: Same as `run` (--diff, --output, --batch, --no-questions, --no-clipboard)

Implementation: One line — calls the `run` pipeline with file content as raw_prompt.
                No separate logic, no separate tests beyond a smoke test.
```

### Command: `promptforge version`

```
Purpose: Print installed version.
Output: "promptforge 1.0.0"
Exit code: 0
```

---

## § 8 — Logic & Algorithms

### 8.1 Rule-Based Vagueness Detection (Analyzer)

**Purpose:** Detect specific types of poor prompt quality without any LLM call.

**Architecture:** All detectors except `ExampleDetector` are pure functions: `detect(raw_prompt: str) -> list[Issue]`.
`ExampleDetector` takes `(raw_prompt: str, analysis_report: AnalysisReport) -> list[Issue]` to avoid duplicating
output-format detection logic without creating a hidden inter-detector dependency.
The `Analyzer` passes the partially-built report to `ExampleDetector` after all other detectors have run.
New detectors are registered in `DETECTOR_REGISTRY` in `analyzer/engine.py`.

**Detector logic (per detector):**

```
MissingContextDetector:
  Scope: Fires only when the prompt OPENS with a bare pronoun used as imperative subject
         and no concrete noun has appeared yet. Mid-prompt pronouns are never flagged.

  Algorithm (precise — implementable as-is):
  1. Lowercase the prompt. Split into whitespace-separated tokens.
  2. Define SKIP_TOKENS = {"please", "can", "could", "would", "i", "we", "you", "ll"}
     (these are filler/auxiliary words that may precede the real opening verb)
  3. Define PRONOUNS = {"it", "they", "this", "that", "these", "those", "them"}
  4. Walk the first 10 tokens, skipping any token in SKIP_TOKENS and any token
     of length ≤ 2 that consists entirely of punctuation.
  5. Let `first_content_token` = the first token not skipped.
  6. If `first_content_token` is in PRONOUNS:
       Check the first 10 tokens for any token of length ≥ 4 that is not a pronoun,
       not in SKIP_TOKENS, and contains only alphabetic chars (heuristic for "a noun").
       If none found → Issue(severity=HIGH, detector_id="missing_context",
                              fragment=first_content_token).
  7. Otherwise: do not fire.

  Examples:
    "fix it"                              → fires (first content token is "it", no noun)
    "Write a function that sorts. It..."  → does not fire ("write" is first content token)
    "This is a task about X"              → fires (but acceptable — "this" + copula is
                                            still vague; let the user clarify what "this" is)
    "Please handle them carefully"        → fires ("them" is first content token after "please",
                                            no preceding noun)

  Rationale: Words like "function", "list", "code" are length ≥ 4 and alphabetic, so the
  noun heuristic catches them without needing a real parser. False positives on rare nouns
  shorter than 4 chars (e.g. "API", "URL") are acceptable — those are usually all-caps and
  would trigger the alphabetic check anyway via the .lower() at step 1.

AudienceDetector:
  1. Check for role/audience markers: ["for a", "as a", "you are", "act as", "role:", "audience:"]
  2. Also check for technical level signals: ["beginner", "expert", "junior", "senior", "non-technical"]
  3. If none found AND prompt length > 20 words → Issue(severity=MEDIUM, detector_id="audience")
  Edge case: short prompts (< 20 words) — skip this detector, noise > signal

OutputFormatDetector:
  1. Check for explicit format keywords: ["json", "markdown", "list", "table", "code", "function",
     "paragraph", "bullet", "csv", "yaml", "xml", "plain text", "numbered", "step by step"]
  2. Check for output signal phrases: ["output:", "return:", "format:", "respond with", "give me a"]
  3. If none found → Issue(severity=HIGH, detector_id="output_format")

ScopeDetector:
  1. Check for unbounded scope words: ["everything", "all of", "complete", "entire", "fully",
     "comprehensive", "thoroughly", "in detail", "in depth"]
  2. If found without a limiting qualifier within 5 tokens → Issue(severity=MEDIUM, detector_id="scope")
  Qualifying limiters: ["related to", "about", "regarding", "for", "on the topic of"]

InputSchemaDetector:
  1. Check if prompt implies the agent will receive input: verbs like ["analyze", "review", "process",
     "evaluate", "check", "read", "summarize", "translate", "convert", "transform"]
  2. If these verbs found AND no input description present (no "input:", "given:", "here is", code block)
     → Issue(severity=HIGH, detector_id="input_schema")

ActionVerbDetector:
  1. Extract first imperative verb (first word if it's a base-form verb, or verb after "please")
  2. Check against weak verb list: ["help", "do", "make", "handle", "deal with", "work on",
     "look at", "think about", "figure out", "fix", "improve"]
  3. If weak verb found → Issue(severity=MEDIUM, detector_id="action_verb")
  Strong verbs (acceptable): "generate", "write", "extract", "classify", "summarize", "convert",
  "refactor", "list", "explain", "compare", "translate", "validate"

ExampleDetector:
  Signature: detect(raw_prompt: str, analysis_report: AnalysisReport) -> list[Issue]
  1. Count total word count of prompt
  2. Check for example markers: ["example:", "e.g.", "for instance", "such as", "like this:", "input:"]
  3. Check for output format keywords inline (duplicate of OutputFormatDetector's keyword list —
     do not call OutputFormatDetector; use analysis_report.has_output_format_issue instead):
     if analysis_report.has_output_format_issue is True → output format is unclear
  4. If word_count > 50 AND no example markers AND analysis_report.has_output_format_issue →
     Issue(severity=LOW, detector_id="examples")
  Rationale: Short prompts rarely need examples; complex prompts with unclear output almost always benefit.
  The AnalysisReport.has_output_format_issue flag (set by Analyzer after OutputFormatDetector runs)
  is passed in explicitly — ExampleDetector does not call OutputFormatDetector directly.
```

**Detected intent/domain heuristics (used by ContextAssembler):**

```
Intent detection (keyword scan, first match wins):
  "generate|write|create|draft" → "generate content"
  "summarize|recap|tldr|condense" → "summarize"
  "analyze|review|evaluate|assess" → "analyze"
  "refactor|improve|fix|debug|optimize" → "transform existing content"
  "explain|describe|define|what is" → "explain concept"
  "compare|contrast|difference between" → "compare options"
  "translate|convert" → "transform format"
  default → "general task"

Domain detection (keyword scan, first match wins):
  "code|function|class|api|database|sql|python|java|javascript" → "software engineering"
  "write|essay|blog|article|story|copy|marketing" → "writing"
  "data|dataset|csv|analysis|chart|statistics" → "data analysis"
  "email|message|slack|communication" → "communication"
  "legal|contract|compliance|policy" → "legal/compliance"
  default → "general"
```

### 8.2 Question Generation (QuestionEngine)

**Purpose:** Map each `Issue` to exactly one `ClarifyingQuestion`. Avoid asking redundant questions.

**Algorithm:**
```
1. Sort issues by severity: HIGH first, then MEDIUM, then LOW
2. For each issue in sorted order:
   a. Look up QuestionTemplate for issue.detector_id
   b. Personalize the template using issue.fragment (inject the actual vague text)
   c. Check deduplication: if a question with the same question_id already in output list → skip
   d. Append to output list
3. Return list (max 7 questions — truncate LOW severity if over limit)
```

**Question templates (static, in `questions/templates.py`):**

```python
TEMPLATES = {
    "output_format": ClarifyingQuestion(
        question_id="q_output_format",
        question_text="What format should the output be in? (e.g. JSON, markdown list, code function, plain paragraph)",
        is_required=True
    ),
    "missing_context": ClarifyingQuestion(
        question_id="q_missing_context",
        question_text="'{fragment}' — what specific thing does this refer to? Add 1-2 sentences of context.",
        is_required=True
    ),
    "audience": ClarifyingQuestion(
        question_id="q_audience",
        question_text="Who is the target audience or reader? (e.g. junior developer, non-technical manager, general public)",
        is_required=False
    ),
    "scope": ClarifyingQuestion(
        question_id="q_scope",
        question_text="The scope seems open-ended. What are the specific limits? (e.g. max length, specific aspect only, particular version)",
        is_required=False
    ),
    "input_schema": ClarifyingQuestion(
        question_id="q_input_schema",
        question_text="What exactly will the agent receive as input? Describe the format, structure, or provide a sample.",
        is_required=True
    ),
    "action_verb": ClarifyingQuestion(
        question_id="q_action_verb",
        question_text="'{fragment}' is vague. What specifically should happen? (e.g. generate new, refactor existing, extract from, validate against)",
        is_required=False
    ),
    "examples": ClarifyingQuestion(
        question_id="q_examples",
        question_text="Should the optimized prompt include an example of the expected output? If yes, paste one here.",
        is_required=False
    ),
}
```

### 8.3 Meta-Prompt Construction (Synthesizer — MetaPromptBuilder)

**Purpose:** Build the smallest possible prompt that instructs the LLM to synthesize an optimized prompt.
This is the prompt that gets sent to the LLM — it must itself be token-efficient.

**Algorithm:**
```
1. Build system prompt (static, loaded from synthesizer/system_prompt.txt — not hardcoded inline)
   Load via: importlib.resources.files("promptforge.synthesizer").joinpath("system_prompt.txt").read_text()
   (Python 3.9+ API — read_text() from importlib.resources is deprecated in 3.11+)
2. Build user message from PromptContext:
   a. Include: raw_prompt, detected_intent, detected_domain
   b. Include each non-null field of PromptContext as a labeled line
   c. Omit null/skipped fields entirely — do not pad with "N/A"
   d. Include user answers verbatim — do not rephrase
3. Estimated token count before call:
   total = len(system_prompt.split()) * 1.33 + len(user_message.split()) * 1.33
   if total > 1500: truncate additional_context field first, then scope_constraints
4. Call LiteLLM: completion(model=config.litellm_model_string, messages=[system, user], max_tokens=800)
5. Parse response: extract the prompt text (LLM is instructed to return only the prompt, no preamble)
6. Compute output token estimate: len(response.split()) * 1.33
7. Return OptimizedPrompt (includes a fresh uuid4 as session_id)
8. Immediately call UsageLogger.record() with initial UsageRecord (rating=None)
```

**System prompt (`synthesizer/system_prompt.txt`) — written to this spec:**
```
You are a prompt optimization engine. You receive a structured description of what a user wants 
to accomplish and produce a single, optimized prompt ready for use with any LLM agent.

The optimized prompt must:
1. Open with a role definition: "You are a [role] that..."
2. State the task in one clear imperative sentence
3. Define the input: what the agent will receive, its format and structure
4. Define the output: exact format, schema, and any constraints
5. List step-by-step instructions if the task has multiple stages
6. Include one example if examples_requested is true
7. End with constraints: what NOT to do, scope limits, tone

Rules:
- Return ONLY the optimized prompt text. No preamble, no explanation, no "Here is your prompt:".
- Be concise — every word must earn its place. Target 30% fewer tokens than the original.
- Use second person ("You will...", "Return...", "Do not...").
- Never ask follow-up questions inside the prompt.
```

### 8.4a Renderer execution order (FIXED — Renderer must follow this exact sequence)

```
Step 1.  Write OptimizedPrompt.text to stdout (single write, no trailing newline beyond
         what's in the text itself, no decoration).
Step 2.  Display Rich panel with the optimized prompt to stderr.
Step 3.  If --diff: display unified diff to stderr (after the panel, before clipboard line).
Step 4.  If --output PATH: write OptimizedPrompt.text to PATH. On failure, print warning
         to stderr; do NOT exit.
Step 5.  If not --no-clipboard: attempt pyperclip.copy(). On success print
         "✓ Copied to clipboard" to stderr. On PyperclipException print
         "⚠ Clipboard unavailable — use --output to save" to stderr.
Step 6.  Rating collection (see § 8.6). Only attempted if stdin AND stderr are both TTYs.
Step 7.  Return — CLI exits 0.
```

Order is fixed because users redirecting stdout still see the panel, diff, and clipboard
status together on stderr in a predictable flow. Tests assert this order on captured output.

### 8.4 Diff Rendering (Renderer)

**Purpose:** Show meaningful before/after when `--diff` is passed. Always written to stderr.

**Algorithm:**
```
1. Split original and optimized prompts into lines
2. Use difflib.unified_diff to compute line-level diff
3. Render with Rich to stderr:
   - Removed lines (original): red background, "−" prefix
   - Added lines (optimized): green background, "+" prefix
   - Unchanged: grey, no prefix
4. Show summary line: "Original: ~N tokens → Optimized: ~M tokens (X% reduction)"
   token estimate: len(text.split()) * 1.33, rounded to nearest int
   Note: estimate uses word-count heuristic — accurate for prose; may undercount code-heavy prompts
         (code tokenizes at 2-3x word count). Treat as an approximation, not a precise measurement.
```

### 8.5 Clipboard Copy (Renderer)

**Purpose:** Automatically copy the optimized prompt to the system clipboard after every successful
synthesis — so the user can immediately paste it into any LLM interface without selecting text.

**Library:** `pyperclip` — handles macOS (`pbcopy`) and Linux (`xclip`/`xsel`/`wl-copy`).

**Algorithm:**
```
1. After OptimizedPrompt is returned and written to stdout:
2. Call pyperclip.copy(optimized_prompt.text)
3. On success:
   → Print to stderr below the Rich panel: "✓ Copied to clipboard"
4. On PyperclipException (no clipboard mechanism found — headless server, SSH without X11):
   → Log WARNING to stderr: "Clipboard not available in this environment"
   → Print to stderr: "⚠ Clipboard unavailable — use --output to save"
   → Do NOT raise, do NOT exit — clipboard failure is always non-fatal
5. If --no-clipboard flag passed:
   → Skip pyperclip call entirely
   → Do not show "✓ Copied" line
```

**Linux clipboard note (documented in README):**
pyperclip on Linux requires one of: `xclip`, `xsel`, or `wl-clipboard` to be installed.
```bash
sudo apt install xclip        # X11
sudo apt install wl-clipboard  # Wayland
```
The tool degrades gracefully if none are present (see step 4 above).

### 8.6 Rating Collection (Renderer)

**Purpose:** Collect a single-keypress rating after every session (run, correct, repo ask).

**Library:** `readchar` — captures a single keypress without requiring Enter. Handles macOS/Linux
via termios; no dependency on interactive terminal state.

**Algorithm:**
```
After clipboard step (or skip if --no-clipboard):
0. TTY guard — check BEFORE calling readchar:
   if not sys.stdin.isatty() or not sys.stderr.isatty():
       return  # silent skip — do NOT print the rating prompt at all
   Rationale: if stdout is redirected (`> out.txt`) but stderr is a TTY, readchar would
   work and the user would see a prompt — but if stdin is a pipe (`echo ... | promptforge run`),
   readchar would hang or read piped bytes as keypresses. Skip cleanly in both cases.

1. Print to stderr: "Was this prompt helpful? [y=👍 / n=👎 / s=skip]: "
2. Call readchar.readchar() inside a broad try/except — any exception is treated as skip.
3. y / Y → rating = 1
   n / N → rating = -1
   s / S or any other key → rating = None (treated as skip)
4. If rating is not None:
   → Write RatingRecord(session_id=..., rating=..., rated_at=<now ISO 8601>) to usage_log.jsonl
   → Print to stderr: "✓ Feedback recorded."
5. If rating is None:
   → Print nothing (silent skip)
```

### 8.7 Usage Logging — Two-Record Strategy (UsageLogger)

**Problem:** The rating is collected *after* the `OptimizedPrompt` is rendered, but the synthesis
record must be written *before* rendering so a Renderer crash cannot cause a lost record.
An append-only JSONL file cannot update a previously written line.

**Solution:** Two record types, merged at read time:

```
Record type 1 — UsageRecord (written by Synthesizer, before Renderer):
  { "record_type": "session", "session_id": "...", "timestamp": "...", "rating": null, ... }

Record type 2 — RatingRecord (written by Renderer after user rates):
  { "record_type": "rating", "session_id": "...", "rating": 1, "rated_at": "..." }

UsageLogger.load_all() merge algorithm:
  1. Read all lines, parse JSON, skip malformed lines with WARNING
  2. Build dict: session_id → UsageRecord (from "session" records)
  3. For each "rating" record: find matching session_id, patch in rating and rated_at
  4. Return merged list[UsageRecord]
```

This keeps the append-only guarantee, keeps the pre-render write guarantee, and correctly
associates ratings with sessions even if the process crashes between the two writes.

### 8.8 API Key Validation (ConfigManager)

**Algorithm:**
```
1. Call LiteLLM completion with:
   model = litellm_model_string
   messages = [{"role": "user", "content": "ping"}]
   max_tokens = 1
2. If response received without exception → key is valid
3. If AuthenticationError → key invalid
4. If any other exception → surface error message to user, allow retry
5. Max 3 attempts before exit 2
```

---

## § 9 — Error Handling Strategy

### Error taxonomy

| Category | Examples | Handling |
|---|---|---|
| `ConfigError` | Config file missing, malformed TOML, missing required field | Print user-friendly message + "Run promptforge configure" hint → exit 1 |
| `InputError` | No prompt provided, file not found, empty prompt, file > 50KB | Print specific message → exit 1 |
| `AnalysisError` | Detector throws unexpected exception | Log to stderr with traceback in DEBUG mode; skip that detector, continue with remaining → do not crash |
| `LLMError` | API call failed — see sub-types below | Print specific hint based on exception class → exit 2; no retry |

**LLM error sub-types (differentiated by LiteLLM exception class):**

| LiteLLM exception | User-facing message | Hint |
|---|---|---|
| `AuthenticationError` | "API key was rejected by {provider}." | "Run `promptforge configure` to update your key." |
| `RateLimitError` | "{provider} rate limit reached." | "Wait a few minutes or check your provider's usage dashboard." |
| `Timeout` / `APIConnectionError` | "Could not reach {provider}." | "Check your network connection and try again." |
| `BadRequestError` | "{provider} rejected the request: {error}." | "This usually means a bad model name in config — run `promptforge configure` again." |
| `ServiceUnavailableError` / 5xx | "{provider} is temporarily unavailable." | "Try again in a few minutes." |
| Any other LiteLLM exception | "LLM call failed: {error}." | "Run with --debug for full traceback." |

All map to exit code 2.
| `ClipboardError` | No clipboard mechanism (headless server, SSH without X11, missing xclip) | Log WARNING to stderr; print "⚠ Clipboard unavailable — use --output to save"; continue → exit 0 (non-fatal) |
| `RatingError` | Non-TTY environment (pipe, CI), readchar fails | Catch silently, treat as skip → exit 0 (non-fatal) |
| `RenderError` | File write permission denied | Print "Could not write to <path>: <reason>" → still display to terminal → exit 0 |
| `UnexpectedError` | Anything not caught above | Print "Unexpected error. Run with --debug for details." → exit 99 |

### Error display contract (all user-facing errors)

```
✗ [Category]: <specific message>
  Hint: <one-line actionable fix>
```

### Propagation rules

- Detectors: catch-and-skip. One broken detector does not stop the pipeline.
- LLM call: do not retry. Surface the error immediately.
- File I/O: catch-and-degrade. Failed file write is non-fatal; stdout output always succeeds.
- Config read: fail fast. No config = no run.
- Rating collection: catch-and-skip. Non-TTY or unexpected input → silent skip, exit 0.

### `--debug` flag

Available on all commands. When set:
- Print full tracebacks on all exceptions (to stderr)
- Print the meta-prompt sent to LLM before the call (to stderr)
- Print raw LLM response before parsing (to stderr)
- Print each detector's `List[Issue]` result (to stderr)

---

## § 10 — Testing Strategy

### Unit Tests

- **Coverage target:** 85% line coverage minimum across all non-CLI modules
- **Framework:** pytest 8+
- **Naming convention:** `test_<function>_<scenario>_<expected_result>`
  Example: `test_output_format_detector_no_format_keywords_returns_high_severity_issue`
- **What must be unit tested:**
  - Every detector in `analyzer/detectors/` — minimum 3 test cases each (trigger, no-trigger, edge case)
  - `MissingContextDetector` specifically: must include tests for mid-prompt pronouns that should NOT fire
  - `ExampleDetector` specifically: must test with a mock `AnalysisReport` where `has_output_format_issue` is True and False
  - `QuestionEngine.generate()` — correct questions for each issue type, deduplication, severity ordering
  - `ContextAssembler.assemble()` — all fields populated, null fields omitted, skipped answers handled
  - `MetaPromptBuilder.build()` — correct message structure, null fields excluded, truncation when > 1500 tokens
  - `ConfigManager` read/write/validate — happy path, missing file, malformed TOML
  - `ProviderRegistry` — all **6** providers present, all models have a non-empty `litellm_string`, recommended model flagged. Copilot's exact prefix is whatever was verified in Phase 2 (§5.3) — test asserts the registry value matches the resolved prefix; do not hardcode `"github/"` in the test.
  - `Renderer` token estimate calculation
  - `Renderer` clipboard copy — success path, `PyperclipException` handled gracefully, `--no-clipboard` skips call
  - `Renderer` rating collection — y/n/s handled, `readchar` exception treated as skip, RatingRecord written for y/n only
  - `UsageLogger` — initial record written, rating record written separately, `load_all()` merges correctly, malformed lines skipped
- **What to mock:** All `litellm.completion()` calls — mock at HTTP level. All `pyperclip.copy()` calls. All `readchar.readchar()` calls.
- **Test data:** Fixture factory in `tests/fixtures.py` — `make_issue()`, `make_analysis_report()`, `make_prompt_context()`, `make_app_config()`, `make_usage_record()`, `make_rating_record()` — no hardcoded strings scattered in test files

### Integration Tests

- **Scope:** Full pipeline from raw prompt string → `OptimizedPrompt`, with LLM mocked at HTTP level
- **What to cover:**
  - Happy path: vague prompt with all detector types firing, questions answered, optimized prompt returned, stdout contains only raw text
  - No issues detected: prompt is already clear, `--no-questions` path
  - `--batch` mode: all questions printed and answered in one pass (HIGH + MEDIUM + LOW up to 7)
  - `--no-questions`: Interviewer stage is fully skipped; QuestionEngine still runs but output ignored
  - `--diff` rendering: diff output goes to stderr, raw text still goes to stdout
  - Config missing: correct exit code and error message
  - LLM errors: one test per LiteLLM exception sub-type listed in §9 — `AuthenticationError`, `RateLimitError`, `Timeout`/`APIConnectionError`, `BadRequestError`, `ServiceUnavailableError`, and a catch-all. Each must produce exit code 2 AND the hint string specified in §9 (assert on stderr capture).
  - Clipboard success: `pyperclip.copy` called with exact `OptimizedPrompt.text`
  - Clipboard failure: `PyperclipException` raised → warning shown to stderr, exit code still 0
  - `--no-clipboard` flag: `pyperclip.copy` never called
  - Rating y: `RatingRecord` with rating=1 written to log; initial UsageRecord has rating=None
  - Rating s (skip): no RatingRecord written; UsageRecord remains with rating=None
  - readchar exception: silently treated as skip, exit code 0
  - `UsageLogger.load_all()`: returns merged records with correct rating values
- **LLM mock strategy:** Use `respx` to intercept httpx requests that LiteLLM makes.
  Return a valid completion response JSON fixture. Do not patch `litellm.completion` at the
  function level — patching there skips LiteLLM's own response parsing, which is part of
  what needs testing. `respx` correctly intercepts httpx (LiteLLM 1.40+'s HTTP client).

### End-to-End Tests

- **Scope:** Not in scope for v1. Would require a real API key and spend real tokens.

### Performance Tests

- Each detector must process a 1000-word prompt in < 50ms.
  Enforced with a `pytest-benchmark` test on each detector.

### Test Data Strategy

- All fixture factories in `tests/fixtures.py` — single source of truth
- Each test is fully independent — no shared mutable state, no global config written to disk
- Tests that need `config.toml` or `usage_log.jsonl` use `tmp_path` pytest fixture, never `~/.config/promptforge/`

---

## § 11 — Observability & Logging

### Logging

- **Library:** Python stdlib `logging` — no external logging library
- **All log output goes to stderr** — never stdout (stdout is reserved for `OptimizedPrompt.text`)
- **Format string:** `[%(levelname)s] %(name)s: %(message)s`
- **Log levels:**
  - `DEBUG`: only when `--debug` flag set.
  - `WARNING`: non-fatal degradation — detector skipped, clipboard unavailable, rating collection failed
  - `ERROR`: unrecoverable failures before exit

### What gets logged

| Event | Level | Message |
|---|---|---|
| Detector skipped due to exception | WARNING | `Detector {id} failed: {error}. Skipping.` |
| LLM call initiated | DEBUG | `LLM call: model={model}, estimated_tokens={n}` |
| LLM response received | DEBUG | `LLM response received: {token_count} tokens` |
| Config not found | ERROR | `Config not found at {path}` |
| Config saved | DEBUG | `Config written to {path}` |
| Meta-prompt content | DEBUG | `Meta-prompt:\n{text}` |
| Raw LLM response | DEBUG | `Raw LLM response:\n{text}` |
| Clipboard unavailable | WARNING | `Clipboard not available: {error}` |
| Rating collection failed | WARNING | `Rating collection failed (non-TTY?): {error}. Skipping.` |
| UsageLogger write failed (disk full, permission denied) | WARNING | `Usage log write failed: {error}. Continuing without recording this session.` |
| UsageLogger malformed line skipped at load time | WARNING | `Skipping malformed usage log line {n}: {error}` |

---

## § 12 — Security Considerations

### API Key Storage

- Stored in `~/.config/promptforge/config.toml` on the user's local machine
- File permissions set to `600` (owner read/write only) immediately after writing on macOS/Linux:
  `os.chmod(config_path, 0o600)` — this call is wrapped in a platform check and skipped on Windows
  (where NTFS ACLs are used instead and `os.chmod` is a no-op). Native Windows is not a supported
  target for v1; WSL users get full POSIX file permission protection.
- Never logged — use `AppConfig.masked_key` property in all log statements
- Never appears in `--debug` output, error messages, or the meta-prompt sent to the LLM
- Never read from environment variables

### Input Sanitization

- Raw prompt is passed through the rule engine as plain text — no eval, no subprocess, no exec
- `--file` flag: validate path exists and is a regular file before reading. Max file size: 50KB.
- No shell expansion on prompt text — never pass raw prompt to subprocess

### Dependency Security

- `pip-audit` run as part of dev workflow (documented in README)
- All dependencies pinned to minor version in `pyproject.toml` (e.g. `litellm>=1.40,<2.0`)

### Network

- The only outbound network call is `litellm.completion()` to the user's configured provider
- No telemetry, no analytics, no phone-home
- HTTPS enforced by LiteLLM for all providers

---

## § 13 — File & Directory Structure

```
promptforge/                          # repo root
│
├── src/
│   └── promptforge/                  # installable package
│       ├── __init__.py               # version string only: __version__ = "1.0.0"
│       ├── cli.py                    # Typer app, all command definitions
│       │
│       ├── config/
│       │   ├── __init__.py           # empty
│       │   ├── manager.py            # ConfigManager: read/write/validate config.toml
│       │   ├── providers.py          # ProviderRegistry: static provider+model data (6 providers)
│       │   └── models.py             # AppConfig, Provider, Model dataclasses
│       │
│       ├── analyzer/
│       │   ├── __init__.py           # empty
│       │   ├── engine.py             # Analyzer + DETECTOR_REGISTRY list
│       │   ├── models.py             # Issue, IssueSeverity, AnalysisReport dataclasses
│       │   └── detectors/
│       │       ├── __init__.py       # empty
│       │       ├── missing_context.py
│       │       ├── audience.py
│       │       ├── output_format.py
│       │       ├── scope.py
│       │       ├── input_schema.py
│       │       ├── action_verb.py
│       │       └── examples.py       # takes (raw_prompt, analysis_report) — not a pure detect(str)
│       │
│       ├── questions/
│       │   ├── __init__.py           # empty
│       │   ├── engine.py             # QuestionEngine: Issue → ClarifyingQuestion
│       │   ├── models.py             # ClarifyingQuestion, UserAnswer dataclasses
│       │   └── templates.py          # TEMPLATES dict: detector_id → QuestionTemplate
│       │
│       ├── interviewer/
│       │   ├── __init__.py           # empty
│       │   └── terminal.py           # Interviewer: interactive + batch terminal I/O
│       │
│       ├── assembler/
│       │   ├── __init__.py           # empty
│       │   ├── context.py            # ContextAssembler: builds PromptContext
│       │   └── models.py             # PromptContext dataclass
│       │
│       ├── synthesizer/
│       │   ├── __init__.py           # empty
│       │   ├── engine.py             # Synthesizer: MetaPromptBuilder + LiteLLM call + UsageLogger.record()
│       │   ├── models.py             # OptimizedPrompt dataclass (includes session_id)
│       │   └── system_prompt.txt     # Static system prompt — loaded via importlib.resources.files()
│       │
│       ├── renderer/
│       │   ├── __init__.py           # empty
│       │   └── display.py            # Renderer: stdout (raw text) + stderr (Rich UI) + clipboard + rating
│       │
│       └── stats/
│           ├── __init__.py           # empty
│           ├── logger.py             # UsageLogger: record(), load_all() (with merge), reset(), export()
│           ├── engine.py             # StatsEngine: all savings computation functions
│           ├── display.py            # StatsRenderer: Rich panels for summary/detailed/projection
│           ├── models.py             # UsageRecord, RatingRecord dataclasses
│           └── pricing.py            # PRICING dict: hardcoded model → $/1M tokens
│
├── tests/
│   ├── __init__.py
│   ├── fixtures.py                   # All factory functions
│   ├── unit/
│   │   ├── analyzer/
│   │   │   ├── test_engine.py
│   │   │   └── detectors/
│   │   │       ├── test_missing_context.py   # includes mid-prompt pronoun no-fire cases
│   │   │       ├── test_audience.py
│   │   │       ├── test_output_format.py
│   │   │       ├── test_scope.py
│   │   │       ├── test_input_schema.py
│   │   │       ├── test_action_verb.py
│   │   │       └── test_examples.py          # mocks AnalysisReport.has_output_format_issue
│   │   ├── questions/
│   │   │   ├── test_engine.py
│   │   │   └── test_templates.py
│   │   ├── assembler/
│   │   │   └── test_context.py
│   │   ├── synthesizer/
│   │   │   └── test_meta_prompt_builder.py
│   │   ├── stats/
│   │   │   ├── test_engine.py
│   │   │   └── test_logger.py                # two-record merge, malformed line skip, reset, export
│   │   └── config/
│   │       ├── test_manager.py
│   │       └── test_providers.py             # verifies all 6 providers; Copilot prefix matches whatever Phase 2 resolved
│   └── integration/
│       ├── test_run_command.py               # full pipeline; respx mocks httpx; stdout/stderr verified
│       ├── test_configure_command.py
│       ├── test_correct_command.py
│       └── test_stats_command.py
│
├── docs/
│   └── plan-promptforge-v4.md        # This file
│
├── pyproject.toml                    # Hatchling build, dependencies, tool config
├── README.md
└── .github/
    └── workflows/
        └── ci.yml
```

---

## § 14 — Implementation Order

Each phase must be independently runnable and testable before the next phase begins.

### Phase 1 — Skeleton

1. Create repo structure exactly as defined in § 13
2. Write `pyproject.toml`: Hatchling backend, all dependencies declared (including `readchar`),
   entry point `promptforge = "promptforge.cli:app"`
3. Write `__init__.py` files — all empty except root (version string)
4. Write `cli.py` — all commands defined as stubs: `typer.echo("not implemented")` and `raise typer.Exit()`
5. Write all dataclasses in `models.py` files — no logic, just the dataclass definitions.
   Include `session_id: str` in `OptimizedPrompt`, `has_output_format_issue: bool` in `AnalysisReport`,
   and both `UsageRecord` and `RatingRecord` in `stats/models.py`
6. Confirm: `pip install -e .` succeeds, `promptforge --help` shows all commands, `pytest` runs (0 tests, no errors)

### Phase 2 — Config layer

7. Implement `ProviderRegistry` with all **6** providers and their models
   - **Verify Copilot prefix before locking it in** (see § 15 open question): run a smoke test with a real PAT against the pinned LiteLLM version to confirm whether `github/`, `github_copilot/`, or a custom-endpoint config works. Set `Model.litellm_string` accordingly. Set `auth_label` to "GitHub Personal Access Token (copilot scope)".
8. Implement `ConfigManager`: read, write, `os.chmod(600)` wrapped in platform check, path resolution
9. Implement configure wizard in `cli.py`: provider selection → model selection → key input → validation → save
10. Unit tests: `test_manager.py`, `test_providers.py` (6 providers, Copilot routing verified)
11. Confirm: `promptforge configure` runs, saves config correctly for all providers

### Phase 3 — Rule engine

12. Implement `OutputFormatDetector` first (other detectors depend on knowing its keyword list)
13. Implement remaining 5 pure detectors — one at a time, test each before writing the next
14. Implement `ExampleDetector` last — takes `(raw_prompt, analysis_report)`, add `has_output_format_issue`
    flag to `AnalysisReport`, update `Analyzer` to set it after `OutputFormatDetector` runs
15. Unit tests for each detector: minimum 3 cases (fires, does not fire, edge case)
    - `MissingContextDetector`: include tests for mid-prompt pronouns that must NOT fire
    - `ExampleDetector`: mock `AnalysisReport` with `has_output_format_issue` True/False
16. Implement `Analyzer.analyze()` — registers all detectors in `DETECTOR_REGISTRY`, aggregates results,
    calls `ExampleDetector` last with the partially-built report
17. Unit test `Analyzer`: all detectors called, results merged, empty prompt handled
18. Confirm: import `Analyzer`, call with vague strings, inspect `AnalysisReport` in scratch script

### Phase 4 — Question + Interview layer

19. Implement `TEMPLATES` dict in `questions/templates.py`
20. Implement `QuestionEngine.generate()`: Issue → ClarifyingQuestion, deduplication, severity sort
21. Unit tests: `test_engine.py` for QuestionEngine
22. Implement `Interviewer`: interactive mode (Rich prompts to stderr), batch mode (`--batch`)
    - Batch mode shows all questions (HIGH + MEDIUM + LOW, up to 7) in one pass
23. Implement `ContextAssembler.assemble()`
24. Unit tests: `test_context.py`
25. Confirm: wire Phase 3 + Phase 4 in scratch script — raw prompt → questions in terminal → PromptContext

### Phase 5 — Synthesizer + Renderer + Usage logging (full pipeline)

26. Write `system_prompt.txt` — finalize the meta-prompt template text
27. Implement `MetaPromptBuilder.build()` — PromptContext → system + user messages
    - Use `importlib.resources.files("promptforge.synthesizer").joinpath("system_prompt.txt").read_text()`
28. Unit tests: `test_meta_prompt_builder.py`
29. Implement `UsageLogger` with these PUBLIC methods (Renderer needs to call `record_rating` —
    so it cannot be underscore-prefixed):
    - `record(usage_record)` — append a `UsageRecord` line
    - `record_rating(session_id, rating)` — append a `RatingRecord` line
    - `load_all()` — read all lines, merge session + rating records by `session_id`
    - `reset(skip_confirmation: bool = False)` — see §18.5
    - `export(output_path)` — write merged records as JSON array
30. Unit tests: `test_logger.py` — two-record merge, malformed line skip, reset (TTY + --yes paths), export
31. Implement `Synthesizer.synthesize()`:
    - LiteLLM call (httpx, mocked with respx in tests)
    - Generate `session_id = str(uuid4())` before the call, attach to `OptimizedPrompt`
    - Synthesizer does **not** touch disk — no UsageLogger import in this module
32. Unit tests for Synthesizer: LLM mocked at httpx level with respx; verify each LiteLLM exception
    sub-type from §9 surfaces correctly. Assert via grep on imports that Synthesizer does not import
    UsageLogger (enforces the layering rule from §5.11).
33. Wire `UsageLogger.record()` into `cli.py`'s `run` command between Synthesizer and Renderer:
    - Build `UsageRecord` from `OptimizedPrompt` + analyzer/context metadata
    - Call `UsageLogger.record(record)` — catch disk-write errors, log WARNING per §11, continue
    - Pass `OptimizedPrompt` (which carries `session_id`) to Renderer for the eventual rating write
34. Implement `Renderer` in the exact step order specified by §8.4a:
    - Step 1: stdout write (raw text only)
    - Step 2: Rich panel → stderr
    - Step 3: `--diff` → stderr
    - Step 4: `--output` file write (non-fatal)
    - Step 5: Clipboard (pyperclip, non-fatal, `PyperclipException` handled)
    - Step 6: Rating (per §8.6 — TTY guard before readchar, broad except, skip silently if not TTY)
    - On y or n: call `UsageLogger.record_rating(session_id, rating)`
35. Unit tests for Renderer: stdout contains only raw text; stderr has the panel in the right order;
    readchar exception or non-TTY → silent skip; rating=y → RatingRecord written with matching `session_id`;
    rating=s → no RatingRecord
36. Confirm: full `promptforge run "some vague prompt"` works end-to-end with real API key

### Phase 6 — CLI hardening + integration tests

37. Wire `promptforge correct` as thin wrapper over `run` pipeline (calls the same orchestration in §5.11)
38. Implement `--debug` flag across all commands (all debug output to stderr)
39. Add all error handling per § 9 — every exit code AND every LLM error sub-type tested
40. Write all integration tests in `tests/integration/`
    - Verify stdout = raw text, stderr = UI, using captured output fixtures
    - Use `respx` for LLM HTTP mocking
    - One test per LLM exception class from §9 — assert hint string on stderr
41. Run `pytest --cov=src/promptforge --cov-report=term-missing` — hit 85% coverage
42. Run `ruff check src/ tests/` — zero violations
43. Run `mypy src/promptforge --strict` — zero errors

### Phase 7 — Stats command + Polish + Packaging

44. Implement `StatsEngine` computation functions (§ 18.3)
45. Implement `StatsRenderer` Rich panels (§ 18.4)
46. Wire `promptforge stats` command with all flags:
    - `--detailed` + `--reuse N` are combinable: show per-session table, then projection panel below
    - `--last N`: filter to last N sessions before computing (applied before all other computations)
    - `--reset`: interactive confirmation; refuses without `--yes` in non-TTY (§18.5)
    - `--yes`: skip confirmation for `--reset`
    - `--export PATH`: write full merged records as JSON array
47. Integration tests: `test_stats_command.py` — summary, detailed, reuse projection, reset (TTY + --yes paths), export
48. Write `README.md` per § 17 spec
49. Confirm `pip install .` from clean virtualenv — all commands work
50. Test on macOS + Linux (WSL). Confirm `~/.config/promptforge/` created, permissions set correctly.
51. Tag v1.0.0. Publish to PyPI with `hatch publish`.

---

## § 15 — Open Questions & Deferred Decisions

| Question | Assumption made to unblock | Revisit before |
|---|---|---|
| Should `promptforge run` accept multi-line prompts via heredoc? | Yes — stdin reads until EOF automatically | Phase 5 |
| Should the system prompt in `system_prompt.txt` be user-overridable? | No in v1 | v2 |
| What happens if the user's answer to a clarifying question is itself vague? | Accept verbatim | v2 |
| Should token estimates use the provider's actual tokenizer (tiktoken for OpenAI)? | No — use `len(text.split()) * 1.33` approximation. Accurate for prose; known to undercount code by 2-3x. Display with a note: "~N tokens (estimate)". | v2 if users report significant discrepancy |
| `promptforge configure --update-key` flag? | Not in v1 — `configure` overwrites the full config | v2 |
| PyPI package name: `promptforge` may be taken. | Check before Phase 7. Fallback: `prompt-forge` or `pforge`. | Phase 7 |
| Hardcoded pricing in `stats/pricing.py` will go stale. | Acceptable for v1 — show a dated disclaimer. | v2 |
| `usage_log.jsonl` grows unbounded. | No rotation in v1. `--reset` to clear. | v2 |
| `readchar` behavior in CI / non-TTY environments. | Skip rating prompt entirely when either stdin or stderr is not a TTY (check before calling readchar). Verified in integration tests with mocked `sys.stdin.isatty`. | Phase 5 |
| LiteLLM provider prefix for GitHub Copilot. | **MUST be verified before Phase 2.** Candidate prefixes: `github/`, `github_copilot/`, or custom endpoint config with explicit base_url + auth header. Run a smoke test against a real PAT to confirm which works with the pinned LiteLLM version. If none of the built-in providers works, treat Copilot as an OpenAI-compatible custom endpoint. | Phase 2 |
| `promptforge stats --reset` in non-TTY environments. | The `input()` confirmation raises `EOFError` on closed stdin. Solution: add a `--yes` flag for scripted use. If `--reset` is passed without `--yes` AND stdin is not a TTY, print "Refusing to reset without --yes in non-interactive mode." and exit 1. | Phase 7 |
| `httpx` version drift between LiteLLM and respx. | Pin `httpx >=0.27,<0.29` in dev dependencies. If LiteLLM updates to a newer httpx, bump the pin after verifying `respx` still intercepts correctly. | Phase 5 |

---

## § 16 — Agent Instructions

You are implementing PromptForge as described in this plan. Read every section before writing a single line of code.

1. **Follow § 14 phase by phase.** Do not begin Phase 3 until Phase 2 passes all its tests.

2. **Match § 13 exactly.** Do not create `utils.py` or `helpers.py`.

3. **Detectors are pure functions with one exception.** All detectors take `raw_prompt: str`, return `list[Issue]`. `ExampleDetector` takes `(raw_prompt: str, analysis_report: AnalysisReport)` as its second argument because it legitimately needs to know if output format issues were detected — the `AnalysisReport.has_output_format_issue` flag is passed by the Analyzer, not by calling another detector. This is the only exception to the pure-string signature.

4. **The synthesizer makes exactly one LiteLLM call per session.** If you find yourself calling `litellm.completion()` anywhere other than `synthesizer/engine.py`, stop and restructure.

5. **Stdout is reserved for `OptimizedPrompt.text` only.** All Rich panels, all `typer.echo()` calls for interactive messages, all warnings, all errors go to stderr. Implement this from Phase 1. Test it in integration tests by asserting stdout equals only the raw prompt text.

6. **`system_prompt.txt` is a file, not a string in code.** Load it with:
   ```python
   importlib.resources.files("promptforge.synthesizer").joinpath("system_prompt.txt").read_text(encoding="utf-8")
   ```
   Do NOT use the deprecated `importlib.resources.read_text()` — it is deprecated in Python 3.11 and removed in 3.13.

7. **Mock LLM calls at the HTTP level in tests.** Use `respx` to intercept httpx requests (LiteLLM 1.40+ uses httpx). Do NOT mock `litellm.completion` at the function level — that skips LiteLLM's own parsing. Do NOT use `responses` — it only mocks `requests`, not `httpx`.

8. **API key is never logged.** Use `AppConfig.masked_key` in all log statements. Never log `config.api_key` directly.

9. **File permissions on config.toml must be set to 600 immediately after every write, on macOS/Linux only:**
   ```python
   import sys
   if sys.platform != "win32":
       os.chmod(config_path, 0o600)
   ```

10. **Clipboard copy is always non-fatal.** Wrap every `pyperclip.copy()` in `try/except PyperclipException`.

11. **Rating collection is always non-fatal.** Wrap every `readchar.readchar()` in a broad `try/except Exception` — a non-TTY environment (pipe, CI) raises an OS-level exception, not a readchar-specific one.

12. **UsageLogger writes two records.** `cli.py` orchestrates: after Synthesizer returns, CLI builds the `UsageRecord` and calls `UsageLogger.record()` *before* invoking Renderer. Renderer later writes the `RatingRecord` (different shape, same `session_id`). `load_all()` merges them. Synthesizer must not import UsageLogger — keep it pure.

13. **`ProviderRegistry` has 6 providers, not 5.** OpenAI, Anthropic, Google Gemini, Mistral, Groq, and GitHub Copilot. **The exact LiteLLM provider prefix for Copilot is unverified — see § 15 open question.** Before writing Copilot config in `ProviderRegistry`, run a smoke test with a real PAT against the pinned LiteLLM version to confirm which prefix works (`github/`, `github_copilot/`, or custom endpoint). Do not hardcode a prefix based on this plan alone — verify first.

14. **Rating prompt requires both stdin AND stderr to be TTYs.** Check `sys.stdin.isatty() and sys.stderr.isatty()` *before* calling `readchar.readchar()`. If either is not a TTY, skip the prompt silently — do not even print "Was this prompt helpful?". This prevents hangs when stdout is redirected or input is piped.

15. **Input precedence is fixed.** When `run` receives a positional prompt, a `--file`, and stdin all at once: `--file` wins. Then positional. Then stdin. The losers are silently discarded — no error.

14. **If § 15 has an open question that blocks your current phase, stop and surface it before making a unilateral architectural decision.**

---

## § 17 — README Specification

```markdown
# PromptForge

> Turn vague prompts into structured, token-efficient prompts — from your terminal.

PromptForge is a CLI tool that analyses a vague prompt, asks you targeted clarifying questions,
and synthesizes a final prompt that is clear, structured, and uses fewer tokens when sent to any
LLM agent. One API call. No bloat. No retries.

---

## Why PromptForge

Vague prompts cost you in two ways:

1. **Bad output** — you retry 2–3 times, each retry spending more tokens than the last.
2. **Bloated prompts** — you add more and more context hoping something sticks, ballooning token count.

PromptForge fixes both. It asks the right questions upfront, then synthesizes a prompt that is
precise and lean — so your agent gets it right on the first attempt.

---

## Installation

**Recommended (pipx — installs in isolated env, available system-wide):**
```bash
pipx install promptforge
```

**Standard pip:**
```bash
pip install promptforge
```

**From source:**
```bash
git clone https://github.com/<your-org>/promptforge
cd promptforge
pip install -e .
```

Requires Python 3.11 or higher. macOS and Linux (including WSL) only.

---

## Quick Start

### Step 1 — Configure once

```bash
promptforge configure
```

You will be prompted to:
- Select your LLM provider (OpenAI, Anthropic, Google Gemini, Mistral, Groq, GitHub Copilot)
- Select a model (recommended models marked with ★)
- Enter your API key (validated before saving)

Config is saved to `~/.config/promptforge/config.toml` with permissions set to 600.

---

### Step 2 — Run on a vague prompt

```bash
promptforge run "help me with the code"
```

PromptForge will:
1. Analyse your prompt for vagueness (no API call)
2. Ask you targeted clarifying questions
3. Make one API call to synthesize the optimized prompt
4. Display the result and copy it to your clipboard

**Example session:**

```
$ promptforge run "help me with the code"

 Analysing prompt...

 Issues detected:
  • No output format specified
  • Action verb is ambiguous ("help")
  • No input structure defined

 Clarifying questions:

[1/3] What specifically should happen to the code?
      (e.g. refactor for readability, fix a bug, add type hints, write tests)
> refactor for readability and add type hints

[2/3] What format should the output be in?
      (e.g. full file, only changed functions, diff patch)
> full file with only changed functions shown

[3/3] What will you provide as input?
      (e.g. a Python file, a code snippet, a GitHub link)
> a Python function pasted inline

 Synthesizing optimized prompt...

╭─────────────────────────────────────────────────╮
│  Optimized Prompt                               │
│─────────────────────────────────────────────────│
│                                                 │
│  You are a senior Python engineer specialising  │
│  in clean, idiomatic Python 3.11+ code.         │
│                                                 │
│  Task: Refactor the provided Python function    │
│  for readability and add complete type hints.   │
│                                                 │
│  Input: A Python function pasted inline below   │
│  the prompt. Assume it is syntactically valid.  │
│                                                 │
│  Output: Return only the refactored function(s) │
│  that changed. Do not return unchanged code.    │
│  Format: plain Python code block, no markdown   │
│  wrapper.                                       │
│                                                 │
│  Steps:                                         │
│  1. Read the function and identify readability  │
│     issues (naming, nesting, length, clarity).  │
│  2. Refactor — preserve all existing behaviour. │
│  3. Add PEP 484 type hints to all parameters    │
│     and return values.                          │
│  4. Return only the modified function(s).       │
│                                                 │
│  Constraints:                                   │
│  • Do not change function signatures.           │
│  • Do not add docstrings unless asked.          │
│  • Do not explain your changes.                 │
│                                                 │
│  Estimated tokens: ~118  (original: ~9)         │
╰─────────────────────────────────────────────────╯

✓ Copied to clipboard
Was this prompt helpful? [y=👍 / n=👎 / s=skip]: y
✓ Feedback recorded.
```

> **Token estimates** are based on a word-count approximation (~1.33 tokens/word).
> For code-heavy prompts, actual token counts may be 2–3× higher. Treat as a guide, not a precise measurement.

---

## All Commands

### `promptforge configure`

First-time setup. Select provider, model, enter and validate API key.

```bash
promptforge configure
```

Re-running overwrites existing config.

---

### `promptforge run`

Analyse and optimise a prompt.

```bash
# Inline prompt
promptforge run "your vague prompt here"

# From stdin (pipe)
echo "your prompt" | promptforge run

# From file
promptforge run --file my_prompt.txt

# Show before/after diff
promptforge run "your prompt" --diff

# Save output to file (also still prints to terminal)
promptforge run "your prompt" --output optimized.txt

# Redirect raw output to file (clipboard + interactive UI still works)
promptforge run "your prompt" > optimized.txt

# Non-interactive (all questions shown at once — good for scripts)
promptforge run "your prompt" --batch

# Skip clarifying questions entirely
promptforge run "your prompt" --no-questions

# Skip clipboard copy
promptforge run "your prompt" --no-clipboard

# Debug mode
promptforge run "your prompt" --debug
```

> **Clipboard behaviour:** The optimized prompt is automatically copied to your clipboard.
> Use `--no-clipboard` to disable for a single run.
>
> **Stdout:** The raw optimized prompt text is written to stdout (no decoration). This means
> `promptforge run "..." > file.txt` works as expected — only the clean prompt text goes to the file.
>
> **Linux users:** clipboard requires `xclip` (X11) or `wl-clipboard` (Wayland):
> ```bash
> sudo apt install xclip        # X11
> sudo apt install wl-clipboard  # Wayland
> ```
> If neither is installed, PromptForge degrades gracefully.

---

### `promptforge correct`

Optimise an existing prompt file. Convenience alias for `run --file`.

```bash
promptforge correct my_existing_prompt.txt
promptforge correct my_existing_prompt.txt --diff --output corrected.txt
```

Accepts all the same flags as `run`.

---

### `promptforge stats`

Show token savings analytics from your session history.

```bash
# Summary view
promptforge stats

# Detailed per-session log (last 10 by default)
promptforge stats --detailed

# Detailed + limit to last N sessions
promptforge stats --detailed --last 20

# Project savings at N× reuse per prompt
promptforge stats --reuse 15

# Detailed per-session table with projection panel below
promptforge stats --detailed --reuse 15

# Reset session history
promptforge stats --reset

# Export as JSON
promptforge stats --export stats.json
```

---

### `promptforge version`

```bash
promptforge version
# promptforge 1.0.0
```

---

## Token Savings Analytics

Every session logs:
- Estimated tokens in your original prompt
- Estimated tokens in the optimised prompt
- Tool cost (tokens spent on the synthesis call)
- Net saving for that session

```
╭──────────────────────────────────────────────────╮
│  PromptForge — Token Savings Report              │
│──────────────────────────────────────────────────│
│  Sessions tracked:        23                     │
│  Total original tokens:   8,450                  │
│  Total optimised tokens:  3,210                  │
│  Total tool cost:         14,490                 │
│  Net tokens saved:        1,450  ← see note*     │
│  Average reduction/prompt: 62%                   │
│──────────────────────────────────────────────────│
│  Break-even at reuse:     5× per prompt          │
│  Estimated break-even:    Reached at session 4   │
╰──────────────────────────────────────────────────╯

* Net saving = (original − optimised) × reuse_count − tool_cost
  PromptForge cannot track reuse count automatically.
  Set your expected reuse count: promptforge stats --reuse 10

Token estimates use a word-count approximation (~1.33 tokens/word). For code-heavy prompts,
actual counts may be higher. Treat as a guide.
```

Data is stored locally at `~/.config/promptforge/usage_log.jsonl`. Never sent anywhere.

---

## How It Works

```
Your vague prompt
      ↓
 Rule-based Analyser    ← zero API calls
      ↓
 Question Engine        ← zero API calls
      ↓
 You answer questions
      ↓
 Context Assembler      ← zero API calls
      ↓
 Synthesiser            ← ONE API call (small model)
      ↓
 Optimised prompt       → stdout (raw text, safe to redirect)
                        → clipboard (auto-copy)
                        → terminal panel (stderr)
```

---

## Configuration File

Located at `~/.config/promptforge/config.toml`. Permissions: 600 (owner read/write only, macOS/Linux).

```toml
[llm]
provider = "anthropic"
model = "claude-haiku-3-5"
api_key = "sk-ant-..."
litellm_model_string = "anthropic/claude-haiku-3-5"

[preferences]
default_mode = "interactive"
show_diff = false
```

---

## Supported Providers & Models

| Provider | Recommended model | Other available models |
|---|---|---|
| Anthropic | claude-haiku-3-5 ★ | claude-sonnet-4-5, claude-opus-4-5 |
| OpenAI | gpt-4o-mini ★ | gpt-4o, gpt-4-turbo |
| Google Gemini | gemini-1.5-flash ★ | gemini-1.5-pro |
| Mistral | mistral-small ★ | mistral-medium, mistral-large |
| Groq | llama-3.1-8b-instant ★ | llama-3.1-70b, mixtral-8x7b |
| GitHub Copilot | gpt-4o ★ | gpt-4o-mini |

For GitHub Copilot: enter a GitHub Personal Access Token with `copilot` scope when prompted.

---

## Exit Codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Usage error (bad input, config missing, file not found) |
| 2 | LLM error (auth failure, rate limit, timeout) |
| 99 | Unexpected internal error (run with --debug) |

---

## Privacy

- Your prompts are sent to your configured LLM provider only.
- Usage stats are stored locally at `~/.config/promptforge/usage_log.jsonl`.
- No telemetry, no analytics, no phone-home.

---

## Contributing

```bash
git clone https://github.com/<your-org>/promptforge
cd promptforge
pip install -e ".[dev]"
pytest
ruff check src/ tests/
mypy src/promptforge --strict
```

All three commands must pass with zero errors before submitting a PR.

---

## License

MIT
```

---

## § 18 — Token Savings Analytics

### 18.1 — Usage Log Data Model

**File:** `~/.config/promptforge/usage_log.jsonl`
**Format:** One JSON object per line (JSONL). Append-only. Two record types — merged at read time.

```python
# stats/models.py
# Use kw_only=True so we can put record_type (with default) first
# without triggering "non-default argument follows default argument" errors.

@dataclass(kw_only=True)
class UsageRecord:
    session_id: str                # uuid4, generated by Synthesizer, attached to OptimizedPrompt
    timestamp: str                 # ISO 8601: "2025-06-08T14:32:01Z"
    command: str                   # "run" | "correct" | "repo_ask"
    mode: str                      # "standard" | "repo"
    original_token_estimate: int
    optimized_token_estimate: int
    tool_input_tokens: int
    tool_output_tokens: int
    tool_total_tokens: int
    provider: str
    model: str
    issues_detected: int
    questions_asked: int
    questions_answered: int
    reduction_pct: float           # can be negative for short prompts that expand
    # Repo-mode-only fields — None in standard mode:
    injected_tokens: int | None = None
    repo_slug: str | None = None
    files_indexed: int | None = None
    files_injected: int | None = None
    template_id: str | None = None
    # Filled in at load time by merging with RatingRecord — never written directly:
    rating: int | None = None
    rated_at: str | None = None
    # Discriminator — kept last because it has a default. Always "session" for this class.
    record_type: str = "session"

@dataclass(kw_only=True)
class RatingRecord:
    session_id: str                # links to UsageRecord
    rating: int                    # 1 | -1
    rated_at: str                  # ISO 8601
    record_type: str = "rating"    # discriminator — always "rating"
```

**Merge in `UsageLogger.load_all()`:**
```
1. Read all lines, parse JSON, skip malformed lines with WARNING
2. Separate into session_records and rating_records by record_type
3. Build dict: session_id → UsageRecord from session_records
4. For each rating_record: find matching UsageRecord, patch rating and rated_at
5. Return list[UsageRecord] sorted by timestamp ascending
```

### 18.2 — Stats Command Flags

| Flag | Type | Default | Behaviour |
|---|---|---|---|
| `--detailed` | bool | False | Show per-session table |
| `--reuse N` | int | 1 | Project savings at N× reuse |
| `--detailed --reuse N` | combined | — | Show per-session table, then a projection panel below |
| `--reset` | bool | False | Delete `usage_log.jsonl` after interactive confirmation. Refuses if stdin is not a TTY unless `--yes` is also passed. |
| `--yes` | bool | False | Skip the confirmation prompt for `--reset`. Required for scripted use in non-TTY environments. |
| `--export PATH` | Path | None | Write full merged records as JSON array to file |
| `--last N` | int | all | Limit to last N sessions (applied before all computations) |

### 18.3 — Stats Computation Logic

All computed in `stats/engine.py`. Pure Python math, no external library.

```python
total_sessions = len(records)
total_original_tokens = sum(r.original_token_estimate for r in records)
total_optimized_tokens = sum(r.optimized_token_estimate for r in records)
total_tool_cost = sum(r.tool_total_tokens for r in records)

avg_reduction_pct = mean([
    r.reduction_pct for r in records
    if r.original_token_estimate > 0
])

break_even_per_session = [
    ceil(r.tool_total_tokens / max(r.original_token_estimate - r.optimized_token_estimate, 1))
    if r.original_token_estimate > r.optimized_token_estimate
    else None
    for r in records
]

def projected_net_saving(records, reuse_count):
    gross = sum(
        (r.original_token_estimate - r.optimized_token_estimate) * reuse_count
        for r in records
    )
    return gross - sum(r.tool_total_tokens for r in records)

def projected_reduction_pct(records, reuse_count):
    baseline = sum(r.original_token_estimate for r in records) * reuse_count
    with_tool = (sum(r.optimized_token_estimate for r in records) * reuse_count
                 + sum(r.tool_total_tokens for r in records))
    if baseline == 0:
        return 0.0
    return (baseline - with_tool) / baseline * 100
```

### 18.4 — Stats Display Format

**Default (`promptforge stats`):**

```
╭──────────────────────────────────────────────────────╮
│  PromptForge — Token Savings Report                  │
│──────────────────────────────────────────────────────│
│  Sessions tracked:            23  (18 standard, 5 repo)  │
│  Total original tokens:    8,450                     │
│  Total optimised tokens:   3,210                     │
│  Total tool cost:         14,490                     │
│                                                      │
│  ── Standard mode ─────────────────────────────────  │
│  Average prompt reduction:   62%                     │
│  Avg break-even reuse count:  4×                     │
│  Net saving at 10× reuse: +61,310 tokens             │
│                                                      │
│  ── Repo mode ─────────────────────────────────────  │
│  Avg LLM turns saved per session:  2.8 turns         │
│  Top-rated prompt pattern: include middleware stack  │
│  Lowest-rated pattern:     describe-only (no inject) │
│                                                      │
│  ── Feedback ──────────────────────────────────────  │
│  Sessions rated:     19 of 23                        │
│  👍 Positive:        14  (74%)                       │
│  👎 Negative:         5  (26%)                       │
╰──────────────────────────────────────────────────────╯

Token estimates use a word-count approximation (~1.33 tokens/word).
Pricing estimates based on public rates as of [date]. Verify at your provider's pricing page.
```

**With `--detailed --reuse 15` (both flags combined):**

```
╭─────────────────────────────────────────────────────────────────────────────╮
│  Session Log                                                                │
│─────────────────────────────────────────────────────────────────────────────│
│  Date       │ Original │ Optimised │ Tool cost │ Reduction │ Break-even    │
│─────────────────────────────────────────────────────────────────────────────│
│  2025-06-08 │       9t │      118t │      513t │    -1211% │ N/A (expanded)│
│  2025-06-07 │     312t │      180t │      490t │      42%  │      4×       │
│  ...                                                                        │
╰─────────────────────────────────────────────────────────────────────────────╯

ℹ  'Expanded' means your original prompt was short and the optimised version
   is longer. This is expected — reuse amortises the tool cost.

╭──────────────────────────────────────────────────────╮
│  Projection: 15× reuse per prompt                    │
│──────────────────────────────────────────────────────│
│  Baseline (raw prompts × 15):    126,750 tokens      │
│  With PromptForge (opt × 15                          │
│                   + tool cost):   62,640 tokens      │
│  Net saving vs baseline:          64,110 tokens      │
│  Reduction vs baseline:            50.6%             │
╰──────────────────────────────────────────────────────╯
```

### 18.5 — UsageLogger Implementation

```python
class UsageLogger:
    log_path: Path  # ~/.config/promptforge/usage_log.jsonl

    def record(self, record: UsageRecord) -> None:
        # Append one JSON line (record_type="session") — never overwrite

    def record_rating(self, session_id: str, rating: int) -> None:
        # Append one JSON line (record_type="rating") with session_id link

    def load_all(self) -> list[UsageRecord]:
        # Read all lines, merge session + rating records by session_id
        # Skip malformed lines with WARNING

    def reset(self, skip_confirmation: bool = False) -> None:
        # If skip_confirmation is False:
        #   if stdin is not a TTY → raise UsageError("Refusing to reset without --yes in non-interactive mode.")
        #   else → prompt "This will delete X sessions. Type 'yes' to confirm:" and only delete on exact match
        # If skip_confirmation is True: delete immediately, no prompt

    def export(self, output_path: Path) -> None:
        # Write merged records as JSON array to output_path
```

**When to call:**
- `UsageLogger.record()` — in `Synthesizer.synthesize()` after `OptimizedPrompt` is built, before returning
- `UsageLogger.record_rating()` — in `Renderer` after `readchar.readchar()` returns y or n

---

## § 19 — Repo Intelligence

### 19.1 — Overview & Token Economics

In standard mode, savings come from prompt compression. In repo mode, savings come from interaction
reduction — one precise prompt with the right context gets the correct answer in turn 1 instead of
3–5 back-and-forth turns.

```
Without PromptForge repo mode:
  Turn 1: "how does auth work in my app?" → LLM asks for code → 400 tokens
  Turn 2: paste AuthService.java → 2,000 tokens → LLM misses JwtFilter
  Turn 3: paste JwtFilter.java → 1,500 tokens → finally correct answer
  Total: ~3,900 tokens across 3 turns

With PromptForge repo mode:
  Tool cost:     ~600 tokens (index lookup + synthesis)
  Injected:      ~800 tokens (AuthService + JwtFilter — correct files picked automatically)
  Output prompt: ~1,000 tokens total → LLM answers correctly in 1 turn
  Net saving: ~2,300 tokens + 2 fewer turns
```

### 19.2 — New Commands

#### `promptforge repo add <path-or-url>`

```
Arguments:
  target: str  — local path OR GitHub HTTPS URL

Flags:
  --name / -n TEXT        Human-readable alias (default: repo directory name)
  --branch / -b TEXT      Branch to index (default: default branch)
  --depth INT             Max directory depth (default: 5, max: 10)
  --exclude TEXT          Comma-separated glob patterns (default: node_modules,.git,__pycache__,*.min.js,dist/,build/,*.lock)
  --token TEXT            GitHub PAT for private repos (or GITHUB_TOKEN env var)
  --max-file-kb INT       Skip files larger than N KB (default: 100)

Flow:
  1. Detect local vs remote (starts with "https://github.com/" → remote)
  2. Local: walk with pathlib, respect --exclude globs
     Remote: use PyGithub Contents API (recursive=True)
  3. For each text file: read content, detect language, extract symbols, compute importance score
  4. Detect stack (see § 19.5)
  5. Auto-detect remote URL for local repos using gitpython:
     Repo(path).remotes['origin'].url if origin exists
  6. Save index.json + files/<sha256>.txt to ~/.config/promptforge/repos/<slug>/
  7. Print summary

Exit codes: 0, 1 (path/URL invalid), 2 (GitHub API error), 3 (no text files found)
```

#### `promptforge repo ask "<question>"`

```
Flags:
  --repo / -r TEXT        Repo slug or alias (default: auto-detect from CWD git remote via gitpython)
  --inject-code / -i      Inject relevant code snippets into output prompt
  --max-inject-kb INT     Max KB of injected code (default: 20KB)
  --diff, --output, --no-clipboard, --batch  — same as `run`

Flow:
  1. Resolve repo: --repo flag → auto-detect via gitpython Repo('.').remotes['origin'].url → error
     (Do NOT use subprocess to call `git remote get-url origin` — use gitpython consistently)
  2. Load RepoIndex
  3. Run standard Analyzer on question
  4. Run RepoContextBuilder: rank files by relevance (§ 19.4)
  5. Run clarifying questions if HIGH/MEDIUM issues detected
  6. Assemble RepoPromptContext
  7. Call Synthesizer (ONE LLM call) with repo-aware system prompt
  8. UsageLogger.record() with repo fields before returning
  9. Render + clipboard + rating prompt
  10. UsageLogger.record_rating() if rated
  11. Save PromptTemplate

Exit codes: 0, 1 (repo not indexed), 2 (LLM error), 3 (repo stale — suggest refresh)
```

#### `promptforge repo list`
#### `promptforge repo refresh <name-or-slug>`
#### `promptforge repo templates`

(Same as original plan — no changes needed for these commands)

### 19.3 — Data Models

(Same as original plan — no changes needed)

### 19.4 — File Importance Scoring Algorithm

(Same as original plan — no changes needed)

### 19.5 — Stack Detection Algorithm

**Fixes:** Add precedence ordering and deduplication to prevent redundant stack entries (e.g., a Spring Boot repo should not show both "Java + Spring Boot" and "Java + Maven").

```python
STACK_SIGNALS = [
    # Ordered most-specific first — first match wins within each language group
    ("Java + Spring Boot",   lambda files, contents: "pom.xml" in files and "spring" in contents.get("pom.xml", "")),
    ("Java + Spring Boot",   lambda files, contents: "build.gradle" in files and "spring" in contents.get("build.gradle", "")),
    ("Kotlin + Spring Boot", lambda files, contents: "build.gradle.kts" in files and "spring" in contents.get("build.gradle.kts", "")),
    ("Java + Maven",         lambda files, contents: "pom.xml" in files),
    ("Java + Gradle",        lambda files, contents: "build.gradle" in files or "settings.gradle" in files),
    ("Python + FastAPI",     lambda files, contents: "fastapi" in contents.get("requirements.txt", "") or "fastapi" in contents.get("pyproject.toml", "")),
    ("Python + Django",      lambda files, contents: "manage.py" in files),
    ("Python + Flask",       lambda files, contents: "flask" in contents.get("requirements.txt", "") or "flask" in contents.get("pyproject.toml", "")),
    ("Python",               lambda files, contents: any(f in files for f in ["requirements.txt", "pyproject.toml", "setup.py"])),
    ("TypeScript + Next.js", lambda files, contents: any(f in files for f in ["next.config.js", "next.config.ts"])),
    ("TypeScript + React",   lambda files, contents: "react" in contents.get("package.json", "") and "tsconfig.json" in files),
    ("TypeScript",           lambda files, contents: "tsconfig.json" in files),
    ("JavaScript",           lambda files, contents: "package.json" in files),
    ("Go",                   lambda files, contents: "go.mod" in files),
    ("Rust",                 lambda files, contents: "Cargo.toml" in files),
    ("C# + .NET",            lambda files, contents: any(f.endswith(".csproj") or f.endswith(".sln") for f in files)),
    ("Ruby + Rails",         lambda files, contents: "Gemfile" in files and "config/routes.rb" in files),
    ("PHP + Laravel",        lambda files, contents: "artisan" in files),
]

def detect_stack(file_paths: list[str], file_contents: dict[str, str]) -> list[str]:
    """
    Evaluate signals in order. For each language family (Java, Python, TypeScript, etc.),
    only the first matching signal is kept — preventing redundant entries like
    ["Java + Spring Boot", "Java + Maven"] for the same repo.
    """
    matched_languages: set[str] = set()
    result: list[str] = []
    for stack_name, test_fn in STACK_SIGNALS:
        language_family = stack_name.split()[0]  # "Java", "Python", "TypeScript", etc.
        if language_family in matched_languages:
            continue  # already have a more-specific match for this language
        if test_fn(set(file_paths), file_contents):
            result.append(stack_name)
            matched_languages.add(language_family)
    return result
```

### 19.6 — Repo-Aware System Prompt

Stored in `synthesizer/system_prompt_repo.txt`. Loaded the same way as the standard system prompt.
(Content unchanged from original plan.)

### 19.7 — Feedback & Learning Engine

(Same as original plan. `readchar` is already a core dependency from Phase 1, so it is available here.)

### 19.8 — File & Directory Structure (additions to § 13)

```
src/promptforge/
│
└── repo/
    ├── __init__.py
    ├── indexer.py            # RepoIndexer: orchestrates local or remote reader
    ├── local.py              # LocalRepoReader: pathlib + gitpython
    ├── remote.py             # RemoteRepoReader: PyGithub API client
    ├── context_builder.py    # RepoContextBuilder: relevance ranking
    ├── stack_detector.py     # StackDetector: detect_stack() with precedence ordering
    ├── template_store.py     # TemplateStore
    ├── learning.py           # LearningEngine
    └── models.py             # FileEntry, RepoIndex, PromptTemplate, RepoPromptContext, LearningInsights
```

### 19.9 — Implementation Order (Phase 8)

All prior phases (1–7) must be complete before beginning Phase 8.

52. Add `gitpython`, `PyGithub`, `rapidfuzz` to `pyproject.toml` (`readchar` is already there from Phase 1).
53. Implement `stack_detector.py` — ordered signal list with language-family deduplication. Unit test all signals, including overlap cases (Spring Boot repo must NOT emit "Java + Maven" redundantly).
54. Implement `local.py` (LocalRepoReader) — walk directory, respect excludes, extract symbols with regex, read git remote URL via `gitpython.Repo(path).remotes['origin'].url`. Unit test with `tmp_path`.
55. Implement `remote.py` (RemoteRepoReader) — PyGithub API calls mocked in all tests. Test: tree fetch, file content fetch, rate limit handling, private repo auth error.
56. Implement `indexer.py` (RepoIndexer) — orchestrates local or remote reader, builds `RepoIndex`, writes `index.json` and `files/<hash>.txt`.
57. Implement `promptforge repo add`. Integration test: local path → index written to tmp dir.
58. Implement `context_builder.py` — relevance ranking from § 19.4, repo auto-detect via gitpython (not subprocess). Unit test with synthetic 50-file index.
59. Implement `template_store.py`. Unit test all operations.
60. Implement `learning.py` (LearningEngine). Unit test with synthetic rated sessions.
61. Implement `repo ask` pipeline.
62. Implement `repo list`, `repo refresh`, `repo templates` commands.
63. Update `UsageLogger.record()` to handle repo mode fields.
64. Update `StatsEngine` for interaction reduction and feedback analysis.
65. Update `StatsRenderer` for repo mode and feedback panels.
66. Integration test: `test_repo_ask_command.py` — synthetic index, respx-mocked LLM.
67. Update README with repo intelligence section (§ 19.10 below).

### 19.10 — README additions

Add after `promptforge stats` section:

```markdown
---

## Repo Intelligence

PromptForge can index any git repository and generate prompts that are aware of your actual
codebase — referencing real file paths, class names, and your tech stack.

### Index a repo

```bash
# Local repo
promptforge repo add ./my-project

# Remote GitHub repo (public)
promptforge repo add https://github.com/my-org/my-project

# Remote private repo
promptforge repo add https://github.com/my-org/private-repo --token ghp_...
# or: export GITHUB_TOKEN=ghp_... first

# Set a short alias
promptforge repo add ./my-project --name myapp
```

### Ask a question about your repo

```bash
# Describe-only (no code injected — smaller output prompt)
promptforge repo ask "how does authentication work?"

# With code injection — relevant files included inline
promptforge repo ask "how does authentication work?" --inject-code

# Specify repo (default: auto-detected from CWD git remote)
promptforge repo ask "add a new REST endpoint for user profiles" --repo my-org/my-project
```

PromptForge will:
1. Find the most relevant files for your question (no LLM call)
2. Ask clarifying questions if needed
3. Make **one API call** to synthesize a repo-aware prompt
4. Copy the result to your clipboard automatically

### Manage indexed repos

```bash
promptforge repo list
promptforge repo refresh myapp
promptforge repo templates --repo my-org/my-project --top
```

### How repo mode affects token savings

In repo mode, the output prompt is larger (it references specific files and may include code).
The saving comes from fewer LLM turns — one precise prompt instead of 3–5 back-and-forths.

`promptforge stats` tracks this and shows estimated turns saved alongside token counts.

### GitHub Copilot

```bash
promptforge configure
# Select: GitHub Copilot
# Enter: your GitHub Personal Access Token (needs `copilot` scope)
```
```
