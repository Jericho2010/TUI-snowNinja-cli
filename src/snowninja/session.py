from typing import Optional
from snowninja.core.config import load_config, SnowNinjaConfig

class SessionManager:
    def __init__(self):
        self.config: SnowNinjaConfig = load_config()
        self.current_workspace: Optional[str] = None

        # Shared Planner → Implementer task list.
        # Populated by the Planner lane; injected as context for the Implementer.
        self.task_list: str = ""

        # Structured requirements gathered during a /interview session.
        # Stored alongside task_list so Implementer has full context.
        self.requirements: str = ""

        # Interview mode state
        self.interview_mode: bool = False
        self.interview_turn_count: int = 0   # tracks Q&A rounds for auto-finalization

        # Determine if we have the minimum required config
        self.is_configured = bool(
            self.config.nvidia_pat and
            (self.config.snowflake_profile or self.config.snowflake_pat)
        )

    def reset_interview(self) -> None:
        """Reset interview state without clearing task list."""
        self.interview_mode = False
        self.interview_turn_count = 0

    def reload_config(self):
        self.config = load_config()
        self.is_configured = bool(
            self.config.nvidia_pat and
            (self.config.snowflake_profile or self.config.snowflake_pat)
        )

# Global session instance
session = SessionManager()
