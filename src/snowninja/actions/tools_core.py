import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from snowninja.core.connections import get_connection, list_profiles

class ToolsCore:
    """Core Snowflake and Local tools for the SnowNinja Agent Harness."""

    def __init__(self, profile: Optional[str] = None):
        self.profile = profile

    def _execute_query(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Helper to execute SQL and return results as a list of dicts."""
        from snowninja.governance.policies import check_query_safety
        
        if not check_query_safety(sql):
            return [{"status": "blocked", "message": "Query blocked by governance policy"}]

        ctx = get_connection(self.profile)
        cs = ctx.cursor()
        try:
            cs.execute("ALTER SESSION SET QUERY_TAG = 'snowninja_agent'")
            if params:
                cs.execute(sql, params)
            else:
                cs.execute(sql)
            
            if cs.description:
                columns = [col[0] for col in cs.description]
                results = []
                for row in cs.fetchall():
                    results.append(dict(zip(columns, row)))
                return results
            return [{"status": "success", "message": "Query executed successfully"}]
        finally:
            cs.close()
            ctx.close()

    # --- Identity Domain (3) ---
    def get_current_user(self) -> Dict[str, Any]:
        res = self._execute_query("SELECT current_user() AS user, current_role() AS role, current_warehouse() AS warehouse")
        return res[0] if res else {}

    def get_account_info(self) -> Dict[str, Any]:
        res = self._execute_query("SELECT current_account() AS account, current_region() AS region")
        return res[0] if res else {}

    def list_connection_profiles(self) -> List[str]:
        return list_profiles()

    # --- Metadata Domain (6) ---
    def list_databases(self) -> List[Dict[str, Any]]:
        return self._execute_query("SHOW DATABASES")

    def list_schemas(self, database: Optional[str] = None) -> List[Dict[str, Any]]:
        sql = "SHOW SCHEMAS"
        if database:
            sql += f" IN DATABASE {database}"
        return self._execute_query(sql)

    def list_tables(self, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        sql = "SHOW TABLES"
        if schema:
            sql += f" IN SCHEMA {schema}"
        return self._execute_query(sql)

    def describe_table(self, table_name: str) -> List[Dict[str, Any]]:
        return self._execute_query(f"DESCRIBE TABLE {table_name}")

    def search_objects(self, keyword: str) -> List[Dict[str, Any]]:
        # A simple search across common objects in the current database/schema
        return self._execute_query(f"SHOW OBJECTS LIKE '%{keyword}%'")

    def get_table_ddl(self, table_name: str) -> str:
        res = self._execute_query(f"SELECT get_ddl('table', '{table_name}') AS ddl")
        return res[0]["DDL"] if res else ""

    # --- SQL Domain (3) ---
    def execute_sql(self, query: str) -> List[Dict[str, Any]]:
        return self._execute_query(query)

    def validate_sql(self, query: str) -> Dict[str, Any]:
        try:
            self._execute_query(f"EXPLAIN {query}")
            return {"status": "valid"}
        except Exception as e:
            return {"status": "invalid", "error": str(e)}

    def get_query_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        sql = f"SELECT * FROM table(information_schema.query_history()) ORDER BY start_time DESC LIMIT {limit}"
        return self._execute_query(sql)

    # --- Warehouse Domain (4) ---
    def list_warehouses(self) -> List[Dict[str, Any]]:
        return self._execute_query("SHOW WAREHOUSES")

    def create_warehouse(self, name: str, size: str = "X-SMALL") -> Dict[str, Any]:
        return self._execute_query(f"CREATE WAREHOUSE {name} WAREHOUSE_SIZE = '{size}'")[0]

    def resize_warehouse(self, name: str, size: str) -> Dict[str, Any]:
        return self._execute_query(f"ALTER WAREHOUSE {name} SET WAREHOUSE_SIZE = '{size}'")[0]

    def suspend_warehouse(self, name: str) -> Dict[str, Any]:
        return self._execute_query(f"ALTER WAREHOUSE {name} SUSPEND")[0]

    # --- Data Eng Domain (8) ---
    def create_database(self, name: str) -> Dict[str, Any]:
        return self._execute_query(f"CREATE DATABASE IF NOT EXISTS {name}")[0]

    def create_schema(self, name: str) -> Dict[str, Any]:
        return self._execute_query(f"CREATE SCHEMA IF NOT EXISTS {name}")[0]

    def create_table(self, name: str, columns: str) -> Dict[str, Any]:
        return self._execute_query(f"CREATE TABLE IF NOT EXISTS {name} ({columns})")[0]

    def drop_object(self, object_type: str, name: str) -> Dict[str, Any]:
        return self._execute_query(f"DROP {object_type} IF EXISTS {name}")[0]

    def list_stages(self) -> List[Dict[str, Any]]:
        return self._execute_query("SHOW STAGES")
        
    def list_tasks(self) -> List[Dict[str, Any]]:
        return self._execute_query("SHOW TASKS")
        
    def list_streams(self) -> List[Dict[str, Any]]:
        return self._execute_query("SHOW STREAMS")
        
    def list_pipes(self) -> List[Dict[str, Any]]:
        return self._execute_query("SHOW PIPES")

    # --- Cortex AI Domain (4) ---
    def cortex_complete(self, model: str, prompt: str) -> str:
        sql = "SELECT snowflake.cortex.complete(?, ?) AS result"
        res = self._execute_query(sql, (model, prompt))
        return res[0]["RESULT"] if res else ""

    def cortex_summarize(self, text: str) -> str:
        sql = "SELECT snowflake.cortex.summarize(?) AS result"
        res = self._execute_query(sql, (text,))
        return res[0]["RESULT"] if res else ""

    def cortex_sentiment(self, text: str) -> float:
        sql = "SELECT snowflake.cortex.sentiment(?) AS result"
        res = self._execute_query(sql, (text,))
        return float(res[0]["RESULT"]) if res else 0.0

    def cortex_classify(self, text: str, categories: List[str]) -> str:
        # Note: Classify isn't always standard Cortex everywhere, using basic completion fallback if needed
        sql = f"SELECT snowflake.cortex.complete('mistral-large', 'Classify this text: {text} into one of these categories: {categories}') AS result"
        res = self._execute_query(sql)
        return res[0]["RESULT"] if res else ""

    # --- Governance Domain (6) ---
    def list_roles(self) -> List[Dict[str, Any]]:
        return self._execute_query("SHOW ROLES")

    def show_grants_on(self, object_type: str, object_name: str) -> List[Dict[str, Any]]:
        return self._execute_query(f"SHOW GRANTS ON {object_type} {object_name}")

    def show_grants_to(self, role_name: str) -> List[Dict[str, Any]]:
        return self._execute_query(f"SHOW GRANTS TO ROLE {role_name}")

    def list_tags(self) -> List[Dict[str, Any]]:
        return self._execute_query("SHOW TAGS")

    def list_masking_policies(self) -> List[Dict[str, Any]]:
        return self._execute_query("SHOW MASKING POLICIES")
        
    def list_row_access_policies(self) -> List[Dict[str, Any]]:
        return self._execute_query("SHOW ROW ACCESS POLICIES")

    # --- Cost Domain (3) ---
    def get_warehouse_usage(self, days: int = 7) -> List[Dict[str, Any]]:
        sql = f"""
        SELECT warehouse_name, SUM(credits_used) as total_credits 
        FROM snowflake.account_usage.warehouse_metering_history 
        WHERE start_time >= DATEADD(day, -{days}, current_date()) 
        GROUP BY 1 ORDER BY 2 DESC
        """
        try:
            return self._execute_query(sql)
        except Exception as e:
            return [{"status": "error", "message": f"Must have IMPORTED PRIVILEGES on SNOWFLAKE db: {e}"}]

    def get_storage_usage(self) -> List[Dict[str, Any]]:
        try:
            return self._execute_query("SELECT * FROM snowflake.account_usage.storage_usage ORDER BY usage_date DESC LIMIT 30")
        except Exception as e:
            return [{"status": "error", "message": f"Must have IMPORTED PRIVILEGES on SNOWFLAKE db: {e}"}]

    def get_login_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._execute_query(f"SELECT * FROM table(information_schema.login_history()) ORDER BY event_timestamp DESC LIMIT {limit}")

    # --- Local Domain (3) ---
    def write_local_file(self, file_path: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
        p = Path(file_path)
        if p.exists() and not overwrite:
            return {"status": "skipped", "message": "File exists and overwrite=False"}
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return {"status": "success", "file_path": str(p)}

    def read_local_file(self, file_path: str) -> str:
        p = Path(file_path)
        if not p.exists():
            return f"Error: File {file_path} not found."
        return p.read_text()

    def run_shell_command(self, command: str) -> Dict[str, Any]:
        # Basic allowlist for safety
        allowed_prefixes = ["ls", "echo", "pwd", "snow", "git"]
        if not any(command.startswith(prefix) for prefix in allowed_prefixes):
            return {"status": "blocked", "message": "Command not allowed for security reasons"}
            
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            return {"status": "success", "stdout": result.stdout, "stderr": result.stderr}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "stdout": e.stdout, "stderr": e.stderr, "exit_code": e.returncode}


# Singleton instance
tools = ToolsCore()
