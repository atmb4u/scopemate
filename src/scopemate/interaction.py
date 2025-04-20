#!/usr/bin/env python3
"""
scopemate Interaction - Functions for user interaction

This module handles all interactive aspects of scopemate, including
collecting user input and displaying information.
"""
from typing import List, Optional, Dict, Any

from .models import (
    ScopeMateTask, Purpose, Scope, Outcome, Meta,
    get_utc_now, VALID_URGENCY_TYPES, VALID_OUTCOME_TYPES,
    VALID_SIZE_TYPES, VALID_TIME_ESTIMATES, VALID_CONFIDENCE_LEVELS,
    VALID_TEAMS
)

# -------------------------------
# User Input Functions
# -------------------------------
def prompt_user(
    prompt: str, 
    default: Optional[str] = None, 
    choices: Optional[List[str]] = None
) -> str:
    """
    Prompt user for input with optional default and choices validation.
    
    Args:
        prompt: The prompt text to display
        default: Optional default value if user enters nothing
        choices: Optional list of valid choices
        
    Returns:
        User's validated input as a string
    """
    while True:
        suffix = f" [{default}]" if default is not None else ""
        resp = input(f"{prompt}{suffix}: ").strip()
        
        if not resp and default is not None:
            resp = default
            
        if choices:
            low = resp.lower()
            if low not in [c.lower() for c in choices]:
                print(f"Please choose from {choices}.")
                continue
                
        if resp:
            return resp
        
        # If we get here with an empty response and no default, loop again


def generate_concise_title(parent_title: str, subtask_title: str) -> str:
    """
    Generate a concise subtask title without repeating the parent title.
    
    Args:
        parent_title: The title of the parent task
        subtask_title: The proposed title for the subtask
        
    Returns:
        A concise title for the subtask
    """
    # If subtask title already contains parent title, extract the unique part
    if parent_title and parent_title.lower() in subtask_title.lower():
        # Try to find the part after the parent title
        suffix = subtask_title[subtask_title.lower().find(parent_title.lower()) + len(parent_title):].strip()
        if suffix:
            # Remove any leading separators like "-" or ":"
            return suffix.lstrip(" -:").strip()
    
    # If parent title isn't in subtask or couldn't extract suffix, use the subtask title directly
    return subtask_title


def build_custom_subtask(parent_task: ScopeMateTask) -> ScopeMateTask:
    """
    Interactively gather information to create a custom subtask.
    
    Args:
        parent_task: The parent ScopeMateTask
        
    Returns:
        A new ScopeMateTask object as a subtask of the parent
    """
    # This is a simplified version - the full version should include all the prompts
    # from the original code in core.py
    
    import uuid
    
    print(f"\n=== Creating Custom Subtask for: {parent_task.title} ===")
    
    title = prompt_user("Give a short TITLE for this subtask")
    title = generate_concise_title(parent_task.title, title)
    
    summary = prompt_user("What is the primary PURPOSE of this subtask?")
    outcome_def = prompt_user("Define the desired OUTCOME")
    
    # Ask for team assignment
    print("\nTEAM options:")
    print("- Product: Product management team")
    print("- Design: Design and user experience team")
    print("- Frontend: Frontend development team")
    print("- Backend: Backend development team")
    print("- ML: Machine learning team")
    print("- Infra: Infrastructure and DevOps team")
    print("- Testing: QA and testing team")
    print("- Other: Any other team")
    team = prompt_user(
        "TEAM responsible", 
        default=parent_task.meta.team, 
        choices=VALID_TEAMS
    )
    
    # Create the subtask with sensible defaults inheriting from parent
    subtask = ScopeMateTask(
        id=f"TASK-{uuid.uuid4().hex[:6]}",
        title=title,
        purpose=Purpose(
            detailed_description=summary, 
            alignment=parent_task.purpose.alignment.copy(), 
            urgency=parent_task.purpose.urgency
        ),
        scope=Scope(
            size="straightforward", 
            time_estimate="days", 
            dependencies=[], 
            risks=[]
        ),
        outcome=Outcome(
            type=parent_task.outcome.type,
            detailed_outcome_definition=outcome_def,
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
            confidence="medium",
            team=team
        ),
        parent_id=parent_task.id
    )
    
    return subtask


