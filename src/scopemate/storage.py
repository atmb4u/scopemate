#!/usr/bin/env python3
"""
scopemate Storage - Functions for saving and loading task data

This module manages persistence of task data to disk and loading from files.
"""
import os
import json
from typing import List, Dict, Any

from pydantic import ValidationError
from .models import ScopeMateTask

# -------------------------------
# Configuration
# -------------------------------
CHECKPOINT_FILE = ".scopemate_checkpoint.json"

# -------------------------------
# File Operations
# -------------------------------
def save_checkpoint(tasks: List[ScopeMateTask], filename: str = CHECKPOINT_FILE) -> None:
    """
    Save tasks to a checkpoint file for later resumption.
    
    Args:
        tasks: List of ScopeMateTask objects to save
        filename: Path to save the checkpoint file
    """
    payload = {"tasks": [t.model_dump() for t in tasks]}
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"[Checkpoint saved to {filename}]")


def save_plan(tasks: List[ScopeMateTask], filename: str) -> None:
    """
    Save tasks to a plan file.
    
    This function serializes a list of ScopeMateTask objects to JSON and writes them
    to a file. The file format uses a consistent structure with a top-level "tasks"
    array containing serialized task objects. This ensures compatibility with other
    tooling and future versions of scopemate.
    
    The function handles all serialization details including proper encoding and
    indentation for readability. Each task is completely serialized with all its
    nested structures (purpose, scope, outcome, meta) for complete persistence.
    
    Args:
        tasks: List of ScopeMateTask objects to save to disk
        filename: Path to save the plan file
        
    Side Effects:
        - Writes to file system at the specified path
        - Prints confirmation message upon successful save
        
    Example:
        ```python
        tasks = [task1, task2, task3]  # List of ScopeMateTask objects
        save_plan(tasks, "project_alpha_plan.json")
        # Saves all tasks to project_alpha_plan.json with proper formatting
        ```
    """
    payload = {"tasks": [t.model_dump() for t in tasks]}
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"✅ Plan saved to {filename}.")


def load_plan(filename: str) -> List[ScopeMateTask]:
    """
    Load tasks from a plan file.
    
    This function reads a JSON file containing serialized tasks and deserializes them
    into ScopeMateTask objects. It handles various backward compatibility issues and
    performs validation on the loaded data to ensure integrity.
    
    The function is robust against various common issues:
    - It properly handles missing parent_id fields for backward compatibility
    - It removes legacy fields that may exist in older files
    - It skips invalid tasks with validation errors rather than failing entirely
    - It provides clear warnings about skipped tasks
    
    Args:
        filename: Path to the plan file to load
        
    Returns:
        List of validated ScopeMateTask objects from the file
        
    Raises:
        FileNotFoundError: If the specified file doesn't exist
        
    Example:
        ```python
        try:
            tasks = load_plan("project_alpha_plan.json")
            print(f"Loaded {len(tasks)} tasks successfully")
            
            # Process loaded tasks
            for task in tasks:
                if task.meta.status == "backlog":
                    # Do something with backlog tasks...
                    pass
        except FileNotFoundError:
            print("Plan file not found, starting with empty task list")
            tasks = []
        ```
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File not found: {filename}")
        
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    tasks = []
    for raw in data.get("tasks", []):
        try:
            # Ensure parent_id field exists for backward compatibility
            if "parent_id" not in raw:
                raw["parent_id"] = None
                
            # Handle legacy fields in scope
            if "scope" in raw and isinstance(raw["scope"], dict):
                for legacy_field in ["owner", "team"]:
                    if legacy_field in raw["scope"]:
                        del raw["scope"][legacy_field]
                    
            tasks.append(ScopeMateTask(**raw))
        except ValidationError as e:
            print(f"[Warning] Skipping invalid task: {e}")
            
    print(f"✅ Loaded {len(tasks)} tasks from {filename}.")
    return tasks


def checkpoint_exists() -> bool:
    """
    Check if a checkpoint file exists.
    
    Returns:
        True if checkpoint file exists, False otherwise
    """
    return os.path.exists(CHECKPOINT_FILE)


def delete_checkpoint() -> None:
    """
    Delete the checkpoint file if it exists.
    """
    if checkpoint_exists():
        os.remove(CHECKPOINT_FILE)
        print(f"Checkpoint file {CHECKPOINT_FILE} deleted.") 