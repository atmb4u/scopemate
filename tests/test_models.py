"""Tests for scopemate models module"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from scopemate.models import (
    Purpose, Scope, Outcome, Meta, ScopeMateTask,
    TIME_COMPLEXITY, SIZE_COMPLEXITY, get_utc_now
)


def test_get_utc_now():
    """Test the get_utc_now function returns a valid ISO format time string"""
    now = get_utc_now()
    assert isinstance(now, str)
    assert now.endswith("Z")  # UTC "Zulu" time indicator
    # Verify it's a valid ISO format by parsing it - don't double add the timezone
    dt = datetime.fromisoformat(now[:-1])  # Remove the Z
    assert dt is not None


def test_constants():
    """Test that constants are properly defined"""
    # Check time complexity map
    assert "hours" in TIME_COMPLEXITY
    assert "days" in TIME_COMPLEXITY
    assert "week" in TIME_COMPLEXITY
    assert "sprint" in TIME_COMPLEXITY
    assert "multi-sprint" in TIME_COMPLEXITY
    assert TIME_COMPLEXITY["hours"] < TIME_COMPLEXITY["days"]
    assert TIME_COMPLEXITY["days"] < TIME_COMPLEXITY["week"]
    assert TIME_COMPLEXITY["week"] < TIME_COMPLEXITY["sprint"]
    assert TIME_COMPLEXITY["sprint"] < TIME_COMPLEXITY["multi-sprint"]
    
    # Check size complexity map
    assert "trivial" in SIZE_COMPLEXITY
    assert "straightforward" in SIZE_COMPLEXITY
    assert "complex" in SIZE_COMPLEXITY
    assert "uncertain" in SIZE_COMPLEXITY
    assert "pioneering" in SIZE_COMPLEXITY
    assert SIZE_COMPLEXITY["trivial"] < SIZE_COMPLEXITY["straightforward"]
    assert SIZE_COMPLEXITY["straightforward"] < SIZE_COMPLEXITY["complex"]
    assert SIZE_COMPLEXITY["complex"] < SIZE_COMPLEXITY["uncertain"]
    assert SIZE_COMPLEXITY["uncertain"] < SIZE_COMPLEXITY["pioneering"]


class TestPurposeModel:
    """Tests for the Purpose model"""
    
    def test_valid_purpose(self):
        """Test creating a valid Purpose model"""
        purpose = Purpose(
            detailed_description="Test description",
            alignment=["Goal 1", "Goal 2"],
            urgency="strategic"
        )
        assert purpose.detailed_description == "Test description"
        assert len(purpose.alignment) == 2
        assert purpose.urgency == "strategic"
    
    def test_invalid_urgency(self):
        """Test that invalid urgency value raises validation error"""
        with pytest.raises(ValidationError):
            Purpose(
                detailed_description="Test description",
                alignment=[],
                urgency="invalid"  # Invalid value
            )
    
    def test_empty_alignment(self):
        """Test that empty alignment list is valid"""
        purpose = Purpose(
            detailed_description="Test description",
            urgency="strategic"
        )
        assert purpose.alignment == []


class TestScopeModel:
    """Tests for the Scope model"""
    
    def test_valid_scope(self):
        """Test creating a valid Scope model"""
        scope = Scope(
            size="straightforward",
            time_estimate="days",
            dependencies=["Dependency 1"],
            risks=["Risk 1", "Risk 2"]
        )
        assert scope.size == "straightforward"
        assert scope.time_estimate == "days"
        assert len(scope.dependencies) == 1
        assert len(scope.risks) == 2
    
    def test_invalid_size(self):
        """Test that invalid size value raises validation error"""
        with pytest.raises(ValidationError):
            Scope(
                size="simple",  # Invalid value
                time_estimate="days"
            )
    
    def test_invalid_time_estimate(self):
        """Test that invalid time_estimate value raises validation error"""
        with pytest.raises(ValidationError):
            Scope(
                size="straightforward",
                time_estimate="months"  # Invalid value
            )


class TestOutcomeModel:
    """Tests for the Outcome model"""
    
    def test_valid_outcome(self):
        """Test creating a valid Outcome model"""
        outcome = Outcome(
            type="customer-facing",
            detailed_outcome_definition="Test outcome",
            acceptance_criteria=["Criterion 1"],
            metric="User satisfaction",
            validation_method="Survey"
        )
        assert outcome.type == "customer-facing"
        assert outcome.detailed_outcome_definition == "Test outcome"
        assert len(outcome.acceptance_criteria) == 1
        assert outcome.metric == "User satisfaction"
        assert outcome.validation_method == "Survey"
    
    def test_invalid_type(self):
        """Test that invalid type value raises validation error"""
        with pytest.raises(ValidationError):
            Outcome(
                type="invalid",  # Invalid value
                detailed_outcome_definition="Test outcome"
            )
    
    def test_optional_fields(self):
        """Test that optional fields can be omitted"""
        outcome = Outcome(
            type="technical-debt",
            detailed_outcome_definition="Test outcome"
        )
        assert outcome.metric is None
        assert outcome.validation_method is None
        assert outcome.acceptance_criteria == []


class TestMetaModel:
    """Tests for the Meta model"""
    
    def test_valid_meta(self):
        """Test creating a valid Meta model"""
        now = get_utc_now()
        meta = Meta(
            status="backlog",
            priority=1,
            created=now,
            updated=now,
            due_date=None,
            confidence="medium",
            team="Frontend"
        )
        assert meta.status == "backlog"
        assert meta.priority == 1
        assert meta.created == now
        assert meta.updated == now
        assert meta.due_date is None
        assert meta.confidence == "medium"
        assert meta.team == "Frontend"
    
    def test_invalid_status(self):
        """Test that invalid status value raises validation error"""
        now = get_utc_now()
        with pytest.raises(ValidationError):
            Meta(
                status="pending",  # Invalid value
                created=now,
                updated=now
            )
    
    def test_invalid_confidence(self):
        """Test that invalid confidence value raises validation error"""
        now = get_utc_now()
        with pytest.raises(ValidationError):
            Meta(
                status="backlog",
                created=now,
                updated=now,
                confidence="maybe"  # Invalid value
            )


class TestScopeMateTaskModel:
    """Tests for the ScopeMateTask model"""
    
    def test_valid_task(self):
        """Test creating a valid ScopeMateTask model"""
        now = get_utc_now()
        task = ScopeMateTask(
            id="TEST-123",
            title="Test Task",
            purpose=Purpose(
                detailed_description="Test purpose",
                alignment=[],
                urgency="strategic"
            ),
            scope=Scope(
                size="straightforward",
                time_estimate="days",
                dependencies=[],
                risks=[]
            ),
            outcome=Outcome(
                type="customer-facing",
                detailed_outcome_definition="Test outcome",
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
        assert task.id == "TEST-123"
        assert task.title == "Test Task"
        assert task.parent_id is None
    
    def test_task_with_parent(self):
        """Test creating a task with a parent ID"""
        now = get_utc_now()
        task = ScopeMateTask(
            id="TEST-456",
            title="Child Task",
            purpose=Purpose(
                detailed_description="Test purpose",
                alignment=[],
                urgency="strategic"
            ),
            scope=Scope(
                size="straightforward",
                time_estimate="days",
                dependencies=[],
                risks=[]
            ),
            outcome=Outcome(
                type="customer-facing",
                detailed_outcome_definition="Test outcome",
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
            parent_id="TEST-123"
        )
        assert task.parent_id == "TEST-123" 