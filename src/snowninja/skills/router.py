"""
skills/router.py — Keyword-based intent router for SnowNinja.

Maps user message keywords to relevant Snowflake skill docs.
Zero latency, zero tokens — no LLM call required.

Strategy:
- Planner: extracts only the "Critical Rules" / "When to Use" section → constrains task list
- Implementer: injects full truncated skill content → drives correct code patterns
"""
from __future__ import annotations

import re
from pathlib import Path

# Directory containing vendored SKILL.md files
SKILLS_DIR = Path(__file__).parent

# Max characters to inject per skill (safety cap)
MAX_SKILL_CHARS = 5000

# Keyword → skill name mapping
SKILL_MAP: dict[str, list[str]] = {
    "snowflake-dynamic-tables": [
        "dynamic table", "dynamic tables", "materialized view", "continuous",
        "lag", "target_lag", "declarative pipeline",
    ],
    "snowflake-streams-tasks": [
        "stream", "task", "cdc", "change data capture", "schedule",
        "task dag", "system$stream_has_data", "append_only",
    ],
    "snowflake-cortex-ai": [
        "cortex", "llm", "complete", "summarize", "sentiment", "classify",
        "cortex.complete", "ai function", "snowflake.cortex",
    ],
    "snowflake-stages-loading": [
        "stage", "copy into", "snowpipe", "load", "external table",
        "auto-ingest", "file format", "put", "get",
    ],
    "snowflake-native-apps": [
        "native app", "app package", "application role", "provider",
        "consumer", "manifest.yml", "setup script", "application package",
        "application specification", "versioned schema",
    ],
    "snowflake-streamlit": [
        "streamlit", "streamlit in snowflake", "sis", "streamlit app",
        "snow streamlit", "st.write", "st.dataframe", "st.sidebar",
        "get_active_session", "snowflake.yml",
    ],
    "snowflake-security": [
        "role", "grant", "masking policy", "row access policy", "rbac",
        "tag", "privilege", "network policy", "column mask",
    ],
    "snowflake-cost-governance": [
        "cost", "credit", "warehouse size", "suspend", "metering",
        "budget", "resource monitor", "auto_suspend",
    ],
    "snowflake-medallion": [
        "medallion", "bronze", "silver", "gold", "pipeline",
        "data architecture", "layered architecture",
    ],
    "snowflake-git-repos": [
        "git", "repository", "fetch", "branch", "api integration",
        "git repository",
    ],
    "snowflake-data-sharing": [
        "share", "secure share", "data clean room", "marketplace",
        "listing", "delta sharing", "data exchange",
    ],
    "snowflake-iceberg": [
        "iceberg", "open format", "polaris", "external volume",
        "iceberg table", "open table format",
    ],
    "snowflake-python-udf": [
        "udf", "udtf", "snowpark", "python", "stored procedure",
        "vectorized udf", "handler", "packages",
    ],
    "snowflake-alerts": [
        "alert", "snowflake alert", "system$send_email", "send_email",
        "notification integration", "email notification", "condition_query",
        "scheduled alert",
    ],
    "snowflake-query-performance": [
        "query profile", "slow query", "search optimization", "result cache",
        "query acceleration", "spilling", "clustering key", "explain plan",
        "query history", "warehouse queuing", "active_warehouse_load",
    ],
    "snowflake-devops": [
        "snow cli", "snow sql", "snow object", "schemachange", "ci/cd",
        "snowflake cli", "deploy script", "definition_version", "snow streamlit deploy",
    ],
}


