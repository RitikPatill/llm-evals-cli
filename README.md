# llm-evals-cli

> Lightweight, zero-fuss LLM evaluation suites for the command line.

![PyPI](https://img.shields.io/badge/pypi-not%20yet%20published-lightgrey?label=PyPI)
![License: MIT](https://img.shields.io/badge/license-MIT-blue)
![CI](https://img.shields.io/badge/CI-not%20configured-lightgrey?label=CI)

## Why this tool

Prompt changes break things silently. Existing eval platforms are either cloud-only, require heavy setup, or lock you into a single framework — making it painful to get a quick regression check before shipping.

`llm-evals-cli` gives you a fast, local, CI-friendly feedback loop: define test cases in YAML, run one command, get a colour-coded pass/fail table in under a minute.

## What works now (M3 — async LLM runner)

- Python package layout under `src/llm_evals_cli/` with `pyproject.toml` (hatchling build, Python ≥ 3.11)
- Pinned runtime dependencies: `typer`, `rich`, `httpx`, `pydantic`, `pyyaml`
- **`evals validate <suite.yaml>`** — fully implemented: loads and validates a YAML suite, prints a success message or structured error
- **`evals run <suite.yaml>`** — fully implemented: async batched requests to any OpenAI-compatible endpoint with concurrency limit and per-case timeout; prints a summary line
- Pydantic v2 models (`Suite`, `Case`, `MetricEnum`) in `schema.py`; auto-assigns `id` to cases that omit it
- YAML loader in `loader.py` using `yaml.safe_load`
- Async runner in `runner.py`: `run_suite()` + `RunResult` dataclass; resolves API key from `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` env vars; supports `--base-url` flag and `LLM_BASE_URL` env var for local models (Ollama, etc.)
- Example suites in `examples/basic_suite.yaml` and `examples/llm_judge_suite.yaml`
- Unit tests in `tests/test_schema.py` and `tests/test_runner.py` (uses `httpx.MockTransport`, no real network calls)
- `evals show-report` is a scaffolded stub (not yet implemented)

## Planned features

- **YAML eval suite format** — `prompt`, `expected`, `metric`, optional `system` message and `tags`
- **Async LLM runner** — batched requests via `httpx` to any OpenAI-compatible endpoint (OpenAI, Anthropic, Ollama, …)
- **Four metrics** — `exact_match`, `contains`, `regex`, `llm_judge`
- **Rich terminal reporter** — live progress bar, per-case colour table, summary score and latency stats
- **JSON & HTML export** — `--output report.json` / `--output report.html`
- **CI-ready** — exits non-zero on any failure; no server, no account required

## Quickstart

```bash
pip install llm-evals-cli

# Check your suite is valid before spending tokens
evals validate suite.yaml

# Run against OpenAI (set OPENAI_API_KEY first)
evals run suite.yaml

# Run against a local Ollama instance
evals run suite.yaml --base-url http://localhost:11434/v1

# Tune concurrency and timeout
evals run suite.yaml --concurrency 10 --timeout 60
```

> **Note:** `evals show-report` is a stub. `evals validate` and `evals run` are fully working as of M3.

## Eval suite format

```yaml
# suite.yaml
model: gpt-4o-mini
cases:
  - prompt: "What is 2 + 2?"
    expected: "4"
    metric: exact_match

  - prompt: "Summarise the water cycle in one sentence."
    expected: "evaporation"
    metric: contains

  - system: "You are a JSON API. Reply with valid JSON only."
    prompt: "Return a user object with name and age fields."
    expected: '^\s*\{.*"name".*"age".*\}\s*$'
    metric: regex
    tags: [json, structured-output]

  - prompt: "Explain recursion to a 10-year-old."
    expected: "A clear, jargon-free explanation suitable for a child."
    metric: llm_judge
```

## Architecture

```
llm-evals-cli/
├── src/
│   └── llm_evals_cli/
│       ├── __init__.py          # package version (0.1.0)
│       ├── cli.py               # Typer app; validate + run (done), show-report stub
│       ├── schema.py            # Pydantic v2 models: Suite, Case, MetricEnum
│       ├── loader.py            # load_suite(path) → Suite
│       └── runner.py            # async run_suite(); RunResult dataclass
├── examples/
│   ├── basic_suite.yaml         # exact_match, contains, regex examples
│   └── llm_judge_suite.yaml     # llm_judge with system prompt and tags
├── tests/
│   ├── test_schema.py           # unit tests for schema parsing and validation
│   └── test_runner.py           # async runner tests using httpx.MockTransport
├── pyproject.toml               # build config, pinned deps, entry point
├── requirements.txt             # pinned runtime deps
├── requirements-dev.txt         # dev/test dependencies (pytest, pytest-asyncio, etc.)
└── LICENSE
```

## Roadmap

| Milestone | Scope | Status |
|-----------|-------|--------|
| M1 | Repo scaffold, package layout, stub CLI, dev toolchain | done |
| M2 | YAML loader, Pydantic suite models, `validate` command | done |
| M3 | Async LLM runner, concurrency limit, per-case timeout | done |
| M4 | Metrics engine (`exact_match`, `contains`, `regex`), Rich reporter | planned |
| M5 | `llm_judge` metric, JSON / HTML export, CI workflow | planned |

<!-- TODO: update Status column as milestones ship -->

## License

[MIT](LICENSE)
