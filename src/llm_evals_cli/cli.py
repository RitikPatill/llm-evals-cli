import typer

app = typer.Typer(name="evals", help="Run repeatable LLM eval suites from the CLI.")


@app.command()
def run(
    suite: str = typer.Argument(..., help="Path to the eval suite YAML file."),
    output: str | None = typer.Option(None, "--output", "-o", help="Write report to this file (.json or .html)."),
    model: str = typer.Option("gpt-4o-mini", "--model", "-m", help="LLM model to use for evaluation."),
) -> None:
    """Run an eval suite against an LLM endpoint."""
    print("not implemented yet")


@app.command()
def validate(
    suite: str = typer.Argument(..., help="Path to the eval suite YAML file."),
) -> None:
    """Validate an eval suite YAML file without running it."""
    print("not implemented yet")


@app.command("show-report")
def show_report(
    report: str = typer.Argument(..., help="Path to a report JSON file."),
) -> None:
    """Display a previously generated eval report in the terminal."""
    print("not implemented yet")
