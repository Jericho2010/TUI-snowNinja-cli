---
name: snowflake-dynamic-tables
description: Creating and managing continuous data pipelines using Dynamic Tables
---

# Snowflake Dynamic Tables

Dynamic Tables are the building blocks of declarative data pipelines in Snowflake.

## Critical Rules
1. Always specify `TARGET_LAG`. For batch, use `DOWNSTREAM`. For continuous, use an interval like `1 minute`.
2. Specify a `WAREHOUSE` that has enough compute to handle the refresh interval.
3. Understand that they replace standard Materialized Views for complex joins and aggregations.
