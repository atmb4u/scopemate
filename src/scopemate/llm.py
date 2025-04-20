#!/usr/bin/env python3
"""
scopemate LLM - Handles interactions with Large Language Models

This module provides functions for interacting with LLMs for task estimation,
breakdown, and optimization.
"""
import json
from typing import Dict, Any, List, Optional
from openai import OpenAI

from .models import (
    ScopeMateTask, Scope, TIME_COMPLEXITY, SIZE_COMPLEXITY,
    VALID_SIZE_TYPES, VALID_TIME_ESTIMATES, get_utc_now
)

# -------------------------------
# Configuration
# -------------------------------
DEFAULT_MODEL = "o4-mini"

# -------------------------------
# LLM Interaction
# -------------------------------
def call_llm(prompt: str, model: str = DEFAULT_MODEL) -> dict:
    """
    Invoke LLM to get a structured JSON response.
    
    Args:
        prompt: The prompt to send to the LLM
        model: The model to use (defaults to DEFAULT_MODEL)
        
    Returns:
        A dictionary containing the parsed JSON response
    """
    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system", 
                "content": "You are a JSON assistant specialized in structured data for product management tasks. "
                           "Respond only with valid JSON. Follow the exact requested format in the user's prompt, "
                           "using the exact field names and adhering to all constraints on field values."
            },
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError as e:
        print(f"[Error] Failed to parse LLM response as JSON: {e}")
        print(f"Raw response: {response.choices[0].message.content}")
        return {}


def estimate_scope(task: ScopeMateTask) -> Scope:
    """
    Use LLM to estimate the scope of a task.
    
    Args:
        task: The ScopeMateTask to estimate scope for
        
    Returns:
        A Scope object with the estimated values
    """
    # Add parent context to prompt for subtasks
    parent_context = ""
    if task.parent_id:
        parent_context = (
            f"\nIMPORTANT: This is a subtask with parent_id: {task.parent_id}. "
            f"Subtasks should be SIMPLER than their parent tasks. "
            f"If the parent task is complex, a subtask should typically be straightforward or simpler. "
            f"If the parent task has a multi-sprint or sprint time estimate, a subtask should have a shorter estimate."
        )
    
    prompt = (
        f"You are an AI assistant helping a product manager estimate the scope of an engineering task.\n\n"
        f"Based on this task description, estimate its scope with the following fields:\n"
        f"- 'size': one of [\"trivial\", \"straightforward\", \"complex\", \"uncertain\", \"pioneering\"]\n"
        f"- 'time_estimate': one of [\"hours\", \"days\", \"week\", \"sprint\", \"multi-sprint\"]\n"
        f"- 'dependencies': array of strings describing dependencies\n"
        f"- 'risks': array of strings describing potential blockers or challenges\n\n"
        f"Provide detailed reasoning for your estimates, considering:\n"
        f"1. The task complexity and unknowns\n"
        f"2. Skills and expertise required\n"
        f"3. Potential dependencies and risks\n"
        f"4. Similar tasks from typical product development\n\n"
        f"{parent_context}\n\n"
        f"Return your analysis as a JSON object with the fields above, plus a 'reasoning' field explaining your thinking.\n\n"
        f"Here is the task:\n{task.model_dump_json(indent=2)}"
    )
    
    # Get response from LLM
    response = call_llm(prompt)
    
    try:
        # Extract any reasoning to show the user
        if "reasoning" in response:
            print(f"\n[AI Scope Analysis]\n{response['reasoning']}\n")
            del response["reasoning"]
            
        # Ensure required fields are present with defaults
        if "size" not in response:
            response["size"] = "uncertain"
        if "time_estimate" not in response:
            response["time_estimate"] = "sprint"
        if "dependencies" not in response:
            response["dependencies"] = []
        if "risks" not in response:
            response["risks"] = []
            
        # Remove legacy fields if present
        for legacy_field in ["owner", "team"]:
            if legacy_field in response:
                del response[legacy_field]
            
        # If the task already has risks defined, merge them
        if task.scope.risks:
            combined_risks = set(task.scope.risks)
            combined_risks.update(response["risks"])
            response["risks"] = list(combined_risks)
            
        # Create new scope with validated data
        return Scope(**response)
    except Exception as e:
        print(f"[Warning] Scope validation failed; keeping original scope: {e}")
        return task.scope


