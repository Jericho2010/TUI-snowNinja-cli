---
name: snowflake-alerts
description: Creating Snowflake alerts, notification integrations, and email-driven operational checks.
version: 1.0
---

# Snowflake Alerts

Use this guide when the user wants scheduled checks, threshold-based notifications, or email alerts triggered from Snowflake.

## Critical Rules
1. Alerts evaluate a condition on a schedule; model the condition query first, then the notification action.
2. Use a `NOTIFICATION INTEGRATION` for email delivery and `SYSTEM$SEND_EMAIL` in the alert action when email is required.
3. Keep the condition deterministic and cheap; alerts should check for a narrow failure state, not run a large transformation query.
4. Distinguish operational alerts from Resource Monitor budget controls; warehouse spend governance belongs with cost governance, not alert logic.

## When to Use
- The user asks for an email alert, anomaly notification, SLA breach monitor, or scheduled operational check.
- The ask mentions `ALERT`, `SYSTEM$SEND_EMAIL`, notification integrations, or scheduled data health checks.

## Key Patterns
- **Condition query**: return rows only when something is wrong, overdue, or outside the expected threshold.
- **Action**: send concise email content with the failing condition and the object or table involved.
- **Scheduling**: align the alert cadence with the freshness/SLA of the monitored dataset or pipeline.

## Agent Instructions
- Start by defining the exact failure condition and the recipient path before writing SQL.
- For budget or warehouse credit questions, route to cost governance instead of treating them as generic alerts.
- If the user wants multi-step remediation, pair alerts with tasks or procedures rather than overloading the alert action.
