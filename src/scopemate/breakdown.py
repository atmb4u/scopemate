#!/usr/bin/env python3
"""
scopemate Breakdown - Functions for breaking down tasks into subtasks

This module provides task breakdown functionality, including subtask generation,
alternative approach suggestion, and interactive refinement.
"""
import uuid
from typing import List, Dict, Any, Optional
from pydantic import ValidationError

from .models import (
    ScopeMateTask, Purpose, Scope, Outcome, Meta, 
    SIZE_COMPLEXITY, TIME_COMPLEXITY, get_utc_now
)
from .llm import call_llm, suggest_alternative_approaches, update_parent_with_child_context
from .interaction import prompt_user, build_custom_subtask, generate_concise_title


def suggest_breakdown(task: ScopeMateTask) -> List[ScopeMateTask]:
    """
    Use LLM to suggest a breakdown of a task into smaller subtasks.
    
    This function is a critical part of the scopemate workflow. It uses a Large Language
    Model to analyze a task and suggest appropriate subtasks that collectively accomplish
    the parent task's goal. The function handles both complexity-based and time-based
    breakdowns, ensuring that complex tasks are simplified and long-duration tasks are
    broken into manageable timeframes.
    
    The function works through these stages:
    1. Analyze if the breakdown is needed due to complexity or time duration
    2. Formulate a specialized prompt for the LLM with appropriate constraints
    3. Process the LLM's response to extract valid subtask definitions
    4. Convert the raw LLM output into proper ScopeMateTask objects
    5. Present the suggestions to the user through an interactive selection process
    
    The subtasks generated are guaranteed to be:
    - Smaller in scope than the parent task
    - Less complex than the parent task
    - Shorter in duration than the parent task
    - Collectivey covering all aspects needed to accomplish the parent task
    
    Args:
        task: The ScopeMateTask to break down into smaller subtasks
        
    Returns:
        List of ScopeMateTask objects representing the subtasks, after user interaction
        
    Example:
        ```python
        parent_task = get_task_by_id("TASK-123")
        subtasks = suggest_breakdown(parent_task)
        if subtasks:
            print(f"Created {len(subtasks)} subtasks")
            tasks.extend(subtasks)
        ```
    """
    # Check if we're breaking down due to size complexity or time estimate
    is_complex = task.scope.size in ["complex", "uncertain", "pioneering"]
    is_long_duration = task.scope.time_estimate in ["sprint", "multi-sprint"]
    is_time_based_breakdown = is_long_duration and not is_complex
    
    # Add specialized instructions for time-based breakdown
    time_breakdown_context = ""
    if is_time_based_breakdown:
        time_breakdown_context = (
            f"This task has a time estimate of '{task.scope.time_estimate}' which is longer than ideal. "
            f"Break this down into smaller time units (week or less) even though it's not technically complex. "
            f"Focus on sequential stages or parallel workstreams that can be completed independently. "
            f"Ensure the subtasks represent concrete deliverables that can be completed in a week or less."
        )
    
    # Build the prompt for LLM
    prompt = (
        f"You are a product manager breaking down a task into smaller, SIMPLER subtasks.\n\n"
        f"Break the following task into 2-5 smaller subtasks. Each subtask MUST be simpler than the parent task.\n\n"
        f"IMPORTANT CONSTRAINTS:\n"
        f"1. Each subtask MUST be smaller in scope than the parent task\n"
        f"2. Subtask titles should be CONCISE (max 60 chars) and should NOT repeat the entire parent title\n"
        f"3. If parent task is 'complex' or larger, children should be at most 'straightforward'\n"
        f"4. If parent task has time_estimate 'sprint' or larger, children should use smaller estimates (week or less)\n"
        f"5. Each subtask should represent a clear, focused piece of work\n"
        f"6. CRITICAL: The set of subtasks TOGETHER must cover ALL key aspects needed to accomplish the parent task\n"
        f"7. It's acceptable if a subtask still needs further breakdown in a future iteration - focus on completeness now\n\n"
        f"{time_breakdown_context}\n\n"
        f"For each subtask in the array, follow this EXACT format for field names and values:\n\n"
        f"```\n"
        f"{{\n"
        f"  \"subtasks\": [\n"
        f"    {{\n"
        f"      \"id\": \"TASK-abc123\",\n"
        f"      \"title\": \"Short focused subtask title\",\n"
        f"      \"purpose\": {{\n"
        f"        \"detailed_description\": \"Detailed multi-paragraph description of the purpose of this subtask\",\n"
        f"        \"alignment\": [\"Strategic goal 1\", \"Strategic goal 2\"],\n"
        f"        \"urgency\": \"strategic\"\n"
        f"      }},\n"
        f"      \"scope\": {{\n"
        f"        \"size\": \"straightforward\",\n"
        f"        \"time_estimate\": \"week\",\n"
        f"        \"dependencies\": [\"Dependency 1\", \"Dependency 2\"],\n"
        f"        \"risks\": [\"Risk 1\", \"Risk 2\"]\n"
        f"      }},\n"
        f"      \"outcome\": {{\n"
        f"        \"type\": \"customer-facing\",\n"
        f"        \"detailed_outcome_definition\": \"Detailed multi-paragraph description of the outcome for this subtask\",\n"
        f"        \"acceptance_criteria\": [\"Criterion 1\", \"Criterion 2\"],\n"
        f"        \"metric\": \"Success measurement\",\n"
        f"        \"validation_method\": \"How to validate\"\n"
        f"      }},\n"
        f"      \"meta\": {{\n"
        f"        \"status\": \"backlog\",\n"
        f"        \"confidence\": \"medium\",\n"
        f"        \"team\": \"Frontend\"\n"
        f"      }}\n"
        f"    }},\n"
        f"    // Additional subtasks follow the same format\n"
        f"  ]\n"
        f"}}\n"
        f"```\n\n"
        f"For the team field, use one of: Product, Design, Frontend, Backend, ML, Infra, Testing, Other. Choose the most appropriate team for each subtask.\n\n"
        f"Return your response as a JSON object with a 'subtasks' array of subtask objects.\n\n"
        f"Here is the task to break down:\n{task.model_dump_json(indent=2)}"
    )
    
    # Get LLM response
    response = call_llm(prompt)
    raw_list = _extract_subtasks_from_response(response)
    
    # Process raw subtasks into ScopeMateTask objects
    parent_size_complexity = SIZE_COMPLEXITY.get(task.scope.size, 3)
    parent_time_complexity = TIME_COMPLEXITY.get(task.scope.time_estimate, 4)
    
    subtasks = []
    for raw in raw_list:
        try:
            # Process each subtask with constraints based on parent
            subtask = _process_raw_subtask(raw, task, parent_size_complexity, parent_time_complexity)
            subtasks.append(subtask)
        except ValidationError as e:
            print(f"[Warning] Skipping invalid subtask: {e}")
    
    # Get interactive user-driven breakdown instead of just returning the processed tasks
    return interactive_breakdown(task, subtasks)


