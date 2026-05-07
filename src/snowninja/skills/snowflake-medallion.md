---
name: snowflake-medallion
description: Building Medallion Architecture (Bronze/Silver/Gold)
---

# Medallion Architecture

Organizing data logically.

## Critical Rules
1. Bronze: Raw data ingestion (append-only).
2. Silver: Cleansed and conformed data.
3. Gold: Business-level aggregates. Use Dynamic Tables to drive these layers.
