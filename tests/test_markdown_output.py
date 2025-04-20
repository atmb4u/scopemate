"""Tests for the Markdown output functionality in storage module"""
import os
import tempfile
import json
from datetime import datetime

import pytest

from scopemate.models import ScopeMateTask, Purpose, Scope, Outcome, Meta, get_utc_now
from scopemate.storage import save_plan, generate_markdown_from_json, save_markdown_plan


@pytest.fixture
def sample_tasks():
    """Create sample tasks for testing Markdown output"""
    now = get_utc_now()
    parent_task = ScopeMateTask(
        id="TASK-001",
        title="Create User Authentication System",
        purpose=Purpose(
            detailed_description="We need a secure authentication system to protect user data and ensure proper access control.",
            alignment=["Security Initiative", "User Trust"],
            urgency="strategic"
        ),
        scope=Scope(
            size="complex",
            time_estimate="sprint",
            dependencies=["Database Setup"],
            risks=["Security vulnerabilities", "Performance impact"]
        ),
        outcome=Outcome(
            type="customer-facing",
            detailed_outcome_definition="A fully functional authentication system with login, registration, password reset, and account management capabilities.",
            acceptance_criteria=[
                "Users can register with email verification",
                "Users can log in with username/password",
                "Users can reset passwords via email",
                "Account lockout after 5 failed attempts"
            ],
            metric="99.9% authentication success rate",
            validation_method="Automated testing and security audit"
        ),
        meta=Meta(
            status="backlog",
            priority=1,
            created=now,
            updated=now,
            due_date=None,
            confidence="medium",
            team="Backend"
        ),
        parent_id=None
    )
    
    child_task = ScopeMateTask(
        id="TASK-002",
        title="Implement Login Form",
        purpose=Purpose(
            detailed_description="Create a user-friendly login form for the authentication system.",
            alignment=["UX Improvement"],
            urgency="strategic"
        ),
        scope=Scope(
            size="straightforward",
            time_estimate="days",
            dependencies=[],
            risks=["Accessibility issues"]
        ),
        outcome=Outcome(
            type="customer-facing",
            detailed_outcome_definition="A responsive, accessible login form with validation.",
            acceptance_criteria=[
                "Form validates input before submission",
                "Form is responsive on all device sizes",
                "Form meets WCAG 2.1 AA accessibility standards"
            ],
            metric="95% successful first-time form submission",
            validation_method="User testing and accessibility audit"
        ),
        meta=Meta(
            status="backlog",
            priority=2,
            created=now,
            updated=now,
            due_date=None,
            confidence="high",
            team="Frontend"
        ),
        parent_id="TASK-001"
    )
    
    return [parent_task, child_task]


def test_save_plan_creates_md_file(sample_tasks):
    """Test that save_plan creates both JSON and MD files"""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a filename in the temporary directory
        json_filename = os.path.join(temp_dir, "test_plan.json")
        md_filename = os.path.join(temp_dir, "test_plan.md")
        
        # Save the plan
        save_plan(sample_tasks, json_filename)
        
        # Check that both files were created
        assert os.path.exists(json_filename)
        assert os.path.exists(md_filename)
        
        # Verify the JSON file contains expected data
        with open(json_filename, "r", encoding="utf-8") as f:
            json_data = json.load(f)
            assert "tasks" in json_data
            assert len(json_data["tasks"]) == 2
        
        # Verify the MD file has content
        with open(md_filename, "r", encoding="utf-8") as f:
            md_content = f.read()
            assert "# Project Scope Plan" in md_content
            assert "TASK-001: Create User Authentication System" in md_content
            assert "TASK-002: Implement Login Form" in md_content


def test_markdown_formatting(sample_tasks):
    """Test the structure and content of the generated Markdown"""
    # Convert tasks to serializable format
    payload = {"tasks": [t.model_dump() for t in sample_tasks]}
    
    # Generate markdown
    markdown = generate_markdown_from_json(payload)
    
    # Check for expected sections and formatting
    assert "# Project Scope Plan" in markdown
    assert "## Summary" in markdown
    assert "This document contains **2** tasks" in markdown
    assert "## Task Details" in markdown
    
    # Check for task information
    assert "### TASK-001: Create User Authentication System" in markdown
    assert "#### TASK-002: Implement Login Form" in markdown
    
    # Check for task details
    assert "**Purpose:**" in markdown
    assert "**Scope:**" in markdown
    assert "**Outcome:**" in markdown
    assert "**Meta:**" in markdown
    
    # Check for sections with specific information
    assert "*Size:* Complex" in markdown
    assert "*Time Estimate:* Sprint" in markdown
    assert "Security Initiative, User Trust" in markdown
    assert "*Team:* Backend" in markdown
    
    # Check for acceptance criteria formatting
    assert "- Users can register with email verification" in markdown
    assert "- Form validates input before submission" in markdown


def test_save_markdown_plan():
    """Test saving markdown to a file"""
    test_data = {
        "tasks": [
            {
                "id": "TEST-123",
                "title": "Simple Test Task",
                "purpose": {
                    "detailed_description": "Testing markdown output",
                    "alignment": [],
                    "urgency": "strategic"
                },
                "scope": {
                    "size": "trivial",
                    "time_estimate": "hours",
                    "dependencies": [],
                    "risks": []
                },
                "outcome": {
                    "type": "learning",
                    "detailed_outcome_definition": "Test outcome",
                    "acceptance_criteria": [],
                    "metric": None,
                    "validation_method": None
                },
                "meta": {
                    "status": "backlog",
                    "priority": None,
                    "created": get_utc_now(),
                    "updated": get_utc_now(),
                    "due_date": None,
                    "confidence": "high",
                    "team": "Testing"
                },
                "parent_id": None
            }
        ]
    }
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as temp:
        temp_path = temp.name
    
    try:
        # Save markdown to the file
        save_markdown_plan(test_data, temp_path)
        
        # Verify file exists and has content
        assert os.path.exists(temp_path)
        
        # Check file content
        with open(temp_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "# Project Scope Plan" in content
            assert "TEST-123: Simple Test Task" in content
            assert "Testing markdown output" in content
            
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path) 