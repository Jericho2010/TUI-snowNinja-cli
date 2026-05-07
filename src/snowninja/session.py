from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from .core.config import load_config, SnowNinjaConfig

class PlanItem(BaseModel):
    id: str
    title: str
    description: str
    status: str = "pending"
    assigned_role: str = "planner"

class SessionManager:
    """Manages the global state for the SnowNinja CLI session."""
    
    def __init__(self):
        self.config: SnowNinjaConfig = load_config()
        self.task_list: List[PlanItem] = []
        self.requirements: List[str] = []
        self.interview_mode: bool = False
        self.interview_turn_count: int = 0
        self.active_connection = None
    
    @property
    def is_configured(self) -> bool:
        """Returns True if the system has basic configuration (like an NVIDIA PAT)."""
        # We need either an NVIDIA PAT for NIM, or an external LLM proxy setup
        # For now, base it on nvidia_pat
        return bool(self.config.nvidia_pat)
    
    def reset_interview(self):
        """Resets interview state but preserves tasks and requirements."""
        self.interview_mode = False
        self.interview_turn_count = 0

# Global session singleton
session = SessionManager()
