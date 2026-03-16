"""
All file content templates for generated projects.
"""
from .config import ProjectConfig


# ── Core ──────────────────────────────────────────────────────────────────────

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
    db_field = '\n    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"' if c.db else ""
    jwt_fields = """
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30""" if c.auth else ""
    return f'''from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "{c.name}"
    VERSION: str = "0.1.0"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]{db_field}{jwt_fields}

    class Config:
        env_file = ".env"


settings = Settings()
'''


def api_router(c: ProjectConfig) -> str:
    auth_import = "\nfrom src.api.v1.endpoints.auth import router as auth_router" if c.auth else ""
    auth_include = '\nrouter.include_router(auth_router, prefix="/auth", tags=["auth"])' if c.auth else ""
    return f'''from fastapi import APIRouter
from src.api.v1.endpoints.health import router as health_router{auth_import}

router = APIRouter()
router.include_router(health_router, prefix="/health", tags=["health"]){auth_include}
'''


def health_endpoint() -> str:
    return '''from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def health_check():
    return {"status": "ok"}
'''


# ── Database ──────────────────────────────────────────────────────────────────

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
import uuid
from sqlalchemy import Column, String
from sqlalchemy.dialects.sqlite import TEXT


class Base(DeclarativeBase):
    pass
'''


# ── Auth ──────────────────────────────────────────────────────────────────────

def security(c: ProjectConfig) -> str:
    return '''from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from src.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    return jwt.encode({"sub": subject, "exp": expire}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
'''


def auth_endpoint(c: ProjectConfig) -> str:
    db_dep = "from src.db.session import get_db\nfrom sqlalchemy.ext.asyncio import AsyncSession\n" if c.db else ""
    return f'''from fastapi import APIRouter, HTTPException, status{"," if c.db else ""}{"Depends" if c.db else ""}
from src.core.security import hash_password, verify_password, create_access_token
{db_dep}
router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(email: str, password: str):
    # TODO: persist user to DB
    hashed = hash_password(password)
    return {{"email": email, "message": "User created"}}


@router.post("/login")
async def login(email: str, password: str):
    # TODO: look up user from DB and verify
    # Example: verify_password(password, user.hashed_password)
    token = create_access_token(subject=email)
    return {{"access_token": token, "token_type": "bearer"}}
'''


def user_model() -> str:
    return '''from sqlalchemy import Column, String, Boolean
from src.models.base import Base
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
'''


def user_schema() -> str:
    return '''from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: str
    email: EmailStr
    is_active: bool

    model_config = {"from_attributes": True}
'''


# ── Alembic ───────────────────────────────────────────────────────────────────

def alembic_ini(c: ProjectConfig) -> str:
    return f'''[alembic]
script_location = alembic
sqlalchemy.url = sqlite:///./dev.db

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
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("+aiosqlite", ""))
target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(config.get_section(config.config_ini_section), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''


# ── Tests ─────────────────────────────────────────────────────────────────────

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


# ── Docker ────────────────────────────────────────────────────────────────────

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
    db_service = """
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
""" if c.db else ""

    db_depends = "\n    depends_on:\n      - postgres" if c.db else ""

    return f'''version: "3.9"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - .:/app{db_depends}
{db_service}'''


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


# ── Project root ──────────────────────────────────────────────────────────────

def pyproject_toml(c: ProjectConfig) -> str:
    extras = ['fastapi[standard]', 'pydantic-settings', 'uvicorn[standard]']
    if c.db:
        extras += ['sqlalchemy[asyncio]', 'aiosqlite']
    if c.auth:
        extras += ['python-jose[cryptography]', 'passlib[bcrypt]']
    if c.alembic:
        extras.append('alembic')
    if c.tests:
        extras += ['pytest', 'pytest-anyio', 'httpx']

    deps = "\n".join(f'  "{dep}",' for dep in extras)

    return f'''[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

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


def env_example(c: ProjectConfig) -> str:
    lines = ['PROJECT_NAME="My FastAPI App"']
    if c.db:
        lines.append('DATABASE_URL="sqlite+aiosqlite:///./dev.db"')
    if c.auth:
        lines += [
            'SECRET_KEY="super-secret-change-me"',
            'ACCESS_TOKEN_EXPIRE_MINUTES=30',
        ]
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
    features = []
    if c.db: features.append("- 🗄️ SQLAlchemy async ORM")
    if c.alembic: features.append("- 🔄 Alembic migrations")
    if c.auth: features.append("- 🔒 JWT Authentication")
    if c.docker: features.append("- 🐳 Docker + docker-compose")
    if c.tests: features.append("- 🧪 Pytest async test suite")
    feature_block = "\n".join(features) if features else "- ⚡ FastAPI with async support"

    run_cmd = "docker-compose up --build" if c.docker else "uvicorn src.main:app --reload"

    return f'''# {c.name}

> Generated with [fastapi-gen](https://github.com/your-org/fastapi-gen) ⚡

## Features

{feature_block}

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -e .
cp .env.example .env
{"alembic upgrade head" + chr(10) if c.alembic else ""}{run_cmd}
```

Open **http://localhost:8000/docs** for the interactive API docs.

## Project structure

```
src/
  main.py          # App entrypoint
  core/
    config.py      # Settings (pydantic-settings){"" if not c.auth else chr(10) + "    security.py    # JWT helpers"}
  api/v1/
    router.py
    endpoints/
      health.py{"" if not c.auth else chr(10) + "      auth.py"}
{"  db/" + chr(10) + "    session.py" + chr(10) + "  models/" + chr(10) + "  schemas/" if c.db else ""}
```
'''