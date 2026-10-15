# llm-evals-cli

> Lightweight, zero-fuss LLM evaluation suites for the command line.

![PyPI](https://img.shields.io/badge/pypi-not%20yet%20published-lightgrey?label=PyPI)
![License: MIT](https://img.shields.io/badge/license-MIT-blue)
![CI](https://img.shields.io/badge/CI-not%20configured-lightgrey?label=CI)

## Why this tool

Prompt changes break things silently. Existing eval platforms are either cloud-only, require heavy setup, or lock you into a single framework — making it painful to get a quick regression check before shipping.

`llm-evals-cli` gives you a fast, local, CI-friendly feedback loop: define test cases in YAML, run one command, get a colour-coded pass/fail table in under a minute.

## What works now (M1 — scaffold)

- Python package layout under `src/llm_evals_cli/` with `pyproject.toml` (hatchling build, Python ≥ 3.11)
- Pinned runtime dependencies: `typer`, `rich`, `httpx`, `pydantic`
- Three CLI entry points scaffolded — `evals run`, `evals validate`, `evals show-report` — each parses arguments but returns `not implemented yet`
- `evals` console script registered; `pip install -e .` produces a working (stub) binary
- Dev toolchain configured: `pytest`, `ruff` (line-length 100), `mypy` (strict)
- MIT licence and `.gitignore`

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

> **Note:** commands are stubs as of M1 and print `not implemented yet`. Full implementation begins in M2.

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
│       └── cli.py               # Typer app; run / validate / show-report stubs
├── pyproject.toml               # build config, pinned deps, entry point
├── requirements.txt             # pinned runtime deps
├── requirements-dev.txt         # pinned dev deps (pytest, ruff, mypy)
└── LICENSE
```

<!-- TODO: expand once core modules (loader, runner, metrics, reporter) are added in M2+ -->

## Roadmap

| Milestone | Scope | Status |
|-----------|-------|--------|
| M1 | Repo scaffold, package layout, stub CLI, dev toolchain | done |
| M2 | YAML loader, Pydantic suite models, `validate` command | planned |
| M3 | Async LLM runner, `exact_match` / `contains` metrics | planned |
| M4 | `regex` metric, Rich reporter, `run` command end-to-end | planned |
| M5 | `llm_judge` metric, JSON / HTML export, CI workflow | planned |

<!-- TODO: update Status column as milestones ship -->

## License

[MIT](LICENSE)
