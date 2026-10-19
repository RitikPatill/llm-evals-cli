import re

import httpx


_JUDGE_PROMPT = """\
You are an impartial grader.
Actual response: \"\"\"{actual}\"\"\"
Expected answer: \"\"\"{expected}\"\"\"
Does the actual response correctly satisfy the expected answer?
Reply with PASS or FAIL on the first line only, then optionally give a brief reason."""


def score_exact_match(response: str, expected: str) -> tuple[bool, None]:
    return response.strip() == expected.strip(), None


def score_contains(response: str, expected: str) -> tuple[bool, None]:
    return expected in response, None


def score_regex(response: str, expected: str) -> tuple[bool, None]:
    try:
        matched = bool(re.search(expected, response, re.DOTALL))
    except re.error:
        matched = False
    return matched, None


async def score_llm_judge(
    response: str,
    expected: str,
    client: httpx.AsyncClient,
    base_url: str,
    model: str,
) -> tuple[bool, str | None]:
    prompt = _JUDGE_PROMPT.format(actual=response, expected=expected)
    body = {
        "model": model,
        "temperature": 0.0,
        "max_tokens": 256,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        resp = await client.post(f"{base_url}/chat/completions", json=body)
        resp.raise_for_status()
        raw: str = resp.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as exc:
        return False, f"judge error: {exc}"

    lines = raw.strip().splitlines()
    first_line = lines[0].strip().upper() if lines else ""
    rationale = lines[1].strip() if len(lines) > 1 else None

    if first_line.startswith("PASS"):
        return True, rationale
    if first_line.startswith("FAIL"):
        return False, rationale
    return False, f"unparseable judge response: {raw}"


async def score(
    metric: str,
    response: str,
    expected: str,
    *,
    client: httpx.AsyncClient | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> tuple[bool, str | None]:
    if metric == "exact_match":
        return score_exact_match(response, expected)
    if metric == "contains":
        return score_contains(response, expected)
    if metric == "regex":
        return score_regex(response, expected)
    if metric == "llm_judge":
        if client is None or base_url is None or model is None:
            raise ValueError("llm_judge requires client, base_url, and model")
        return await score_llm_judge(response, expected, client, base_url, model)
    raise ValueError(f"unknown metric: {metric}")