def suggest_alternative_approaches(task: ScopeMateTask) -> Dict[str, Any]:
    """
    Get a list of alternative approaches to implementing the task from the LLM.
    
    Args:
        task: The ScopeMateTask to get alternatives for
        
    Returns:
        A dictionary containing suggested alternative approaches
    """
    # Build the prompt for LLM
    prompt = (
        f"You are a product manager helping to identify alternative approaches to a task.\n\n"
        f"For the following task, suggest 2-5 ALTERNATIVE APPROACHES or implementation methods. "
        f"For example, if the task is 'Implement authentication', you might suggest:\n"
        f"1. Username/password based authentication with email verification\n"
        f"2. Social authentication using OAuth with platforms like Google, Facebook, etc.\n"
        f"3. Passwordless authentication using magic links sent to email\n\n"
        f"Each approach should be meaningfully different in IMPLEMENTATION STRATEGY, not just small variations.\n"
        f"Give each approach a short, clear name and a detailed description explaining the pros and cons.\n\n"
        f"IMPORTANT: For each approach, also include:\n"
        f"- 'scope': One of [\"trivial\", \"straightforward\", \"complex\", \"uncertain\", \"pioneering\"] indicating complexity\n"
        f"- 'time_estimate': One of [\"hours\", \"days\", \"week\", \"sprint\", \"multi-sprint\"] indicating time required\n\n"
        f"Return your response as a JSON object with this structure:\n"
        f"{{\n"
        f"  \"alternatives\": [\n"
        f"    {{\n"
        f"      \"name\": \"Short name for approach 1\",\n"
        f"      \"description\": \"Detailed description of approach 1 with pros and cons\",\n"
        f"      \"scope\": \"straightforward\",\n"
        f"      \"time_estimate\": \"days\"\n"
        f"    }},\n"
        f"    {{\n"
        f"      \"name\": \"Short name for approach 2\",\n"
        f"      \"description\": \"Detailed description of approach 2 with pros and cons\",\n"
        f"      \"scope\": \"complex\",\n"
        f"      \"time_estimate\": \"sprint\"\n"
        f"    }},\n"
        f"    ...\n"
        f"  ]\n"
        f"}}\n\n"
        f"Here is the task:\n{task.model_dump_json(indent=2)}"
    )
    
    # Get LLM response
    response = call_llm(prompt)
    
    # Check if response contains alternatives
    if not isinstance(response, dict) or "alternatives" not in response:
        print("[Warning] LLM did not return proper alternatives structure")
        return {"alternatives": []}
        
    alternatives = response.get("alternatives", [])
    
    # Validate and process alternatives
    valid_alternatives = []
    for idx, alt in enumerate(alternatives):
        if not isinstance(alt, dict):
            continue
            
        name = alt.get("name", f"Alternative {idx+1}")
        description = alt.get("description", "No description provided")
        
        # Extract scope and time_estimate with defaults
        scope = alt.get("scope", "uncertain")
        if scope not in ["trivial", "straightforward", "complex", "uncertain", "pioneering"]:
            scope = "uncertain"
            
        time_estimate = alt.get("time_estimate", "sprint")
        if time_estimate not in ["hours", "days", "week", "sprint", "multi-sprint"]:
            time_estimate = "sprint"
        
        valid_alternatives.append({
            "name": name, 
            "description": description,
            "scope": scope,
            "time_estimate": time_estimate
        })
        
    return {"alternatives": valid_alternatives}


