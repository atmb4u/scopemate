#!/usr/bin/env python3
"""
ScopeMate Storage - Functions for saving and loading task data

This module handles persistence of task data to/from files, including
checkpointing and loading plans.
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
    
    Args:
        tasks: List of ScopeMateTask objects to save
        filename: Path to save the plan file
    """
    payload = {"tasks": [t.model_dump() for t in tasks]}
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"✅ Plan saved to {filename}.")


def load_plan(filename: str) -> List[ScopeMateTask]:
    """
    Load tasks from a plan file.
    
    Args:
        filename: Path to the plan file
        
    Returns:
        List of ScopeMateTask objects
        
    Raises:
        FileNotFoundError: If the file doesn't exist
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