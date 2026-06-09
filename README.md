# PromptForge

> Turn vague prompts into structured, token-efficient prompts — from your terminal.

PromptForge analyses a vague prompt, asks you targeted clarifying questions, and synthesises a final prompt that is clear, structured, and uses fewer tokens when sent to any LLM agent. **One API call. No bloat. No retries.**

---

## Table of Contents

- [Why PromptForge](#why-promptforge)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Step 1 — Configure](#step-1--configure)
- [Step 2 — Run](#step-2--run)
- [Interactive REPL](#interactive-repl)
- [All Commands](#all-commands)
- [Repo Intelligence (graphify)](#repo-intelligence-graphify)
- [Supported Providers](#supported-providers)
- [How to Get API Keys](#how-to-get-api-keys)
- [Configuration File](#configuration-file)
- [Token Savings Analytics](#token-savings-analytics)
- [Exit Codes](#exit-codes)
- [Privacy](#privacy)

---

## Why PromptForge

Vague prompts cost you in two ways:

1. **Bad output** — you retry 2–3 times, each retry spending more tokens than the last.
2. **Bloated prompts** — you add more and more context hoping something sticks, ballooning token count.

PromptForge fixes both. It asks the right questions upfront, then synthesises a prompt that is precise and lean — so your agent gets it right on the first attempt.

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.11 or higher |
| Operating system | macOS or Linux (including WSL) |
| Native Windows | ❌ Not supported |

Check your Python version:
```bash
python3 --version
```

---

## Installation

### Option 1 — pip (recommended)

```bash
pip3 install promptforge
```

### Option 2 — pipx (isolated environment, no conflicts)

```bash
# Install pipx if you don't have it
pip3 install pipx
pipx ensurepath

# Then install PromptForge
pipx install promptforge
```

### Option 3 — From source

```bash
git clone https://github.com/your-org/promptforge
cd promptforge

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # macOS / Linux

# Install from pyproject.toml
pip install -e .
```

### Verify the installation

```bash
promptforge
```

You should see the PromptForge welcome banner with available commands listed.

---

## Quick Start

```
Configure once  →  Run on any vague prompt  →  Paste the result
```

---

## Step 1 — Configure

Run the setup wizard once. It walks you through choosing a provider, selecting a model, and entering your API key.

```bash
promptforge configure
```

**What happens:**

```
Select your LLM provider:
  1. OpenAI
  2. Anthropic
  3. Google Gemini
  4. Mistral
  5. Groq
  6. GitHub Copilot

Provider number: 2

Select a model for Anthropic:
  1. Claude Haiku 3.5 ★  ← recommended (fastest, cheapest)
  2. Claude Sonnet 4.5
  3. Claude Opus 4.5

Model number: 1

Anthropic API Key: sk-ant-...   ← hidden while typing

Validating key (attempt 1/3)...
✓ Key validated. Config saved to ~/.config/promptforge/config.toml
```

**Tip:** Start with the ★ recommended model. It is the fastest and cheapest option for each provider and works well for prompt optimisation.

Config is saved to `~/.config/promptforge/config.toml` with file permissions set to `600` (owner read/write only).

To reconfigure at any time (change provider, model, or key):
```bash
promptforge configure
```

---

## Step 2 — Run

Pass any vague prompt and PromptForge will analyse it, ask clarifying questions, and return an optimised version.

```bash
promptforge run "help me fix the code"
```

**Example session:**

```
Analysing prompt...

Issues detected:
  • No output format specified (HIGH)
  • Action verb is ambiguous: "help" (MEDIUM)
  • No input structure defined (HIGH)

[1/3] What format should the output be in?
      (e.g. JSON, markdown list, code function, plain paragraph)
> full file with only changed functions shown

[2/3] "help" is vague. What specifically should happen?
      (e.g. generate new, refactor existing, extract from, validate against)
> refactor for readability and add type hints

[3/3] What exactly will the agent receive as input?
      Describe the format, structure, or provide a sample.
> a Python function pasted inline

Synthesising optimised prompt...

╭─────────────────────────────────────────────────────────────╮
│  Optimised Prompt                                           │
│─────────────────────────────────────────────────────────────│
│  You are a senior Python engineer specialising in clean,    │
│  idiomatic Python 3.11+ code.                               │
│                                                             │
│  Task: Refactor the provided Python function for            │
│  readability and add complete type hints.                   │
│                                                             │
│  Input: A Python function pasted inline. Assume it is       │
│  syntactically valid.                                       │
│                                                             │
│  Output: Return only the refactored function(s) that        │
│  changed. Format: plain Python code block.                  │
│                                                             │
│  Steps:                                                     │
│  1. Read the function and identify readability issues.      │
│  2. Refactor — preserve all existing behaviour.             │
│  3. Add PEP 484 type hints to all parameters and returns.   │
│  4. Return only the modified function(s).                   │
│                                                             │
│  Constraints:                                               │
│  • Do not change function signatures.                       │
│  • Do not add docstrings unless asked.                      │
│  • Do not explain your changes.                             │
╰─────────────────────────────────────────────────────────────╯

✓ Copied to clipboard

Was this prompt helpful? [y=👍 / n=👎 / s=skip]: y
✓ Feedback recorded.
```

The optimised prompt is automatically copied to your clipboard. Paste it directly into any LLM interface.

---

## Interactive REPL

Run `promptforge` with no arguments to launch the interactive session. PromptForge loads once and stays open — no cold-start delay between prompts.

```bash
promptforge
```

```
⚡ promptforge > fix my authentication flow
⚡ promptforge > /diff summarise this article
⚡ promptforge > /quick write a SQL query for user retention
⚡ promptforge > /stats
⚡ promptforge > /exit
```

You can also just type a prompt directly (no slash needed) — it runs as `/run` by default.

### REPL slash commands

| Command | Description |
|---|---|
| `/run <prompt>` | Optimise a prompt (asks clarifying questions) |
| `/quick <prompt>` | Optimise without questions |
| `/batch <prompt>` | Show all questions at once, answer in one pass |
| `/diff <prompt>` | Optimise with before/after token comparison |
| `/load <file>` | Load a prompt from a file and optimise it |
| `/configure` | Set up provider and API key |
| `/stats` | Show token savings analytics |
| `/stats reset` | Clear session history |
| `/history` | Show your last 10 sessions |
| `/clear` | Clear the terminal |
| `/help` | Show the full command list |
| `/exit` | Quit PromptForge |

---

## All Commands

### `promptforge configure`

First-time setup (or reconfigure at any time).

```bash
promptforge configure
```

---

### `promptforge run`

Analyse and optimise a vague prompt.

```bash
# Inline prompt
promptforge run "your vague prompt here"

# From a file
promptforge run --file my_prompt.txt

# From stdin (pipe)
echo "your prompt" | promptforge run

# Show before/after token diff
promptforge run "your prompt" --diff

# Save the optimised prompt to a file (also prints to terminal)
promptforge run "your prompt" --output optimised.txt

# Redirect raw output to a file (no decoration, safe for scripts)
promptforge run "your prompt" > optimised.txt

# Non-interactive: show all questions at once, answer in one pass
promptforge run "your prompt" --batch

# Skip all questions entirely — synthesise directly from raw prompt
promptforge run "your prompt" --no-questions

# Disable clipboard copy (useful in CI or scripts)
promptforge run "your prompt" --no-clipboard

# Debug mode: print meta-prompt, raw LLM response, detector results
promptforge run "your prompt" --debug
```

**Input precedence when multiple sources are provided:**
`--file` > positional argument > stdin. Lower-priority sources are silently ignored.

**Stdout vs stderr:**
- `stdout` — only the raw optimised prompt text (safe to redirect to a file or pipe)
- `stderr` — all panels, questions, progress, errors, and feedback prompts

---

### `promptforge correct`

Convenience alias for `promptforge run --file <file>`. Optimise an existing prompt file.

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

# Detailed per-session table
promptforge stats --detailed

# Limit to last N sessions
promptforge stats --detailed --last 20

# Project savings at N× reuse per prompt
promptforge stats --reuse 10

# Detailed table + projection panel combined
promptforge stats --detailed --reuse 10

# Reset session history (asks for confirmation)
promptforge stats --reset

# Reset without confirmation (for scripts)
promptforge stats --reset --yes

# Export all session records as JSON
promptforge stats --export sessions.json
```

---

### `promptforge version`

```bash
promptforge version
# promptforge 1.0.0
```

---

## Repo Intelligence (graphify)

PromptForge integrates with [graphify](https://pypi.org/project/graphifyy/) to build a knowledge graph of your codebase and use it as context when synthesising prompts.

### Install the optional dependency

```bash
pip install "promptforge[repo]"
# or inside your venv:
pip install graphifyy
```

### Usage (inside the REPL)

```bash
# Index a local repo (builds a knowledge graph — takes a few minutes for large repos)
/repo add ~/projects/my-api

# Ask a question — retrieves graph context then synthesises an optimised prompt
/repo ask my-api how does the authentication middleware work?

# Same but skip clarifying questions
/repo quick my-api explain the database connection pooling

# Raw graph query only (no prompt synthesis)
/repo query my-api what are the main entry points?

# Open the interactive graph visualisation in your browser
/repo graph my-api

# List all indexed repos
/repo list

# Re-index after code changes
/repo refresh my-api

# Remove a repo from the index
/repo remove my-api
```

If graphify is not installed, PromptForge will prompt you to install it when you use a `/repo` command.

---

## Supported Providers

| # | Provider | Recommended model ★ | Other available models | Key type |
|---|---|---|---|---|
| 1 | **OpenAI** | GPT-4.1 Mini | GPT-4.1, GPT-4o, GPT-4o Mini, o4-mini | OpenAI API Key |
| 2 | **Anthropic** | Claude Haiku 4.5 | Claude Sonnet 4.6, Claude Opus 4.7 | Anthropic API Key |
| 3 | **Google Gemini** | Gemini 2.5 Flash | Gemini 2.5 Pro, Gemini 2.0 Flash, Gemini 1.5 Flash | Google AI API Key |
| 4 | **Mistral** | Mistral Small | Mistral Large, Codestral, Mistral Nemo | Mistral API Key |
| 5 | **Groq** | LLaMA 3.3 70B | LLaMA 3.1 8B Instant, Gemma 2 9B, Mixtral 8x7B | Groq API Key |
| 6 | **GitHub Copilot** | GPT-4.1 | GPT-4o, GPT-4o Mini | GitHub PAT (copilot scope) |

★ = recommended — best balance of speed and quality for prompt optimisation.

> **Models are current as of June 2025.** Run `promptforge configure` to see the full live list shown during setup.

---

## How to Get API Keys

### OpenAI
1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign in → click your profile → **API keys**
3. Click **Create new secret key**
4. Copy the key — it starts with `sk-`
5. ⚠️ You need a funded account or free-tier credits

### Anthropic
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign in → **API Keys** in the left sidebar
3. Click **Create Key**
4. Copy the key — it starts with `sk-ant-`
5. ⚠️ You need a funded account or free-tier credits

### Google Gemini
1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in → click **Get API key** → **Create API key**
3. Copy the key — it starts with `AIza`
4. ✅ Free tier available with generous limits

### Mistral
1. Go to [console.mistral.ai](https://console.mistral.ai)
2. Sign in → **API Keys** in the left sidebar
3. Click **Create new key**
4. Copy the key — it starts with a random string
5. ⚠️ You need a funded account

### Groq
1. Go to [console.groq.com](https://console.groq.com)
2. Sign in → **API Keys** in the left sidebar
3. Click **Create API Key**
4. Copy the key — it starts with `gsk_`
5. ✅ Free tier available — fastest inference of all providers

### GitHub Copilot
1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Click **Generate new token (classic)**
3. Give it a name (e.g. "PromptForge")
4. Under **Scopes**, tick **`copilot`**
5. Click **Generate token**
6. Copy the token — it starts with `ghp_`
7. ⚠️ Requires an active GitHub Copilot subscription

---

## Configuration File

Located at `~/.config/promptforge/config.toml`. Created automatically by `promptforge configure`.

```toml
[llm]
provider = "anthropic"
model = "claude-haiku-3-5"
api_key = "sk-ant-..."
litellm_model_string = "anthropic/claude-haiku-3-5"

[preferences]
default_mode = "interactive"
show_diff = false
default_inject_code = false
```

**File permissions:** set to `600` (owner read/write only) on macOS and Linux. Your API key never leaves this file.

To change provider, model, or key — just re-run `promptforge configure`. It overwrites the existing config.

---

## Token Savings Analytics

Every session logs:
- Estimated tokens in your original (vague) prompt
- Estimated tokens in the optimised prompt
- Tool cost (tokens spent on the synthesis call itself)
- Net saving for that session

```
╭──────────────────────────────────────────────────────╮
│  PromptForge — Token Savings Report                  │
│──────────────────────────────────────────────────────│
│  Sessions tracked:          23                       │
│  Total original tokens:  8,450                       │
│  Total optimised tokens: 3,210                       │
│  Total tool cost:       14,490                       │
│                                                      │
│  Average prompt reduction:   62%                     │
│  Net saving at 10× reuse: +61,310 tokens             │
│                                                      │
│  Sessions rated:   19 of 23                          │
│  👍 Positive:      14  (74%)                         │
│  👎 Negative:       5  (26%)                         │
╰──────────────────────────────────────────────────────╯

Token estimates use a word-count approximation (~1.33 tokens/word).
```

> **Note:** Token estimates are approximate. For code-heavy prompts, actual counts may be 2–3× higher. Treat as a guide, not a precise measurement.

Data is stored locally at `~/.config/promptforge/usage_log.jsonl`. Never sent anywhere.

---

## Linux Clipboard

On Linux, clipboard copy requires one of:

```bash
sudo apt install xclip        # X11
sudo apt install wl-clipboard  # Wayland
```

If neither is installed, PromptForge degrades gracefully — the prompt is still printed to stdout and you can redirect it:

```bash
promptforge run "your prompt" > optimised.txt
```

---

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Usage error — bad input, config missing, file not found |
| `2` | LLM error — auth failure, rate limit, timeout, bad request |
| `99` | Unexpected internal error — run with `--debug` for details |

---

## Privacy

- Your prompts are sent only to your configured LLM provider.
- Usage stats are stored locally at `~/.config/promptforge/usage_log.jsonl`.
- No telemetry, no analytics, no phone-home.
- API key stored at `~/.config/promptforge/config.toml` with permissions `600`.

---

## Contributing

```bash
git clone https://github.com/your-org/promptforge
cd promptforge

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # macOS / Linux

# Install with dev dependencies
pip3 install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/

# Type check
mypy src/promptforge --strict
```

All three must pass with zero errors before submitting a PR.

---

## License

MIT
