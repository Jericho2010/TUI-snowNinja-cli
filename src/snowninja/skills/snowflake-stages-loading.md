---
name: snowflake-stages-loading
description: Loading data using Stages, COPY INTO, and Snowpipe
---

# Stages & Data Loading

Data enters Snowflake via Internal or External Stages.

## Critical Rules
1. Use `COPY INTO` for bulk batch loading.
2. Use `Snowpipe` (auto-ingest) for continuous loading from cloud storage event notifications.
3. Always define a `FILE_FORMAT` object instead of hardcoding format options in the `COPY` statement.
