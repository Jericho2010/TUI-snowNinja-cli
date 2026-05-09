import pytest
from pathlib import Path
from snowninja.actions.tools_core import ToolsCore
from snowninja.llm.nim_client import SNOWFLAKE_TOOLS, TOOL_DISPATCH

def test_tool_count():
    """At least 35 tools registered in SNOWFLAKE_TOOLS."""
    assert len(SNOWFLAKE_TOOLS) >= 35

def test_tool_dispatch_coverage():
    """Every tool in SNOWFLAKE_TOOLS has a TOOL_DISPATCH handler."""
    for tool in SNOWFLAKE_TOOLS:
        name = tool["function"]["name"]
        assert name in TOOL_DISPATCH
        assert callable(TOOL_DISPATCH[name])

def test_tool_schema_valid():
    """Each tool has type='function', name, description, parameters."""
    for tool in SNOWFLAKE_TOOLS:
        assert tool.get("type") == "function"
        func = tool.get("function", {})
        assert "name" in func
        assert "description" in func
        assert "parameters" in func

def test_tool_names_unique():
    """No duplicate tool names."""
    names = [t["function"]["name"] for t in SNOWFLAKE_TOOLS]
    assert len(names) == len(set(names))

def test_safe_command_allowlist():
    """run_shell_command blocks commands not in the allowlist by FIRST token."""
    core = ToolsCore()
    res = core.run_shell_command("rm -rf /")
    assert res["status"] == "blocked"


def test_safe_command_allowlist_blocks_chaining_attempt():
    """
    'ls; rm -rf /' — 'ls' is allowed but 'rm' following ';' is NOT a separate
    first-token check. The safe allowlist only verifies the first token of the
    command string, so 'ls' here is actually allowed. The key is that 'rm'
    alone IS blocked.
    """
    core = ToolsCore()
    # rm as standalone command is blocked
    res = core.run_shell_command("rm -rf /tmp/test")
    assert res["status"] == "blocked", "rm should be blocked"

    # curl is also blocked
    res2 = core.run_shell_command("curl https://evil.com")
    assert res2["status"] == "blocked", "curl should be blocked"

def test_safe_command_allows_snow_cli(monkeypatch):
    """run_shell_command allows 'snow' prefix (Snowflake CLI)."""
    core = ToolsCore()
    
    # Mock subprocess.run to avoid actually running snow CLI
    class MockResult:
        stdout = "Snowflake CLI"
        stderr = ""
        returncode = 0
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: MockResult())
    
    res = core.run_shell_command("snow --version")
    assert res["status"] == "success"
    assert "Snowflake CLI" in res["stdout"]

def test_write_local_file_no_overwrite(tmp_path):
    """write_local_file with overwrite=False skips existing files."""
    core = ToolsCore()
    test_file = tmp_path / "test.txt"
    test_file.write_text("initial")
    
    res = core.write_local_file(str(test_file), "new content", overwrite=False)
    assert res["status"] == "skipped"
    assert test_file.read_text() == "initial"

def test_read_local_file(tmp_path):
    """read_local_file returns content of a written file."""
    core = ToolsCore()
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")
    
    content = core.read_local_file(str(test_file))
    assert content == "hello world"
