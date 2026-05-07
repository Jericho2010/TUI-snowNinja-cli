---
name: snowflake-cost-governance
description: Managing compute and storage costs
---

# Cost Governance

Controlling Snowflake spend.

## Critical Rules
1. Always set `AUTO_SUSPEND` on warehouses (usually 60 seconds).
2. Apply Resource Monitors at the account or warehouse level to alert or halt on budget thresholds.
3. Query `snowflake.account_usage.warehouse_metering_history` to analyze spend.
