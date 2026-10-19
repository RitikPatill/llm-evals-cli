import io
import json

import pytest
from rich.console import Console

from llm_evals_cli.reporter import export_html, export_json, render_results
from llm_evals_cli.runner import RunResult


def _make_result(
    case_id: str = "1",
    prompt: str = "What is 2+2?",
    expected: str = "4",
    metric: str = "exact_match",
    response: str | None = "4",
    latency_s: float = 0.5,
    passed: bool | None = True,
    rationale: str | None = None,
    error: str | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
) -> RunResult:
    return RunResult(
        case_id=case_id,
        prompt=prompt,
        expected=expected,
        metric=metric,
        response=response,
        latency_s=latency_s,
        passed=passed,
        rationale=rationale,
        error=error,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )


def test_render_results_no_crash():
    results = [
        _make_result(case_id="1", passed=True),
        _make_result(case_id="2", passed=False, response="5"),
        _make_result(case_id="3", error="timeout", passed=False, response=None),
    ]
    buf = io.StringIO()
    console = Console(file=buf, highlight=False)
    render_results(results, suite_name="test-suite", console=console)
    output = buf.getvalue()

    assert "PASS" in output
    assert "FAIL" in output
    assert "Pass rate:" in output


def test_export_json_roundtrip(tmp_path):
    results = [
        _make_result(case_id="1", passed=True, prompt_tokens=10, completion_tokens=5),
        _make_result(case_id="2", passed=False),
    ]
    path = str(tmp_path / "report.json")
    export_json(results, path)

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    assert "generated_at" in data
    assert len(data["results"]) == 2
    assert data["results"][0]["case_id"] == "1"
    assert data["results"][0]["prompt_tokens"] == 10
    assert data["results"][1]["passed"] is False


def test_export_html_self_contained(tmp_path):
    results = [
        _make_result(case_id="1", passed=True),
        _make_result(case_id="2", passed=False),
    ]
    path = str(tmp_path / "report.html")
    export_html(results, suite_name="my-suite", path=path)

    content = open(path, encoding="utf-8").read()
    assert "<!DOCTYPE html>" in content
    assert "my-suite" in content
    assert "const DATA" in content
    assert "<script src=" not in content


def test_cost_estimate_shown_when_tokens_present():
    results = [
        _make_result(case_id="1", passed=True, prompt_tokens=100, completion_tokens=50),
    ]
    buf = io.StringIO()
    console = Console(file=buf, highlight=False)
    render_results(results, console=console)
    output = buf.getvalue()
    assert "$" in output


def test_cost_na_when_no_tokens():
    results = [
        _make_result(case_id="1", passed=True, prompt_tokens=None, completion_tokens=None),
    ]
    buf = io.StringIO()
    console = Console(file=buf, highlight=False)
    render_results(results, console=console)
    output = buf.getvalue()
    assert "N/A" in output
