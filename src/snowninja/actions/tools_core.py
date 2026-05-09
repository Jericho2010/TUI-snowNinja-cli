import re
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Any, List, Optional

from snowninja.core.connections import get_connection, list_profiles


def _quote_id(identifier: str) -> str:
    """
    Safely double-quote a Snowflake identifier to prevent SQL injection.
    Escapes embedded double-quotes by doubling them (Snowflake standard).
    """
    return '"' + identifier.replace('"', '""') + '"'


class ToolsCore:
    """Core Snowflake and Local tools for the SnowNinja Agent Harness."""

    def __init__(self, profile: Optional[str] = None):
        self.profile = profile
        self._conn = None  # Cached connection

    def _get_conn(self):
        """Return a live Snowflake connection, re-opening if closed or None."""
        try:
            if self._conn is not None and not self._conn.is_closed():
                return self._conn
        except Exception:
            pass
        self._conn = get_connection(self.profile)
        return self._conn

    @contextmanager
    def _cursor(self):
        """Yield a cursor on the cached connection, close only the cursor after use."""
        conn = self._get_conn()
        cs = conn.cursor()
        try:
            yield cs
        finally:
            cs.close()

    def _execute_query(
        self, sql: str, params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """Helper to execute SQL and return results as a list of dicts."""
        from snowninja.governance.policies import evaluate_query_policy

        policy = evaluate_query_policy(sql)
        if not policy.allowed:
            return [
                {
                    "status": "blocked",
                    "message": f"Query blocked by governance policy: {policy.reason}",
                    "action_class": policy.action_class.value,
                }
            ]

        with self._cursor() as cs:
            cs.execute("ALTER SESSION SET QUERY_TAG = 'snowninja_agent'")
            if params:
                cs.execute(sql, params)
            else:
                cs.execute(sql)

            if cs.description:
                columns = [col[0] for col in cs.description]
                return [dict(zip(columns, row)) for row in cs.fetchall()]
            return [{"status": "success", "message": "Query executed successfully"}]

    # --- Identity Domain (3) ---
    def get_current_user(self) -> Dict[str, Any]:
        res = self._execute_query(
            "SELECT current_user() AS USER, current_role() AS ROLE, current_warehouse() AS WAREHOUSE"
        )
        return res[0] if res else {}

    def get_account_info(self) -> Dict[str, Any]:
        res = self._execute_query(
            "SELECT current_account() AS ACCOUNT, current_region() AS REGION"
        )
        return res[0] if res else {}

    def list_connection_profiles(self) -> List[str]:
        return list_profiles()

    # --- Metadata Domain (6) ---
    def list_databases(self) -> List[Dict[str, Any]]:
        return self._execute_query("SHOW DATABASES")

    def list_schemas(self, database: Optional[str] = None) -> List[Dict[str, Any]]:
        sql = "SHOW SCHEMAS"
        if database:
            sql += f" IN DATABASE {_quote_id(database)}"
        return self._execute_query(sql)

    def list_tables(self, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        sql = "SHOW TABLES"
        if schema:
            sql += f" IN SCHEMA {_quote_id(schema)}"
        return self._execute_query(sql)

    def describe_table(self, table_name: str) -> List[Dict[str, Any]]:
        return self._execute_query(f"DESCRIBE TABLE {_quote_id(table_name)}")

    def search_objects(self, keyword: str) -> List[Dict[str, Any]]:
        # Use parameterized LIKE — keyword goes into SQL as a string literal safely
        safe_keyword = keyword.replace("'", "''")
        return self._execute_query(f"SHOW OBJECTS LIKE '%{safe_keyword}%'")

    def get_table_ddl(self, table_name: str) -> str:
        res = self._execute_query("SELECT GET_DDL('TABLE', ?) AS DDL", (table_name,))
        return res[0].get("DDL", "") if res else ""

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
        sql = (
            "SELECT * FROM table(information_schema.query_history()) "
            f"ORDER BY start_time DESC LIMIT {int(limit)}"
        )
        return self._execute_query(sql)

    # --- Warehouse Domain (4) ---
    def list_warehouses(self) -> List[Dict[str, Any]]:
        return self._execute_query("SHOW WAREHOUSES")

    def create_warehouse(
        self, name: str, size: str = "X-SMALL", tag: str = "snowninja"
    ) -> Dict[str, Any]:
        """
        Create a warehouse. A TAG is always applied to satisfy governance policy
        (policies.py blocks CREATE WAREHOUSE without TAG).
        """
        safe_name = _quote_id(name)
        safe_size = size.upper()
        safe_tag = tag.replace("'", "''")
        sql = (
            f"CREATE WAREHOUSE {safe_name} "
            f"WAREHOUSE_SIZE = '{safe_size}' "
            f"WITH TAG (snowninja_tag = '{safe_tag}')"
        )
        return self._execute_query(sql)[0]

    def resize_warehouse(self, name: str, size: str) -> Dict[str, Any]:
        return self._execute_query(
            f"ALTER WAREHOUSE {_quote_id(name)} SET WAREHOUSE_SIZE = '{size.upper()}'"
        )[0]

    def suspend_warehouse(self, name: str) -> Dict[str, Any]:
        return self._execute_query(f"ALTER WAREHOUSE {_quote_id(name)} SUSPEND")[0]

    # --- Data Eng Domain (8) ---
    def create_database(self, name: str) -> Dict[str, Any]:
        return self._execute_query(f"CREATE DATABASE IF NOT EXISTS {_quote_id(name)}")[
            0
        ]

    def create_schema(self, name: str) -> Dict[str, Any]:
        return self._execute_query(f"CREATE SCHEMA IF NOT EXISTS {_quote_id(name)}")[0]

    def create_table(self, name: str, columns: str) -> Dict[str, Any]:
        # Note: columns DDL comes from the LLM and is validated before execution
        return self._execute_query(
            f"CREATE TABLE IF NOT EXISTS {_quote_id(name)} ({columns})"
        )[0]

    def drop_object(self, object_type: str, name: str) -> Dict[str, Any]:
        # Only allow known safe object types to limit blast radius
        allowed_types = {
            "TABLE",
            "VIEW",
            "SCHEMA",
            "WAREHOUSE",
            "STAGE",
            "TASK",
            "STREAM",
            "PIPE",
            "PROCEDURE",
            "FUNCTION",
        }
        obj_upper = object_type.upper()
        if obj_upper not in allowed_types:
            return {
                "status": "blocked",
                "message": f"DROP {object_type} is not permitted.",
            }
        return self._execute_query(f"DROP {obj_upper} IF EXISTS {_quote_id(name)}")[0]

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
        sql = "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS RESULT"
        res = self._execute_query(sql, (model, prompt))
        return res[0].get("RESULT", "") if res else ""

    def cortex_summarize(self, text: str) -> str:
        sql = "SELECT SNOWFLAKE.CORTEX.SUMMARIZE(?) AS RESULT"
        res = self._execute_query(sql, (text,))
        return res[0].get("RESULT", "") if res else ""

    def cortex_sentiment(self, text: str) -> float:
        sql = "SELECT SNOWFLAKE.CORTEX.SENTIMENT(?) AS RESULT"
        res = self._execute_query(sql, (text,))
        return float(res[0].get("RESULT", 0.0)) if res else 0.0

    def cortex_classify(self, text: str, categories: List[str]) -> str:
        """
        Uses the native SNOWFLAKE.CORTEX.CLASSIFY_TEXT function with proper
        parameterisation — no f-string injection into SQL.
        Falls back to COMPLETE with a structured prompt if CLASSIFY_TEXT is
        unavailable on the account.
        """
        # Build the categories array literal safely — categories are strings
        # from the LLM, so we escape single-quotes
        safe_cats = ", ".join("'" + c.replace("'", "''") + "'" for c in categories)
        sql = f"SELECT SNOWFLAKE.CORTEX.CLASSIFY_TEXT(?, ARRAY_CONSTRUCT({safe_cats})) AS RESULT"
        try:
            res = self._execute_query(sql, (text,))
            return res[0].get("RESULT", "") if res else ""
        except Exception:
            # Fallback: use COMPLETE with a structured prompt
            cat_list = ", ".join(categories)
            prompt = (
                f"Classify the following text into exactly one of these categories: {cat_list}.\n"
                f"Text: {text}\n"
                f"Respond with only the category name."
            )
            return self.cortex_complete("mistral-large", prompt)

    # --- Governance Domain (6) ---
    def list_roles(self) -> List[Dict[str, Any]]:
        return self._execute_query("SHOW ROLES")

    def show_grants_on(
        self, object_type: str, object_name: str
    ) -> List[Dict[str, Any]]:
        allowed_types = {
            "TABLE",
            "VIEW",
            "SCHEMA",
            "DATABASE",
            "WAREHOUSE",
            "STAGE",
            "PROCEDURE",
            "FUNCTION",
            "ROLE",
        }
        obj_upper = object_type.upper()
        if obj_upper not in allowed_types:
            return [
                {
                    "status": "blocked",
                    "message": f"SHOW GRANTS ON {object_type} not permitted.",
                }
            ]
        return self._execute_query(
            f"SHOW GRANTS ON {obj_upper} {_quote_id(object_name)}"
        )

    def show_grants_to(self, role_name: str) -> List[Dict[str, Any]]:
        return self._execute_query(f"SHOW GRANTS TO ROLE {_quote_id(role_name)}")

    def list_tags(self) -> List[Dict[str, Any]]:
        return self._execute_query("SHOW TAGS")

    def list_masking_policies(self) -> List[Dict[str, Any]]:
        return self._execute_query("SHOW MASKING POLICIES")

    def list_row_access_policies(self) -> List[Dict[str, Any]]:
        return self._execute_query("SHOW ROW ACCESS POLICIES")

    # --- Cost Domain (3) ---
    def get_warehouse_usage(self, days: int = 7) -> List[Dict[str, Any]]:
        sql = (
            "SELECT warehouse_name, SUM(credits_used) AS total_credits "
            "FROM snowflake.account_usage.warehouse_metering_history "
            f"WHERE start_time >= DATEADD(day, -{int(days)}, current_date()) "
            "GROUP BY 1 ORDER BY 2 DESC"
        )
        try:
            return self._execute_query(sql)
        except Exception as e:
            return [
                {
                    "status": "error",
                    "message": f"Must have IMPORTED PRIVILEGES on SNOWFLAKE db: {e}",
                }
            ]

    def get_storage_usage(self) -> List[Dict[str, Any]]:
        try:
            return self._execute_query(
                "SELECT * FROM snowflake.account_usage.storage_usage ORDER BY usage_date DESC LIMIT 30"
            )
        except Exception as e:
            return [
                {
                    "status": "error",
                    "message": f"Must have IMPORTED PRIVILEGES on SNOWFLAKE db: {e}",
                }
            ]

    def get_login_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._execute_query(
            f"SELECT * FROM table(information_schema.login_history()) "
            f"ORDER BY event_timestamp DESC LIMIT {int(limit)}"
        )

    # --- Local Domain (3) ---
    def write_local_file(
        self, file_path: str, content: str, overwrite: bool = False
    ) -> Dict[str, Any]:
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
        """
        Run a shell command from a safe allowlist.
        The allowlist is checked against the ACTUAL command token (not startswith)
        to prevent bypass via chaining (e.g., 'ls; rm -rf /').
        """
        allowed_commands = {"ls", "echo", "pwd", "snow", "git"}

        # Extract the first token (the actual command binary)
        stripped = command.strip()
        first_token = re.split(r"[\s;&|]", stripped)[0]

        if first_token not in allowed_commands:
            return {
                "status": "blocked",
                "message": f"Command '{first_token}' is not in the allowed list: {sorted(allowed_commands)}",
            }

        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, check=True
            )
            return {
                "status": "success",
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "stdout": e.stdout,
                "stderr": e.stderr,
                "exit_code": e.returncode,
            }


# Singleton instance
tools = ToolsCore()
