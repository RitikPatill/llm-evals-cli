import dataclasses
import json
from datetime import datetime, timezone

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from llm_evals_cli.runner import RunResult


def render_results(
    results: list[RunResult],
    suite_name: str = "",
    console: Console | None = None,
) -> None:
    if console is None:
        console = Console()

    has_judge = any(r.metric == "llm_judge" for r in results)

    table = Table(title=f"Results: {suite_name}" if suite_name else "Results", show_lines=False)
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Prompt", max_width=40)
    table.add_column("Metric", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Latency", no_wrap=True)
    if has_judge:
        table.add_column("Rationale", max_width=50)

    for r in results:
        prompt_display = r.prompt[:40] + "…" if len(r.prompt) > 40 else r.prompt
        if r.error:
            status = "[yellow]ERROR[/yellow]"
        elif r.passed:
            status = "[green]PASS[/green]"
        else:
            status = "[red]FAIL[/red]"
        latency = f"{r.latency_s:.2f}s"

        if has_judge:
            rationale = r.rationale or ""
            rationale_display = rationale[:50] + "…" if len(rationale) > 50 else rationale
            table.add_row(r.case_id, prompt_display, r.metric, status, latency, rationale_display)
        else:
            table.add_row(r.case_id, prompt_display, r.metric, status, latency)

    console.print(table)

    # Summary stats
    total = len(results)
    passed = sum(1 for r in results if r.passed and not r.error)
    non_error = [r for r in results if not r.error]
    mean_lat = (
        sum(r.latency_s for r in non_error) / len(non_error) if non_error else 0.0
    )
    pass_pct = (passed / total * 100) if total else 0.0

    total_tokens = sum(
        (r.prompt_tokens or 0) + (r.completion_tokens or 0) for r in results
    )
    if total_tokens > 0:
        cost = total_tokens / 1_000_000 * 0.15
        cost_str = f"~${cost:.4f} (est. @ $0.15/1M tok, gpt-4o-mini default)"
    else:
        cost_str = "N/A (no token data)"

    summary = (
        f"[bold]Pass rate:[/bold] {passed}/{total} ({pass_pct:.1f}%)\n"
        f"[bold]Mean latency:[/bold] {mean_lat:.2f}s\n"
        f"[bold]Cost estimate:[/bold] {cost_str}"
    )
    console.print(Panel(summary, title="Summary", expand=False))


def export_json(results: list[RunResult], path: str) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": [dataclasses.asdict(r) for r in results],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Eval Report: {suite_name}</title>
<style>
body {{ font-family: system-ui, sans-serif; padding: 1rem 2rem; background: #f9f9f9; }}
h1 {{ color: #333; }}
table {{ border-collapse: collapse; width: 100%; background: #fff; }}
th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
th {{ background: #333; color: #fff; cursor: pointer; user-select: none; }}
th:hover {{ background: #555; }}
tr:nth-child(even) {{ background: #f2f2f2; }}
.pass {{ color: green; font-weight: bold; }}
.fail {{ color: red; font-weight: bold; }}
.error {{ color: orange; font-weight: bold; }}
</style>
</head>
<body>
<h1>Eval Report: {suite_name}</h1>
<p>Generated: {generated_at}</p>
<table id="results">
<thead><tr>
<th onclick="sortTable(0)">ID</th>
<th onclick="sortTable(1)">Prompt</th>
<th onclick="sortTable(2)">Metric</th>
<th onclick="sortTable(3)">Status</th>
<th onclick="sortTable(4)">Latency (s)</th>
<th onclick="sortTable(5)">Rationale</th>
</tr></thead>
<tbody id="tbody"></tbody>
</table>
<script>
const DATA = {data_json};
const tbody = document.getElementById("tbody");
function render(rows) {{
  tbody.innerHTML = rows.map(r => {{
    const st = r.error ? '<span class="error">ERROR</span>'
      : r.passed ? '<span class="pass">PASS</span>'
      : '<span class="fail">FAIL</span>';
    const prompt = (r.prompt || "").substring(0, 60);
    const rat = (r.rationale || "").substring(0, 80);
    return `<tr><td>${{r.case_id}}</td><td>${{prompt}}</td><td>${{r.metric}}</td><td>${{st}}</td><td>${{r.latency_s.toFixed(2)}}</td><td>${{rat}}</td></tr>`;
  }}).join("");
}}
render(DATA);
let sortCol = -1, asc = true;
function sortTable(col) {{
  asc = sortCol === col ? !asc : true;
  sortCol = col;
  const keys = ["case_id","prompt","metric","passed","latency_s","rationale"];
  const sorted = [...DATA].sort((a, b) => {{
    const va = String(a[keys[col]] ?? ""), vb = String(b[keys[col]] ?? "");
    return asc ? va.localeCompare(vb) : vb.localeCompare(va);
  }});
  render(sorted);
}}
</script>
</body>
</html>
"""


def export_html(results: list[RunResult], suite_name: str, path: str) -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    data_json = json.dumps([dataclasses.asdict(r) for r in results], indent=2)
    html = _HTML_TEMPLATE.format(
        suite_name=suite_name,
        generated_at=generated_at,
        data_json=data_json,
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
