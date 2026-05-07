---
name: snowpark-python
description: Developing Python-native dataframes and stored procedures with Snowpark.
version: 1.0
---

# Snowpark Python Developer Guide

Snowpark allows you to write Python code that is executed directly inside the Snowflake engine.

## 1. Dataframe API
- **Pattern**: `session.table("DATABASE.SCHEMA.TABLE").filter(col("active") == True).select(col("id"), col("name"))`.
- **Transformation**: Use `df.with_column()` and `df.join()` for standard ETL tasks.

## 2. Stored Procedures (sprocs)
- **Objective**: Encapsulate logic for deployment and scheduling.
- **Pattern**:
  ```python
  def main(session: snowflake.snowpark.Session, table_name: str):
      df = session.table(table_name)
      # business logic here
      return "Success"
  ```

## 3. User Defined Functions (UDFs)
- **Vectorized UDFs**: Use `pandas_udf` for high-performance batch processing.
- **Imports**: Define Anaconda package requirements in the UDF definition.

## Agent Instructions
- If the user asks for "Python in Snowflake", prefer **Snowpark** over local processing.
- When generating Snowpark code, always ensure the `snowflake-snowpark-python` library is used and the code is structured to be deployed as a Stored Procedure or UDF.
