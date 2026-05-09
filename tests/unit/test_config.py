from snowninja.core.config import SnowNinjaConfig, load_config, save_config

def test_config_defaults():
    """SnowNinjaConfig has sane defaults."""
    config = SnowNinjaConfig()
    assert config.nvidia_pat == ""
    assert config.snowflake_profile == ""
    assert config.planner_model == "meta/llama-4-maverick-17b-128e-instruct"
    assert config.implementer_model == "qwen/qwen3-coder-480b-a35b-instruct"

def test_config_roundtrip(tmp_path, monkeypatch):
    """save_config → load_config roundtrip preserves all fields."""
    test_config_dir = tmp_path / ".snowninja"
    test_config_file = test_config_dir / "config.yaml"
    monkeypatch.setattr("snowninja.core.config.CONFIG_DIR", test_config_dir)
    monkeypatch.setattr("snowninja.core.config.CONFIG_FILE", test_config_file)
    
    config = SnowNinjaConfig(
        nvidia_pat="test_pat",
        snowflake_profile="test_profile",
        planner_model="test_planner",
        implementer_model="test_implementer"
    )
    save_config(config)
    
    loaded = load_config()
    assert loaded.nvidia_pat == "test_pat"
    assert loaded.snowflake_profile == "test_profile"
    assert loaded.planner_model == "test_planner"
    assert loaded.implementer_model == "test_implementer"

def test_config_missing_file_returns_defaults(tmp_path, monkeypatch):
    """Missing config.yaml returns defaults, not crash."""
    test_config_file = tmp_path / "nonexistent.yaml"
    monkeypatch.setattr("snowninja.core.config.CONFIG_FILE", test_config_file)
    
    loaded = load_config()
    assert loaded.nvidia_pat == ""
    assert loaded.planner_model == "meta/llama-4-maverick-17b-128e-instruct"

def test_snowflake_profile_default():
    """Default snowflake_profile is empty string."""
    config = SnowNinjaConfig()
    assert config.snowflake_profile == ""
