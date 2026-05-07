import re

def check_query_safety(sql: str) -> bool:
    """
    Evaluates a SQL query for safety violations.
    Returns True if the query is safe, False if it violates a policy.
    
    Current Policies:
    - Prevent accidental DROP DATABASE.
    - Prevent CREATE WAREHOUSE without appropriate tags (placeholder check).
    """
    sql_upper = sql.upper()
    
    # Policy 1: Prevent DROP DATABASE
    if re.search(r'\bDROP\s+DATABASE\b', sql_upper):
        return False
        
    # Policy 2: Prevent CREATE WAREHOUSE without TAG
    if re.search(r'\bCREATE\s+(?:OR\s+REPLACE\s+)?WAREHOUSE\b', sql_upper):
        if 'TAG' not in sql_upper and 'WITH TAG' not in sql_upper:
            # We enforce that warehouses must be tagged for cost governance
            return False
            
    # Policy 3: Prevent DROP ACCOUNT
    if re.search(r'\bDROP\s+ACCOUNT\b', sql_upper):
        return False

    return True
