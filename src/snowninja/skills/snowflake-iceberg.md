---
name: snowflake-iceberg
description: Apache Iceberg tables in Snowflake
---

# Snowflake Iceberg Tables

Querying open format data.

## Critical Rules
1. Use `EXTERNAL VOLUME` to define the cloud storage location.
2. Iceberg tables can be unmanaged (external catalog) or managed (Snowflake catalog).
3. Performance is similar to native tables, but features like Time Travel depend on the catalog.
