import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint
import re

from .generator import generate_project
from .config import ProjectConfig

app = typer.Typer(add_completion=False)
console = Console()


def validate_name(name: str) -> str:
    if not re.match(r'^[a-z][a-z0-9_-]*$', name):
        raise typer.BadParameter(
            "Project name must be lowercase, start with a letter, and contain only letters, numbers, hyphens, or underscores."
        )
    return name


@app.command()
def create(
    project_name: str = typer.Argument(None, help="Name of the project to create"),
    db: bool = typer.Option(False, "--db", help="Add SQLAlchemy + database support"),
    docker: bool = typer.Option(False, "--docker", help="Add Dockerfile & docker-compose"),
    alembic: bool = typer.Option(False, "--alembic", help="Add Alembic migrations"),
    tests: bool = typer.Option(False, "--tests", help="Add pytest test suite"),
    no_interactive: bool = typer.Option(False, "--no-interactive", "-y", help="Skip prompts, use defaults/flags"),
):
    """
    ⚡ Create a new FastAPI project.
    """
    console.print()
    console.print(Panel.fit(
        Text.from_markup(
            "[bold cyan]⚡ FastAPI Project Generator[/bold cyan]\n"
            "[dim]Scaffold a production-ready FastAPI app in seconds[/dim]"
        ),
        border_style="cyan",
        padding=(0, 2),
    ))
    console.print()

    # --- Project name ---
    if project_name is None:
        project_name = Prompt.ask("[bold]? Project name[/bold]", default="my-fastapi-app")
    try:
        validate_name(project_name.replace("-", "_").replace(" ", "_"))
    except typer.BadParameter as e:
        console.print(f"[red]✗ {e}[/red]")
        raise typer.Exit(1)

    # --- Interactive prompts (unless -y) ---
    if not no_interactive:
        console.print()
        console.print("[dim]Select features to include:[/dim]")
        if not db:
            db = Confirm.ask("  [bold]? Include SQLAlchemy[/bold] (database models)", default=False)
        if db and not alembic:
            alembic = Confirm.ask("  [bold]? Include Alembic[/bold] (database migrations)", default=False)
        if not docker:
            docker = Confirm.ask("  [bold]? Include Docker[/bold] (Dockerfile + docker-compose)", default=False)
        if not tests:
            tests = Confirm.ask("  [bold]? Include Pytest[/bold] (test suite)", default=False)

    config = ProjectConfig(
        name=project_name,
        db=db,
        docker=docker,
        alembic=alembic,
        tests=tests,
    )

    console.print()
    generate_project(config, console)


if __name__ == "__main__":
    app()