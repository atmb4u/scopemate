"""Tests for ScopeMate CLI module"""
import sys
import tempfile
import os
import pytest
from unittest.mock import patch, MagicMock

from scopemate.cli import (
    create_task_from_args,
    process_task_with_breakdown,
    command_line,
    main
)


@pytest.fixture
def mock_llm_for_cli():
    """Mock LLM functions for CLI testing"""
    # Mock estimate_scope
    with patch('scopemate.cli.estimate_scope') as mock_estimate:
        # Return the scope unchanged for simplicity
        mock_estimate.side_effect = lambda task: task.scope
        
        # Mock generate_title_from_purpose_outcome
        with patch('scopemate.cli.generate_title_from_purpose_outcome') as mock_title:
            mock_title.return_value = "CLI Generated Title"
            
            # Mock suggest_breakdown
            with patch('scopemate.cli.suggest_breakdown') as mock_breakdown:
                # Return empty list of subtasks for simplicity
                mock_breakdown.return_value = []
                
                # Mock check_and_update_parent_estimates
                with patch('scopemate.cli.check_and_update_parent_estimates') as mock_check:
                    # Return the tasks unchanged
                    mock_check.side_effect = lambda tasks: tasks
                    
                    yield


def test_create_task_from_args(mock_llm_for_cli):
    """Test creating a task from command line arguments"""
    purpose = "CLI test purpose"
    outcome = "CLI test outcome"
    
    task = create_task_from_args(purpose, outcome)
    
    assert task.title == "CLI Generated Title"
    assert task.purpose.detailed_description == purpose
    assert task.outcome.detailed_outcome_definition == outcome
    assert task.purpose.urgency == "strategic"
    assert task.meta.status == "backlog"
    assert task.parent_id is None


def test_process_task_with_breakdown(mock_llm_for_cli):
    """Test processing a task with breakdown"""
    purpose = "CLI test purpose"
    outcome = "CLI test outcome"
    
    # Create a task
    task = create_task_from_args(purpose, outcome)
    
    # Process the task
    all_tasks = process_task_with_breakdown(task)
    
    # With our mocks, this should just return the task itself
    assert len(all_tasks) == 1
    assert all_tasks[0].id == task.id


@patch('scopemate.cli.argparse.ArgumentParser.parse_args')
@patch('scopemate.cli.TaskEngine')
@patch('scopemate.cli.save_plan')
def test_command_line_interactive(mock_save_plan, mock_task_engine, mock_parse_args, mock_llm_for_cli):
    """Test command_line function in interactive mode"""
    # Mock arguments with interactive flag
    mock_args = MagicMock()
    mock_args.interactive = True
    mock_parse_args.return_value = mock_args
    
    # Mock task engine
    mock_engine_instance = MagicMock()
    mock_task_engine.return_value = mock_engine_instance
    
    # Run command_line
    command_line()
    
    # Verify engine was created and run
    mock_task_engine.assert_called_once()
    mock_engine_instance.run.assert_called_once()
    
    # save_plan should not be called in interactive mode
    mock_save_plan.assert_not_called()


@patch('scopemate.cli.argparse.ArgumentParser.parse_args')
@patch('scopemate.cli.create_task_from_args')
@patch('scopemate.cli.process_task_with_breakdown')
@patch('scopemate.cli.save_plan')
def test_command_line_non_interactive(mock_save_plan, mock_process, mock_create, mock_parse_args, mock_llm_for_cli):
    """Test command_line function in non-interactive mode"""
    # Mock arguments
    mock_args = MagicMock()
    mock_args.interactive = False
    mock_args.purpose = "CLI purpose"
    mock_args.outcome = "CLI outcome"
    mock_args.output = "test_output.json"
    mock_parse_args.return_value = mock_args
    
    # Mock create_task_from_args
    mock_task = MagicMock()
    mock_create.return_value = mock_task
    
    # Mock process_task_with_breakdown
    mock_all_tasks = [mock_task]
    mock_process.return_value = mock_all_tasks
    
    # Run command_line
    command_line()
    
    # Verify functions were called with correct arguments
    mock_create.assert_called_once_with("CLI purpose", "CLI outcome")
    mock_process.assert_called_once_with(mock_task)
    mock_save_plan.assert_called_once_with(mock_all_tasks, "test_output.json")


@patch('scopemate.cli.argparse.ArgumentParser.parse_args')
def test_command_line_missing_args(mock_parse_args, mock_llm_for_cli):
    """Test command_line function with missing arguments"""
    # Mock arguments with missing purpose
    mock_args = MagicMock()
    mock_args.interactive = False
    mock_args.purpose = None
    mock_args.outcome = "CLI outcome"
    mock_parse_args.return_value = mock_args
    
    # Run command_line, should exit with error
    with pytest.raises(SystemExit) as exc_info:
        command_line()
    
    assert exc_info.value.code == 1


@patch('scopemate.cli.command_line')
def test_main_success(mock_command_line, mock_llm_for_cli):
    """Test main function with successful execution"""
    mock_command_line.return_value = None
    
    # Run main
    main()
    
    # Verify command_line was called
    mock_command_line.assert_called_once()


@patch('scopemate.cli.command_line')
def test_main_keyboard_interrupt(mock_command_line, mock_llm_for_cli):
    """Test main function with KeyboardInterrupt"""
    mock_command_line.side_effect = KeyboardInterrupt()
    
    # Run main, should exit gracefully
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    assert exc_info.value.code == 1


@patch('scopemate.cli.command_line')
def test_main_exception(mock_command_line, mock_llm_for_cli):
    """Test main function with general exception"""
    mock_command_line.side_effect = ValueError("Test error")
    
    # Run main, should exit with error
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    assert exc_info.value.code == 1 