---
name: snowflake-query-performance
description: Troubleshooting slow queries with query profile, caching, search optimization, and warehouse diagnostics.
version: 1.0
---

# Snowflake Query Performance

Use this guide for slow dashboards, expensive ad hoc SQL, queueing, and warehouse/query tuning work.

## Critical Rules
1. Diagnose before resizing: inspect query profile, query history, and warehouse load before increasing warehouse size.
2. Separate compute problems from SQL shape problems; poor filters, large scans, and bad joins are not fixed reliably by bigger warehouses alone.
3. Use caching, pruning, clustering, and search optimization selectively based on observed access patterns, not as default boilerplate.
4. Avoid broad performance advice without a concrete symptom such as spilling, queueing, scan volume, or repeated point lookups.

## When to Use
- The user asks about slow queries, query profile, explain plans, cache behavior, queueing, or dashboard latency.
- The ask mentions `search optimization`, `query acceleration`, `spilling`, `query history`, or `clustering key`.

## Key Patterns
- **First pass**: identify whether the bottleneck is queueing, scan volume, join explosion, remote spill, or repeated point lookup access.
- **Warehouse symptoms**: queueing and under-provisioned concurrency usually point to compute sizing or multi-cluster policy.
- **SQL symptoms**: large scans, poor filters, and late aggregations point to query design, table shape, or data layout.
- **Feature usage**: use Search Optimization Service for selective point-lookups; use clustering only for very large tables with consistent pruneable predicates.

## Agent Instructions
- Ask for or inspect the query profile and recent query history before recommending warehouse changes.
- For cost-only questions, pair this with `snowflake-cost-governance`; for UI latency in Streamlit, pair this with `snowflake-streamlit`.
- Be explicit about the likely bottleneck and the narrowest change that addresses it.
