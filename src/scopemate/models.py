#!/usr/bin/env python3
"""
ScopeMate Models - Pydantic models for task representation

This module contains the data models used throughout ScopeMate for representing
tasks, their purpose, scope, outcome, and metadata.
"""
import datetime as dt
from datetime import UTC
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ValidationError

# -------------------------------
# Constants and lookup tables
# -------------------------------
# Complexity rankings for time estimates
TIME_COMPLEXITY = {
    "hours": 1,
    "days": 2,
    "week": 3,
    "sprint": 4,
    "multi-sprint": 5
}

# Complexity rankings for task size
SIZE_COMPLEXITY = {
    "trivial": 1,
    "straightforward": 2, 
    "complex": 3,
    "uncertain": 4,
    "pioneering": 5
}

# Valid values for data validation
VALID_OUTCOME_TYPES = ["customer-facing", "business-metric", "technical-debt", "operational", "learning"]
VALID_URGENCY_TYPES = ["mission-critical", "strategic", "growth", "maintenance", "exploratory"]
VALID_SIZE_TYPES = ["trivial", "straightforward", "complex", "uncertain", "pioneering"]
VALID_TIME_ESTIMATES = ["hours", "days", "week", "sprint", "multi-sprint"]
VALID_STATUSES = ["backlog", "discovery", "in-progress", "review", "validated", "shipped", "killed"]
VALID_CONFIDENCE_LEVELS = ["high", "medium", "low"]
VALID_TEAMS = ["Product", "Design", "Frontend", "Backend", "ML", "Infra", "Testing", "Other"]

# Common mappings for fixing incorrect values
OUTCOME_TYPE_MAPPING = {
    "internal": "operational",
    "deliverable": "customer-facing", 
    "experiment": "learning",
    "enabler": "technical-debt",
    "maintenance": "technical-debt",
    "stability": "technical-debt"
}

# -------------------------------
# Helper Functions
# -------------------------------
def get_utc_now() -> str:
    """Returns current UTC time in ISO format with Z suffix."""
    return dt.datetime.now(UTC).isoformat(timespec="seconds") + "Z"

# -------------------------------
# Pydantic Models
# -------------------------------
class Purpose(BaseModel):
    """Purpose of a task - why it matters."""
    detailed_description: str
    alignment: List[str] = Field(
        default_factory=list, 
        description="Strategic goals this task aligns with"
    )
    urgency: str = Field(
        ..., 
        pattern="^(mission-critical|strategic|growth|maintenance|exploratory)$", 
        description="Strategic importance"
    )


class Scope(BaseModel):
    """Scope of a task - how big it is and what's required."""
    size: str = Field(
        ..., 
        pattern="^(trivial|straightforward|complex|uncertain|pioneering)$", 
        description="Complexity and effort"
    )
    time_estimate: str = Field(
        ..., 
        pattern="^(hours|days|week|sprint|multi-sprint)$", 
        description="Estimated time to complete"
    )
    dependencies: List[str] = Field(default_factory=list)
    risks: List[str] = Field(
        default_factory=list, 
        description="Potential blockers or challenges"
    )


class Outcome(BaseModel):
    """Outcome of a task - what's delivered and how it's measured."""
    type: str = Field(
        ..., 
        pattern="^(customer-facing|business-metric|technical-debt|operational|learning)$", 
        description="Type of value created"
    )
    detailed_outcome_definition: str
    acceptance_criteria: List[str] = Field(
        default_factory=list, 
        description="How we'll know this is done"
    )
    metric: Optional[str] = Field(
        default=None, 
        description="How success will be measured"
    )
    validation_method: Optional[str] = Field(
        default=None, 
        description="How to validate success (qualitative/quantitative)"
    )


class Meta(BaseModel):
    """Metadata about a task - status, priority, dates, etc."""
    status: str = Field(
        ..., 
        pattern="^(backlog|discovery|in-progress|review|validated|shipped|killed)$"
    )
    priority: Optional[int] = Field(
        default=None, 
        description="Relative priority (lower is higher)"
    )
    created: str
    updated: str
    due_date: Optional[str] = Field(
        default=None, 
        description="Target completion date"
    )
    confidence: Optional[str] = Field(
        default=None, 
        pattern="^(high|medium|low)$", 
        description="Confidence in estimates"
    )
    team: Optional[str] = Field(
        default=None,
        pattern="^(Product|Design|Frontend|Backend|ML|Infra|Testing|Other)$",
        description="Team responsible for this task"
    )


class ScopeMateTask(BaseModel):
    """A Purpose/Context/Outcome task representing a unit of work."""
    id: str
    title: str = Field(..., description="Short descriptive title")
    purpose: Purpose
    scope: Scope
    outcome: Outcome
    meta: Meta
    parent_id: Optional[str] = Field(
        default=None, 
        description="ID of parent task if this is a subtask"
    ) 