---
name: medallion-pipeline
description: Best practices for implementing Bronze/Silver/Gold architectures in Snowflake.
version: 1.0
---

# Snowflake Medallion Architecture Guide

When building pipelines with SnowNinja, follow these architectural patterns for a robust Medallion data lakehouse.

## 1. Bronze Layer (Raw Ingestion)
- **Format**: Store data in its rawest form. Use `VARIANT` columns for semi-structured data (JSON/Avro).
- **Tooling**: Use `COPY INTO` or Snowpipe for ingestion.
- **Pattern**: `CREATE OR REPLACE TABLE bronze_table (raw_data VARIANT, metadata_filename STRING, ingestion_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP());`

## 2. Silver Layer (Cleaned & Conformed)
- **Objective**: Filter, clean, and join data. 
- **Pattern**: Use Transient tables if data can be re-generated to save on storage costs.
- **Logic**: Cast VARIANT fields to typed columns. Apply deduplication using `QUALIFY ROW_NUMBER() OVER (...) = 1`.

## 3. Gold Layer (Business Ready)
- **Objective**: Highly aggregated data for BI and Analytics.
- **Pattern**: Use **Dynamic Tables** or **Materialized Views** for low-latency reporting.
- **Governance**: Apply Row Access Policies (RAP) at this layer to ensure data security.

## Agent Instructions
- If asked to "build a pipeline", always start by creating the separate databases or schemas for `BRONZE`, `SILVER`, and `GOLD`.
- Use `TASK` objects to orchestrate the movement between layers if not using Dynamic Tables.
