---
name: snowflake-devops
description: Using Snowflake CLI, project definitions, and deployment automation for SQL, Snowpark, and Streamlit workflows.
version: 1.0
---

# Snowflake DevOps and CLI

Use this guide when the user wants repeatable deployment workflows for Snowflake objects and app projects.

## Critical Rules
1. Prefer declarative project files and repeatable CLI commands over one-off manual deployment steps.
2. Keep `definition_version` and project metadata in source control so deploy behavior is deterministic across environments.
3. Separate build, deploy, and post-deploy validation steps; do not hide environment-specific assumptions inside ad hoc shell commands.
4. Use Snowflake CLI for app, Streamlit, and Snowpark packaging flows, and use SQL migration tooling when the ask is schema evolution rather than app deployment.

## When to Use
- The user asks about Snowflake CLI, `snow sql`, `snow streamlit deploy`, `definition_version`, schemachange, or CI/CD automation.
- The ask involves deploying scaffolds created by SnowNinja, especially Streamlit or Snowpark projects.

## Key Patterns
- **Snowflake CLI**: use `snow sql` for repeatable SQL execution and the project-specific commands for Streamlit or Snowpark deploys.
- **Project config**: keep `snowflake.yml` small and environment-aware; inject environment-specific names through config or deployment variables rather than copy-pasting files.
- **Migration discipline**: use ordered migration scripts for schema changes, especially when promoting across dev, test, and prod.
- **CI/CD**: validate auth, target environment, and object drift before deploy; fail loudly on missing warehouses, stages, or privileges.

## Agent Instructions
- If the user asks how to deploy a SnowNinja scaffold, show the exact Snowflake CLI command path first.
- Pair this with `snowflake-streamlit`, `snowflake-native-apps`, or `snowflake-python-udf` based on the artifact being deployed.
- Avoid vague “use CI/CD” advice; recommend concrete command sequences and config files.
