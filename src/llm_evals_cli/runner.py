import asyncio
import os
import time
from dataclasses import dataclass

import httpx

from llm_evals_cli.schema import Suite, Case
from llm_evals_cli.metrics import score


@dataclass
class RunResult:
    case_id: str
    prompt: str
    expected: str
    metric: str
    response: str | None      # raw LLM output text, None on error
    latency_s: float           # wall-clock seconds for the request
    passed: bool | None
    rationale: str | None      # judge rationale or None
    error: str | None          # exception message if request failed


async def run_suite(
    suite: Suite,
    base_url: str | None = None,
    concurrency: int = 5,
    timeout_s: float = 30.0,
) -> list[RunResult]:
    resolved_url = (
        base_url
        or suite.base_url
        or os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
    )
    resolved_url = resolved_url.rstrip("/")

    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")

    headers: dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    sem = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient(
        headers=headers,
        timeout=httpx.Timeout(timeout_s),
    ) as client:
        results = await asyncio.gather(
            *[_run_case(client, sem, resolved_url, suite, case) for case in suite.cases]
        )

    return list(results)


async def _run_case(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    base_url: str,
    suite: Suite,
    case: Case,
) -> RunResult:
    async with sem:
        start = time.perf_counter()
        try:
            messages = []
            if case.system is not None:
                messages.append({"role": "system", "content": case.system})
            messages.append({"role": "user", "content": case.prompt})

            body = {
                "model": suite.model,
                "temperature": suite.temperature,
                "max_tokens": suite.max_tokens,
                "messages": messages,
            }

            resp = await client.post(f"{base_url}/chat/completions", json=body)
            resp.raise_for_status()

            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            latency = time.perf_counter() - start

            judge_model = suite.judge_model or suite.model
            passed, rationale = await score(
                case.metric,
                content,
                case.expected,
                client=client,
                base_url=base_url,
                model=judge_model,
            )

            return RunResult(
                case_id=case.id or "",
                prompt=case.prompt,
                expected=case.expected,
                metric=case.metric,
                response=content,
                latency_s=latency,
                passed=passed,
                rationale=rationale,
                error=None,
            )

        except httpx.TimeoutException as exc:
            latency = time.perf_counter() - start
            return RunResult(
                case_id=case.id or "",
                prompt=case.prompt,
                expected=case.expected,
                metric=case.metric,
                response=None,
                latency_s=latency,
                passed=False,
                rationale=None,
                error=f"timeout: {exc}",
            )
        except httpx.HTTPStatusError as exc:
            latency = time.perf_counter() - start
            return RunResult(
                case_id=case.id or "",
                prompt=case.prompt,
                expected=case.expected,
                metric=case.metric,
                response=None,
                latency_s=latency,
                passed=False,
                rationale=None,
                error=f"HTTP {exc.response.status_code}: {exc}",
            )
        except httpx.RequestError as exc:
            latency = time.perf_counter() - start
            return RunResult(
                case_id=case.id or "",
                prompt=case.prompt,
                expected=case.expected,
                metric=case.metric,
                response=None,
                latency_s=latency,
                passed=False,
                rationale=None,
                error=f"request error: {exc}",
            )
        except Exception as exc:
            latency = time.perf_counter() - start
            return RunResult(
                case_id=case.id or "",
                prompt=case.prompt,
                expected=case.expected,
                metric=case.metric,
                response=None,
                latency_s=latency,
                passed=False,
                rationale=None,
                error=f"unexpected error: {exc}",
            )
