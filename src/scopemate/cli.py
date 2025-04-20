#!/usr/bin/env python3
"""
🪜 scopemate CLI - Command-line interface for scopemate

Provides command-line interface for scopemate with options for setting purpose,
outcome, and output file.
"""

import sys
import argparse
import uuid
import json
import os
from typing import List

from .models import (
    ScopeMateTask, Purpose, Scope, Outcome, Meta, get_utc_now
)
from .storage import save_plan, save_markdown_plan, generate_markdown_from_json
from .llm import estimate_scope, generate_title_from_purpose_outcome
from .breakdown import suggest_breakdown
from .task_analysis import check_and_update_parent_estimates
from .engine import TaskEngine


def create_task_from_args(purpose: str, outcome: str) -> ScopeMateTask:
    """
    Create a ScopeMateTask from command line arguments.
    
    Args:
        purpose: The purpose description from arguments
        outcome: The outcome description from arguments
        
    Returns:
        A ScopeMateTask object with values from arguments
    """
    # Create a basic task from the command line arguments
    task_id = f"TASK-{uuid.uuid4().hex[:8]}"
    now = get_utc_now()
    
    # Generate a concise title from purpose and outcome
    title = generate_title_from_purpose_outcome(purpose, outcome)
    
    # Create task with basic details
    task = ScopeMateTask(
        id=task_id,
        title=title, 
        purpose=Purpose(
            detailed_description=purpose,
            alignment=[],
            urgency="strategic"
        ),
        scope=Scope(
            size="uncertain",
            time_estimate="sprint",
            dependencies=[],
            risks=[]
        ),
        outcome=Outcome(
            type="customer-facing",
            detailed_outcome_definition=outcome,
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
    
    # Use LLM to estimate scope
    task.scope = estimate_scope(task)
    
    return task


def process_task_with_breakdown(task: ScopeMateTask) -> List[ScopeMateTask]:
    """
    Process a task by generating subtasks and checking estimates.
    
    Args:
        task: The ScopeMateTask to process
        
    Returns:
        List of ScopeMateTask objects including the parent and any subtasks
    """
    # Generate subtasks
    subtasks = suggest_breakdown(task)
    
    # Add all tasks to a list
    all_tasks = [task] + subtasks
    
    # Check and fix estimates
    all_tasks = check_and_update_parent_estimates(all_tasks)
    
    return all_tasks


def command_line() -> None:
    """
    Process command line arguments and execute appropriate actions.
    
    This function is the primary entry point for the scopemate CLI, responsible 
    for parsing command-line arguments and routing execution to the appropriate
    workflow based on those arguments. It supports two main modes of operation:
    
    1. Interactive mode (--interactive): Launches the full guided workflow with
       the TaskEngine for an interactive task creation and breakdown experience.
       
    2. Non-interactive mode (--purpose and --outcome): Creates a task directly
       from command-line arguments, generates subtasks using LLM, and saves the
       resulting task hierarchy to a JSON file with an automatic Markdown version.
       
    The function validates required arguments depending on the mode, provides
    helpful error messages when arguments are missing, and handles the entire
    lifecycle of task creation, breakdown, and saving in non-interactive mode.
    
    Command line arguments:
        --interactive: Flag to launch interactive workflow
        --purpose: Text describing why the task matters (required in non-interactive mode)
        --outcome: Text describing what will be delivered (required in non-interactive mode)
        --output: Path to save the output JSON file (default: scopemate_plan.json)
        
    Side Effects:
        - Saves task data to a file on disk (both JSON and Markdown versions)
        - Prints progress and error messages to stdout
        - Exits with non-zero status code on errors
    
    Example Usage:
        ```bash
        # Interactive mode
        scopemate --interactive
        
        # Non-interactive mode
        scopemate --purpose "Improve website performance" \
                 --outcome "Page load time under 2 seconds" \
                 --output "perf_project.json"
        ```
        
    Note: Markdown files are automatically generated with the same base name 
    as the JSON file (e.g., "perf_project.md" for "perf_project.json").
    """
    parser = argparse.ArgumentParser(
        description="🪜  scopemate - Break down complex projects with LLMs",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Launch guided workflow to define task, generate LLM-powered breakdowns, and estimate scope"
    )
    
    parser.add_argument(
        "--outcome", 
        help="🎯 Outcome: Clearly define what will be delivered and how success will be measured (asks: What will change once this is done?)"
    )

    parser.add_argument(
        "--purpose", 
        help="🧭 Purpose: Clearly define why this project matters strategically (asks: Why does this matter now?)"
    )
    
    parser.add_argument(
        "--output", 
        default="scopemate_plan.json",
        help="JSON file to save the task breakdown and scope estimates (default: scopemate_plan.json). A matching .md file will also be created."
    )

    args = parser.parse_args()
    
    # Check if running in interactive mode
    if args.interactive:
        # Run interactive builder
        engine = TaskEngine()
        engine.run()
        return
    
    # Process command-line arguments for non-interactive mode
    if not args.purpose or not args.outcome:
        parser.print_help()
        print("\nError: Both --purpose and --outcome are required in non-interactive mode.")
        sys.exit(1)
    
    # Create task from arguments
    print("Creating task from command line arguments...")
    task = create_task_from_args(args.purpose, args.outcome)
    
    # Process task with subtasks
    print("Generating subtasks...")
    all_tasks = process_task_with_breakdown(task)
    
    # Save plan to output file (this will also create the MD version)
    save_plan(all_tasks, args.output)
    
    # Show message about MD file creation
    md_filename = os.path.splitext(args.output)[0] + ".md"
    print(f"✅ Both JSON and Markdown versions have been saved. You can share {md_filename} with team members.")


def main():
    """Main entry point for the scopemate command-line tool."""
    try:
        command_line()
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 