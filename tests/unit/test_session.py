from snowninja.session import SessionManager

def test_session_defaults():
    """Fresh session has empty task_list, requirements, interview_mode=False."""
    session = SessionManager()
    assert session.task_list == ""
    assert session.requirements == ""
    assert session.interview_mode is False
    assert session.interview_turn_count == 0

def test_session_not_configured_without_nim_key(monkeypatch):
    """is_configured=False when nvidia_pat is empty."""
    # Create an empty config file mock in the session module where it's used
    monkeypatch.setattr("snowninja.session.load_config", lambda: type('obj', (object,), {
        'nvidia_pat': '', 
        'snowflake_profile': '', 
        'snowflake_pat': ''
    })())
    
    session = SessionManager()
    assert session.is_configured is False
    
    # Change config and reload
    monkeypatch.setattr("snowninja.session.load_config", lambda: type('obj', (object,), {
        'nvidia_pat': 'some_pat', 
        'snowflake_profile': 'default', 
        'snowflake_pat': ''
    })())
    session.reload_config()
    assert session.is_configured is True

def test_reset_interview():
    """reset_interview clears mode and turn count, preserves task_list."""
    session = SessionManager()
    session.interview_mode = True
    session.interview_turn_count = 5
    session.task_list = "- [ ] Task 1"
    
    session.reset_interview()
    
    assert session.interview_mode is False
    assert session.interview_turn_count == 0
    assert session.task_list == "- [ ] Task 1"
