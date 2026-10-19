import asyncio
import json

import httpx
import pytest

from llm_evals_cli.runner import run_suite, RunResult
from llm_evals_cli.schema import Suite


def _make_suite(n: int = 2) -> Suite:
    return Suite(
        name="test",
        model="gpt-4o-mini",
        cases=[
            {"prompt": f"prompt {i}", "expected": f"expected {i}", "metric": "exact_match"}
            for i in range(n)
        ],
    )


def _ok_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": "hello"}}]})


@pytest.mark.asyncio
async def test_run_suite_success():
    suite = _make_suite(2)
    transport = httpx.MockTransport(_ok_handler)

    import llm_evals_cli.runner as runner_mod
    orig = httpx.AsyncClient

    class PatchedClient(httpx.AsyncClient):
        def __init__(self, **kwargs):
            kwargs["transport"] = transport
            super().__init__(**kwargs)

    import unittest.mock as mock
    with mock.patch("llm_evals_cli.runner.httpx.AsyncClient", PatchedClient):
        results = await run_suite(suite)

    assert len(results) == 2
    for r in results:
        assert r.response == "hello"
        assert r.latency_s >= 0
        assert r.error is None
        assert r.passed is not None  # metrics engine populates this


@pytest.mark.asyncio
async def test_run_suite_timeout():
    suite = _make_suite(1)

    def timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    transport = httpx.MockTransport(timeout_handler)

    import unittest.mock as mock

    class PatchedClient(httpx.AsyncClient):
        def __init__(self, **kwargs):
            kwargs["transport"] = transport
            super().__init__(**kwargs)

    with mock.patch("llm_evals_cli.runner.httpx.AsyncClient", PatchedClient):
        results = await run_suite(suite)

    assert len(results) == 1
    r = results[0]
    assert r.response is None
    assert r.error is not None
    assert "timeout" in r.error.lower()


@pytest.mark.asyncio
async def test_run_suite_http_error():
    suite = _make_suite(1)

    def unauthorized_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})

    transport = httpx.MockTransport(unauthorized_handler)

    import unittest.mock as mock

    class PatchedClient(httpx.AsyncClient):
        def __init__(self, **kwargs):
            kwargs["transport"] = transport
            super().__init__(**kwargs)

    with mock.patch("llm_evals_cli.runner.httpx.AsyncClient", PatchedClient):
        results = await run_suite(suite)

    assert len(results) == 1
    r = results[0]
    assert r.error is not None
    assert "401" in r.error


@pytest.mark.asyncio
async def test_concurrency_limit():
    suite = _make_suite(10)
    in_flight = 0
    max_in_flight = 0
    lock = asyncio.Lock()
    gate = asyncio.Event()

    async def slow_handler(request: httpx.Request) -> httpx.Response:
        nonlocal in_flight, max_in_flight
        async with lock:
            in_flight += 1
            if in_flight > max_in_flight:
                max_in_flight = in_flight
        await asyncio.sleep(0.01)
        async with lock:
            in_flight -= 1
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    class AsyncMockTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            return await slow_handler(request)

    import unittest.mock as mock

    class PatchedClient(httpx.AsyncClient):
        def __init__(self, **kwargs):
            kwargs["transport"] = AsyncMockTransport()
            super().__init__(**kwargs)

    with mock.patch("llm_evals_cli.runner.httpx.AsyncClient", PatchedClient):
        results = await run_suite(suite, concurrency=2)

    assert len(results) == 10
    assert max_in_flight <= 2


@pytest.mark.asyncio
async def test_system_message_omitted_when_none():
    suite = Suite(
        name="test",
        model="gpt-4o-mini",
        cases=[{"prompt": "hello", "expected": "world", "metric": "exact_match", "system": None}],
    )
    captured_bodies: list[dict] = []

    def capturing_handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        captured_bodies.append(body)
        return httpx.Response(200, json={"choices": [{"message": {"content": "world"}}]})

    transport = httpx.MockTransport(capturing_handler)

    import unittest.mock as mock

    class PatchedClient(httpx.AsyncClient):
        def __init__(self, **kwargs):
            kwargs["transport"] = transport
            super().__init__(**kwargs)

    with mock.patch("llm_evals_cli.runner.httpx.AsyncClient", PatchedClient):
        await run_suite(suite)

    assert len(captured_bodies) == 1
    messages = captured_bodies[0]["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
