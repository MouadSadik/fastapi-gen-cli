# fastapi-gen ⚡

> Create production-ready FastAPI projects in seconds.

## Install
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ fastapi-gen-newone
```

Or run directly with `pipx`:
```bash
pipx run fastapi-gen-newone my-app
```

## Usage

### Interactive (recommended)
```bash
fastapi-gen my-app
```

You'll be prompted to select features:
```
⚡ FastAPI Project Generator
Scaffold a production-ready FastAPI app in seconds

? Project name: my-app
? Include SQLAlchemy (database models): Yes
? Include Alembic (database migrations): Yes
? Include JWT Auth (login/register routes): Yes
? Include Docker (Dockerfile + docker-compose): Yes
? Include Pytest (test suite): Yes
```

### With flags (non-interactive)
```bash
fastapi-gen my-app --db --auth --docker --alembic --tests
```

### Skip prompts entirely
```bash
fastapi-gen my-app -y            # bare project, no extras
fastapi-gen my-app -y --auth     # just auth, no prompts
```

## Generated structure
```
my-app/
├── src/
│   ├── main.py            ← FastAPI app entrypoint
│   ├── core/
│   │   └── config.py    ← pydantic-settings
│   ├── api/v1/
│   │   ├── router.py
│   │   └── endpoints/
│   │       └── health.py   
│   ├── db/                ← (if --db)
│   │   └── session.py
│   ├── models/            ← (if --db)
│   └── schemas/           ← (if --db)
├── alembic/               ← (if --alembic)
├── tests/                 ← (if --tests)
├── Dockerfile             ← (if --docker)
├── docker-compose.yml     ← (if --docker)
├── pyproject.toml
├── .env.example
└── README.md
```

## Options

| Flag | Description |
|------|-------------|
| `--db` | SQLAlchemy async ORM + aiosqlite |
| `--alembic` | Alembic migration setup |
| `--docker` | Dockerfile + docker-compose |
| `--tests` | pytest + httpx async test suite |
| `-y / --no-interactive` | Skip all prompts |