class SkillRouter:
    """
    Keyword-based router that maps a user message to 0–2 relevant skill names.
    No LLM call, no latency. O(skills × keywords) per message.
    """

    def _keyword_matches(self, keyword: str, message: str) -> bool:
        """Match a keyword/phrase without false positives like stream -> streamlit."""
        pattern = rf"(?<!\w){re.escape(keyword.lower())}(?!\w)"
        return re.search(pattern, message.lower()) is not None

    def route(self, message: str, max_skills: int = 2) -> list[str]:
        """
        Return a list of skill names (up to max_skills) that match the message.
        Scored by number of keyword hits — highest scoring skills win.
        """
        scores: dict[str, int] = {}

        for skill, keywords in SKILL_MAP.items():
            hits = sum(1 for kw in keywords if self._keyword_matches(kw, message))
            if hits > 0:
                scores[skill] = scores.get(skill, 0) + hits

        # Sort by score descending, return top N unique skill names
        ranked = sorted(scores, key=lambda s: scores[s], reverse=True)
        seen: set[str] = set()
        result: list[str] = []
        for skill in ranked:
            if skill not in seen:
                seen.add(skill)
                result.append(skill)
            if len(result) >= max_skills:
                break
        return result

    def skill_names(self) -> list[str]:
        """Return the canonical, routable skill names."""
        return sorted(SKILL_MAP.keys())

    def load_skill(self, skill_name: str) -> str | None:
        """Load full vendored skill content (already truncated at copy time)."""
        path = SKILLS_DIR / f"{skill_name}.md"
        if not path.exists():
            return None
        content = path.read_text(encoding="utf-8")
        # Safety cap
        if len(content) > MAX_SKILL_CHARS:
            content = content[:MAX_SKILL_CHARS] + "\n\n*[truncated]*"
        return content

    def load_critical_rules(self, skill_name: str) -> str | None:
        """
        Extract only the most important section from a skill for Planner injection.
        Tries to find: Critical Rules, When to Use, Important, or Quick Decision sections.
        Falls back to first 800 chars if no section found.
        """
        content = self.load_skill(skill_name)
        if not content:
            return None

        # Section headers to try, in priority order
        section_patterns = [
            r"(#{1,3}\s*(critical rules?|always follow|important rules?)[^\n]*\n.*?)(?=\n#{1,3}\s|\Z)",
            r"(#{1,3}\s*(when to use[^\n]*)\n.*?)(?=\n#{1,3}\s|\Z)",
            r"(#{1,3}\s*(quick decision[^\n]*)\n.*?)(?=\n#{1,3}\s|\Z)",
            r"(#{1,3}\s*(overview|quick start)[^\n]*\n.*?)(?=\n#{1,3}\s|\Z)",
        ]

        for pattern in section_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                section = match.group(1).strip()
                # Cap at 1200 chars for Planner injection
                if len(section) > 1200:
                    section = section[:1200] + "\n*[...]*"
                return section

        # Fallback: first 800 chars
        return content[:800] + "\n*[...]*"

    def format_for_planner(self, skill_names: list[str]) -> str:
        """Format skill content for Planner injection — critical rules only."""
        if not skill_names:
            return ""
        parts = []
        for name in skill_names:
            rules = self.load_critical_rules(name)
            if rules:
                parts.append(
                    f"--- SKILL GUIDANCE [{name}] (Critical Rules for Planning) ---\n"
                    f"{rules}\n"
                    f"--- END [{name}] ---"
                )
        return "\n\n".join(parts)

    def format_for_implementer(self, skill_names: list[str]) -> str:
        """Format skill content for Implementer injection — full truncated content."""
        if not skill_names:
            return ""
        parts = []
        for name in skill_names:
            content = self.load_skill(name)
            if content:
                parts.append(
                    f"--- SKILL GUIDANCE [{name}] ---\n"
                    f"{content}\n"
                    f"--- END [{name}] ---"
                )
        return "\n\n".join(parts)

    def skill_index(self) -> str:
        """
        Compact index of all available skills (~500 chars).
        Injected when no specific skill is matched, so the LLM knows what's available.
        """
        lines = ["Available Snowflake skill guides (use /skills <name> to view):"]
        for name in self.skill_names():
            skill_file = SKILLS_DIR / f"{name}.md"
            # Read description from frontmatter
            text = skill_file.read_text(encoding="utf-8")
            m = re.search(r'description:\s*["\']?(.+?)["\']?\s*\n', text)
            desc = m.group(1)[:80] if m else ""
            lines.append(f"  • {name}: {desc}")
        return "\n".join(lines)


# Singleton
skill_router = SkillRouter()