def update_parent_with_child_context(parent_task: ScopeMateTask, child_task: ScopeMateTask) -> ScopeMateTask:
    """
    Update parent task details when a custom child task is added by passing context to LLM.
    
    Args:
        parent_task: The parent ScopeMateTask to update
        child_task: The child ScopeMateTask that was just created
        
    Returns:
        Updated parent ScopeMateTask
    """
    # Build the prompt for LLM
    prompt = (
        f"You are a product manager updating a parent task based on a new child task that was just created.\n\n"
        f"Review the parent task and the new child task details. Then update the parent task to:\n"
        f"1. Include any important details from the child task not already reflected in the parent\n"
        f"2. Ensure the parent's purpose and outcome descriptions accurately reflect all child tasks\n"
        f"3. Add any new risks or dependencies that this child task implies for the parent\n"
        f"4. Consider if the team assignment should be updated based on the child task\n\n"
        f"Return a JSON object with these updated fields, keeping most of the parent task the same, but updating:\n"
        f"- purpose.detailed_description: Generated enhanced description including child context\n"
        f"- scope.risks: Updated list of risks (merged from both parent and any new ones)\n"
        f"- outcome.detailed_outcome_definition: Generated enhanced description including child outcome\n"
        f"- meta.team: One of (Product, Design, Frontend, Backend, ML, Infra, Testing, Other), if it should be changed\n\n"
        f"Here is the parent task:\n{parent_task.model_dump_json(indent=2)}\n\n"
        f"Here is the new child task:\n{child_task.model_dump_json(indent=2)}\n\n"
        f"Return ONLY these updated fields in a JSON structure like:\n"
        f"{{\n"
        f"  \"purpose\": {{\n"
        f"    \"detailed_description\": \"Generated enhanced description...\"\n"
        f"  }},\n"
        f"  \"scope\": {{\n"
        f"    \"risks\": [\"Risk 1\", \"Risk 2\", \"New risk from child\"]\n"
        f"  }},\n"
        f"  \"outcome\": {{\n"
        f"    \"detailed_outcome_definition\": \"Generated enhanced outcome description...\"\n"
        f"  }},\n"
        f"  \"meta\": {{\n"
        f"    \"team\": \"Frontend\"\n"
        f"  }}\n"
        f"}}\n"
    )
    
    # Get LLM response
    response = call_llm(prompt)
    
    # Make a copy of the parent task to update
    updated_parent = parent_task.model_copy(deep=True)
    
    # Update purpose description if provided
    if (
        isinstance(response, dict) 
        and "purpose" in response 
        and isinstance(response["purpose"], dict) 
        and "detailed_description" in response["purpose"]
    ):
        updated_parent.purpose.detailed_description = response["purpose"]["detailed_description"]
    
    # Update risks if provided
    if (
        isinstance(response, dict) 
        and "scope" in response 
        and isinstance(response["scope"], dict) 
        and "risks" in response["scope"]
    ):
        # Combine existing risks with new ones while removing duplicates
        combined_risks = set(updated_parent.scope.risks)
        combined_risks.update(response["scope"]["risks"])
        updated_parent.scope.risks = list(combined_risks)
    
    # Update outcome definition if provided
    if (
        isinstance(response, dict) 
        and "outcome" in response 
        and isinstance(response["outcome"], dict) 
        and "detailed_outcome_definition" in response["outcome"]
    ):
        updated_parent.outcome.detailed_outcome_definition = response["outcome"]["detailed_outcome_definition"]
    
    # Update team if provided
    if (
        isinstance(response, dict) 
        and "meta" in response 
        and isinstance(response["meta"], dict) 
        and "team" in response["meta"]
        and response["meta"]["team"] in ["Product", "Design", "Frontend", "Backend", "ML", "Infra", "Testing", "Other"]
    ):
        updated_parent.meta.team = response["meta"]["team"]
    
    # Update the timestamp
    updated_parent.meta.updated = get_utc_now()
    
    return updated_parent


def generate_title_from_purpose_outcome(purpose: str, outcome: str) -> str:
    """
    Use LLM to generate a concise title from purpose and outcome descriptions.
    
    Args:
        purpose: The purpose description
        outcome: The outcome description
        
    Returns:
        A concise title string
    """
    client = OpenAI()
    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {
                "role": "system", 
                "content": "You are a concise title generator. Generate a brief, clear title (maximum 60 characters) "
                          "that captures the essence of a task based on its purpose and outcome description."
            },
            {
                "role": "user", 
                "content": f"Purpose: {purpose}\n\nOutcome: {outcome}\n\nGenerate a concise title (max 60 chars):"
            }
        ]
    )
    
    # Extract title from LLM response
    title = response.choices[0].message.content.strip()
    # Limit title length if needed
    if len(title) > 60:
        title = title[:57] + "..."
        
    return title 