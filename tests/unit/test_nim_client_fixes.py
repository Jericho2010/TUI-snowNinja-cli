"""
tests/unit/test_nim_client_fixes.py

Tests covering the fixes applied to NimClient:
- Client is cached (same instance returned on repeated calls)
- invalidate_client() forces a new client on next call
- Fallback chain walks the full lane tree instead of hardcoding Mistral Large 3
- Permissive ## Estimated Iterations regex parsing
"""
import re
import pytest
from unittest import mock
from snowninja.llm.nim_client import NimClient
from snowninja.llm.models import ModelRole, NimModel


# ─────────────────────────────────────────────────────────────
# Client caching
# ─────────────────────────────────────────────────────────────

def test_get_client_returns_same_instance():
    """_get_client() returns the same AsyncOpenAI instance on consecutive calls."""
    client = NimClient()
    inst_a = client._get_client()
    inst_b = client._get_client()
    assert inst_a is inst_b


def test_invalidate_client_forces_new_instance():
    """After invalidate_client(), _get_client() creates a fresh instance."""
    client = NimClient()
    inst_a = client._get_client()
    client.invalidate_client()
    inst_b = client._get_client()
    assert inst_a is not inst_b


# ─────────────────────────────────────────────────────────────
# Fallback chain
# ─────────────────────────────────────────────────────────────

def test_planner_fallback_chain_does_not_include_coder_models():
    """Planner lane chain should contain reasoning models, not coder models."""
    client = NimClient()
    chain = client.get_fallback_chain(ModelRole.PLANNER)
    for model in chain:
        assert "coder" not in model.lower(), f"Coder model in planner chain: {model}"


def test_implementer_fallback_chain_does_not_include_planner_models():
    """Implementer lane chain should not contain the flagship planner model."""
    client = NimClient()
    chain = client.get_fallback_chain(ModelRole.IMPLEMENTER)
    assert NimModel.LLAMA_4_MAVERICK.value not in chain


def test_planner_fallback_chain_is_non_empty():
    client = NimClient()
    assert len(client.get_fallback_chain(ModelRole.PLANNER)) >= 2


def test_implementer_fallback_chain_is_non_empty():
    client = NimClient()
    assert len(client.get_fallback_chain(ModelRole.IMPLEMENTER)) >= 2


def test_implementer_fallback_chain_prefers_working_models():
    client = NimClient()
    chain = client.get_fallback_chain(ModelRole.IMPLEMENTER)
    assert chain == [
        NimModel.QWEN_3_CODER.value,
        NimModel.DEEPSEEK_V4_FLASH.value,
        NimModel.MISTRAL_SMALL_4.value,
        NimModel.DEEPSEEK_V4_PRO.value,
    ]


@pytest.mark.asyncio
async def test_agent_chat_walks_full_fallback_chain_on_error():
    """
    When the primary model fails with a fallback-eligible error, agent_chat
    should walk the full lane chain — not just jump to a hardcoded model.
    """
    client = NimClient()
    role = ModelRole.PLANNER
    chain = client.get_fallback_chain(role)

    call_log: list[str] = []

    async def fake_retry(**kwargs):
        call_log.append(kwargs["model"])
        raise Exception("503 capacity")  # always fail

    with mock.patch.object(client, "_resolve_model", return_value=chain[0]):
        with mock.patch.object(client, "_chat_with_retry", side_effect=fake_retry):
            events = []
            async for ev_type, data in client.agent_chat("test", role=role):
                events.append((ev_type, data))

    # Should have yielded model_switch events for each fallback tried
    switch_events = [d for t, d in events if t == "model_switch"]
    # All switched-to models should be in the chain
    for switched in switch_events:
        assert switched in chain, f"Unexpected fallback model: {switched}"

    # Must end with an error (all exhausted)
    error_events = [d for t, d in events if t == "error"]
    assert error_events, "Expected an error event when all fallbacks fail"


# ─────────────────────────────────────────────────────────────
# ## Estimated Iterations regex (tested via re module directly)
# ─────────────────────────────────────────────────────────────

ITER_RE = re.compile(r"##\s*Estimated Iterations[^\d]*([\d]+)", re.IGNORECASE)


@pytest.mark.parametrize("text,expected", [
    ("## Estimated Iterations\n15", 15),
    ("## Estimated Iterations: 15", 15),
    ("## Estimated Iterations\n**15**", 15),
    ("## Estimated Iterations\n\n20", 20),
    ("## estimated iterations\n8", 8),
    ("## Estimated Iterations (total model calls): 12", 12),
])
def test_iter_regex_permissive_formats(text, expected):
    """Permissive regex should match various LLM output formats."""
    m = ITER_RE.search(text)
    assert m is not None, f"Regex failed to match: {text!r}"
    assert int(m.group(1)) == expected


def test_iter_regex_no_match_on_missing():
    """Regex returns None when there's no ## Estimated Iterations section."""
    text = "## Task List\n- [ ] Do something"
    assert ITER_RE.search(text) is None
