---
name: snowflake-python-udf
description: Creating Python UDFs and UDTFs with Snowpark
---

# Python UDFs in Snowflake

Executing Python code natively inside Snowflake compute.

## Critical Rules
1. Always specify the `PACKAGES` (e.g., `('pandas', 'numpy')`) from the Anaconda channel.
2. Use vectorized UDFs (batch API) for better performance on large datasets.
3. Keep the handler function deterministic and side-effect free.
