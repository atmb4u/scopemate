"""Basic tests for scopemate package"""
import pytest
from scopemate import __version__


def test_version():
    """Test that version is set correctly"""
    assert __version__ == "0.1.1"


def test_imports():
    """Test that main modules can be imported"""
    import scopemate.models
    import scopemate.engine
    assert scopemate.models
    assert scopemate.engine 