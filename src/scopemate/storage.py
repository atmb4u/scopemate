#!/usr/bin/env python3
"""
scopemate Storage - Functions for saving and loading task data

This module manages persistence of task data to disk and loading from files.
"""
import os
import json
from datetime import datetime
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
    
    # Automatically generate markdown version with the same basename
    md_filename = os.path.splitext(filename)[0] + ".md"
    save_markdown_plan(payload, md_filename)


def save_markdown_plan(data: Dict[str, Any], filename: str) -> None:
    """
    Save tasks to a Markdown file for human readability.
    
    This function converts the JSON task data into a well-structured Markdown format
    for easier reading and sharing with team members who may not use scopemate directly.
    
    Args:
        data: Dictionary containing the tasks data (with "tasks" key)
        filename: Path to save the Markdown file
    """
    markdown = generate_markdown_from_json(data)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"✅ Markdown version saved to {filename}.")


def generate_markdown_from_json(data: Dict[str, Any]) -> str:
    """
    Convert scopemate JSON data to a well-structured Markdown format.
    
    Args:
        data: The scopemate JSON data as a dictionary
        
    Returns:
        A string containing the Markdown representation
    """
    # Start building markdown content
    md = ["# Project Scope Plan\n"]
    md.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
    
    # Add summary section
    tasks = data.get("tasks", [])
    md.append(f"## Summary\n\n")
    md.append(f"This document contains **{len(tasks)}** tasks.\n\n")
    
    # Get counts by size complexity
    size_counts = {}
    for task in tasks:
        if "scope" in task and "size" in task["scope"]:
            size = task["scope"]["size"]
            size_counts[size] = size_counts.get(size, 0) + 1
            
    if size_counts:
        md.append("**Complexity Breakdown:**\n\n")
        for size, count in size_counts.items():
            md.append(f"- {size.capitalize()}: {count} task(s)\n")
        md.append("\n")
    
    # Create hierarchical task structure
    main_tasks = [t for t in tasks if not t.get("parent_id")]
    child_tasks = {}
    for task in tasks:
        if task.get("parent_id"):
            if task["parent_id"] not in child_tasks:
                child_tasks[task["parent_id"]] = []
            child_tasks[task["parent_id"]].append(task)
    
    # Add detailed task section
    md.append("## Task Details\n\n")
    
    # Process main tasks with their children
    for task in main_tasks:
        md.extend(format_task_as_markdown(task, child_tasks, 0))
    
    return "\n".join(md)


def format_task_as_markdown(task: Dict[str, Any], child_tasks: Dict[str, List[Dict[str, Any]]], level: int) -> List[str]:
    """
    Format a single task and its children as Markdown.
    
    Args:
        task: The task data
        child_tasks: Dictionary mapping parent_id to list of child tasks
        level: Current indentation level
        
    Returns:
        List of markdown formatted lines
    """
    md_lines = []
    
    # Add task title with appropriate heading level
    heading_level = "###" + "#" * level
    task_id = task.get("id", "NO-ID")
    title = task.get("title", "Untitled Task")
    md_lines.append(f"{heading_level} {task_id}: {title}\n")
    
    # Add purpose section
    if "purpose" in task:
        purpose = task["purpose"]
        md_lines.append("**Purpose:**\n\n")
        if "detailed_description" in purpose:
            md_lines.append(f"{purpose['detailed_description']}\n\n")
        if "alignment" in purpose and purpose["alignment"]:
            md_lines.append("*Strategic Alignment:* ")
            md_lines.append(", ".join(purpose["alignment"]))
            md_lines.append("\n\n")
        if "urgency" in purpose:
            md_lines.append(f"*Urgency:* {purpose['urgency'].capitalize()}\n\n")
    
    # Add scope section
    if "scope" in task:
        scope = task["scope"]
        md_lines.append("**Scope:**\n\n")
        if "size" in scope:
            md_lines.append(f"*Size:* {scope['size'].capitalize()}\n\n")
        if "time_estimate" in scope:
            md_lines.append(f"*Time Estimate:* {scope['time_estimate'].capitalize()}\n\n")
        if "dependencies" in scope and scope["dependencies"]:
            md_lines.append("*Dependencies:*\n\n")
            for dep in scope["dependencies"]:
                md_lines.append(f"- {dep}\n")
            md_lines.append("\n")
        if "risks" in scope and scope["risks"]:
            md_lines.append("*Risks:*\n\n")
            for risk in scope["risks"]:
                md_lines.append(f"- {risk}\n")
            md_lines.append("\n")
    
    # Add outcome section
    if "outcome" in task:
        outcome = task["outcome"]
        md_lines.append("**Outcome:**\n\n")
        if "type" in outcome:
            md_lines.append(f"*Type:* {outcome['type'].capitalize().replace('-', ' ')}\n\n")
        if "detailed_outcome_definition" in outcome:
            md_lines.append(f"{outcome['detailed_outcome_definition']}\n\n")
        if "acceptance_criteria" in outcome and outcome["acceptance_criteria"]:
            md_lines.append("*Acceptance Criteria:*\n\n")
            for ac in outcome["acceptance_criteria"]:
                md_lines.append(f"- {ac}\n")
            md_lines.append("\n")
        if "metric" in outcome and outcome["metric"]:
            md_lines.append(f"*Success Metric:* {outcome['metric']}\n\n")
        if "validation_method" in outcome and outcome["validation_method"]:
            md_lines.append(f"*Validation Method:* {outcome['validation_method']}\n\n")
    
    # Add meta section
    if "meta" in task:
        meta = task["meta"]
        md_lines.append("**Meta:**\n\n")
        if "status" in meta:
            md_lines.append(f"*Status:* {meta['status'].capitalize()}\n")
        if "priority" in meta and meta["priority"] is not None:
            md_lines.append(f"*Priority:* {meta['priority']}\n")
        if "confidence" in meta:
            md_lines.append(f"*Confidence:* {meta['confidence'].capitalize()}\n")
        if "team" in meta and meta["team"]:
            md_lines.append(f"*Team:* {meta['team']}\n")
        md_lines.append("\n")
    
    # Add separator line if not the last task
    md_lines.append("---\n\n")
    
    # Process children recursively
    if task.get("id") in child_tasks:
        for child in child_tasks[task["id"]]:
            md_lines.extend(format_task_as_markdown(child, child_tasks, level + 1))
    
    return md_lines


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