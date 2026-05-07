---
name: snowflake-streams-tasks
description: Building CDC pipelines with Streams and Tasks
---

# Snowflake Streams & Tasks

Streams track DML changes, and tasks schedule execution.

## Critical Rules
1. Never consume a stream in a `SELECT` statement unless it's part of a DML operation (`INSERT`, `MERGE`), otherwise the offset advances and data is lost.
2. Use `SYSTEM$STREAM_HAS_DATA` as a task condition to save compute costs.
3. Manage task DAGs using the `AFTER` keyword.
