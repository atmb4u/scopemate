"""Tests for platform compatibility"""
import os
import sys
import platform
import tempfile

from scopemate.storage import save_plan, load_plan
from scopemate.models import ScopeMateTask, Purpose, Scope, Outcome, Meta, get_utc_now


def test_file_paths():
    """Test file path handling is cross-platform compatible"""
    # Create a temporary file with platform-specific path
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp:
        temp_path = temp.name
    
    try:
        # Create a simple task
        task = ScopeMateTask(
            id="TEST-123",
            title="Test Task",
            purpose=Purpose(
                detailed_description="Test purpose",
                alignment=[],
                urgency="strategic"
            ),
            scope=Scope(
                size="straightforward",
                time_estimate="days",
                dependencies=[],
                risks=[]
            ),
            outcome=Outcome(
                type="customer-facing",
                detailed_outcome_definition="Test outcome",
                acceptance_criteria=[],
                metric=None,
                validation_method=None
            ),
            meta=Meta(
                status="backlog",
                priority=None,
                created=get_utc_now(),
                updated=get_utc_now(),
                due_date=None,
                confidence="medium"
            ),
            parent_id=None
        )
        
        # Save and load the task
        save_plan([task], temp_path)
        loaded_tasks = load_plan(temp_path)
        
        # Verify task was loaded correctly
        assert len(loaded_tasks) == 1
        assert loaded_tasks[0].id == "TEST-123"
        assert loaded_tasks[0].title == "Test Task"
    
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_platform_info():
    """Output platform info for debugging"""
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"System: {platform.system()}")
    print(f"Machine: {platform.machine()}")
    assert True  # Always passes, just for info 