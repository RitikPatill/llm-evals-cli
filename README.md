# llm-evals-cli

> Lightweight, zero-fuss LLM evaluation suites for the command line.

![PyPI](https://img.shields.io/badge/pypi-not%20yet%20published-lightgrey?label=PyPI)
![License: MIT](https://img.shields.io/badge/license-MIT-blue)
![CI](https://img.shields.io/badge/CI-not%20configured-lightgrey?label=CI)

## Why this tool

Prompt changes break things silently. Existing eval platforms are either cloud-only, require heavy setup, or lock you into a single framework — making it painful to get a quick regression check before shipping.

`llm-evals-cli` gives you a fast, local, CI-friendly feedback loop: define test cases in YAML, run one command, get a colour-coded pass/fail table in under a minute.

## What works now (M5 — rich reporter + export)

- Python package layout under `src/llm_evals_cli/` with `pyproject.toml` (hatchling build, Python ≥ 3.11)
- Pinned runtime dependencies: `typer`, `rich`, `httpx`, `pydantic`, `pyyaml`
- **`evals validate <suite.yaml>`** — loads and validates a YAML suite, prints a success message or structured error
- **`evals run <suite.yaml>`** — async batched requests to any OpenAI-compatible endpoint; streams a live Rich progress bar as cases complete, then renders a colour-coded per-case results table and a summary panel (pass rate, mean latency, cost estimate)
- **`evals show-report <report.json>`** — loads a saved JSON report and re-renders the terminal table
- **`--output` flag** — `--output report.json` serialises results to JSON; `--output report.html` produces a fully self-contained HTML file with a sortable table (click column headers to sort)
- **Metrics engine** in `metrics.py`: four scorers wired into the runner:
  - `exact_match` — strips whitespace, case-sensitive string equality
  - `contains` — substring check
  - `regex` — `re.search` with `re.DOTALL`; invalid patterns fail gracefully
  - `llm_judge` — calls a configurable judge model, parses PASS/FAIL + rationale; errors return `(False, "judge error: …")`
- `RunResult` dataclass includes `passed`, `rationale`, `prompt_tokens`, `completion_tokens` fields
- Optional `judge_model` field in `Suite` YAML; defaults to `suite.model` when omitted
- Pydantic v2 models (`Suite`, `Case`, `MetricEnum`) in `schema.py`; auto-assigns `id` to cases that omit it
- YAML loader in `loader.py` using `yaml.safe_load`
- Async runner in `runner.py`: `run_suite()` with optional `on_result` callback; resolves API key from `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` env vars; supports `--base-url` flag and `LLM_BASE_URL` env var for local models (Ollama, etc.)
- Example suites in `examples/basic_suite.yaml` and `examples/llm_judge_suite.yaml`
- Unit tests in `tests/test_schema.py`, `tests/test_runner.py`, `tests/test_metrics.py`, and `tests/test_reporter.py`
- **CI-ready** — exits non-zero when any case fails

## Quickstart

```bash
pip install llm-evals-cli

# Check your suite is valid before spending tokens
evals validate suite.yaml

# Run against OpenAI (set OPENAI_API_KEY first)
evals run suite.yaml

# Run against a local Ollama instance
evals run suite.yaml --base-url http://localhost:11434/v1

# Save a JSON report
evals run suite.yaml --output report.json

# Save a self-contained HTML report with a sortable table
evals run suite.yaml --output report.html

# Re-render a saved JSON report in the terminal
evals show-report report.json

# Tune concurrency and timeout
evals run suite.yaml --concurrency 10 --timeout 60
```

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
│       ├── cli.py               # Typer app: validate, run, show-report commands
│       ├── schema.py            # Pydantic v2 models: Suite, Case, MetricEnum
│       ├── loader.py            # load_suite(path) → Suite
│       ├── metrics.py           # four scorers: exact_match, contains, regex, llm_judge
│       ├── reporter.py          # render_results(), export_json(), export_html()
│       └── runner.py            # async run_suite(); RunResult dataclass
├── examples/
│   ├── basic_suite.yaml         # exact_match, contains, regex examples
│   └── llm_judge_suite.yaml     # llm_judge with system prompt and tags
├── tests/
│   ├── test_schema.py           # unit tests for schema parsing and validation
│   ├── test_runner.py           # async runner tests using httpx.MockTransport
│   ├── test_metrics.py          # unit tests for all four scorers
│   └── test_reporter.py         # unit tests for reporter (render, export JSON/HTML)
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
| M4 | Metrics engine (`exact_match`, `contains`, `regex`, `llm_judge`) | done |
| M5 | Rich terminal reporter, JSON / HTML export, CI workflow | done |

<!-- TODO: update Status column as milestones ship -->

## License

[MIT](LICENSE)
