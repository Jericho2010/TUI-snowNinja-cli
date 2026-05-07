import os
from pathlib import Path

def create_dbt_project(project_name: str, target_dir: str = "."):
    """Creates a basic dbt-snowflake project structure."""
    base_path = Path(target_dir) / project_name
    base_path.mkdir(parents=True, exist_ok=True)
    
    (base_path / "models").mkdir(exist_ok=True)
    (base_path / "macros").mkdir(exist_ok=True)
    (base_path / "tests").mkdir(exist_ok=True)
    (base_path / "seeds").mkdir(exist_ok=True)
    
    dbt_project_yml = f"""
name: '{project_name}'
version: '1.0.0'
config-version: 2
profile: '{project_name}'

models:
  {project_name}:
    +materialized: view
"""
    (base_path / "dbt_project.yml").write_text(dbt_project_yml.strip())
    
    profiles_yml = f"""
{project_name}:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: <account_identifier>
      user: <username>
      password: <password>
      role: <role>
      database: <database>
      warehouse: <warehouse>
      schema: <schema>
      threads: 4
"""
    (base_path / "profiles.yml").write_text(profiles_yml.strip())
    return str(base_path)

def create_streamlit_app(app_name: str, target_dir: str = "."):
    """Creates a basic Streamlit in Snowflake app structure."""
    base_path = Path(target_dir) / app_name
    base_path.mkdir(parents=True, exist_ok=True)
    
    app_py = """
import streamlit as st
from snowflake.snowpark.context import get_active_session

st.title("Streamlit in Snowflake App")
st.write("Hello from SnowNinja!")

# Get the current credentials
session = get_active_session()

# Execute a simple query
df = session.sql("SELECT CURRENT_USER(), CURRENT_ROLE()").to_pandas()
st.dataframe(df)
"""
    (base_path / "app.py").write_text(app_py.strip())
    
    environment_yml = """
name: sf_env
channels:
  - snowflake
dependencies:
  - python=3.10
  - streamlit
  - snowflake-snowpark-python
"""
    (base_path / "environment.yml").write_text(environment_yml.strip())
    return str(base_path)

def create_snowpark_project(project_name: str, target_dir: str = "."):
    """Creates a basic Snowpark project structure for UDFs/UDTFs."""
    base_path = Path(target_dir) / project_name
    base_path.mkdir(parents=True, exist_ok=True)
    
    (base_path / "src").mkdir(exist_ok=True)
    (base_path / "tests").mkdir(exist_ok=True)
    
    udf_py = """
import sys

def hello_udf(name: str) -> str:
    return f"Hello {name} from Snowpark! Running Python {sys.version}"
"""
    (base_path / "src" / "udfs.py").write_text(udf_py.strip())
    
    requirements_txt = """
snowflake-snowpark-python
pytest
"""
    (base_path / "requirements.txt").write_text(requirements_txt.strip())
    return str(base_path)
