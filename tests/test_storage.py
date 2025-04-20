"""Tests for scopemate storage module"""
import os
import tempfile
import json
import pytest

from scopemate.models import ScopeMateTask, Purpose, Scope, Outcome, Meta, get_utc_now
from scopemate.storage import save_plan, load_plan, save_checkpoint, checkpoint_exists, delete_checkpoint


@pytest.fixture
def sample_task():
    """Create a sample task for testing storage functions"""
    now = get_utc_now()
    return ScopeMateTask(
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
            created=now,
            updated=now,
            due_date=None,
            confidence="medium"
        ),
        parent_id=None
    )


def test_save_and_load_plan(sample_task):
    """Test saving and loading a plan to/from a file"""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp:
        temp_path = temp.name
    
    try:
        # Save the task to the temporary file
        save_plan([sample_task], temp_path)
        
        # Verify the file exists and has content
        assert os.path.exists(temp_path)
        file_size = os.path.getsize(temp_path)
        assert file_size > 0
        
        # Load the plan and verify the task was loaded correctly
        loaded_tasks = load_plan(temp_path)
        assert len(loaded_tasks) == 1
        loaded_task = loaded_tasks[0]
        assert loaded_task.id == sample_task.id
        assert loaded_task.title == sample_task.title
        assert loaded_task.purpose.detailed_description == sample_task.purpose.detailed_description
        assert loaded_task.scope.size == sample_task.scope.size
        assert loaded_task.outcome.type == sample_task.outcome.type
        assert loaded_task.meta.status == sample_task.meta.status
        
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_save_and_load_multiple_tasks(sample_task):
    """Test saving and loading multiple tasks"""
    # Create a second task (child of the sample task)
    now = get_utc_now()
    child_task = ScopeMateTask(
        id="TEST-456",
        title="Child Task",
        purpose=Purpose(
            detailed_description="Child purpose",
            alignment=[],
            urgency="strategic"
        ),
        scope=Scope(
            size="trivial",
            time_estimate="hours",
            dependencies=[],
            risks=[]
        ),
        outcome=Outcome(
            type="customer-facing",
            detailed_outcome_definition="Child outcome",
            acceptance_criteria=[],
            metric=None,
            validation_method=None
        ),
        meta=Meta(
            status="backlog",
            priority=None,
            created=now,
            updated=now,
            due_date=None,
            confidence="high"
        ),
        parent_id=sample_task.id
    )
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp:
        temp_path = temp.name
    
    try:
        # Save both tasks to the temporary file
        tasks = [sample_task, child_task]
        save_plan(tasks, temp_path)
        
        # Load the plan and verify both tasks were loaded correctly
        loaded_tasks = load_plan(temp_path)
        assert len(loaded_tasks) == 2
        
        # Verify parent-child relationship is preserved
        parent_task = next((t for t in loaded_tasks if t.id == sample_task.id), None)
        child = next((t for t in loaded_tasks if t.id == child_task.id), None)
        assert parent_task is not None
        assert child is not None
        assert child.parent_id == parent_task.id
        
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_checkpoint_functions(sample_task, monkeypatch):
    """Test checkpoint saving, checking, and deletion"""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set the current working directory to the temp directory so files are created there
        original_dir = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Use the default checkpoint name that the code will actually use
            checkpoint_file = ".scopemate_checkpoint.json"
            
            # Directly write to this file to verify we can detect it
            with open(checkpoint_file, 'w') as f:
                f.write('{"test": true}')
            
            # Verify checkpoint exists now (since we created it directly)
            assert os.path.exists(checkpoint_file)
            assert checkpoint_exists()
            
            # Delete the checkpoint
            delete_checkpoint()
            
            # Verify checkpoint no longer exists
            assert not os.path.exists(checkpoint_file)
            assert not checkpoint_exists()
            
            # Now test save_checkpoint
            save_checkpoint([sample_task])
            
            # Verify checkpoint now exists
            assert os.path.exists(checkpoint_file)
            
            # Verify checkpoint content
            with open(checkpoint_file, 'r') as f:
                data = json.load(f)
                assert "tasks" in data
                assert len(data["tasks"]) == 1
                assert data["tasks"][0]["id"] == sample_task.id
        finally:
            # Restore the original directory
            os.chdir(original_dir)


def test_load_plan_nonexistent_file():
    """Test loading from a nonexistent file raises appropriate exception"""
    with pytest.raises(FileNotFoundError):
        load_plan("nonexistent_file.json")


def test_load_plan_handles_invalid_json():
    """Test loading invalid JSON data"""
    # Create a temporary file with invalid JSON
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp:
        temp.write(b'{"tasks": [{"id": "TEST-123", "invalid": true}]}')
        temp_path = temp.name
    
    try:
        # Should not raise an exception but skip the invalid task
        loaded_tasks = load_plan(temp_path)
        assert len(loaded_tasks) == 0
        
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path) 