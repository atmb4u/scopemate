#!/usr/bin/env python3
"""
scopemate Engine - Main application logic for scopemate

This module contains the TaskEngine class which coordinates all the functionality
of scopemate, handling the workflow for creating, breaking down, and saving tasks.
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
    Main engine for scopemate that coordinates task creation, breakdown, and management.
    
    The TaskEngine is the central coordinator of the scopemate application, managing the entire
    lifecycle of tasks from creation to breakdown to final output. It handles loading and saving
    task data, organizing the task hierarchy, and orchestrating the breakdown of complex tasks
    into simpler subtasks.
    
    Attributes:
        tasks (List[ScopeMateTask]): List of all tasks in the current session
        task_depths (Dict[str, int]): Mapping of task IDs to their depth in the hierarchy
        max_depth (int): Maximum allowed depth for task nesting (default: 5)
    """
    
    def __init__(self):
        """
        Initialize the TaskEngine with empty task list and depth tracking.
        
        Creates a new TaskEngine instance with an empty task list and depth tracking dictionary.
        Sets the default maximum depth for task hierarchies to 5 levels.
        """
        self.tasks: List[ScopeMateTask] = []
        self.task_depths: Dict[str, int] = {}
        self.max_depth: int = 5  # Maximum depth of task hierarchy
        
    def load_from_checkpoint(self) -> bool:
        """
        Load tasks from checkpoint file if it exists.
        
        Checks for the existence of a checkpoint file and prompts the user about whether
        to resume from this checkpoint. If the user confirms, loads the tasks from the
        checkpoint file into the engine.
        
        Returns:
            bool: True if checkpoint was loaded successfully, False otherwise
            
        Example:
            ```python
            engine = TaskEngine()
            if engine.load_from_checkpoint():
                print(f"Loaded {len(engine.tasks)} tasks from checkpoint")
            else:
                print("Starting with a new task list")
            ```
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
        
        Prompts the user about whether to load an existing plan. If confirmed,
        asks for the filename and attempts to load tasks from that file.
        
        Args:
            default_filename (str): Default filename to suggest to the user
            
        Returns:
            bool: True if file was loaded successfully, False otherwise
            
        Raises:
            FileNotFoundError: Handled internally, prints error message if file not found
            
        Example:
            ```python
            engine = TaskEngine()
            if engine.load_from_file("my_project_plan.json"):
                print(f"Loaded {len(engine.tasks)} tasks from file")
            ```
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
        """
        Create a new root task interactively.
        
        Initiates an interactive dialog to build a new root task, adds it to the task list,
        and automatically saves a checkpoint. The dialog collects all necessary information
        for a well-defined task including title, purpose, scope, and expected outcomes.
        
        Side Effects:
            - Appends new task to self.tasks
            - Saves checkpoint to disk
            
        Example:
            ```python
            engine = TaskEngine()
            engine.create_new_task()  # Interactively creates a new root task
            ```
        """
        self.tasks.append(build_root_task())
        save_checkpoint(self.tasks)
    
    def breakdown_complex_tasks(self) -> None:
        """
        Process all tasks and break down complex ones.
        
        This is a core function that analyzes all tasks to identify those that are too complex 
        or have long durations, then interactively breaks them down into smaller subtasks.
        It maintains the task hierarchy, updates parent-child relationships, and ensures
        estimate consistency across the task tree.
        
        The function uses a breadth-first approach to process tasks, breaking down parent tasks
        before their children, and saving checkpoints after each breakdown.
        
        Algorithm:
            1. Initialize task depths to track hierarchy
            2. Process each task and check if it needs breakdown
            3. For tasks needing breakdown, use LLM to suggest subtasks
            4. Add approved subtasks to the task list
            5. Update parent estimates based on subtask characteristics
            6. Save checkpoint after each task breakdown
            
        Side Effects:
            - Modifies self.tasks by adding subtasks
            - Updates self.task_depths with new depth information
            - Saves checkpoints to disk after each breakdown
            
        Example:
            ```python
            engine = TaskEngine()
            engine.load_from_file("my_project.json")
            engine.breakdown_complex_tasks()  # Interactively breaks down complex tasks
            ```
        """
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
        """
        Find and handle long duration leaf tasks.
        
        Identifies leaf tasks (tasks with no children) that have long duration estimates,
        presents them to the user, and offers the opportunity to break them down further.
        This helps ensure that all tasks in the final plan are of manageable size.
        
        The function uses task_analysis.find_long_duration_leaf_tasks to identify candidates
        for further breakdown, then interactively processes user-selected tasks.
        
        Side Effects:
            - May modify self.tasks by adding subtasks for long-duration leaf tasks
            - Updates parent estimates via check_and_update_parent_estimates
            - Saves checkpoints to disk after each breakdown
            
        Example:
            ```python
            engine = TaskEngine()
            engine.load_from_file("my_project.json")
            engine.handle_long_duration_tasks()  # Interactively processes long-duration tasks
            ```
        """
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
        """
        Review and save the final plan.
        
        Performs a final consistency check on all task estimates, displays a summary
        of the entire task hierarchy to the user, and prompts for saving the finalized
        plan to a permanent file. If saved, removes the temporary checkpoint file.
        
        Side Effects:
            - Ensures consistency in parent-child estimate relationships
            - Saves final plan to user-specified file
            - May delete checkpoint file if plan is saved
            
        Example:
            ```python
            engine = TaskEngine()
            engine.load_from_file("my_project.json")
            engine.breakdown_complex_tasks()
            engine.handle_long_duration_tasks()
            engine.finalize_plan()  # Review and save final plan
            ```
        """
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
        """
        Run the full interactive workflow.
        
        Executes the complete scopemate workflow from start to finish:
        1. Displays introduction to the user
        2. Loads existing checkpoint or creates new task
        3. Processes and breaks down complex tasks
        4. Handles long-duration leaf tasks
        5. Finalizes and saves the plan
        
        This is the main entry point for using the TaskEngine to build a complete
        task breakdown plan interactively.
        
        Side Effects:
            - Interacts with the user via console
            - Modifies task list based on user input
            - Creates/updates files on disk for checkpoints and final plan
            
        Example:
            ```python
            engine = TaskEngine()
            engine.run()  # Runs the complete interactive workflow
            ```
        """
        # Display introduction
        print("=== scopemate Action Plan Builder ===")
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

    def run_interactive(self) -> None:
        """
        Run the interactive mode of the application.
        
        This is a placeholder method for running an alternative interactive mode.
        Currently just prints the header and would be extended in future versions.
        
        Example:
            ```python
            engine = TaskEngine()
            engine.run_interactive()  # Would run an alternative interactive mode
            ```
        """
        print("=== scopemate Action Plan Builder ===")


def interactive_builder():
    """
    Legacy function for backward compatibility that runs the TaskEngine.
    
    Creates a TaskEngine instance and runs the full workflow, handling
    KeyboardInterrupt exceptions by saving progress to a checkpoint.
    
    This function provides backward compatibility with older versions
    that used this entry point directly.
    
    Side Effects:
        - Creates and runs a TaskEngine instance
        - Handles KeyboardInterrupt by saving checkpoint
        
    Example:
        ```python
        from scopemate.engine import interactive_builder
        interactive_builder()  # Runs the complete workflow
        ```
    """
    engine = TaskEngine()
    try:
        engine.run()
    except KeyboardInterrupt:
        print("\nOperation cancelled. Progress saved in checkpoint.")
        save_checkpoint(engine.tasks) 