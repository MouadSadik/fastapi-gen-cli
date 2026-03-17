from typer.testing import CliRunner
from fastapi_gen.cli import app

runner = CliRunner()

def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0

def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0