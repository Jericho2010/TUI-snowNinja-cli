import pytest
from snowninja.session import SessionManager

def test_session_defaults():
    """Fresh session has empty task_list, requirements, interview_mode=False."""
    session = SessionManager()
    assert session.task_list == []
    assert session.requirements == []
    assert session.interview_mode is False
    assert session.interview_turn_count == 0

def test_session_not_configured_without_nim_key(monkeypatch):
    """is_configured=False when nvidia_pat is empty."""
    session = SessionManager()
    session.config.nvidia_pat = ""
    assert session.is_configured is False
    
    session.config.nvidia_pat = "some_pat"
    assert session.is_configured is True

def test_reset_interview():
    """reset_interview clears mode and turn count, preserves task_list."""
    session = SessionManager()
    session.interview_mode = True
    session.interview_turn_count = 5
    session.task_list = [{"id": "1", "title": "Task 1", "description": "Desc", "status": "pending", "assigned_role": "planner"}]
    
    session.reset_interview()
    
    assert session.interview_mode is False
    assert session.interview_turn_count == 0
    assert len(session.task_list) == 1
