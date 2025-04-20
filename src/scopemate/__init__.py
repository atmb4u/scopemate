"""🪜 scopemate - A CLI tool for Purpose/Scope/Outcome planning

This package provides tools for breaking down complex tasks using
the Purpose/Scope/Outcome planning approach.
"""

__version__ = "0.1.1"

# Public API
from .models import (
    ScopeMateTask, Purpose, Scope, Outcome, Meta, get_utc_now
)
from .engine import TaskEngine, interactive_builder
from .storage import save_plan, load_plan
from .llm import estimate_scope
from .breakdown import suggest_breakdown 