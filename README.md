# llm-evals-cli

> Lightweight, zero-fuss LLM evaluation suites for the command line.

![PyPI](https://img.shields.io/badge/pypi-not%20yet%20published-lightgrey?label=PyPI)
![License: MIT](https://img.shields.io/badge/license-MIT-blue)
![CI](https://img.shields.io/badge/CI-not%20configured-lightgrey?label=CI)

## Why this tool

Prompt changes break things silently. Existing eval platforms are either cloud-only, require heavy setup, or lock you into a single framework — making it painful to get a quick regression check before shipping.

`llm-evals-cli` gives you a fast, local, CI-friendly feedback loop: define test cases in YAML, run one command, get a colour-coded pass/fail table in under a minute.

## What works now (M2 — YAML schema + validator)

- Python package layout under `src/llm_evals_cli/` with `pyproject.toml` (hatchling build, Python ≥ 3.11)
- Pinned runtime dependencies: `typer`, `rich`, `httpx`, `pydantic`, `pyyaml`
- **`evals validate <suite.yaml>`** — fully implemented: loads and validates a YAML suite, prints a success message or structured error
- Pydantic v2 models (`Suite`, `Case`, `MetricEnum`) in `schema.py`; auto-assigns `id` to cases that omit it
- YAML loader in `loader.py` using `yaml.safe_load`
- Example suites in `examples/basic_suite.yaml` and `examples/llm_judge_suite.yaml`
- Unit tests in `tests/test_schema.py` covering valid parsing, defaults, and all validation error paths
- `evals run` and `evals show-report` are scaffolded stubs (not yet implemented)

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

# Run it
evals run suite.yaml --output report.json
```

> **Note:** `evals run` and `evals show-report` are stubs. `evals validate` is fully working as of M2.

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
│       ├── cli.py               # Typer app; validate (done), run / show-report stubs
│       ├── schema.py            # Pydantic v2 models: Suite, Case, MetricEnum
│       └── loader.py            # load_suite(path) → Suite
├── examples/
│   ├── basic_suite.yaml         # exact_match, contains, regex examples
│   └── llm_judge_suite.yaml     # llm_judge with system prompt and tags
├── tests/
│   └── test_schema.py           # unit tests for schema parsing and validation
├── pyproject.toml               # build config, pinned deps, entry point
├── requirements.txt             # pinned runtime deps
├── requirements-dev.txt         # dev/test dependencies (pytest, etc.)
└── LICENSE
```

## Roadmap

| Milestone | Scope | Status |
|-----------|-------|--------|
| M1 | Repo scaffold, package layout, stub CLI, dev toolchain | done |
| M2 | YAML loader, Pydantic suite models, `validate` command | done |
| M3 | Async LLM runner, `exact_match` / `contains` metrics | planned |
| M4 | `regex` metric, Rich reporter, `run` command end-to-end | planned |
| M5 | `llm_judge` metric, JSON / HTML export, CI workflow | planned |

<!-- TODO: update Status column as milestones ship -->

## License

[MIT](LICENSE)
