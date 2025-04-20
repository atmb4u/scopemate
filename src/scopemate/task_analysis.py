#!/usr/bin/env python3
"""
scopemate Task Analysis - Functions for analyzing and validating tasks

This module provides functions for analyzing task structures, validating
task relationships, and ensuring estimate consistency.
"""
from typing import List, Dict, Tuple, Optional, Set

from .models import (
    ScopeMateTask, SIZE_COMPLEXITY, TIME_COMPLEXITY, get_utc_now
)

def check_and_update_parent_estimates(tasks: List[ScopeMateTask]) -> List[ScopeMateTask]:
    """
    Check and update parent task estimates based on child task complexity.
    
    This function ensures consistency in the task hierarchy by making sure that 
    parent tasks have appropriate size and time estimates relative to their children.
    If a child task has a higher complexity or longer time estimate than its parent,
    the parent's estimates are automatically increased to maintain logical consistency.
    
    The function works by:
    1. Creating maps of task IDs to task objects and parent IDs
    2. Computing complexity values for all tasks based on their size and time estimates
    3. Identifying inconsistencies where child tasks have higher complexity than parents
    4. Updating parent estimates to match or exceed their children's complexity
    5. Recursively propagating updates up the task hierarchy to maintain consistency
    
    Args:
        tasks: List of ScopeMateTask objects to analyze and update
        
    Returns:
        Updated list of ScopeMateTask objects with consistent parent-child estimates
        
    Example:
        ```python
        # Before: parent task has "straightforward" size but child has "complex" size
        updated_tasks = check_and_update_parent_estimates(tasks)
        # After: parent task is updated to "complex" or higher to maintain consistency
        ```
    """
    # Create a map of tasks by ID for easy access
    task_map = {t.id: t for t in tasks}
    
    # Create a map of parent IDs for each task
    parent_map = {t.id: t.parent_id for t in tasks}
    
    # Map to track size and time complexity values
    size_complexity_map = {}
    time_complexity_map = {}
    
    # First pass: Calculate complexity values for all tasks
    for task in tasks:
        size_complexity_map[task.id] = SIZE_COMPLEXITY.get(task.scope.size, 3)
        time_complexity_map[task.id] = TIME_COMPLEXITY.get(task.scope.time_estimate, 4)
    
    # Second pass: Check for inconsistencies and update parent estimates
    inconsistencies_fixed = 0
    
    # Create a list of child tasks (tasks with parents)
    child_tasks = [t for t in tasks if t.parent_id]
    
    # Process child tasks to update parents
    for child in child_tasks:
        if not child.parent_id or child.parent_id not in task_map:
            continue
            
        parent = task_map[child.parent_id]
        parent_size_complexity = size_complexity_map[parent.id]
        parent_time_complexity = time_complexity_map[parent.id]
        child_size_complexity = size_complexity_map[child.id]
        child_time_complexity = time_complexity_map[child.id]
        
        # Check if child has higher complexity than parent
        size_inconsistent = child_size_complexity > parent_size_complexity
        time_inconsistent = child_time_complexity > parent_time_complexity
        
        if size_inconsistent or time_inconsistent:
            # Prepare update data
            parent_copy = parent.model_copy(deep=True)
            updated = False
            
            # Update size estimate if needed
            if size_inconsistent:
                # Find the corresponding size value
                for size_name, complexity in SIZE_COMPLEXITY.items():
                    if complexity >= child_size_complexity:
                        parent_copy.scope.size = size_name
                        updated = True
                        break
            
            # Update time estimate if needed
            if time_inconsistent:
                # Find the corresponding time value
                for time_name, complexity in TIME_COMPLEXITY.items():
                    if complexity >= child_time_complexity:
                        parent_copy.scope.time_estimate = time_name
                        updated = True
                        break
            
            # Apply updates if needed
            if updated:
                parent_copy.meta.updated = get_utc_now()
                task_map[parent.id] = parent_copy
                
                # Update the complexity maps
                size_complexity_map[parent.id] = SIZE_COMPLEXITY.get(parent_copy.scope.size, 3)
                time_complexity_map[parent.id] = TIME_COMPLEXITY.get(parent_copy.scope.time_estimate, 4)
                
                # Propagate changes to ancestors
                _update_ancestors(
                    parent.id, 
                    task_map, 
                    parent_map, 
                    update_size=size_inconsistent, 
                    update_time=time_inconsistent,
                    size_value=SIZE_COMPLEXITY.get(parent_copy.scope.size, 3), 
                    time_value=TIME_COMPLEXITY.get(parent_copy.scope.time_estimate, 4)
                )
                
                inconsistencies_fixed += 1
    
    # Return the updated task list
    updated_tasks = list(task_map.values())
    
    if inconsistencies_fixed > 0:
        print(f"✅ Fixed {inconsistencies_fixed} estimate inconsistencies")
    
    return updated_tasks


