#!/usr/bin/env python3
"""
scopemate LLM - Handles interactions with Large Language Models

This module provides functions for interacting with LLMs for task estimation,
breakdown, and optimization.
"""
import json
import os
from typing import Dict, Any, List, Optional
from enum import Enum, auto

# Import LLM providers
from openai import OpenAI
import google.generativeai as genai
from anthropic import Anthropic

from .models import (
    ScopeMateTask, Scope, TIME_COMPLEXITY, SIZE_COMPLEXITY,
    VALID_SIZE_TYPES, VALID_TIME_ESTIMATES, get_utc_now
)

# -------------------------------
# Configuration
# -------------------------------
class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = auto()
    GEMINI = auto()
    CLAUDE = auto()

# Default configuration
DEFAULT_PROVIDER = LLMProvider.OPENAI
DEFAULT_OPENAI_MODEL = "o4-mini"
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
DEFAULT_CLAUDE_MODEL = "claude-3-7-sonnet-20250219"

# Provider-specific model mapping
DEFAULT_MODELS = {
    LLMProvider.OPENAI: DEFAULT_OPENAI_MODEL,
    LLMProvider.GEMINI: DEFAULT_GEMINI_MODEL,
    LLMProvider.CLAUDE: DEFAULT_CLAUDE_MODEL
}

# Get provider from environment variable or use default
def get_llm_provider() -> LLMProvider:
    """Get the LLM provider from environment variable or use default"""
    provider_str = os.environ.get("SCOPEMATE_LLM_PROVIDER", "").upper()
    if provider_str == "OPENAI":
        return LLMProvider.OPENAI
    elif provider_str == "GEMINI":
        return LLMProvider.GEMINI
    elif provider_str == "CLAUDE": 
        return LLMProvider.CLAUDE
    return DEFAULT_PROVIDER

# Get model for the provider from environment variable or use default
def get_llm_model(provider: LLMProvider = None) -> str:
    """Get the LLM model for the provider from environment variable or use default"""
    if provider is None:
        provider = get_llm_provider()
    
    if provider == LLMProvider.OPENAI:
        return os.environ.get("SCOPEMATE_OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    elif provider == LLMProvider.GEMINI:
        return os.environ.get("SCOPEMATE_GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    elif provider == LLMProvider.CLAUDE:
        return os.environ.get("SCOPEMATE_CLAUDE_MODEL", DEFAULT_CLAUDE_MODEL)
    
    return DEFAULT_MODELS[DEFAULT_PROVIDER]

# -------------------------------
# LLM Interaction
# -------------------------------
def call_llm(prompt: str, system_prompt: str = None, model: str = None, provider: LLMProvider = None) -> dict:
    """
    Invoke LLM to get a structured JSON response.
    
    This function is the core LLM integration point for scopemate, handling all
    communication with the supported LLM APIs. It's designed to always return structured
    JSON data that can be easily processed by the application.
    
    The function:
    1. Creates a client for the selected provider (OpenAI, Gemini, or Claude)
    2. Configures a system prompt that instructs the model to return valid JSON
    3. Sends the user's prompt with the task-specific instructions
    4. Parses and returns the JSON response
    
    Error handling is built in to gracefully handle JSON parsing failures by
    printing diagnostic information and returning an empty dictionary rather
    than crashing.
    
    Args:
        prompt (str): The prompt to send to the LLM, containing full instructions
                      and any task data needed for context
        model (str, optional): The model identifier to use (defaults to provider's default model)
        provider (LLMProvider, optional): The LLM provider to use (defaults to configured provider)
        
    Returns:
        dict: A dictionary containing the parsed JSON response from the LLM.
              Returns an empty dict {} if parsing fails.
    """
    # Determine which provider to use
    if provider is None:
        provider = get_llm_provider()
    
    # Determine which model to use
    if model is None:
        model = get_llm_model(provider)
    
    # System prompt is common across providers
    if system_prompt is None:
        system_prompt = (
            "You are a JSON assistant specialized in structured data for product management tasks. "
            "Respond only with valid JSON. Follow the exact requested format in the user's prompt, "
            "using the exact field names and adhering to all constraints on field values."
        )
    
    # Call the appropriate provider with JSON response format
    response_text = _call_provider(prompt, system_prompt, model, provider, response_format="json")
    
    # Parse JSON response
    try:
        if response_text:
            return json.loads(response_text)
        return {}
    except json.JSONDecodeError as e:
        print(f"[Error] Failed to parse LLM response as JSON: {e}")
        print(f"Raw response: {response_text}")
        return {}

def call_llm_text(prompt: str, system_prompt: str = None, model: str = None, provider: LLMProvider = None) -> str:
    """
    Invoke LLM to get a plain text response (not JSON).
    
    This is similar to call_llm but returns plain text instead of JSON.
    
    Args:
        prompt (str): The prompt to send to the LLM
        system_prompt (str, optional): The system prompt to use
        model (str, optional): The model identifier to use (defaults to provider's default model)
        provider (LLMProvider, optional): The LLM provider to use (defaults to configured provider)
        
    Returns:
        str: The text response from the LLM, or empty string on error
    """
    # Determine which provider to use
    if provider is None:
        provider = get_llm_provider()
    
    # Determine which model to use
    if model is None:
        model = get_llm_model(provider)
    
    # System prompt is common across providers
    if system_prompt is None:
        system_prompt = (
            "You are a helpful assistant that provides clear and concise answers. "
            "Respond directly to the question without adding additional explanation or context."
        )
    
    print(f"Calling LLM (text mode) with provider: {provider}, model: {model}")
    
    # Call the appropriate provider with text response format
    return _call_provider(prompt, system_prompt, model, provider, response_format="text")

def _call_provider(prompt: str, system_prompt: str, model: str, provider: LLMProvider, response_format: str = "json") -> str:
    """
    Internal helper function to call the appropriate LLM provider.
    
    Args:
        prompt (str): The prompt to send to the LLM
        system_prompt (str): The system prompt to use
        model (str): The model to use
        provider (LLMProvider): The provider to use
        response_format (str): Either "json" or "text"
        
    Returns:
        str: The raw text response from the LLM
    """
    try:
        if provider == LLMProvider.OPENAI:
            return _call_openai_provider(prompt, system_prompt, model, response_format)
        elif provider == LLMProvider.GEMINI:
            return _call_gemini_provider(prompt, system_prompt, model, response_format)
        elif provider == LLMProvider.CLAUDE:
            return _call_claude_provider(prompt, system_prompt, model, response_format)
        
        # Fallback to OpenAI if unknown provider
        print(f"[Warning] Unknown provider {provider}, falling back to OpenAI")
        return _call_openai_provider(prompt, system_prompt, DEFAULT_OPENAI_MODEL, response_format)
    except Exception as e:
        print(f"[Error] LLM API call failed: {e}")
        return ""

def _call_openai_provider(prompt: str, system_prompt: str, model: str, response_format: str) -> str:
    """Internal helper function to call OpenAI API"""
    try:
        client = OpenAI()
        
        # Configure response format for JSON if requested
        kwargs = {}
        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            **kwargs
        )
        
        # Return raw content text
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Error] OpenAI API call failed: {e}")
        return ""