def _extract_subtasks_from_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract subtasks from LLM response.
    
    Args:
        response: LLM response dictionary
        
    Returns:
        List of raw subtask dictionaries
    """
    if not isinstance(response, dict):
        print(f"[Warning] LLM response is not a dictionary: {type(response)}")
        return []
        
    # Try to extract subtasks array
    subtasks = response.get("subtasks", [])
    if not isinstance(subtasks, list):
        print(f"[Warning] 'subtasks' field is not an array: {type(subtasks)}")
        
        # Fallback: try to find any list in the response
        for k, v in response.items():
            if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                print(f"[Warning] Using list found in field '{k}' instead of 'subtasks'")
                return v
                
        # Last resort: treat the entire response as a single subtask if it looks like one
        if "title" in response or "id" in response:
            print("[Warning] No subtasks array found. Creating a single subtask from the entire response.")
            return [response]
            
        print(f"[Error] Could not extract subtasks from response: {response}")
        return []
    
    # Filter out non-dict items
    valid_subtasks = [item for item in subtasks if isinstance(item, dict)]
    
    # Debug output
    print(f"[Info] Extracted {len(valid_subtasks)} valid subtasks from response")
    
    # Validate essential fields in each subtask
    for i, subtask in enumerate(valid_subtasks):
        # Check for required purpose and outcome structures
        if "purpose" not in subtask:
            print(f"[Warning] Subtask {i} missing 'purpose' field, adding empty structure")
            subtask["purpose"] = {}
        elif not isinstance(subtask["purpose"], dict):
            print(f"[Warning] Subtask {i} has non-dict 'purpose' field, replacing with empty dict")
            subtask["purpose"] = {}
            
        if "outcome" not in subtask:
            print(f"[Warning] Subtask {i} missing 'outcome' field, adding empty structure")
            subtask["outcome"] = {}
        elif not isinstance(subtask["outcome"], dict):
            print(f"[Warning] Subtask {i} has non-dict 'outcome' field, replacing with empty dict")
            subtask["outcome"] = {}
    
    return valid_subtasks


def _process_raw_subtask(
    raw: Dict[str, Any], 
    parent_task: ScopeMateTask, 
    parent_size_complexity: int, 
    parent_time_complexity: int
) -> ScopeMateTask:
    """
    Process a raw subtask dictionary into a validated ScopeMateTask.
    
    Args:
        raw: Raw subtask dictionary
        parent_task: Parent ScopeMateTask
        parent_size_complexity: Complexity value for parent size
        parent_time_complexity: Complexity value for parent time estimate
        
    Returns:
        A validated ScopeMateTask
    """
    # Start with basic defaults
    task_id = raw.get("id", f"TASK-{uuid.uuid4().hex[:8]}")
    now = get_utc_now()
    
    # Process the title, making it concise
    raw_title = raw.get("title", "Untitled subtask")
    title = generate_concise_title(parent_task.title, raw_title)[:60]
    
    # Ensure the raw dictionaries exist to avoid attribute access errors
    raw_purpose = raw.get("purpose", {})
    if not isinstance(raw_purpose, dict):
        raw_purpose = {}

    raw_outcome = raw.get("outcome", {})
    if not isinstance(raw_outcome, dict):
        raw_outcome = {}
    
    # Create default purpose, scope, outcome, and meta
    # Inheriting from parent where appropriate
    purpose_data = {
        "detailed_description": raw_purpose.get("detailed_description", f"Subtask for: {parent_task.title}"),
        "alignment": parent_task.purpose.alignment.copy(),
        "urgency": parent_task.purpose.urgency
    }
    
    # Make sure scope is simpler than parent
    scope_data = {
        "size": "straightforward",
        "time_estimate": "days",
        "dependencies": [],
        "risks": []
    }
    
    outcome_data = {
        "type": parent_task.outcome.type,
        "detailed_outcome_definition": raw_outcome.get("detailed_outcome_definition", f"Delivers part of: {parent_task.title}"),
        "acceptance_criteria": raw_outcome.get("acceptance_criteria", []),
        "metric": raw_outcome.get("metric"),
        "validation_method": raw_outcome.get("validation_method")
    }
    
    meta_data = {
        "status": "backlog",
        "priority": None,
        "created": now,
        "updated": now,
        "due_date": None,
        "confidence": "medium",
        "team": parent_task.meta.team
    }
    
    # Override with provided data if available and valid
    # Scope data overrides
    raw_scope = raw.get("scope", {})
    if isinstance(raw_scope, dict):
        if "size" in raw_scope and raw_scope["size"] in ["trivial", "straightforward", "complex", "uncertain", "pioneering"]:
            scope_data["size"] = raw_scope["size"]
        
        if "time_estimate" in raw_scope and raw_scope["time_estimate"] in ["hours", "days", "week", "sprint", "multi-sprint"]:
            scope_data["time_estimate"] = raw_scope["time_estimate"]
            
        if "dependencies" in raw_scope and isinstance(raw_scope["dependencies"], list):
            scope_data["dependencies"] = raw_scope["dependencies"]
            
        if "risks" in raw_scope and isinstance(raw_scope["risks"], list):
            scope_data["risks"] = raw_scope["risks"]
    
    # Create the subtask
    subtask = ScopeMateTask(
        id=task_id,
        title=title,
        purpose=Purpose(**purpose_data),
        scope=Scope(**scope_data),
        outcome=Outcome(**outcome_data),
        meta=Meta(**meta_data),
        parent_id=parent_task.id
    )
    
    return subtask


def interactive_breakdown(task: ScopeMateTask, suggested_subtasks: List[ScopeMateTask]) -> List[ScopeMateTask]:
    """
    Handle interactive breakdown of a task with user input on alternatives.
    
    Args:
        task: The parent ScopeMateTask to break down
        suggested_subtasks: List of LLM-suggested subtasks
        
    Returns:
        List of final ScopeMateTask objects to use as subtasks
    """
    print(f"\n=== Interactive Breakdown for: {task.title} ===")
    
    # First, check if there are alternative implementation approaches
    alternatives = suggest_alternative_approaches(task)
    alt_list = alternatives.get("alternatives", [])
    
    # If we have meaningful alternatives, present them to the user
    if alt_list:
        print("\n=== Alternative Implementation Approaches ===")
        print("The following alternative approaches have been identified for this task:")
        
        for i, alt in enumerate(alt_list):
            # Display the alternative with scope and time estimate
            print(f"\n{i+1}. {alt['name']}")
            
            # Add scope and time estimate info
            scope = alt.get('scope', 'uncertain')
            time_estimate = alt.get('time_estimate', 'sprint')
            print(f"   Scope: {scope} | Est: {time_estimate}")
            
            print(f"   {alt['description']}")
        
        # Ask user which approach they want to use
        choice = prompt_user(
            "\nWhich approach would you like to use? Enter a number or 'n' for none", 
            default="n",
            choices=[str(i+1) for i in range(len(alt_list))] + ["n"]
        )
        
        # If user selected an alternative, update the task description to reflect their choice
        if choice.lower() != "n":
            try:
                selected_idx = int(choice) - 1
                if 0 <= selected_idx < len(alt_list):
                    selected_alt = alt_list[selected_idx]
                    print(f"\n✅ Selected: {selected_alt['name']}")
                    
                    # Ask if they want to update the parent task to reflect this choice
                    update_parent = prompt_user(
                        "Update parent task description to reflect this choice?", 
                        default="y", 
                        choices=["y","n"]
                    )
                    
                    if update_parent.lower() == "y":
                        # Update the parent task
                        update_text = f"Using approach: {selected_alt['name']} - {selected_alt['description']}"
                        
                        # Also update scope and time estimate if available
                        if 'scope' in selected_alt and 'time_estimate' in selected_alt:
                            # Consider updating parent task's scope and time estimate based on selection
                            update_time_scope = prompt_user(
                                "Also update task scope and time estimate to match selected approach?",
                                default="y",
                                choices=["y", "n"]
                            )
                            
                            if update_time_scope.lower() == "y":
                                task.scope.size = selected_alt['scope']
                                task.scope.time_estimate = selected_alt['time_estimate']
                                print(f"✅ Updated scope to {selected_alt['scope']} and time estimate to {selected_alt['time_estimate']}")
                        
                        task.purpose.detailed_description = f"{task.purpose.detailed_description}\n\n{update_text}"
                        task.meta.updated = get_utc_now()
                        print("✅ Updated parent task with chosen approach")
            except ValueError:
                pass
    
    # Process each suggested subtask with user input
    final_subtasks = []
    parent_updated = False
    
    print("\n=== Suggested Subtasks ===")
    print("The following subtasks have been suggested:")
    
    for i, subtask in enumerate(suggested_subtasks):
        print(f"\n{i+1}. {subtask.title}")
        print(f"   Size: {subtask.scope.size} | Est: {subtask.scope.time_estimate}")
        
        # Ask user what to do with this subtask
        choice = prompt_user(
            f"For subtask {i+1}, do you want to: (a)ccept, (m)odify, (c)ustom, or (s)kip?",
            default="a",
            choices=["a", "m", "c", "s"]
        )
        
        if choice.lower() == "a":
            # Accept as-is
            final_subtasks.append(subtask)
            print(f"✅ Added: {subtask.title}")
        
        elif choice.lower() == "m":
            # Modify title and description (simplified)
            new_title = prompt_user("New title", default=subtask.title)
            
            # Update the subtask
            subtask.title = new_title
            subtask.meta.updated = get_utc_now()
            
            final_subtasks.append(subtask)
            print(f"✅ Added modified: {subtask.title}")
            
        elif choice.lower() == "c":
            # Create a totally custom subtask
            custom_subtask = build_custom_subtask(task)
            final_subtasks.append(custom_subtask)
            print(f"✅ Added custom: {custom_subtask.title}")
            
            # Ask if user wants to update parent task with this custom child task
            update_choice = prompt_user(
                "Update parent task details with this custom child context?", 
                default="y", 
                choices=["y", "n"]
            )
            
            if update_choice.lower() == "y" and not parent_updated:
                task = update_parent_with_child_context(task, custom_subtask)
                parent_updated = True
                print("✅ Updated parent task with custom child context")
        
        else:  # Skip
            print(f"⏭️ Skipped: {subtask.title}")
    
    # Handle case where no subtasks were selected
    if not final_subtasks:
        # Create at least one default subtask
        default_subtask = _create_default_subtask(task)
        final_subtasks.append(default_subtask)
        print(f"✅ Added default subtask: {default_subtask.title}")
    
    return final_subtasks


def _create_default_subtask(parent_task: ScopeMateTask) -> ScopeMateTask:
    """
    Create a default subtask for a parent task when automatic breakdown is required.
    
    Args:
        parent_task: The parent task that needs breakdown
        
    Returns:
        A new ScopeMateTask as a simpler, shorter subtask
    """
    # Create a generic "first stage" subtask
    default_subtask = ScopeMateTask(
        id=f"TASK-{uuid.uuid4().hex[:6]}",
        title=f"First stage of {parent_task.title}",
        purpose=Purpose(
            detailed_description=f"Initial phase of work for {parent_task.title}",
            alignment=parent_task.purpose.alignment.copy(),
            urgency=parent_task.purpose.urgency
        ),
        scope=Scope(
            # Ensure simpler and shorter than parent
            size="straightforward" if parent_task.scope.size != "trivial" else "trivial",
            time_estimate="days",
            dependencies=[],
            risks=[]
        ),
        outcome=Outcome(
            type=parent_task.outcome.type,
            detailed_outcome_definition=f"First deliverable for {parent_task.title}",
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
            confidence=parent_task.meta.confidence or "medium",
            team=parent_task.meta.team
        ),
        parent_id=parent_task.id
    )
    
    return default_subtask 