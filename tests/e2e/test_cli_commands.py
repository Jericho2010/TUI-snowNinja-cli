import pytest
from typer.testing import CliRunner
from snowninja.cli import app

runner = CliRunner()

def test_cli_help_output():
    """snowninja --help contains 'SnowNinja'."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "SnowNinja" in result.stdout

def test_cli_doctor_runs(monkeypatch):
    """snowninja doctor exits 0 when configured (mocked)."""
    # Mock is_configured and tools_core to avoid live API calls
    class MockSession:
        is_configured = True
        config = type('obj', (object,), {'nvidia_pat': 'dummy'})()
        
    monkeypatch.setattr("snowninja.cli.session", MockSession())
    
    # Mock OpenAI inside the openai module where it's actually imported from
    class MockOpenAI:
        def __init__(self, *args, **kwargs):
            pass
        @property
        def models(self):
            class Models:
                def list(self): pass
            return Models()
            
    monkeypatch.setattr("openai.OpenAI", MockOpenAI)
    
    # Mock Tools
    class MockTools:
        def get_current_user(self):
            return {"USER": "test", "ROLE": "test", "WAREHOUSE": "test"}
            
    monkeypatch.setattr("snowninja.actions.tools_core.tools", MockTools())
    
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "is fully populated" in result.stdout
    assert "Authenticated as test" in result.stdout

@pytest.mark.e2e
def test_cli_doctor_live():
    """snowninja doctor exits 0 with real Snowflake connection."""
    # Assuming the environment has a valid config via earlier phases
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