def _call_gemini_provider(prompt: str, system_prompt: str, model: str, response_format: str) -> str:
    """Internal helper function to call Gemini API"""
    try:
        # Check for API key in environment
        api_key = os.environ.get("GEMINI_API_KEY", None)
        if not api_key:
            print("[Error] No API key found for Gemini. Set GEMINI_API_KEY environment variable.")
            return ""
        # Initialize the Gemini client
        genai.configure(api_key=api_key)
        
        # Since system role is not supported, combine system prompt and user prompt
        combined_prompt = f"{system_prompt}\n\n{prompt}"
        
        # Configure response format for JSON if requested
        generation_config = {}
        if response_format == "json":
            generation_config["response_mime_type"] = "application/json"
        
        # Generate response using Gemini
        model_name = model if model != system_prompt else DEFAULT_GEMINI_MODEL
        model_obj = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)
        response = model_obj.generate_content(combined_prompt)
        
        text = response.text.strip()
        
        # Remove quotes if present for text responses
        if response_format == "text" and text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
            
        return text
    except Exception as e:
        print(f"[Error] Gemini API call failed: {e}")
        return ""

def _call_claude_provider(prompt: str, system_prompt: str, model: str, response_format: str) -> str:
    """Internal helper function to call Claude API"""
    try:
        client = Anthropic()
        
        # Configure temperature - lower for JSON for more deterministic output
        temperature = 0.1 if response_format == "json" else 0.2
        
        response = client.messages.create(
            model=model,
            system=system_prompt,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature
        )
        
        return response.content[0].text.strip()
    except Exception as e:
        print(f"[Error] Claude API call failed: {e}")
        return ""

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


def generate_title_from_purpose_outcome(purpose: str, outcome: str, model: str = None, provider: LLMProvider = None) -> str:
    """
    Use LLM to generate a concise title from purpose and outcome descriptions.
    
    Args:
        purpose: The purpose description
        outcome: The outcome description
        model (str, optional): The model identifier to use (defaults to provider's default model)
        provider (LLMProvider, optional): The LLM provider to use (defaults to configured provider)
        
    Returns:
        A concise title string
    """
    system_prompt = (
        "You are a concise title generator. Generate a brief, clear title (maximum 60 characters) "
        "that captures the essence of a task based on its purpose and outcome description. "
        "Return ONLY the title with no additional text or quotes."
    )
    
    user_prompt = f"Purpose: {purpose}\n\nOutcome: {outcome}\n\nGenerate a concise title (max 60 chars):"
    
    # Use the common text-based LLM function
    title = call_llm_text(user_prompt, system_prompt, model, provider)
    
    # Handle empty response
    if not title:
        return "Task Title"
    
    # Limit title length if needed
    if len(title) > 60:
        title = title[:57] + "..."
        
    return title 