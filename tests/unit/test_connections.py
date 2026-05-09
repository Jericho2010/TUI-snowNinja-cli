from snowninja.core.connections import list_profiles

def test_list_profiles_parses_toml(tmp_path, monkeypatch):
    """Fake connections.toml with 2 profiles → list_profiles returns both names."""
    test_toml = tmp_path / "connections.toml"
    test_toml.write_text("[default]\naccount = 'acc1'\n[dev]\naccount = 'acc2'\n")
    monkeypatch.setattr("snowninja.core.connections.CONNECTIONS_FILE", test_toml)
    
    profiles = list_profiles()
    assert sorted(profiles) == ["default", "dev"]

def test_list_profiles_missing_file(tmp_path, monkeypatch):
    """Missing connections.toml → empty list, no crash."""
    test_toml = tmp_path / "nonexistent.toml"
    monkeypatch.setattr("snowninja.core.connections.CONNECTIONS_FILE", test_toml)
    
    profiles = list_profiles()
    assert profiles == []

def test_list_profiles_malformed_toml(tmp_path, monkeypatch):
    """Malformed TOML → empty list with warning, no crash."""
    test_toml = tmp_path / "connections.toml"
    test_toml.write_text("invalid [ toml")
    monkeypatch.setattr("snowninja.core.connections.CONNECTIONS_FILE", test_toml)
    
    profiles = list_profiles()
    assert profiles == []
