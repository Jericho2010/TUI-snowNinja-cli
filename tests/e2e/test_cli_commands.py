import pytest
from typer.testing import CliRunner
from snowninja.cli import app

runner = CliRunner()

def test_cli_help_output():
    """snowninja --help contains 'SnowNinja' and 'setup'."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "SnowNinja" in result.stdout
    # 'setup' command should be listed in the help output
    assert "setup" in result.stdout

def test_cli_doctor_runs(monkeypatch):
    """snowninja doctor exits 0 when configured (mocked)."""
    # Mock is_configured and test_connection to avoid live API calls
    monkeypatch.setattr("snowninja.session.SessionManager.is_configured", True)
    monkeypatch.setattr(
        "snowninja.cli.test_connection", 
        lambda x=None: {"status": "success", "user": "test", "account": "test", "role": "test", "warehouse": "test"}
    )
    
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Config: OK" in result.stdout
    assert "Connected as test" in result.stdout

@pytest.mark.e2e
def test_cli_doctor_live():
    """snowninja doctor exits 0 with real Snowflake connection."""
    # Assuming the environment has a valid config via earlier phases
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Snowflake:" in result.stdout
