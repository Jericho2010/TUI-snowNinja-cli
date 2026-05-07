import os
import re
from pathlib import Path
from typing import List, Optional, Dict

SKILLS_DIR = Path(__file__).parent

SKILL_MAP = {
    "snowflake-dynamic-tables": ["dynamic table", "dynamic tables", "materialized view", "continuous", "lag"],
    "snowflake-streams-tasks": ["stream", "task", "cdc", "change data capture", "schedule"],
    "snowflake-cortex-ai": ["cortex", "llm", "complete", "summarize", "sentiment", "classify"],
    "snowflake-stages-loading": ["stage", "copy into", "snowpipe", "load", "external table"],
    "snowflake-native-apps": ["native app", "app package", "application role", "provider", "consumer"],
    "snowflake-security": ["role", "grant", "masking policy", "row access policy", "rbac", "tag"],
    "snowflake-cost-governance": ["cost", "credit", "warehouse size", "suspend", "metering", "budget"],
    "snowflake-medallion": ["medallion", "bronze", "silver", "gold", "pipeline", "dlt"],
    "snowflake-git-repos": ["git", "repository", "fetch", "branch"],
    "snowflake-data-sharing": ["share", "secure share", "data clean room", "marketplace"],
    "snowflake-iceberg": ["iceberg", "open format", "polar", "external volume"],
    "snowflake-python-udf": ["udf", "udtf", "snowpark", "python", "stored procedure"]
}

class SkillRouter:
    """Zero-latency keyword router for Snowflake Skill Guides."""
    
    @staticmethod
    def route(prompt: str, max_skills: int = 2) -> List[str]:
        """Matches a prompt to the relevant skill IDs based on keywords."""
        prompt_lower = prompt.lower()
        matched_skills = []
        
        for skill_id, keywords in SKILL_MAP.items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', prompt_lower):
                    matched_skills.append(skill_id)
                    break # Only add a skill once
                    
        return matched_skills[:max_skills]

    @staticmethod
    def load_skill(skill_id: str) -> Optional[str]:
        """Loads the content of a skill markdown file."""
        file_path = SKILLS_DIR / f"{skill_id}.md"
        if not file_path.exists():
            return None
        return file_path.read_text()

    @staticmethod
    def load_critical_rules(skill_id: str) -> Optional[str]:
        """Extracts the 'Critical Rules' or 'Rules' section from a skill file."""
        content = SkillRouter.load_skill(skill_id)
        if not content:
            return None
            
        # Try to find a section starting with ## Critical Rules or similar
        match = re.search(r'##\s*(?:Critical\s*)?Rules\s*\n(.*?)(?=\n## |\Z)', content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def skill_index() -> str:
        """Returns a string listing all available skills."""
        return ", ".join(SKILL_MAP.keys())
