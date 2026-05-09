from snowninja.scaffold.engine import ScaffoldEngine

def test_scaffold_pipeline(tmp_path, monkeypatch):
    """Creates files (01_bronze.sql, 02_silver.sql)."""
    engine = ScaffoldEngine()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda *a, **k: "test_pipeline")
    
    engine.run("pipeline-project")
    
    project_dir = tmp_path / "test_pipeline"
    assert project_dir.exists()
    assert (project_dir / "src" / "01_bronze.sql").exists()
    assert (project_dir / "src" / "02_silver.sql").exists()
    assert (project_dir / "README.md").exists()
    
    content = (project_dir / "src" / "01_bronze.sql").read_text()
    assert "CREATE OR REPLACE DYNAMIC TABLE bronze_events" in content

def test_scaffold_app(tmp_path, monkeypatch):
    """Creates files (app.py, snowflake.yml)."""
    engine = ScaffoldEngine()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda *a, **k: "test_app")
    
    engine.run("app-project")
    
    project_dir = tmp_path / "test_app"
    assert project_dir.exists()
    assert (project_dir / "app.py").exists()
    assert (project_dir / "snowflake.yml").exists()
    
    content = (project_dir / "app.py").read_text()
    assert "import streamlit as st" in content
    assert "get_active_session" in content

def test_scaffold_cortex(tmp_path, monkeypatch):
    """Creates files (process_docs.sql)."""
    engine = ScaffoldEngine()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda *a, **k: "test_cortex")
    
    engine.run("cortex-project")
    
    project_dir = tmp_path / "test_cortex"
    assert project_dir.exists()
    assert (project_dir / "process_docs.sql").exists()
    
    content = (project_dir / "process_docs.sql").read_text()
    assert "SNOWFLAKE.CORTEX.SENTIMENT" in content

def test_scaffold_snowpark(tmp_path, monkeypatch):
    """Creates files (src/functions.py, snowflake.yml)."""
    engine = ScaffoldEngine()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda *a, **k: "test_snowpark")
    
    engine.run("snowpark-project")
    
    project_dir = tmp_path / "test_snowpark"
    assert project_dir.exists()
    assert (project_dir / "src" / "functions.py").exists()
    assert (project_dir / "snowflake.yml").exists()
    
    content = (project_dir / "src" / "functions.py").read_text()
    assert "def clean_text" in content
