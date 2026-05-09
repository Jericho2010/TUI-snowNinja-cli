from prompt_toolkit.formatted_text import to_formatted_text
from snowninja.repl.shell import (
    SLASH_COMMANDS,
    MODES,
    SlashCompleter,
    SnowNinjaShell,
    SF_BLUE,
    SF_NAVY,
    SF_YELLOW,
)
from snowninja.llm.models import ModelRole
from snowninja.session import session
from prompt_toolkit.document import Document


def test_slash_commands_defined():
    """SLASH_COMMANDS dict has >=20 entries."""
    assert len(SLASH_COMMANDS) >= 20


def test_all_modes_in_modes_dict():
    """plan, implement, explore, operate, govern, cost all in MODES."""
    expected_modes = ["plan", "implement", "explore", "operate", "govern", "cost"]
    for mode in expected_modes:
        assert mode in MODES


def test_slash_completer_returns_matches():
    """SlashCompleter yields completions for '/pl'."""
    completer = SlashCompleter()
    doc = Document("/pl")
    completions = list(completer.get_completions(doc, None))
    # Should match /plan
    assert any(c.text == "/plan" for c in completions)


def test_slash_completer_no_match():
    """SlashCompleter yields nothing for 'hello'."""
    completer = SlashCompleter()
    doc = Document("hello")
    completions = list(completer.get_completions(doc, None))
    assert len(completions) == 0


def test_modes_map_to_valid_roles():
    """Every mode maps to 'planner' or 'implementer'."""
    for mode, (role, icon, color) in MODES.items():
        assert role in [ModelRole.PLANNER.value, ModelRole.IMPLEMENTER.value]


def test_brand_colors_are_hex():
    """All SF_* color constants are valid hex (#XXXXXX)."""
    colors = [SF_BLUE, SF_NAVY, SF_YELLOW]
    for color in colors:
        assert color.startswith("#")
        assert len(color) == 7


def test_bottom_toolbar_shows_active_lane_model():
    shell = SnowNinjaShell()
    original_model = session.active_implementer_model
    session.active_implementer_model = "vendor/runtime-model"
    try:
        toolbar_text = "".join(
            fragment[1] for fragment in to_formatted_text(shell._bottom_toolbar())
        )
        assert "runtime-model" in toolbar_text
    finally:
        session.active_implementer_model = original_model
