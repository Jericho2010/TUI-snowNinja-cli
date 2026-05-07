---
name: cortex-ml
description: Leveraging Snowflake Cortex for LLM and ML functions.
version: 1.0
---

# Snowflake Cortex LLM & ML Guide

Snowflake Cortex provides instant access to LLMs and ML functions directly within SQL.

## 1. LLM Functions
- **COMPLETE**: Generate text or code. 
  `SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3-70b', 'Summarize this: ' || raw_text) FROM my_table;`
- **EXTRACT_ANSWER**: Pull specific info from unstructured text.
  `SELECT SNOWFLAKE.CORTEX.EXTRACT_ANSWER(raw_text, 'What is the invoice number?') FROM invoices;`
- **SENTIMENT**: 
  `SELECT SNOWFLAKE.CORTEX.SENTIMENT(review_text) FROM product_reviews;`

## 2. ML Functions
- **FORECAST**: Time-series forecasting.
- **ANOMALY_DETECTION**: Identify outliers in your data.
- **CONTRIBUTION_ANALYZER**: Find the "why" behind metric changes.

## Agent Instructions
- When the user asks for "AI" or "Summary" features, prefer **Snowflake Cortex** functions over external LLM calls to keep data within the Snowflake security perimeter.
- Always check if the user's current role has the `CORTEX_USER` database role or equivalent privileges before executing Cortex functions.
