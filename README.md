# LLM Evals CLI

> Run structured LLM evaluation suites from the terminal — YAML test cases, multi-metric scoring, rich reports.

![demo](docs/demo.gif)

## What it is

`llm-evals-cli` is a command-line tool for defining and running repeatable evaluation suites against any OpenAI-compatible LLM endpoint — OpenAI, Anthropic, a local Ollama instance, or anything else that speaks `/v1/chat/completions`. You describe test cases in plain YAML, run one command, and get a colour-coded pass/fail table in the terminal plus an optional JSON or HTML report.

The tool fills a specific gap: teams shipping LLM-powered features need a fast regression check before each prompt change, without standing up a full MLflow or LangSmith stack. `evals` fits inside a CI pipeline in under five minutes and requires no external services.

## Quickstart

```bash
git clone https://github.com/RitikPatill/llm-evals-cli.git
cd llm-evals-cli
pip install -e .

# Validate a suite without spending tokens
evals validate examples/basic_suite.yaml

# Run against OpenAI
export OPENAI_API_KEY=sk-...
evals run examples/basic_suite.yaml

# Run against a local Ollama instance (no key required)
evals run examples/basic_suite.yaml --base-url http://localhost:11434/v1

# Save results to JSON or a self-contained HTML report
evals run examples/basic_suite.yaml --output report.json
evals run examples/basic_suite.yaml --output report.html

# Re-render a saved report in the terminal
evals show-report report.json
```

## Usage

Write a suite file:

```yaml
name: My eval suite
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

Run it with `evals run suite.yaml`. A live progress bar streams as requests complete; a per-case results table and a summary panel (pass rate, mean latency, estimated token cost) are printed when the run finishes. The process exits non-zero if any case fails, making it drop-in for CI.

Four metrics are available: `exact_match` (whitespace-stripped string equality), `contains` (substring check), `regex` (`re.search` with `re.DOTALL`), and `llm_judge` (sends actual vs. expected to a configurable judge model, returns pass/fail with a rationale string).

## Architecture

```
YAML suite file
      │
      ▼
  loader.py       load_suite(path) → Suite (Pydantic v2 model)
      │
      ▼
  runner.py       run_suite() — asyncio + httpx, semaphore-limited concurrency
      │  ┌─────────────────────────────────────────┐
      │  │  POST /v1/chat/completions  (batched)   │
      │  └─────────────────────────────────────────┘
      │
      ▼
  metrics.py      score(actual, expected) → (passed, rationale)
      │            exact_match | contains | regex | llm_judge
      ▼
  reporter.py     render_results()  →  Rich terminal table
                  export_json()     →  report.json
                  export_html()     →  report.html (sortable, self-contained)
```

## Project structure

```
llm-evals-cli/
├── src/llm_evals_cli/   # package source
│   ├── cli.py           # Typer app: validate, run, show-report
│   ├── schema.py        # Pydantic v2 models: Suite, Case, MetricEnum
│   ├── loader.py        # YAML → Suite
│   ├── metrics.py       # four scorers
│   ├── reporter.py      # terminal table + JSON/HTML export
│   └── runner.py        # async runner; RunResult dataclass
├── examples/            # sample YAML suites
├── tests/               # pytest suite (mocked HTTP, no live API calls)
├── docs/                # demo GIF + VHS tape script
├── .github/workflows/   # CI: lint (ruff) + test on push/PR
└── pyproject.toml       # hatchling build, pinned deps, entry point
```

## Roadmap

- [ ] Semantic similarity scorer using sentence-transformers (opt-in, skipped when dep absent)
- [ ] `--filter tags=<tag>` flag to run a subset of cases by tag
- [ ] Diff mode: compare two reports and surface regressions
- [ ] Publish to PyPI and add a version badge
- [ ] Structured logging output (`--log-format json`) for ingestion by external dashboards

## License

MIT — see LICENSE.

---

Built autonomously by [autodev](https://github.com/RitikPatill/autodev),
a multi-agent orchestrator I designed. Each commit in this repo was
authored by me; the implementation work was performed by Sonnet under
the orchestrator's control. Read the orchestrator's README to see how.
