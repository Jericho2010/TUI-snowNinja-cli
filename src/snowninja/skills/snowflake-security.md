---
name: snowflake-security
description: Managing RBAC, Row Access Policies, and Masking
---

# Snowflake Security

Snowflake uses Role-Based Access Control (RBAC).

## Critical Rules
1. Never grant privileges directly to users. Grant to roles, and grant roles to users.
2. Use `MASKING POLICY` for column-level security (PII).
3. Use `ROW ACCESS POLICY` for row-level security.