def build_root_task() -> ScopeMateTask:
    """
    Interactively gather information to create a new root task.
    
    Returns:
        A new ScopeMateTask object
    """
    # This is a simplified version - the full version should include all the prompts
    # from the original code in core.py
    
    import uuid
    from .llm import estimate_scope
    
    print("=== scopemate Action Plan Builder ===")
    
    title = prompt_user("Give a short TITLE for this task")
    summary = prompt_user("What is the primary PURPOSE of this task?")
    outcome_def = prompt_user("Define the desired OUTCOME")
    
    # Ask for team assignment
    print("\nTEAM options:")
    print("- Product: Product management team")
    print("- Design: Design and user experience team")
    print("- Frontend: Frontend development team")
    print("- Backend: Backend development team")
    print("- ML: Machine learning team")
    print("- Infra: Infrastructure and DevOps team")
    print("- Testing: QA and testing team")
    print("- Other: Any other team")
    team = prompt_user(
        "TEAM responsible", 
        default="Product", 
        choices=VALID_TEAMS
    )
    
    # Create root task with sensible defaults
    root = ScopeMateTask(
        id=f"TASK-{uuid.uuid4().hex[:6]}",
        title=title,
        purpose=Purpose(
            detailed_description=summary, 
            alignment=[], 
            urgency="strategic"
        ),
        scope=Scope(
            size="straightforward", 
            time_estimate="week", 
            dependencies=[], 
            risks=[]
        ),
        outcome=Outcome(
            type="customer-facing",
            detailed_outcome_definition=outcome_def,
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
            confidence="medium",
            team=team
        )
    )
    
    # Use LLM to estimate scope
    root.scope = estimate_scope(root)
    return root


def print_summary(tasks: List[ScopeMateTask]) -> None:
    """
    Print a hierarchical summary of tasks with complexity indicators and statistics.
    
    Args:
        tasks: List of ScopeMateTask objects to summarize
    """
    print("\n=== Task Summary ===")
    
    # Build hierarchy maps
    task_map = {t.id: t for t in tasks}
    children_map = {}
    
    for t in tasks:
        if t.parent_id:
            if t.parent_id not in children_map:
                children_map[t.parent_id] = []
            children_map[t.parent_id].append(t.id)
    
    # Find root tasks (those without parents or with unknown parents)
    root_tasks = [t.id for t in tasks if not t.parent_id or t.parent_id not in task_map]
    
    # Print the hierarchy starting from root tasks
    for root_id in root_tasks:
        _print_task_hierarchy(root_id, task_map, children_map)
        
    # Print some statistics about task complexity
    complex_count = sum(1 for t in tasks if t.scope.size in ["complex", "uncertain", "pioneering"])
    long_tasks = sum(1 for t in tasks if t.scope.time_estimate in ["sprint", "multi-sprint"])
    leaf_tasks = sum(1 for t_id in task_map if t_id not in children_map)
    
    print("\n=== Task Statistics ===")
    print(f"Total tasks: {len(tasks)}")
    print(f"Leaf tasks (no subtasks): {leaf_tasks}")
    print(f"Complex+ tasks: {complex_count} ({(complex_count/len(tasks))*100:.1f}%)")
    print(f"Sprint+ duration tasks: {long_tasks} ({(long_tasks/len(tasks))*100:.1f}%)")


def _print_task_hierarchy(
    task_id: str, 
    task_map: Dict[str, ScopeMateTask], 
    children_map: Dict[str, List[str]], 
    level: int = 0
) -> None:
    """
    Recursively print a task and its children with hierarchical indentation.
    
    Args:
        task_id: ID of the task to print
        task_map: Dictionary mapping task IDs to tasks
        children_map: Dictionary mapping task IDs to lists of child IDs
        level: Current indentation level
    """
    if task_id not in task_map:
        return
        
    t = task_map[task_id]
    indent = "  " * level
    
    print(f"{indent}{'└─' if level > 0 else ''} [{t.id}] {t.title}")
    print(f"{indent}   Scope: {t.scope.size} | Est: {t.scope.time_estimate} | Team: {t.meta.team or 'Not assigned'}")
    
    # Print children recursively
    if task_id in children_map:
        for child_id in children_map[task_id]:
            _print_task_hierarchy(child_id, task_map, children_map, level + 1) 