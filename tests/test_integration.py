"""Integration tests for scopemate"""
import os
import tempfile
import pytest
from unittest.mock import patch

from scopemate.models import ScopeMateTask, Purpose, Scope, Outcome, Meta, get_utc_now
from scopemate.storage import save_plan, load_plan
from scopemate.task_analysis import check_and_update_parent_estimates
from scopemate.cli import create_task_from_args, process_task_with_breakdown


@pytest.fixture
def mock_llm_responses():
    """Create a patch for the LLM functions to return predictable responses"""
    with patch('scopemate.llm.call_llm') as mock_call_llm:
        # Define standard responses for different LLM calls
        
        # For estimate_scope
        def scope_response(*args, **kwargs):
            prompt = args[0]
            if "estimate its scope" in prompt:
                return {
                    "size": "complex",
                    "time_estimate": "sprint",
                    "dependencies": ["API integration"],
                    "risks": ["Technical complexity", "Integration challenges"]
                }
            return {}
        
        # For suggest_breakdown
        def breakdown_response(*args, **kwargs):
            prompt = args[0]
            if "breaking down a task into smaller" in prompt:
                return {
                    "subtasks": [
                        {
                            "id": "TASK-sub1",
                            "title": "First subtask",
                            "purpose": {
                                "detailed_description": "First subtask purpose"
                            },
                            "scope": {
                                "size": "straightforward",
                                "time_estimate": "days"
                            },
                            "outcome": {
                                "detailed_outcome_definition": "First subtask outcome"
                            },
                            "meta": {
                                "status": "backlog",
                                "team": "Backend"
                            }
                        },
                        {
                            "id": "TASK-sub2",
                            "title": "Second subtask",
                            "purpose": {
                                "detailed_description": "Second subtask purpose"
                            },
                            "scope": {
                                "size": "trivial",
                                "time_estimate": "hours"
                            },
                            "outcome": {
                                "detailed_outcome_definition": "Second subtask outcome"
                            },
                            "meta": {
                                "status": "backlog",
                                "team": "Frontend"
                            }
                        }
                    ]
                }
            return {}
        
        # For alternatives
        def alternatives_response(*args, **kwargs):
            prompt = args[0]
            if "ALTERNATIVE APPROACHES" in prompt:
                return {
                    "alternatives": []
                }
            return {}
        
        # Set the side effect based on the prompt
        mock_call_llm.side_effect = lambda prompt, model=None: (
            scope_response(prompt) if "estimate its scope" in prompt
            else breakdown_response(prompt) if "breaking down a task into smaller" in prompt
            else alternatives_response(prompt)
        )
        
        # Replace the fixture with a direct patch in the test
        yield mock_call_llm


