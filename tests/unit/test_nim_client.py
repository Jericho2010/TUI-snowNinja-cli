import pytest
import json
from types import SimpleNamespace
from unittest import mock
from snowninja.llm.models import ModelRole
from snowninja.llm.nim_client import (
    SYSTEM_PROMPTS,
    INTERVIEW_SYSTEM_PROMPT,
    NimClient,
    SNOWFLAKE_TOOLS,
    TOOL_DISPATCH,
    NO_TOOLS_MODELS,
)
from snowninja.session import session


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


def test_interview_prompt_requires_detailed_requirements_and_tasks():
    assert "## Requirements" in INTERVIEW_SYSTEM_PROMPT
    assert "## Task List" in INTERVIEW_SYSTEM_PROMPT
    assert "4-8 tasks" in INTERVIEW_SYSTEM_PROMPT
    assert "implementation-ready" in INTERVIEW_SYSTEM_PROMPT


def test_tool_dispatch_matches_tools():
    """TOOL_DISPATCH keys == SNOWFLAKE_TOOLS function names."""
    tool_names = [t["function"]["name"] for t in SNOWFLAKE_TOOLS]
    for name in tool_names:
        assert name in TOOL_DISPATCH


def test_no_tools_models_set():
    """NO_TOOLS_MODELS contains expected entries."""
    assert len(NO_TOOLS_MODELS) > 0
    assert "nvidia/llama-3.1-nemotron-ultra-253b-v1" in NO_TOOLS_MODELS


@pytest.mark.asyncio
async def test_execute_tool_unknown():
    """_execute_tool('nonexistent', {}) returns error JSON."""
    client = NimClient()
    result = await client._execute_tool("nonexistent", {})
    parsed = json.loads(result)
    assert parsed.get("status") == "error"
    assert "not found" in parsed.get("message", "")


def _response(content="ok", tool_calls=None):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content, tool_calls=tool_calls)
            )
        ]
    )


def test_should_fallback_only_for_availability_signals():
    client = NimClient()
    assert client._should_fallback(Exception("503 overloaded")) is True
    assert client._should_fallback(Exception("404 not found")) is True
    assert client._should_fallback(Exception("400 bad request")) is False


@pytest.mark.asyncio
async def test_agent_chat_tracks_active_model_after_fallback():
    client = NimClient()
    original_planner_model = session.config.planner_model
    original_active_planner = session.active_planner_model
    session.config.planner_model = "primary-model"
    session.set_active_model("planner", "primary-model")

    async def fake_chat_with_retry(**kwargs):
        if kwargs["model"] == "primary-model":
            raise Exception("503 overloaded")
        return _response(content="resolved")

    try:
        with mock.patch.object(
            client,
            "get_fallback_chain",
            return_value=["primary-model", "fallback-model"],
        ):
            with mock.patch.object(
                client, "_chat_with_retry", side_effect=fake_chat_with_retry
            ):
                events = []
                async for event_type, data in client.agent_chat(
                    "help me",
                    role=ModelRole.PLANNER,
                    max_iterations=1,
                ):
                    events.append((event_type, data))

        assert ("model_switch", "fallback-model") in events
        assert ("text", "resolved") in events
        assert session.active_planner_model == "fallback-model"
    finally:
        session.config.planner_model = original_planner_model
        session.active_planner_model = original_active_planner
