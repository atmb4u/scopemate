"""
🪜 ScopeMate - A CLI tool for Purpose/Scope/Outcome planning

A tool to break down complex tasks into smaller subtasks, with LLM-driven scope
estimation and breakdown.
"""

__version__ = "0.1.0"

# Public API
from .models import (
    ScopeMateTask, Purpose, Scope, Outcome, Meta, get_utc_now
)
from .engine import TaskEngine, interactive_builder
from .storage import save_plan, load_plan
from .llm import estimate_scope
from .breakdown import suggest_breakdown 