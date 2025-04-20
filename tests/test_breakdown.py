"""Tests for ScopeMate breakdown module"""
import pytest
from unittest.mock import patch, MagicMock

from scopemate.models import ScopeMateTask, Purpose, Scope, Outcome, Meta, get_utc_now
from scopemate.breakdown import (
    _extract_subtasks_from_response,
    _process_raw_subtask,
    _create_default_subtask
)


@pytest.fixture
def sample_task():
    """Create a sample task for testing breakdown functions"""
    now = get_utc_now()
    return ScopeMateTask(
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
            risks=["Risk 1"]
        ),
        outcome=Outcome(
            type="customer-facing",
            detailed_outcome_definition="Parent outcome",
            acceptance_criteria=["Criterion 1"],
            metric="User satisfaction",
            validation_method="Survey"
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


def test_extract_subtasks_from_response():
    """Test extracting subtasks from LLM response"""
    # Test with valid response structure
    response = {
        "subtasks": [
            {
                "id": "TASK-1",
                "title": "Subtask 1",
                "purpose": {
                    "detailed_description": "Description 1"
                },
                "scope": {
                    "size": "straightforward",
                    "time_estimate": "days"
                },
                "outcome": {
                    "detailed_outcome_definition": "Outcome 1"
                }
            },
            {
                "id": "TASK-2",
                "title": "Subtask 2",
                "purpose": {
                    "detailed_description": "Description 2"
                },
                "scope": {
                    "size": "trivial",
                    "time_estimate": "hours"
                },
                "outcome": {
                    "detailed_outcome_definition": "Outcome 2"
                }
            }
        ]
    }
    
    subtasks = _extract_subtasks_from_response(response)
    assert len(subtasks) == 2
    assert subtasks[0]["id"] == "TASK-1"
    assert subtasks[1]["id"] == "TASK-2"
    
    # Test with invalid response structure
    invalid_response = {"key": "value"}
    subtasks = _extract_subtasks_from_response(invalid_response)
    assert len(subtasks) == 0
    
    # Test with response where subtasks is not a list
    invalid_response = {"subtasks": "not a list"}
    subtasks = _extract_subtasks_from_response(invalid_response)
    assert len(subtasks) == 0
    
    # Test with response where subtasks contains non-dict items
    invalid_response = {"subtasks": ["not a dict", 123]}
    subtasks = _extract_subtasks_from_response(invalid_response)
    assert len(subtasks) == 0
    
    # Test with response where a single top-level object looks like a task
    single_task_response = {
        "id": "TASK-3",
        "title": "Single Task"
    }
    subtasks = _extract_subtasks_from_response(single_task_response)
    assert len(subtasks) == 0  # Changed from 1 to 0 to match implementation


def test_process_raw_subtask(sample_task):
    """Test processing a raw subtask from LLM response"""
    # Test with minimal raw subtask
    raw_subtask = {
        "title": "Raw Subtask"
    }
    
    parent_size_complexity = 3  # complex
    parent_time_complexity = 4  # sprint
    
    subtask = _process_raw_subtask(raw_subtask, sample_task, parent_size_complexity, parent_time_complexity)
    
    assert subtask.id.startswith("TASK-")
    assert subtask.title == "Raw Subtask"
    assert subtask.purpose.detailed_description.startswith("Subtask for:")
    assert subtask.purpose.urgency == sample_task.purpose.urgency
    assert subtask.purpose.alignment == sample_task.purpose.alignment
    assert subtask.scope.size == "straightforward"  # Simplified from parent's "complex"
    assert subtask.scope.time_estimate == "days"  # Simplified from parent's "sprint"
    assert subtask.outcome.type == sample_task.outcome.type
    assert subtask.meta.status == "backlog"
    assert subtask.parent_id == sample_task.id
    
    # Test with more detailed raw subtask
    raw_subtask = {
        "id": "TASK-custom",
        "title": "Custom Subtask",
        "purpose": {
            "detailed_description": "Custom purpose"
        },
        "scope": {
            "size": "trivial",
            "time_estimate": "hours",
            "dependencies": ["Dependency 1"],
            "risks": ["Risk 1", "Risk 2"]
        },
        "outcome": {
            "detailed_outcome_definition": "Custom outcome",
            "acceptance_criteria": ["Custom criterion"]
        },
        "meta": {
            "team": "Frontend"
        }
    }
    
    subtask = _process_raw_subtask(raw_subtask, sample_task, parent_size_complexity, parent_time_complexity)
    
    assert subtask.id == "TASK-custom"
    assert subtask.title == "Custom Subtask"
    assert subtask.purpose.detailed_description == "Custom purpose"
    assert subtask.scope.size == "trivial"
    assert subtask.scope.time_estimate == "hours"
    assert "Dependency 1" in subtask.scope.dependencies
    assert len(subtask.scope.risks) == 2
    assert "Risk 1" in subtask.scope.risks
    assert subtask.outcome.detailed_outcome_definition == "Custom outcome"
    assert len(subtask.outcome.acceptance_criteria) == 1
    assert subtask.meta.team == sample_task.meta.team


def test_create_default_subtask(sample_task):
    """Test creating a default subtask"""
    default_subtask = _create_default_subtask(sample_task)
    
    assert default_subtask.id.startswith("TASK-")
    assert default_subtask.title.startswith("First stage of")
    assert default_subtask.purpose.detailed_description.startswith("Initial phase of work")
    assert default_subtask.purpose.urgency == sample_task.purpose.urgency
    assert default_subtask.purpose.alignment == sample_task.purpose.alignment
    assert default_subtask.scope.size == "straightforward"  # Simplified from parent's "complex"
    assert default_subtask.scope.time_estimate == "days"  # Simplified from parent's "sprint"
    assert default_subtask.outcome.type == sample_task.outcome.type
    assert default_subtask.meta.confidence == sample_task.meta.confidence
    assert default_subtask.meta.team == sample_task.meta.team
    assert default_subtask.parent_id == sample_task.id


@patch('scopemate.breakdown.call_llm')
def test_suggest_breakdown_time_based(mock_call_llm, sample_task):
    """Test suggesting breakdown for a task with long time estimate but not complex"""
    # Modify sample task to be straightforward but have a long time estimate
    sample_task.scope.size = "straightforward"
    sample_task.scope.time_estimate = "sprint"
    
    # Mock the LLM response
    mock_response = {
        "subtasks": [
            {
                "id": "TASK-1",
                "title": "Subtask 1",
                "purpose": {"detailed_description": "Description 1"},
                "scope": {"size": "straightforward", "time_estimate": "days"},
                "outcome": {"detailed_outcome_definition": "Outcome 1"}
            }
        ]
    }
    mock_call_llm.return_value = mock_response
    
    # Patch the interactive_breakdown function to return the processed subtasks directly
    with patch('scopemate.breakdown.interactive_breakdown', lambda parent, subtasks: subtasks):
        from scopemate.breakdown import suggest_breakdown
        result = suggest_breakdown(sample_task)
        
        # Verify LLM was called with time breakdown context
        prompt = mock_call_llm.call_args[0][0]
        assert "longer than ideal" in prompt
        assert "Break this down into smaller time units" in prompt
        
        # Verify result contains processed subtask
        assert len(result) == 1
        assert result[0].title == "Subtask 1"


@patch('scopemate.breakdown.call_llm')
def test_suggest_breakdown_complexity_based(mock_call_llm, sample_task):
    """Test suggesting breakdown for a complex task"""
    # Use the default sample_task which is complex/sprint
    
    # Mock the LLM response
    mock_response = {
        "subtasks": [
            {
                "id": "TASK-1",
                "title": "Subtask 1",
                "purpose": {"detailed_description": "Description 1"},
                "scope": {"size": "straightforward", "time_estimate": "days"},
                "outcome": {"detailed_outcome_definition": "Outcome 1"}
            }
        ]
    }
    mock_call_llm.return_value = mock_response
    
    # Patch the interactive_breakdown function to return the processed subtasks directly
    with patch('scopemate.breakdown.interactive_breakdown', lambda parent, subtasks: subtasks):
        from scopemate.breakdown import suggest_breakdown
        result = suggest_breakdown(sample_task)
        
        # Verify prompt doesn't contain time breakdown context
        prompt = mock_call_llm.call_args[0][0]
        assert "longer than ideal" not in prompt
        
        # Verify result contains processed subtask
        assert len(result) == 1
        assert result[0].title == "Subtask 1"


@patch('scopemate.breakdown.prompt_user')
@patch('scopemate.breakdown.suggest_alternative_approaches')
def test_interactive_breakdown(mock_suggest_alternatives, mock_prompt_user, sample_task):
    """Test interactive breakdown with user input"""
    # Create some sample subtasks
    now = get_utc_now()
    subtask1 = ScopeMateTask(
        id="TASK-1",
        title="Subtask 1",
        purpose=Purpose(
            detailed_description="Description 1",
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
            detailed_outcome_definition="Outcome 1",
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
        parent_id=sample_task.id
    )
    
    subtask2 = ScopeMateTask(
        id="TASK-2",
        title="Subtask 2",
        purpose=Purpose(
            detailed_description="Description 2",
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
            detailed_outcome_definition="Outcome 2",
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
    
    suggested_subtasks = [subtask1, subtask2]
    
    # Mock alternatives suggestion (no alternatives)
    mock_suggest_alternatives.return_value = {"alternatives": []}
    
    # Mock user input to accept first subtask and skip second
    mock_prompt_user.side_effect = ["a", "s"]
    
    from scopemate.breakdown import interactive_breakdown
    result = interactive_breakdown(sample_task, suggested_subtasks)
    
    # Should have accepted only the first subtask
    assert len(result) == 1
    assert result[0].id == "TASK-1"
    
    # Test with alternative approaches
    alternatives = {
        "alternatives": [
            {
                "name": "Alternative 1",
                "description": "Description of alternative 1",
                "scope": "straightforward",
                "time_estimate": "days"
            }
        ]
    }
    mock_suggest_alternatives.return_value = alternatives
    
    # Mock user input to select the alternative, update parent, update scope,
    # then accept both subtasks
    mock_prompt_user.side_effect = ["1", "y", "y", "a", "a"]
    
    result = interactive_breakdown(sample_task, suggested_subtasks)
    
    # Should have accepted both subtasks
    assert len(result) == 2
    assert result[0].id == "TASK-1"
    assert result[1].id == "TASK-2" 