@pytest.fixture
def temp_json_file():
    """Create a temporary JSON file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp:
        temp_path = temp.name
    
    yield temp_path
    
    # Clean up
    if os.path.exists(temp_path):
        os.unlink(temp_path)


def test_cli_end_to_end(temp_json_file):
    """Test the entire CLI workflow from creation to breakdown to saving"""
    # Create direct patches for both functions
    with patch('scopemate.cli.generate_title_from_purpose_outcome') as mock_title, \
         patch('scopemate.llm.call_llm') as mock_call_llm:
        
        # Set up mock responses
        mock_title.return_value = "Generated Task Title"
        
        # Mock LLM responses like in the fixture
        mock_call_llm.return_value = {
            "size": "complex",
            "time_estimate": "sprint",
            "dependencies": ["API integration"],
            "risks": ["Technical complexity", "Integration challenges"]
        }
        
        # Patch the interactive_breakdown function to return predictable subtasks
        with patch('scopemate.breakdown.interactive_breakdown') as mock_interactive:
            # Create sample subtasks to return
            now = get_utc_now()
            subtask1 = ScopeMateTask(
                id="TASK-sub1",
                title="First subtask",
                purpose=Purpose(
                    detailed_description="First subtask purpose",
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
                    detailed_outcome_definition="First subtask outcome",
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
                parent_id="parent-id"  # Will be replaced
            )
            
            subtask2 = ScopeMateTask(
                id="TASK-sub2",
                title="Second subtask",
                purpose=Purpose(
                    detailed_description="Second subtask purpose",
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
                    detailed_outcome_definition="Second subtask outcome",
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
                parent_id="parent-id"  # Will be replaced
            )
            
            # Function to update parent IDs and return subtasks
            def return_subtasks(parent, subtasks):
                for subtask in [subtask1, subtask2]:
                    subtask.parent_id = parent.id
                return [subtask1, subtask2]
                
            mock_interactive.side_effect = return_subtasks
            
            # Create a task from CLI arguments
            purpose = "Build a feature to improve user experience"
            outcome = "Users can complete tasks more efficiently"
            
            task = create_task_from_args(purpose, outcome)
            
            # Verify the task was created with the expected values
            assert task.title == "Generated Task Title"
            assert task.purpose.detailed_description == purpose
            assert task.outcome.detailed_outcome_definition == outcome
            assert task.scope.size == "complex"
            assert task.scope.time_estimate == "sprint"
            assert len(task.scope.dependencies) == 1
            assert len(task.scope.risks) == 2
            
            # Process the task to generate subtasks
            all_tasks = process_task_with_breakdown(task)
            
            # Verify the task breakdown
            assert len(all_tasks) == 3  # Parent + 2 subtasks
            assert all_tasks[0].id == task.id  # Parent task is first
            
            # Verify the parent-child relationships
            subtasks = [t for t in all_tasks if t.parent_id == task.id]
            assert len(subtasks) == 2
            assert subtasks[0].id == "TASK-sub1"
            assert subtasks[1].id == "TASK-sub2"
            
            # Save the plan to a file
            save_plan(all_tasks, temp_json_file)
            
            # Load the plan back
            loaded_tasks = load_plan(temp_json_file)
            
            # Verify the loaded tasks match the original tasks
            assert len(loaded_tasks) == len(all_tasks)
            loaded_ids = [t.id for t in loaded_tasks]
            original_ids = [t.id for t in all_tasks]
            assert set(loaded_ids) == set(original_ids)


def test_estimate_consistency(mock_llm_responses):
    """Test that child task complexity updates parent estimates"""
    # Create a parent with low complexity
    now = get_utc_now()
    parent = ScopeMateTask(
        id="TASK-parent",
        title="Parent Task",
        purpose=Purpose(
            detailed_description="Parent purpose",
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
            detailed_outcome_definition="Parent outcome",
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
    
    # Create a child with higher complexity
    child = ScopeMateTask(
        id="TASK-child",
        title="Child Task",
        purpose=Purpose(
            detailed_description="Child purpose",
            alignment=[],
            urgency="strategic"
        ),
        scope=Scope(
            size="complex",
            time_estimate="sprint",
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
        parent_id=parent.id
    )
    
    # Create a grandchild with even higher complexity
    grandchild = ScopeMateTask(
        id="TASK-grandchild",
        title="Grandchild Task",
        purpose=Purpose(
            detailed_description="Grandchild purpose",
            alignment=[],
            urgency="strategic"
        ),
        scope=Scope(
            size="pioneering",
            time_estimate="multi-sprint",
            dependencies=[],
            risks=[]
        ),
        outcome=Outcome(
            type="customer-facing",
            detailed_outcome_definition="Grandchild outcome",
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
            confidence="low"
        ),
        parent_id=child.id
    )
    
    # Check and update estimates for the entire hierarchy
    all_tasks = [parent, child, grandchild]
    updated_tasks = check_and_update_parent_estimates(all_tasks)
    
    # Get the updated tasks
    updated_parent = next((t for t in updated_tasks if t.id == parent.id), None)
    updated_child = next((t for t in updated_tasks if t.id == child.id), None)
    updated_grandchild = next((t for t in updated_tasks if t.id == grandchild.id), None)
    
    # Verify that parent and child complexity was updated to match descendants
    assert updated_parent.scope.size == "pioneering"
    assert updated_parent.scope.time_estimate == "multi-sprint"
    assert updated_child.scope.size == "pioneering"
    assert updated_child.scope.time_estimate == "multi-sprint"
    assert updated_grandchild.scope.size == "pioneering"  # Unchanged
    assert updated_grandchild.scope.time_estimate == "multi-sprint"  # Unchanged


def test_save_load_roundtrip(temp_json_file):
    """Test saving and loading a complex task hierarchy with various fields"""
    now = get_utc_now()
    
    # Create a parent task with all fields populated
    parent = ScopeMateTask(
        id="TASK-parent",
        title="Parent Task",
        purpose=Purpose(
            detailed_description="Parent purpose with multiple paragraphs.\n\nThis is the second paragraph.",
            alignment=["Strategic goal 1", "Strategic goal 2"],
            urgency="strategic"
        ),
        scope=Scope(
            size="complex",
            time_estimate="sprint",
            dependencies=["External API", "Database migration"],
            risks=["Technical risk", "Resource constraint"]
        ),
        outcome=Outcome(
            type="customer-facing",
            detailed_outcome_definition="Parent outcome with details",
            acceptance_criteria=["Criterion 1", "Criterion 2", "Criterion 3"],
            metric="Metric value",
            validation_method="Validation method"
        ),
        meta=Meta(
            status="in-progress",
            priority=1,
            created=now,
            updated=now,
            due_date=now,  # Use the same date for simplicity
            confidence="medium",
            team="Backend"
        ),
        parent_id=None
    )
    
    # Create children with various fields
    child1 = ScopeMateTask(
        id="TASK-child1",
        title="Child Task 1",
        purpose=Purpose(
            detailed_description="Child 1 purpose",
            alignment=["Strategic goal 1"],
            urgency="mission-critical"
        ),
        scope=Scope(
            size="straightforward",
            time_estimate="days",
            dependencies=["Parent task"],
            risks=["Integration risk"]
        ),
        outcome=Outcome(
            type="technical-debt",
            detailed_outcome_definition="Child 1 outcome",
            acceptance_criteria=["Child criterion 1"],
            metric=None,
            validation_method=None
        ),
        meta=Meta(
            status="backlog",
            priority=2,
            created=now,
            updated=now,
            due_date=None,
            confidence="high",
            team="Frontend"
        ),
        parent_id=parent.id
    )
    
    child2 = ScopeMateTask(
        id="TASK-child2",
        title="Child Task 2 with a much longer title that includes specific technical details",
        purpose=Purpose(
            detailed_description="Child 2 purpose with special characters: !@#$%^&*()",
            alignment=[],
            urgency="maintenance"
        ),
        scope=Scope(
            size="uncertain",
            time_estimate="week",
            dependencies=[],
            risks=[]
        ),
        outcome=Outcome(
            type="learning",
            detailed_outcome_definition="Child 2 outcome with unicode: 你好世界",
            acceptance_criteria=[],
            metric="Experimental metric",
            validation_method="Qualitative assessment"
        ),
        meta=Meta(
            status="review",
            priority=3,
            created=now,
            updated=now,
            due_date=now,
            confidence="low",
            team="ML"
        ),
        parent_id=parent.id
    )
    
    # Save the tasks to a file
    all_tasks = [parent, child1, child2]
    save_plan(all_tasks, temp_json_file)
    
    # Load the tasks back
    loaded_tasks = load_plan(temp_json_file)
    
    # Verify the correct number of tasks was loaded
    assert len(loaded_tasks) == len(all_tasks)
    
    # Find each loaded task
    loaded_parent = next((t for t in loaded_tasks if t.id == parent.id), None)
    loaded_child1 = next((t for t in loaded_tasks if t.id == child1.id), None)
    loaded_child2 = next((t for t in loaded_tasks if t.id == child2.id), None)
    
    # Verify all tasks were found
    assert loaded_parent is not None
    assert loaded_child1 is not None
    assert loaded_child2 is not None
    
    # Verify complex fields were preserved correctly
    assert loaded_parent.purpose.detailed_description == parent.purpose.detailed_description
    assert loaded_parent.purpose.alignment == parent.purpose.alignment
    assert loaded_parent.scope.dependencies == parent.scope.dependencies
    assert loaded_parent.scope.risks == parent.scope.risks
    assert loaded_parent.outcome.acceptance_criteria == parent.outcome.acceptance_criteria
    
    # Verify parent-child relationships
    assert loaded_child1.parent_id == parent.id
    assert loaded_child2.parent_id == parent.id
    
    # Verify special cases
    assert loaded_child2.purpose.detailed_description == child2.purpose.detailed_description  # Special chars
    assert loaded_child2.outcome.detailed_outcome_definition == child2.outcome.detailed_outcome_definition  # Unicode 