---
name: governance-and-security
description: Best practices for RBAC, Masking, and Row Access Policies in Snowflake.
version: 1.0
---

# Snowflake Governance & Security Guide

Use this guide when managing roles, permissions, and data privacy in Snowflake.

## 1. Role-Based Access Control (RBAC)
- **Hierarchy**: Always use a hierarchy. Functional roles (e.g., `DATA_ENGINEER`) should be granted to user-facing roles, while object-level permissions should be granted to Access Roles (e.g., `READ_ONLY_SALES`).
- **Principle of Least Privilege**: Avoid using `ACCOUNTADMIN` for routine tasks. Use `USERADMIN` for user management and `SECURITYADMIN` for grants.

## 2. Dynamic Data Masking
- **Pattern**: `CREATE MAPPING POLICY...` followed by `ALTER TABLE ... MODIFY COLUMN ... SET MAPPING POLICY`.
- **Logic**: Use the `CURRENT_ROLE()` function to determine if the user should see the raw data or a masked value.

## 3. Row Access Policies (RAP)
- **Objective**: Restrict which rows a user can see based on their role or attributes.
- **Pattern**: `CREATE ROW ACCESS POLICY ... AS (org_id NUMBER) RETURNS BOOLEAN -> EXISTS (SELECT 1 FROM mapping_table WHERE role = CURRENT_ROLE() AND allowed_org = org_id)`.

## Agent Instructions
- When asked to "setup security", always start by proposing a Role Hierarchy diagram in your response.
- Use the `list_roles` and `list_grants` tools to inspect the current state before suggesting changes.
