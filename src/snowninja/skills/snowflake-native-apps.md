---
name: snowflake-native-apps
description: Building and deploying Snowflake Native Apps
---

# Snowflake Native Apps

Native Apps allow sharing data and logic securely.

## Critical Rules
1. All application logic runs in the consumer's account, but IP is protected.
2. You must define a `manifest.yml` and an application setup script.
3. Use `APPLICATION ROLE` to manage permissions inside the app.
