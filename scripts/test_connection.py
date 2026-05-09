import yaml
from pathlib import Path
import snowflake.connector

CONFIG_FILE = Path.home() / ".snowninja" / "config.yaml"

def load_config():
    with open(CONFIG_FILE) as f:
        return yaml.safe_load(f)

def test_connection():
    cfg = load_config()
    account = cfg["snowflake_url"].replace(".snowflakecomputing.com", "")
    user = cfg["snowflake_user"]
    pat = cfg["snowflake_pat"]

    print(f"Account : {account}")
    print(f"User    : {user}")
    print("Connecting...")

    ctx = snowflake.connector.connect(
        account=account,
        user=user,
        token=pat,
        authenticator="programmatic_access_token",
    )

    cs = ctx.cursor()
    cs.execute("SELECT current_user(), current_role(), current_warehouse(), current_version()")
    row = cs.fetchone()
    print("\n✅ Connected!")
    print(f"   User      : {row[0]}")
    print(f"   Role      : {row[1]}")
    print(f"   Warehouse : {row[2]}")
    print(f"   Version   : {row[3]}")
    cs.close()
    ctx.close()

if __name__ == "__main__":
    test_connection()
