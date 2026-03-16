import os
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from rich import print as rprint
import time

from .config import ProjectConfig
from . import templates


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def generate_project(config: ProjectConfig, console: Console):
    base = Path(config.name)

    if base.exists():
        console.print(f"[red]✗ Directory '{config.name}' already exists.[/red]")
        raise SystemExit(1)

    files: dict[str, str] = {}

    # --- Core app files ---
    files["src/main.py"]                   = templates.main_py(config)
    files["src/core/__init__.py"]          = ""
    files["src/core/config.py"]            = templates.core_config(config)
    files["src/api/__init__.py"]           = ""
    files["src/api/v1/__init__.py"]        = ""
    files["src/api/v1/router.py"]          = templates.api_router(config)
    files["src/api/v1/endpoints/__init__.py"] = ""
    files["src/api/v1/endpoints/health.py"] = templates.health_endpoint()

    # --- DB / models ---
    if config.db:
        files["src/db/__init__.py"]        = ""
        files["src/db/session.py"]         = templates.db_session(config)
        files["src/db/base.py"]            = templates.db_base()
        files["src/models/__init__.py"]    = ""
        files["src/models/base.py"]        = templates.model_base()
        files["src/schemas/__init__.py"]   = ""

    # --- Auth ---
    if config.auth:
        files["src/core/security.py"]      = templates.security(config)
        files["src/api/v1/endpoints/auth.py"] = templates.auth_endpoint(config)
        if config.db:
            files["src/models/user.py"]    = templates.user_model()
            files["src/schemas/user.py"]   = templates.user_schema()

    # --- Alembic ---
    if config.alembic:
        files["alembic.ini"]               = templates.alembic_ini(config)
        files["alembic/env.py"]            = templates.alembic_env(config)
        files["alembic/versions/.gitkeep"] = ""

    # --- Tests ---
    if config.tests:
        files["tests/__init__.py"]         = ""
        files["tests/conftest.py"]         = templates.conftest(config)
        files["tests/test_health.py"]      = templates.test_health()

    # --- Docker ---
    if config.docker:
        files["Dockerfile"]                = templates.dockerfile(config)
        files["docker-compose.yml"]        = templates.docker_compose(config)
        files[".dockerignore"]             = templates.dockerignore()

    # --- Project root ---
    files["pyproject.toml"]                = templates.pyproject_toml(config)
    files[".env.example"]                  = templates.env_example(config)
    files[".gitignore"]                    = templates.gitignore()
    files["README.md"]                     = templates.readme(config)
    files["src/__init__.py"]               = ""

    # --- Write files with progress ---
    with Progress(
        SpinnerColumn(spinner_name="dots", style="cyan"),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Creating project...", total=len(files))
        for rel_path, content in files.items():
            write(base / rel_path, content)
            progress.advance(task)
            time.sleep(0.015)

    # --- Print file tree ---
    console.print(_build_tree(config))
    console.print()

    # --- Next steps ---
    console.print("[bold green]✓ Project created successfully![/bold green]")
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print(f"  [cyan]cd {config.name}[/cyan]")
    console.print(f"  [cyan]python -m venv .venv && source .venv/bin/activate[/cyan]")
    console.print(f"  [cyan]pip install -e .[/cyan]")
    if config.alembic:
        console.print(f"  [cyan]alembic upgrade head[/cyan]")
    if config.docker:
        console.print(f"  [cyan]docker-compose up --build[/cyan]")
    else:
        console.print(f"  [cyan]uvicorn src.main:app --reload[/cyan]")
    console.print()
    console.print(f"  Docs → [link]http://localhost:8000/docs[/link]")
    console.print()


def _build_tree(config: ProjectConfig) -> Tree:
    tree = Tree(f"[bold cyan]{config.name}/[/bold cyan]")

    src = tree.add("[bold yellow]src/[/bold yellow]")
    src.add("[dim]__init__.py[/dim]")
    src.add("[green]main.py[/green]  [dim]← app entrypoint[/dim]")

    core = src.add("[bold yellow]core/[/bold yellow]")
    core.add("config.py  [dim]← settings[/dim]")
    if config.auth:
        core.add("security.py  [dim]← JWT utils[/dim]")

    api = src.add("[bold yellow]api/v1/[/bold yellow]")
    api.add("router.py")
    ep = api.add("[bold yellow]endpoints/[/bold yellow]")
    ep.add("health.py")
    if config.auth:
        ep.add("auth.py  [dim]← login/register[/dim]")

    if config.db:
        db = src.add("[bold yellow]db/[/bold yellow]")
        db.add("session.py  [dim]← DB engine[/dim]")
        db.add("base.py")
        src.add("[bold yellow]models/[/bold yellow]").add(
            "user.py  [dim]← User model[/dim]" if config.auth else "[dim](add models here)[/dim]"
        )
        src.add("[bold yellow]schemas/[/bold yellow]").add(
            "user.py  [dim]← Pydantic schemas[/dim]" if config.auth else "[dim](add schemas here)[/dim]"
        )

    if config.alembic:
        alembic = tree.add("[bold yellow]alembic/[/bold yellow]")
        alembic.add("env.py")
        alembic.add("[bold yellow]versions/[/bold yellow]")
        tree.add("alembic.ini")

    if config.tests:
        tests = tree.add("[bold yellow]tests/[/bold yellow]")
        tests.add("conftest.py")
        tests.add("test_health.py")

    if config.docker:
        tree.add("Dockerfile")
        tree.add("docker-compose.yml")
        tree.add(".dockerignore")

    tree.add("pyproject.toml  [dim]← deps & metadata[/dim]")
    tree.add(".env.example")
    tree.add(".gitignore")
    tree.add("README.md")
    return tree