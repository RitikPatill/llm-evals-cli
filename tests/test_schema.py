from pathlib import Path

import pytest
from pydantic import ValidationError

from llm_evals_cli.loader import load_suite
from llm_evals_cli.schema import MetricEnum, Suite

EXAMPLES = Path(__file__).parent.parent / "examples"


def test_load_basic_suite() -> None:
    suite = load_suite(str(EXAMPLES / "basic_suite.yaml"))
    assert suite.name == "Basic smoke tests"
    assert len(suite.cases) == 3
    assert suite.cases[0].metric == MetricEnum.exact_match


def test_load_llm_judge_suite() -> None:
    suite = load_suite(str(EXAMPLES / "llm_judge_suite.yaml"))
    assert suite.cases[0].id == "factual-capital"
    assert suite.cases[0].tags == ["geography", "factual"]


def test_auto_assign_ids() -> None:
    suite = Suite.model_validate(
        {
            "name": "test",
            "cases": [
                {"prompt": "hi", "expected": "hello", "metric": "exact_match"},
                {"prompt": "bye", "expected": "goodbye", "metric": "contains"},
            ],
        }
    )
    assert suite.cases[0].id == "1"
    assert suite.cases[1].id == "2"


def test_missing_required_field() -> None:
    with pytest.raises(ValidationError):
        Suite.model_validate(
            {
                "name": "test",
                "cases": [{"expected": "hello", "metric": "exact_match"}],
            }
        )


def test_invalid_metric() -> None:
    with pytest.raises(ValidationError):
        Suite.model_validate(
            {
                "name": "test",
                "cases": [{"prompt": "hi", "expected": "hello", "metric": "fuzzy_match"}],
            }
        )


def test_empty_cases_list() -> None:
    with pytest.raises(ValidationError):
        Suite.model_validate({"name": "test", "cases": []})


def test_temperature_out_of_range() -> None:
    with pytest.raises(ValidationError):
        Suite.model_validate(
            {
                "name": "test",
                "temperature": 3.0,
                "cases": [{"prompt": "hi", "expected": "hello", "metric": "exact_match"}],
            }
        )


def test_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        load_suite("nonexistent.yaml")
