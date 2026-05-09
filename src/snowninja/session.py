from typing import Optional
from snowninja.core.config import load_config, SnowNinjaConfig


class SessionManager:
    def __init__(self):
        self.config: SnowNinjaConfig = load_config()
        default_config = SnowNinjaConfig()
        self.current_workspace: Optional[str] = None

        # Shared Planner → Implementer task list.
        # Populated by the Planner lane; injected as context for the Implementer.
        self.task_list: str = ""

        # Structured requirements gathered during a /interview session.
        # Stored alongside task_list so Implementer has full context.
        self.requirements: str = ""

        # Interview mode state
        self.interview_mode: bool = False
        self.interview_turn_count: int = 0  # tracks Q&A rounds for auto-finalization

        # Runtime limits
        self.max_iterations: int = 20
        self.active_planner_model: str = getattr(
            self.config,
            "planner_model",
            default_config.planner_model,
        )
        self.active_implementer_model: str = getattr(
            self.config,
            "implementer_model",
            default_config.implementer_model,
        )

        # Determine if we have the minimum required config
        self.is_configured = bool(
            self.config.nvidia_pat
            and (self.config.snowflake_profile or self.config.snowflake_pat)
        )

    def get_active_model(self, role) -> str:
        role_value = getattr(role, "value", role)
        if role_value == "planner":
            return self.active_planner_model
        return self.active_implementer_model

    def set_active_model(self, role, model: str) -> None:
        role_value = getattr(role, "value", role)
        if role_value == "planner":
            self.active_planner_model = model
        else:
            self.active_implementer_model = model

    def reset_active_models(self) -> None:
        default_config = SnowNinjaConfig()
        self.active_planner_model = getattr(
            self.config,
            "planner_model",
            default_config.planner_model,
        )
        self.active_implementer_model = getattr(
            self.config,
            "implementer_model",
            default_config.implementer_model,
        )

    def reset_interview(self) -> None:
        """Reset interview state without clearing task list."""
        self.interview_mode = False
        self.interview_turn_count = 0

    def reload_config(self):
        self.config = load_config()
        self.is_configured = bool(
            self.config.nvidia_pat
            and (self.config.snowflake_profile or self.config.snowflake_pat)
        )
        self.reset_active_models()


# Global session instance
session = SessionManager()
