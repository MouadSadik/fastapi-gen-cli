"""
All file content templates for generated projects.
"""
from .config import ProjectConfig


# -- Core ---------------------------------------------------------------------

def main_py(c: ProjectConfig) -> str:
    router_import = "from src.api.v1.router import router as api_router"
    db_lifespan = ""
    if c.db:
        db_lifespan = """
from contextlib import asynccontextmanager
from src.db.session import engine
from src.db.base import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
"""
    lifespan_arg = "lifespan=lifespan" if c.db else ""

    return f'''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
{router_import}
{db_lifespan}
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    {lifespan_arg}
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["root"])
async def root():
    return {{"message": f"Welcome to {{settings.PROJECT_NAME}}"}}
'''


def core_config(c: ProjectConfig) -> str:
    db_field = '\n    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/appdb"' if c.db else ""
    return f'''from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "{c.name}"
    VERSION: str = "0.1.0"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]{db_field}

    class Config:
        env_file = ".env"


settings = Settings()
'''


def api_router(c: ProjectConfig) -> str:
    return '''from fastapi import APIRouter
from src.api.v1.endpoints.health import router as health_router

router = APIRouter()
router.include_router(health_router, prefix="/health", tags=["health"])
'''


def health_endpoint() -> str:
    return '''from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def health_check():
    return {"status": "ok"}
'''


# -- Database -----------------------------------------------------------------

def db_session(c: ProjectConfig) -> str:
    return '''from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
'''


def db_base() -> str:
    return '''from src.models.base import Base

__all__ = ["Base"]
'''


def model_base() -> str:
    return '''from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
'''


# -- Alembic ------------------------------------------------------------------

def alembic_ini(c: ProjectConfig) -> str:
    return '''[alembic]
script_location = alembic
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/appdb

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
'''


def alembic_env(c: ProjectConfig) -> str:
    return '''from alembic import context
from sqlalchemy import engine_from_config, pool
from src.db.base import Base
from src.core.config import settings

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("+asyncpg", ""))
target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''


# -- Tests --------------------------------------------------------------------

def conftest(c: ProjectConfig) -> str:
    return '''import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
'''


def test_health() -> str:
    return '''import pytest


@pytest.mark.anyio
async def test_health(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
'''


# -- Docker -------------------------------------------------------------------

def dockerfile(c: ProjectConfig) -> str:
    return '''FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''


def docker_compose(c: ProjectConfig) -> str:
    return '''services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - .:/app
    depends_on:
      - postgres

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: appdb
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
'''


def dockerignore() -> str:
    return '''.venv
__pycache__
*.pyc
*.pyo
.git
.env
*.egg-info
dist
build
.pytest_cache
'''


# -- Project root -------------------------------------------------------------

def pyproject_toml(c: ProjectConfig) -> str:
    extras = [
        "fastapi[standard]",
        "pydantic-settings",
        "uvicorn[standard]",
    ]
    if c.db:
        extras += ["sqlalchemy[asyncio]", "asyncpg"]
    if c.alembic:
        extras.append("alembic")
    if c.tests:
        extras += ["pytest", "pytest-anyio", "httpx"]

    deps = "\n".join(f'  "{dep}",' for dep in extras)

    return f'''[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{c.name}"
version = "0.1.0"
description = "A FastAPI application"
requires-python = ">=3.11"
dependencies = [
{deps}
]

[tool.setuptools.packages.find]
where = ["."]
include = ["src*"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
'''


def env_file(c: ProjectConfig) -> str:
    lines = ['PROJECT_NAME="My FastAPI App"']
    if c.db:
        lines.append('DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/appdb"')
    return "\n".join(lines) + "\n"


def gitignore() -> str:
    return '''.venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.env
*.db
*.sqlite3
dist/
build/
*.egg-info/
.pytest_cache/
.mypy_cache/
.ruff_cache/
'''


def readme(c: ProjectConfig) -> str:
    features = ["- FastAPI with async support"]
    if c.db:
        features.append("- SQLAlchemy async ORM with PostgreSQL")
    if c.alembic:
        features.append("- Alembic migrations")
    if c.docker:
        features.append("- Docker + docker-compose with PostgreSQL")
    if c.tests:
        features.append("- Pytest async test suite")

    feature_block = "\n".join(features)
    run_cmd = "docker-compose up --build" if c.docker else "uvicorn src.main:app --reload"

    return f'''# {c.name}

## Features

{feature_block}

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
{"alembic upgrade head" + chr(10) if c.alembic else ""}{run_cmd}
```

Open http://localhost:8000/docs for the interactive API docs.

## Project structure

```
src/
  main.py            # App entrypoint
  core/
    config.py        # Settings (pydantic-settings)
  api/v1/
    router.py
    endpoints/
      health.py
{"  db/" + chr(10) + "    session.py" + chr(10) + "  models/" + chr(10) + "  schemas/" if c.db else ""}
```
'''