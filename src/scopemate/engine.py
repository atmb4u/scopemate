#!/usr/bin/env python3
"""
ScopeMate Engine - Main application logic for ScopeMate

This module contains the TaskEngine class which coordinates all the functionality
of ScopeMate, handling the workflow for creating, breaking down, and saving tasks.
"""
import os
from typing import List, Optional, Dict, Any

from .models import ScopeMateTask
from .storage import (
    save_checkpoint, save_plan, load_plan, 
    checkpoint_exists, delete_checkpoint, CHECKPOINT_FILE
)
from .task_analysis import (
    check_and_update_parent_estimates, find_long_duration_leaf_tasks,
    should_decompose_task, _initialize_task_depths,
    get_task_depth, is_leaf_task
)
from .breakdown import suggest_breakdown
from .interaction import prompt_user, build_root_task, print_summary


class TaskEngine:
    """
    Main engine for ScopeMate that coordinates task creation, breakdown, and management.
    """
    
    def __init__(self):
        """Initialize the TaskEngine."""
        self.tasks: List[ScopeMateTask] = []
        self.task_depths: Dict[str, int] = {}
        self.max_depth: int = 5  # Maximum depth of task hierarchy
        
    def load_from_checkpoint(self) -> bool:
        """
        Load tasks from checkpoint file if it exists.
        
        Returns:
            True if checkpoint was loaded, False otherwise
        """
        if checkpoint_exists():
            resume = prompt_user(
                f"Found checkpoint '{CHECKPOINT_FILE}'. Resume?", 
                default="y", 
                choices=["y","n"]
            )
            if resume.lower() == "y":
                self.tasks = load_plan(CHECKPOINT_FILE)
                return True
            else:
                delete_checkpoint()
        
        return False
    
    def load_from_file(self, default_filename: str = "scopemate_plan.json") -> bool:
        """
        Load tasks from a user-specified file.
        
        Args:
            default_filename: Default filename to suggest
            
        Returns:
            True if file was loaded, False otherwise
        """
        choice = prompt_user("Load existing plan?", default="n", choices=["y","n"])
        if choice.lower() == "y":
            fname = prompt_user("Enter filename to load", default=default_filename)
            try:
                self.tasks = load_plan(fname)
                return True
            except FileNotFoundError:
                print(f"File not found: {fname}")
        
        return False
    
    def create_new_task(self) -> None:
        """Create a new root task interactively."""
        self.tasks.append(build_root_task())
        save_checkpoint(self.tasks)
    
    def breakdown_complex_tasks(self) -> None:
        """Process all tasks and break down complex ones."""
        # Initialize depth tracking
        self.task_depths = _initialize_task_depths(self.tasks)
        
        # Maintain a list of tasks to process (for recursive handling)
        tasks_to_process = list(self.tasks)
        
        # Process tasks with checkpointing
        while tasks_to_process:
            # Get the next task to process
            current_task = tasks_to_process.pop(0)
            
            # Calculate depth for this task if not already tracked
            current_depth = get_task_depth(current_task, self.task_depths, self.tasks)
            
            # Check if this task is a leaf (has no children)
            is_leaf = is_leaf_task(current_task.id, self.tasks)
            
            # Only decompose if criteria met
            if should_decompose_task(current_task, current_depth, self.max_depth, is_leaf):
                print(f"\nDecomposing task {current_task.id} at depth {current_depth}...")
                print(f"  Size: {current_task.scope.size}, Time: {current_task.scope.time_estimate}")
                
                # Get subtask breakdown from LLM with user interaction
                subtasks = suggest_breakdown(current_task)
                
                if subtasks:
                    # Set depth for new subtasks
                    for sub in subtasks:
                        self.task_depths[sub.id] = current_depth + 1
                        
                    # Add subtasks to the task list
                    self.tasks.extend(subtasks)
                    
                    # Add the newly created subtasks to the processing queue
                    tasks_to_process.extend(subtasks)
                    
                    save_checkpoint(self.tasks)
                    
                    print(f"Created {len(subtasks)} subtasks for {current_task.id}")
                    
                    # Check and update parent estimates if needed
                    self.tasks = check_and_update_parent_estimates(self.tasks)
                    save_checkpoint(self.tasks)
    
    def handle_long_duration_tasks(self) -> None:
        """Find and handle long duration leaf tasks."""
        # Find long duration leaf tasks
        long_duration_leaf_tasks = find_long_duration_leaf_tasks(self.tasks)
        
        if long_duration_leaf_tasks:
            print("\n=== Found Long-Duration Leaf Tasks ===")
            print("These tasks have long durations but no subtasks:")
            
            for i, task in enumerate(long_duration_leaf_tasks):
                print(f"{i+1}. [{task.id}] {task.title} - {task.scope.time_estimate}")
            
            print("\nDo you want to break down any of these tasks?")
            choice = prompt_user("Enter task numbers to break down (comma-separated) or 'n' to skip", default="n")
            
            if choice.lower() != "n":
                try:
                    # Parse the choices
                    selected_indices = [int(idx.strip()) - 1 for idx in choice.split(",")]
                    for idx in selected_indices:
                        if 0 <= idx < len(long_duration_leaf_tasks):
                            task_to_breakdown = long_duration_leaf_tasks[idx]
                            print(f"\nBreaking down: [{task_to_breakdown.id}] {task_to_breakdown.title}")
                            
                            # Get subtask suggestions
                            suggested_subtasks = suggest_breakdown(task_to_breakdown)
                            
                            if suggested_subtasks:
                                # Set depth for new subtasks
                                for sub in suggested_subtasks:
                                    if task_to_breakdown.id in self.task_depths:
                                        self.task_depths[sub.id] = self.task_depths[task_to_breakdown.id] + 1
                                    else:
                                        self.task_depths[sub.id] = 1
                                    
                                self.tasks.extend(suggested_subtasks)
                                save_checkpoint(self.tasks)
                                print(f"Created {len(suggested_subtasks)} subtasks for {task_to_breakdown.id}")
                                
                                # Check and update parent estimates
                                self.tasks = check_and_update_parent_estimates(self.tasks)
                                save_checkpoint(self.tasks)
                except ValueError:
                    print("Invalid selection, skipping breakdown.")
    
    def finalize_plan(self) -> None:
        """Review and save the final plan."""
        # Final check of parent-child estimate consistency
        self.tasks = check_and_update_parent_estimates(self.tasks)
        
        # Review and final save
        print_summary(self.tasks)
        proceed = prompt_user("Save final plan?", default="y", choices=["y","n"])
        if proceed.lower() == 'y':
            fname = prompt_user("Save plan to file", default="scopemate_plan.json")
            save_plan(self.tasks, fname)
            delete_checkpoint()
        else:
            print(f"Plan left in checkpoint '{CHECKPOINT_FILE}'. Run again to resume.")
    
    def run(self) -> None:
        """Run the full interactive workflow."""
        # Display introduction
        print("=== ScopeMate Action Plan Builder ===")
        print("This tool helps break down complex tasks and maintain consistent time estimates.")
        print("Now with interactive task breakdown - choose from alternative approaches and customize subtasks!")
        print("Note: Parent tasks will be automatically adjusted if child tasks take longer.\n")
        
        # Try to load existing checkpoint
        if not self.load_from_checkpoint():
            # If no checkpoint, try loading from file or create new
            if not self.load_from_file():
                self.create_new_task()
        
        # Process the tasks
        self.breakdown_complex_tasks()
        
        # Check for leaf tasks with long durations
        self.handle_long_duration_tasks()
        
        # Finalize the plan
        self.finalize_plan()


def interactive_builder():
    """
    Legacy function for backward compatibility that runs the TaskEngine.
    """
    engine = TaskEngine()
    try:
        engine.run()
    except KeyboardInterrupt:
        print("\nOperation cancelled. Progress saved in checkpoint.")
        save_checkpoint(engine.tasks) 