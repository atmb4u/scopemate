"""Basic tests for ScopeMate package"""
import pytest
from scopemate import __version__


def test_version():
    """Test that version is a string"""
    assert isinstance(__version__, str)
    assert __version__ != ""


def test_import():
    """Test that package can be imported"""
    import scopemate.models
    import scopemate.engine
    assert scopemate.models
    assert scopemate.engine 