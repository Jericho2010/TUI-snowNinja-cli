from pathlib import Path
from typing import List, Optional, Dict, Any
import toml
import snowflake.connector
from snowflake.connector import SnowflakeConnection
try:
    from snowflake.core import Root
except ImportError:
    Root = None  # Handle gracefully if not installed yet

from .config import load_config

CONNECTIONS_FILE = Path.home() / ".snowflake" / "connections.toml"

def list_profiles() -> List[str]:
    """Returns a list of profile names from ~/.snowflake/connections.toml"""
    if not CONNECTIONS_FILE.exists():
        return []
    
    try:
        with open(CONNECTIONS_FILE, "r") as f:
            data = toml.load(f)
        return list(data.keys())
    except Exception as e:
        print(f"Warning: Error reading {CONNECTIONS_FILE}: {e}")
        return []

def get_connection(profile: Optional[str] = None) -> SnowflakeConnection:
    """Gets a SnowflakeConnection using the specified profile, or fallback to config.yaml"""
    config = load_config()
    prof_name = profile or config.snowflake_profile
    
    if prof_name and CONNECTIONS_FILE.exists():
        try:
            # Let the snowflake connector handle the connection using connections.toml
            return snowflake.connector.connect(connection_name=prof_name)
        except Exception as e:
            print(f"Error connecting with profile '{prof_name}': {e}")
            # Fall through to config fallback if profile fails
            
    # Fallback to config.yaml manual fields if profile is not provided or fails
    if config.snowflake_url and config.snowflake_pat and config.snowflake_user:
        account = config.snowflake_url.replace(".snowflakecomputing.com", "")
        return snowflake.connector.connect(
            account=account,
            user=config.snowflake_user,
            token=config.snowflake_pat,
            authenticator="programmatic_access_token"
        )
    
    raise ValueError(f"No valid Snowflake connection profile found for '{prof_name}' and fallback credentials missing.")

def get_root(profile: Optional[str] = None) -> Any:
    """Gets a Snowflake core SDK Root object"""
    if Root is None:
        raise ImportError("snowflake.core is not installed. Run: pip install snowflake")
    
    conn = get_connection(profile)
    return Root(conn)

def test_connection(profile: Optional[str] = None) -> Dict[str, str]:
    """Tests the connection and returns account info"""
    try:
        ctx = get_connection(profile)
        cs = ctx.cursor()
        cs.execute("SELECT current_account(), current_user(), current_role(), current_warehouse(), current_version()")
        row = cs.fetchone()
        
        result = {
            "account": row[0],
            "user": row[1],
            "role": row[2],
            "warehouse": row[3],
            "version": row[4],
            "status": "success"
        }
        cs.close()
        ctx.close()
        return result
    except Exception as e:
        return {"status": "error", "error": str(e)}
