from __future__ import annotations

import typer

app = typer.Typer(
    name="aether",
    help="Aether-Native computer-use agent",
    invoke_without_command=True,
)


@app.command()
def run(
    task: str = typer.Argument(..., help="Natural language task to execute"),
) -> None:
    """Run a desktop automation task."""
    typer.echo(f"Task: {task}")
    typer.echo("(Phase 0: CLI executes in-process via RALPH loop)")
    # TODO: Wire up RalphLoop in Phase 0 completion


@app.callback()
def callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version",
        is_eager=True,
    ),
) -> None:
    """Aether-Native: Local-first computer-use agent."""
    if version:
        typer.echo("0.1.0")
        raise typer.Exit()


if __name__ == "__main__":
    app()
