from typer.testing import CliRunner
from snowninja.cli import app
from snowninja.session import session

runner = CliRunner()

def test_cli_help():
    """snowninja --help exits 0, contains 'SnowNinja'."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "SnowNinja" in result.stdout

def test_cli_setup_help():
    """snowninja setup --help exits 0."""
    result = runner.invoke(app, ["setup", "--help"])
    assert result.exit_code == 0

def test_cli_doctor_help():
    """snowninja doctor --help exits 0."""
    result = runner.invoke(app, ["doctor", "--help"])
    assert result.exit_code == 0

def test_cli_unconfigured_exits(monkeypatch):
    """Without config, snowninja exits code 1."""
    # Force unconfigured state
    monkeypatch.setattr("snowninja.session.SessionManager.is_configured", False)
    
    result = runner.invoke(app)
    assert result.exit_code == 1
    assert "not fully configured" in result.stdout
