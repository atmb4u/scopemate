"""Test configuration for ScopeMate tests"""
import os
import tempfile
import pytest
from unittest.mock import patch

from scopemate.models import ScopeMateTask, Purpose, Scope, Outcome, Meta, get_utc_now


@pytest.fixture
def basic_task():
    """Create a basic task for testing"""
    now = get_utc_now()
    return ScopeMateTask(
        id="TASK-test",
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


@pytest.fixture
def complex_task():
    """Create a complex task for testing"""
    now = get_utc_now()
    return ScopeMateTask(
        id="TASK-complex",
        title="Complex Task",
        purpose=Purpose(
            detailed_description="Complex purpose with multiple paragraphs.\n\nThis is a second paragraph.",
            alignment=["Strategic goal 1", "Strategic goal 2"],
            urgency="mission-critical"
        ),
        scope=Scope(
            size="complex",
            time_estimate="sprint",
            dependencies=["Dependency 1", "Dependency 2"],
            risks=["Risk 1", "Risk 2", "Risk 3"]
        ),
        outcome=Outcome(
            type="business-metric",
            detailed_outcome_definition="Complex outcome with details",
            acceptance_criteria=["Criterion 1", "Criterion 2"],
            metric="Business KPI",
            validation_method="Dashboard metrics"
        ),
        meta=Meta(
            status="in-progress",
            priority=1,
            created=now,
            updated=now,
            due_date=now,
            confidence="high",
            team="Backend"
        ),
        parent_id=None
    )


@pytest.fixture
def task_hierarchy():
    """Create a task hierarchy (parent with multiple children) for testing"""
    now = get_utc_now()
    
    # Create parent
    parent = ScopeMateTask(
        id="TASK-parent",
        title="Parent Task",
        purpose=Purpose(
            detailed_description="Parent purpose",
            alignment=["Strategic goal"],
            urgency="strategic"
        ),
        scope=Scope(
            size="complex",
            time_estimate="sprint",
            dependencies=[],
            risks=["Parent risk"]
        ),
        outcome=Outcome(
            type="customer-facing",
            detailed_outcome_definition="Parent outcome",
            acceptance_criteria=["Parent criterion"],
            metric=None,
            validation_method=None
        ),
        meta=Meta(
            status="backlog",
            priority=None,
            created=now,
            updated=now,
            due_date=None,
            confidence="medium",
            team="Backend"
        ),
        parent_id=None
    )
    
    # Create first child
    child1 = ScopeMateTask(
        id="TASK-child1",
        title="Child Task 1",
        purpose=Purpose(
            detailed_description="Child 1 purpose",
            alignment=["Strategic goal"],
            urgency="strategic"
        ),
        scope=Scope(
            size="straightforward",
            time_estimate="days",
            dependencies=["Parent task"],
            risks=["Child 1 risk"]
        ),
        outcome=Outcome(
            type="customer-facing",
            detailed_outcome_definition="Child 1 outcome",
            acceptance_criteria=["Child 1 criterion"],
            metric=None,
            validation_method=None
        ),
        meta=Meta(
            status="backlog",
            priority=None,
            created=now,
            updated=now,
            due_date=None,
            confidence="high",
            team="Frontend"
        ),
        parent_id=parent.id
    )
    
    # Create second child
    child2 = ScopeMateTask(
        id="TASK-child2",
        title="Child Task 2",
        purpose=Purpose(
            detailed_description="Child 2 purpose",
            alignment=["Strategic goal"],
            urgency="strategic"
        ),
        scope=Scope(
            size="trivial",
            time_estimate="hours",
            dependencies=["Parent task", "Child 1 task"],
            risks=["Child 2 risk"]
        ),
        outcome=Outcome(
            type="customer-facing",
            detailed_outcome_definition="Child 2 outcome",
            acceptance_criteria=["Child 2 criterion"],
            metric=None,
            validation_method=None
        ),
        meta=Meta(
            status="backlog",
            priority=None,
            created=now,
            updated=now,
            due_date=None,
            confidence="high",
            team="Backend"
        ),
        parent_id=parent.id
    )
    
    return [parent, child1, child2]


@pytest.fixture
def temp_file():
    """Create a temporary file that gets cleaned up after the test"""
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp_path = temp.name
    
    yield temp_path
    
    # Clean up
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_openai_api():
    """Mock OpenAI API calls for testing without actual API usage"""
    with patch('openai.OpenAI') as mock_openai:
        # Create mock client and response objects
        mock_client = mock_openai.return_value
        mock_response = mock_client.chat.completions.create.return_value
        mock_choice = mock_response.choices[0]
        mock_message = mock_choice.message
        
        # Default response content
        mock_message.content = '{"response": "test response"}'
        
        yield mock_client
        

@pytest.fixture
def disable_input_output(monkeypatch):
    """Disable input and output functions for testing CLI components"""
    # Mock input function
    monkeypatch.setattr('builtins.input', lambda prompt: '')
    
    # Mock print function
    monkeypatch.setattr('builtins.print', lambda *args, **kwargs: None) 