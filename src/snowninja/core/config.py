import os
import yaml
from pathlib import Path
from pydantic import BaseModel, Field

CONFIG_DIR = Path.home() / ".snowninja"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

class SnowNinjaConfig(BaseModel):
    nvidia_pat: str = Field(default="", description="NVIDIA Personal Access Token for NIM API")
    snowflake_profile: str = Field(default="", description="Profile name from ~/.snowflake/connections.toml")
    
    # Optional direct credentials (fallback if not using connections.toml)
    snowflake_url: str = Field(default="", description="Snowflake Workspace/Account URL")
    snowflake_user: str = Field(default="", description="Snowflake Username")
    snowflake_pat: str = Field(default="", description="Snowflake Personal Access Token")
    
    # Model preferences
    planner_model: str = Field(
        default="meta/llama-3.1-405b-instruct", 
        description="Model assigned to the Planner lane"
    )
    implementer_model: str = Field(
        default="qwen/qwen2.5-coder-32b-instruct", 
        description="Model assigned to the Implementer lane"
    )

def load_config() -> SnowNinjaConfig:
    """Loads configuration from ~/.snowninja/config.yaml"""
    if not CONFIG_FILE.exists():
        return SnowNinjaConfig()
    
    try:
        with open(CONFIG_FILE, "r") as f:
            data = yaml.safe_load(f) or {}
        return SnowNinjaConfig(**data)
    except Exception as e:
        print(f"Warning: Error loading config from {CONFIG_FILE}: {e}")
        return SnowNinjaConfig()

def save_config(config: SnowNinjaConfig):
    """Saves configuration to ~/.snowninja/config.yaml"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        yaml.safe_dump(config.model_dump(), f, default_flow_style=False)
