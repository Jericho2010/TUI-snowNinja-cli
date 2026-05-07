import subprocess
import pytest

@pytest.mark.e2e
def test_snowninja_global_command():
    """
    Verifies that typing exactly 'snowninja' in the CLI works and 
    launches the REPL shell (if configured) or shows the unconfigured message.
    
    This ensures that the project setup (pyproject.toml scripts) correctly
    exposes the command globally as per the BricksNinja standard.
    """
    # Start the process without any arguments to simulate a user just typing 'snowninja'
    # We pass `/exit\n` into stdin so that if the interactive shell successfully launches, 
    # it immediately receives the command to gracefully exit instead of hanging the test.
    process = subprocess.Popen(
        ["snowninja"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Give it the exit command
        stdout, stderr = process.communicate(input="/exit\n", timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        pytest.fail("The 'snowninja' command hung and timed out.")

    # 1. Check that the command actually exists and runs (return code 0 or 1)
    # If unconfigured it exits with 1. If configured and it processes /exit, it exits with 0.
    assert process.returncode in [0, 1], f"Command crashed with code {process.returncode}\n{stderr}"
    
    # 2. Check that it is indeed the SnowNinja CLI that responded
    assert ("SnowNinja is not fully configured" in stdout or 
            "Goodbye" in stdout or
            "Snowflake Agent Harness" in stdout)
