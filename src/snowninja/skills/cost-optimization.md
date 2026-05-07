---
name: cost-optimization
description: Managing Snowflake credits, warehouse sizing, and monitor policies.
version: 1.0
---

# Snowflake Cost Optimization Guide

Strategic management of credits and compute resources.

## 1. Warehouse Right-Sizing
- **Rule of Thumb**: Start small. Increase size only if the workload is queued or if you need to reduce wall-clock time for a single large query.
- **Scaling Policy**: Use `ECONOMY` scaling policy for non-critical batch jobs to avoid spinning up new clusters too aggressively.

## 2. Resource Monitors
- **Pattern**: Set up monitors at the Account, Warehouse, or User level.
- **Action**: Use `SUSPEND_IMMEDIATE` when a threshold (e.g., 80% of monthly quota) is reached.

## 3. Storage Optimization
- **Time Travel**: Reduce Time Travel days for transient tables to minimize Fail-safe and storage costs.
- **Clustering**: Avoid manual clustering unless the table is > 1TB and query performance is significantly degraded.

## Agent Instructions
- When asked about "performance" or "slowness", always check the warehouse configuration using `execute_sql('SHOW WAREHOUSES')`.
- Suggest `ALTER WAREHOUSE ... SET AUTO_SUSPEND = 60` for dev warehouses to prevent credit leakage.
