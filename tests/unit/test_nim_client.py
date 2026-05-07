import pytest
import json
from snowninja.llm.models import ModelRole, PLANNER_FALLBACK_CHAIN, IMPLEMENTER_FALLBACK_CHAIN, NO_TOOLS_MODELS
from snowninja.llm.nim_client import SYSTEM_PROMPTS, INTERVIEW_SYSTEM_PROMPT, NimClient
from snowninja.actions.tools_core import SNOWFLAKE_TOOLS, TOOL_DISPATCH

def test_model_role_enum():
    """PLANNER='planner', IMPLEMENTER='implementer'."""
    assert ModelRole.PLANNER == "planner"
    assert ModelRole.IMPLEMENTER == "implementer"

def test_system_prompts_exist():
    """Both PLANNER and IMPLEMENTER have system prompts."""
    assert ModelRole.PLANNER in SYSTEM_PROMPTS
    assert ModelRole.IMPLEMENTER in SYSTEM_PROMPTS

def test_system_prompts_mention_snowflake():
    """Prompts reference Snowflake, not Databricks."""
    for role, prompt in SYSTEM_PROMPTS.items():
        assert "Snowflake" in prompt
        assert "Databricks" not in prompt

def test_interview_prompt_exists():
    """INTERVIEW_SYSTEM_PROMPT is non-empty and mentions Snowflake."""
    assert len(INTERVIEW_SYSTEM_PROMPT) > 0
    assert "Snowflake" in INTERVIEW_SYSTEM_PROMPT

def test_tool_dispatch_matches_tools():
    """TOOL_DISPATCH keys == SNOWFLAKE_TOOLS function names."""
    tool_names = [t["function"]["name"] for t in SNOWFLAKE_TOOLS]
    for name in tool_names:
        assert name in TOOL_DISPATCH

def test_no_tools_models_set():
    """NO_TOOLS_MODELS contains expected entries."""
    assert len(NO_TOOLS_MODELS) > 0
    assert "google/gemma-7b-it" in NO_TOOLS_MODELS

def test_fallback_chain_not_empty():
    """Both fallback chains have >=2 models."""
    assert len(PLANNER_FALLBACK_CHAIN) >= 2
    assert len(IMPLEMENTER_FALLBACK_CHAIN) >= 2

@pytest.mark.asyncio
async def test_execute_tool_unknown():
    """_execute_tool('nonexistent', {}) returns error JSON."""
    client = NimClient()
    result = await client._execute_tool("nonexistent", {})
    parsed = json.loads(result)
    assert parsed.get("status") == "error"
    assert "not found" in parsed.get("message", "")