def _update_ancestors(
    task_id: str, 
    task_map: Dict[str, ScopeMateTask], 
    parent_map: Dict[str, str], 
    update_size: bool = False, 
    update_time: bool = False, 
    size_value: Optional[int] = None, 
    time_value: Optional[int] = None
) -> None:
    """
    Recursively update ancestors' estimates.
    
    Args:
        task_id: ID of the task whose parent should be updated
        task_map: Dictionary mapping task IDs to ScopeMateTask objects
        parent_map: Dictionary mapping task IDs to parent IDs
        update_size: Whether to update size estimate
        update_time: Whether to update time estimate
        size_value: Size complexity value to propagate
        time_value: Time complexity value to propagate
    """
    # Exit if we have nothing to update
    if not update_size and not update_time:
        return
        
    # Exit if no parent ID
    if task_id not in parent_map or not parent_map[task_id]:
        return
        
    # Get parent ID and task
    parent_id = parent_map[task_id]
    if parent_id not in task_map:
        return
        
    parent = task_map[parent_id]
    parent_copy = parent.model_copy(deep=True)
    updated = False
    
    # Update size estimate if needed
    if update_size and size_value is not None:
        parent_size_complexity = SIZE_COMPLEXITY.get(parent_copy.scope.size, 3)
        
        if size_value > parent_size_complexity:
            # Find the corresponding size value
            for size_name, complexity in SIZE_COMPLEXITY.items():
                if complexity >= size_value:
                    parent_copy.scope.size = size_name
                    updated = True
                    break
    
    # Update time estimate if needed
    if update_time and time_value is not None:
        parent_time_complexity = TIME_COMPLEXITY.get(parent_copy.scope.time_estimate, 4)
        
        if time_value > parent_time_complexity:
            # Find the corresponding time value
            for time_name, complexity in TIME_COMPLEXITY.items():
                if complexity >= time_value:
                    parent_copy.scope.time_estimate = time_name
                    updated = True
                    break
    
    # Apply updates if needed
    if updated:
        parent_copy.meta.updated = get_utc_now()
        task_map[parent_id] = parent_copy
        
        # Continue updating ancestors
        _update_ancestors(
            parent_id, 
            task_map, 
            parent_map, 
            update_size=update_size, 
            update_time=update_time,
            size_value=SIZE_COMPLEXITY.get(parent_copy.scope.size, 3) if update_size else None, 
            time_value=TIME_COMPLEXITY.get(parent_copy.scope.time_estimate, 4) if update_time else None
        )


def find_long_duration_leaf_tasks(tasks: List[ScopeMateTask]) -> List[ScopeMateTask]:
    """
    Find leaf tasks (tasks without children) that have long durations.
    
    Args:
        tasks: List of ScopeMateTask objects to analyze
        
    Returns:
        List of tasks with 'week', 'sprint' or 'multi-sprint' estimates that don't have subtasks,
        sorted with longest durations first.
    """
    # Build task hierarchy maps
    task_map = {t.id: t for t in tasks}
    has_children = set()
    
    for task in tasks:
        if task.parent_id and task.parent_id in task_map:
            has_children.add(task.parent_id)
    
    # Find leaf tasks with long durations
    long_durations = ["week", "sprint", "multi-sprint"]
    leaf_tasks_with_long_durations = []
    
    for task in tasks:
        if task.id not in has_children and task.scope.time_estimate in long_durations:
            leaf_tasks_with_long_durations.append(task)
    
    # Sort by duration (longest first)
    return sorted(
        leaf_tasks_with_long_durations, 
        key=lambda t: TIME_COMPLEXITY.get(t.scope.time_estimate, 3), 
        reverse=True
    )


