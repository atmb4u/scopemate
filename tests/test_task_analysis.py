"""Tests for ScopeMate task_analysis module"""
import pytest

from scopemate.models import ScopeMateTask, Purpose, Scope, Outcome, Meta, get_utc_now
from scopemate.task_analysis import (
    check_and_update_parent_estimates,
    find_long_duration_leaf_tasks,
    should_decompose_task,
    is_leaf_task,
    get_task_depth
)


@pytest.fixture
def sample_tasks():
    """Create a sample task hierarchy for testing task analysis functions"""
    now = get_utc_now()
    
    # Create a parent task
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
    
    # Create a child task
    child1 = ScopeMateTask(
        id="TASK-child1",
        title="Child Task 1",
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
        parent_id=parent.id
    )
    
    # Create another child task
    child2 = ScopeMateTask(
        id="TASK-child2",
        title="Child Task 2",
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
        parent_id=parent.id
    )
    
    # Create a standalone task
    standalone = ScopeMateTask(
        id="TASK-standalone",
        title="Standalone Task",
        purpose=Purpose(
            detailed_description="Standalone purpose",
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
            detailed_outcome_definition="Standalone outcome",
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
        parent_id=None
    )
    
    return [parent, child1, child2, standalone]


def test_check_and_update_parent_estimates():
    """Test updating parent estimates based on child complexity"""
    now = get_utc_now()
    
    # Create a parent with straightforward/days estimates
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
    
    # Create a child with complex/sprint estimates (more complex than parent)
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
    
    # Run the function to update parent estimates
    updated_tasks = check_and_update_parent_estimates([parent, child])
    
    # Find the updated parent
    updated_parent = next((t for t in updated_tasks if t.id == parent.id), None)
    assert updated_parent is not None
    
    # Verify parent estimates were updated to match child complexity
    assert updated_parent.scope.size == "complex"
    assert updated_parent.scope.time_estimate == "sprint"


def test_find_long_duration_leaf_tasks(sample_tasks):
    """Test finding leaf tasks with long durations"""
    # Create a new task with long duration
    now = get_utc_now()
    long_task = ScopeMateTask(
        id="TASK-long",
        title="Long Duration Task",
        purpose=Purpose(
            detailed_description="Long purpose",
            alignment=[],
            urgency="strategic"
        ),
        scope=Scope(
            size="straightforward",
            time_estimate="sprint",  # Long duration
            dependencies=[],
            risks=[]
        ),
        outcome=Outcome(
            type="customer-facing",
            detailed_outcome_definition="Long outcome",
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
    
    # Add the long task to our sample tasks
    all_tasks = sample_tasks + [long_task]
    
    # Find long duration leaf tasks
    long_leaf_tasks = find_long_duration_leaf_tasks(all_tasks)
    
    # The standalone task from sample_tasks and our new long_task should be found
    assert len(long_leaf_tasks) == 2
    task_ids = [task.id for task in long_leaf_tasks]
    assert "TASK-long" in task_ids
    assert "TASK-standalone" in task_ids
    
    # The parent from sample_tasks is not a leaf task, so it shouldn't be included
    assert "TASK-parent" not in task_ids


def test_should_decompose_task(sample_tasks):
    """Test the should_decompose_task function"""
    # Get the standalone task (complex/sprint) from sample_tasks
    standalone = next((t for t in sample_tasks if t.id == "TASK-standalone"), None)
    assert standalone is not None
    
    # Task with complex size should be decomposed
    assert should_decompose_task(standalone, depth=0, max_depth=3, is_leaf=True)
    
    # Parent task (straightforward/days) shouldn't be decomposed by default
    parent = next((t for t in sample_tasks if t.id == "TASK-parent"), None)
    assert parent is not None
    assert not should_decompose_task(parent, depth=0, max_depth=3, is_leaf=False)
    
    # Even simple tasks should be decomposed if at depth 0 and max_depth is high
    child = next((t for t in sample_tasks if t.id == "TASK-child1"), None)
    assert child is not None
    # This is false because it's trivial/hours, not complex or long duration
    assert not should_decompose_task(child, depth=0, max_depth=3, is_leaf=True)
    
    # Task at max depth shouldn't be decomposed regardless of complexity
    assert not should_decompose_task(standalone, depth=3, max_depth=3, is_leaf=True)


def test_is_leaf_task(sample_tasks):
    """Test the is_leaf_task function"""
    # Parent should not be a leaf task
    parent_id = "TASK-parent"
    assert not is_leaf_task(parent_id, sample_tasks)
    
    # Children should be leaf tasks
    child1_id = "TASK-child1"
    assert is_leaf_task(child1_id, sample_tasks)
    
    # Standalone should be a leaf task
    standalone_id = "TASK-standalone"
    assert is_leaf_task(standalone_id, sample_tasks)
    
    # Non-existent task should be considered a leaf task
    assert is_leaf_task("NONEXISTENT", sample_tasks)


def test_get_task_depth(sample_tasks):
    """Test the get_task_depth function"""
    # Create a task_depths dictionary
    task_depths = {}
    
    # Get tasks from sample_tasks
    parent = next((t for t in sample_tasks if t.id == "TASK-parent"), None)
    child1 = next((t for t in sample_tasks if t.id == "TASK-child1"), None)
    standalone = next((t for t in sample_tasks if t.id == "TASK-standalone"), None)
    
    assert parent is not None
    assert child1 is not None
    assert standalone is not None
    
    # Test depth calculations
    assert get_task_depth(parent, task_depths, sample_tasks) == 0
    assert get_task_depth(child1, task_depths, sample_tasks) == 1
    assert get_task_depth(standalone, task_depths, sample_tasks) == 0
    
    # Create a grandchild task
    now = get_utc_now()
    grandchild = ScopeMateTask(
        id="TASK-grandchild",
        title="Grandchild Task",
        purpose=Purpose(
            detailed_description="Grandchild purpose",
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
            confidence="high"
        ),
        parent_id=child1.id
    )
    
    # Add grandchild to tasks
    extended_tasks = sample_tasks + [grandchild]
    
    # Test depth calculation for grandchild
    assert get_task_depth(grandchild, task_depths, extended_tasks) == 2 