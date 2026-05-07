import pytest
import os
from pathlib import Path
from snowninja.scaffold.engine import create_dbt_project, create_streamlit_app, create_snowpark_project

def test_scaffold_dbt(tmp_path):
    """Creates files (dbt_project.yml, profiles.yml)."""
    project_dir = create_dbt_project("my_dbt_proj", target_dir=str(tmp_path))
    
    assert os.path.exists(project_dir)
    assert os.path.exists(os.path.join(project_dir, "dbt_project.yml"))
    assert os.path.exists(os.path.join(project_dir, "profiles.yml"))
    assert os.path.exists(os.path.join(project_dir, "models"))
    
    content = Path(os.path.join(project_dir, "dbt_project.yml")).read_text()
    assert "name: 'my_dbt_proj'" in content

def test_scaffold_streamlit(tmp_path):
    """Creates files (app.py, environment.yml)."""
    project_dir = create_streamlit_app("my_st_app", target_dir=str(tmp_path))
    
    assert os.path.exists(project_dir)
    assert os.path.exists(os.path.join(project_dir, "app.py"))
    assert os.path.exists(os.path.join(project_dir, "environment.yml"))
    
    content = Path(os.path.join(project_dir, "app.py")).read_text()
    assert "import streamlit as st" in content
    assert "get_active_session" in content

def test_scaffold_snowpark(tmp_path):
    """Creates files (src/udfs.py, requirements.txt)."""
    project_dir = create_snowpark_project("my_snowpark", target_dir=str(tmp_path))
    
    assert os.path.exists(project_dir)
    assert os.path.exists(os.path.join(project_dir, "src", "udfs.py"))
    assert os.path.exists(os.path.join(project_dir, "requirements.txt"))
    
    content = Path(os.path.join(project_dir, "src", "udfs.py")).read_text()
    assert "def hello_udf" in content
