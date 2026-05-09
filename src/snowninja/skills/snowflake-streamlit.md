---
name: snowflake-streamlit
description: Building Streamlit in Snowflake apps with Snowpark sessions, snowflake.yml, and Snow CLI deployment.
version: 1.0
---

# Streamlit in Snowflake

Use this guide for interactive Snowflake-hosted apps built with Streamlit in Snowflake (SiS).

## Critical Rules
1. Use `from snowflake.snowpark.context import get_active_session` inside the app instead of creating a standalone connector session.
2. Treat `snowflake.yml` as the deployment contract: define the app name, stage, query warehouse, main file, database, and schema there.
3. `streamlit` must not be confused with Snowflake `stream` objects; CDC/task guidance is the wrong pattern for UI apps.
4. Keep app queries scoped, cheap, and predictable; interactive apps should favor selective SQL, cached lookups, and clear warehouse ownership.

## When to Use
- The user wants a Snowflake-hosted dashboard, internal tool, analyst UI, or lightweight workflow app.
- The ask mentions `streamlit`, `snow streamlit deploy`, `snowflake.yml`, `st.dataframe`, or `get_active_session()`.
- The user wants app logic to stay close to Snowflake data without managing an external web server.

## Key Patterns
- **Session access**:
  ```python
  import streamlit as st
  from snowflake.snowpark.context import get_active_session

  session = get_active_session()
  df = session.sql("select current_user(), current_role(), current_warehouse()").to_pandas()
  st.dataframe(df)
  ```
- **Deployment**: use Snowflake CLI with `snow streamlit deploy` from a project that contains `snowflake.yml`.
- **App structure**: keep `app.py` thin, move reusable SQL/query helpers into modules, and avoid long-running synchronous work in the render path.
- **Privileges**: ensure the app has access to the target database/schema and a query warehouse.

## Agent Instructions
- If the user asks for an app UI inside Snowflake, prefer Streamlit in Snowflake unless they explicitly need a Native App package for distribution.
- When scaffolding, generate both `app.py` and `snowflake.yml` and show the deploy command.
- If the request also involves provider/consumer distribution, pair this with `snowflake-native-apps` rather than replacing it.
