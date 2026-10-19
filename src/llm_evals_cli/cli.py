import asyncio
import json

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TimeElapsedColumn

from llm_evals_cli.loader import load_suite
from llm_evals_cli.reporter import export_html, export_json, render_results
from llm_evals_cli.runner import RunResult, run_suite
from llm_evals_cli.schema import MetricEnum

app = typer.Typer(name="evals", help="Run repeatable LLM eval suites from the CLI.")


@app.command()
def run(
    suite: str = typer.Argument(..., help="Path to the eval suite YAML file."),
    output: str | None = typer.Option(None, "--output", "-o", help="Write report to this file (.json or .html)."),
    model: str = typer.Option("gpt-4o-mini", "--model", "-m", help="LLM model to use for evaluation."),
    base_url: str | None = typer.Option(None, "--base-url", help="Override the LLM base URL."),
    concurrency: int = typer.Option(5, "--concurrency", help="Max concurrent requests."),
    timeout: float = typer.Option(30.0, "--timeout", help="Per-request timeout in seconds."),
) -> None:
    """Run an eval suite against an LLM endpoint."""
    try:
        loaded = load_suite(suite)
    except FileNotFoundError:
        typer.echo(f"Error: file not found: {suite}", err=True)
        raise typer.Exit(1)
    except ValidationError as e:
        typer.echo(f"Schema error:\n{e}", err=True)
        raise typer.Exit(1)

    console = Console()

    with Progress(
        SpinnerColumn(),
        "[progress.description]{task.description}",
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Running evals…", total=len(loaded.cases))

        def on_result(r: RunResult) -> None:
            progress.advance(task)

        results = asyncio.run(
            run_suite(loaded, base_url=base_url, concurrency=concurrency, timeout_s=timeout, on_result=on_result)
        )

    render_results(results, suite_name=loaded.name, console=console)

    if output:
        if output.endswith(".html"):
            export_html(results, loaded.name, output)
        else:
            export_json(results, output)
        console.print(f"[dim]Report saved → {output}[/dim]")

    failures = sum(1 for r in results if not r.passed)
    if failures:
        raise typer.Exit(1)


@app.command()
def validate(
    suite: str = typer.Argument(..., help="Path to the eval suite YAML file."),
) -> None:
    """Validate an eval suite YAML file without running it."""
    try:
        loaded = load_suite(suite)
        typer.echo(f"✓ {loaded.name}: {len(loaded.cases)} case(s) valid.")
    except FileNotFoundError:
        typer.echo(f"Error: file not found: {suite}", err=True)
        raise typer.Exit(1)
    except ValidationError as e:
        typer.echo(f"Schema error:\n{e}", err=True)
        raise typer.Exit(1)


@app.command("show-report")
def show_report(
    report: str = typer.Argument(..., help="Path to a JSON report file."),
) -> None:
    """Re-render a saved JSON report in the terminal."""
    try:
        with open(report, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        typer.echo(f"Error: file not found: {report}", err=True)
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        typer.echo(f"Error: invalid JSON: {e}", err=True)
        raise typer.Exit(1)

    raw_results = data.get("results", data) if isinstance(data, dict) else data
    results: list[RunResult] = []
    for item in raw_results:
        item.setdefault("prompt_tokens", None)
        item.setdefault("completion_tokens", None)
        item["metric"] = MetricEnum(item["metric"])
        results.append(RunResult(**item))

    console = Console()
    render_results(results, suite_name="", console=console)
