import pytest
import httpx

from llm_evals_cli.metrics import (
    score_exact_match,
    score_contains,
    score_regex,
    score_llm_judge,
    score,
)


# --- exact_match ---

def test_exact_match_pass():
    passed, rationale = score_exact_match("hello", "hello")
    assert passed is True
    assert rationale is None


def test_exact_match_fail():
    passed, _ = score_exact_match("Hello", "hello")
    assert passed is False


def test_exact_match_strips_whitespace():
    passed, _ = score_exact_match(" hello\n", "hello")
    assert passed is True


# --- contains ---

def test_contains_pass():
    passed, _ = score_contains("the capital is Paris", "Paris")
    assert passed is True


def test_contains_fail():
    passed, _ = score_contains("London", "Paris")
    assert passed is False


# --- regex ---

def test_regex_pass():
    passed, _ = score_regex("2024-01-15", r"\d{4}-\d{2}-\d{2}")
    assert passed is True


def test_regex_fail():
    passed, _ = score_regex("not-a-date", r"\d{4}-\d{2}-\d{2}")
    assert passed is False


def test_regex_invalid_pattern():
    passed, _ = score_regex("some text", r"[unclosed")
    assert passed is False


# --- llm_judge ---

def _make_judge_client(response_text: str) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": response_text}}]},
        )
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _make_error_client(status_code: int) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"error": "error"})
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_llm_judge_pass():
    async with _make_judge_client("PASS\nLooks correct") as client:
        passed, rationale = await score_llm_judge(
            "Paris", "Paris", client, "http://fake", "gpt-4o-mini"
        )
    assert passed is True
    assert rationale == "Looks correct"


@pytest.mark.asyncio
async def test_llm_judge_fail():
    async with _make_judge_client("FAIL\nWrong answer") as client:
        passed, rationale = await score_llm_judge(
            "London", "Paris", client, "http://fake", "gpt-4o-mini"
        )
    assert passed is False
    assert rationale == "Wrong answer"


@pytest.mark.asyncio
async def test_llm_judge_unparseable():
    async with _make_judge_client("sure thing") as client:
        passed, rationale = await score_llm_judge(
            "something", "expected", client, "http://fake", "gpt-4o-mini"
        )
    assert passed is False
    assert rationale is not None
    assert "unparseable judge response" in rationale


@pytest.mark.asyncio
async def test_llm_judge_http_error():
    async with _make_error_client(500) as client:
        passed, rationale = await score_llm_judge(
            "response", "expected", client, "http://fake", "gpt-4o-mini"
        )
    assert passed is False
    assert rationale is not None
    assert "judge error" in rationale


# --- score dispatcher ---

@pytest.mark.asyncio
async def test_score_dispatcher():
    passed, _ = await score("exact_match", "hello", "hello")
    assert passed is True

    passed, _ = await score("contains", "the answer is 42", "42")
    assert passed is True

    passed, _ = await score("regex", "abc123", r"\d+")
    assert passed is True
