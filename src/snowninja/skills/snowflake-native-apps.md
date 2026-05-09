---
name: snowflake-native-apps
description: Building and deploying Snowflake Native Apps with secure provider and consumer patterns.
---

# Snowflake Native Apps

Native Apps package data products, application logic, and UI experiences for installation inside a consumer account.

## Critical Rules
1. Ship every app with a `manifest.yml`, setup script, and explicit versioned artifacts; treat the manifest as the contract for install and upgrade behavior.
2. Use `APPLICATION ROLE` objects for least-privilege access inside the app, and grant only the objects required by each feature.
3. Keep provider-owned logic in secure objects and references; all runtime access happens in the consumer account, so avoid assumptions about provider-side session state.
4. When the app exposes UI, decide early whether that UI is Streamlit in Snowflake, a Native App front end, or both; the packaging and privilege model differ.

## When to Use
- You need to distribute governed data products or application logic to other Snowflake accounts.
- You want installation, upgrade, and permissioning handled inside Snowflake instead of external deployment tooling.
- You need a provider/consumer model with protected IP and controlled object references.

## Key Patterns
- **App package lifecycle**: create the application package first, then stage versioned setup SQL, manifest, shared content, and release directives.
- **Privileges**: map end-user capabilities to `APPLICATION ROLE` grants rather than broad account roles.
- **References**: use object references for consumer-owned warehouses, databases, or external integrations that the app must access.
- **UI composition**: if the user asks for interactive pages, pair this skill with `snowflake-streamlit` when the app is backed by Streamlit in Snowflake.

## Agent Instructions
- When the user asks for a Snowflake app, determine first whether they mean a Native App package, a Streamlit app, or a standalone internal tool.
- For provider/consumer packaging, propose the minimal application package structure and the install/upgrade flow before writing SQL.
- Call out required objects explicitly: `APPLICATION PACKAGE`, `APPLICATION`, `APPLICATION ROLE`, manifest, setup script, and any references.