def should_decompose_task(task: ScopeMateTask, depth: int, max_depth: int, is_leaf: bool = False) -> bool:
    """
    Determine if a task should be broken down based on complexity and time estimates.
    
    This function applies a set of heuristics to decide whether a task needs further
    decomposition. The decision is based on multiple factors:
    
    1. Task depth in the hierarchy - tasks at or beyond max_depth are never decomposed
    2. Task complexity - "complex", "uncertain", or "pioneering" tasks should be broken down
    3. Time estimate - tasks with long durations should be broken down into smaller units
    4. Leaf status - whether the task already has subtasks
    
    The breakdown logic implements a graduated approach where:
    - Very complex tasks are always broken down (unless at max depth)
    - Long duration tasks are broken down, especially if they're leaf tasks
    - Tasks with "week" duration are broken down up to max_depth
    - Tasks at depth 2+ with "sprint" duration aren't broken down (unless they're "multi-sprint")
    
    Args:
        task: The ScopeMateTask to evaluate
        depth: Current depth in the task hierarchy (0 for root tasks)
        max_depth: Maximum allowed depth for the task hierarchy
        is_leaf: Whether this task currently has no children
        
    Returns:
        True if the task should be broken down into subtasks, False otherwise
        
    Example:
        ```python
        task = get_task_by_id("TASK-123")
        depth = get_task_depth(task, task_depths, tasks)
        if should_decompose_task(task, depth, max_depth=5, is_leaf=True):
            subtasks = suggest_breakdown(task)
        ```
    """
    # Always respect max depth limit
    if depth >= max_depth:
        return False
    
    # Define complexity thresholds
    complex_sizes = ["complex", "uncertain", "pioneering"]
    long_durations = ["week", "sprint", "multi-sprint"]
    
    # Always break down complex tasks
    if task.scope.size in complex_sizes:
        return True
    
    # Also break down long-duration tasks, even if they're not "complex"
    if task.scope.time_estimate in long_durations:
        # For leaf tasks, always consider breaking down if they're long
        if is_leaf:
            return True
            
        # Break down tasks with "week" duration up to max_depth
        if task.scope.time_estimate == "week":
            return True
            
        # If it's already at depth 2+, only break down multi-sprint tasks
        if depth >= 2 and task.scope.time_estimate != "multi-sprint":
            return False
        return True
    
    return False


def _initialize_task_depths(tasks: List[ScopeMateTask]) -> Dict[str, int]:
    """
    Initialize the depth tracking dictionary for tasks.
    
    Args:
        tasks: List of ScopeMateTask objects
        
    Returns:
        Dictionary mapping task IDs to depth values
    """
    task_depths = {}
    parent_map = {t.id: t.parent_id for t in tasks}
    
    # Initialize depths for all tasks
    for task in tasks:
        if not task.parent_id:
            # Root tasks are at depth 0
            task_depths[task.id] = 0
    
    # Process tasks with parents
    for task in tasks:
        if task.id not in task_depths and task.parent_id:
            # Traverse up to find a task with known depth
            depth = 0
            current_id = task.id
            while current_id in parent_map and parent_map[current_id]:
                depth += 1
                current_id = parent_map[current_id]
                # If we found a parent with known depth, use that
                if current_id in task_depths:
                    task_depths[task.id] = task_depths[current_id] + depth
                    break
            
            # If we couldn't find a parent with known depth, assume depth 0 for the root
            if task.id not in task_depths:
                task_depths[task.id] = depth
                
    return task_depths


def get_task_depth(task: ScopeMateTask, task_depths: Dict[str, int], tasks: List[ScopeMateTask]) -> int:
    """
    Get the depth of a task in the hierarchy.
    
    Args:
        task: The ScopeMateTask to find depth for
        task_depths: Dictionary mapping task IDs to depths
        tasks: List of all ScopeMateTask objects
        
    Returns:
        The depth of the task
    """
    # If depth is already known, return it
    if task.id in task_depths:
        return task_depths[task.id]
        
    # If task has no parent, it's at root level (0)
    if not task.parent_id:
        task_depths[task.id] = 0
        return 0
        
    # Find the parent task
    parent = next((t for t in tasks if t.id == task.parent_id), None)
    if parent:
        # Get parent's depth (recursively if needed) and add 1
        parent_depth = get_task_depth(parent, task_depths, tasks)
        task_depths[task.id] = parent_depth + 1
        return parent_depth + 1
    
    # If parent not found, assume depth 0
    task_depths[task.id] = 0
    return 0


def is_leaf_task(task_id: str, tasks: List[ScopeMateTask]) -> bool:
    """
    Check if a task is a leaf task (has no children).
    
    Args:
        task_id: ID of the task to check
        tasks: List of all ScopeMateTask objects
        
    Returns:
        True if task has no children, False otherwise
    """
    # A task is a leaf if no other task has it as a parent
    return not any(t.parent_id == task_id for t in tasks) 