---
name: snowflake-git-repos
description: Integrating Snowflake with Git repositories
---

# Snowflake Git Integration

Snowflake can natively integrate with external Git repositories.

## Critical Rules
1. Use `CREATE API INTEGRATION` for the Git provider authentication.
2. Use `CREATE GIT REPOSITORY` to map the repository to a Snowflake object.
3. Always run `ALTER GIT REPOSITORY ... FETCH` to pull the latest changes before execution.
