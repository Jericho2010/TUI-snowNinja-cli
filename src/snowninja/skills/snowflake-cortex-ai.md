---
name: snowflake-cortex-ai
description: Using Snowflake Cortex AI for LLM integration
---

# Snowflake Cortex AI

Cortex provides serverless ML and LLM functions directly in SQL.

## Critical Rules
1. Always prefer `snowflake.cortex.complete()` for raw LLM interactions.
2. Ensure the active role has been granted the `CORTEX_USER` database role.
3. Use the task-specific functions (`summarize`, `sentiment`, `classify`) before resorting to raw prompt engineering with `complete()`.
