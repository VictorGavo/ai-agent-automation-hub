"""
AI Agent Automation Hub - Test Suite

This package contains comprehensive tests for the AI Agent Automation Hub,
including unit tests, integration tests, and performance tests.

Test Structure:
- test_discord_bot.py: Discord bot functionality tests
- test_agents.py: AI agent system tests  
- test_database.py: Database operations tests
- utils.py: Test utilities and mock objects
- conftest.py: Test configuration and fixtures

Test Categories:
- Unit Tests: Fast, isolated tests for individual components
- Integration Tests: Tests for component interactions
- Performance Tests: Tests for system performance and scalability
- Discord Tests: Tests requiring Discord API access (optional)

Running Tests:
    pytest                          # Run all tests
    pytest -m unit                 # Run unit tests only
    pytest -m integration         # Run integration tests only
    pytest -m discord             # Run Discord-specific tests
    pytest --cov=.                # Run with coverage reporting

Markers:
    @pytest.mark.unit             # Unit test marker
    @pytest.mark.integration     # Integration test marker
    @pytest.mark.discord         # Discord API test marker
    @pytest.mark.slow            # Slow test marker
    @pytest.mark.database        # Database test marker
"""

__version__ = "1.0.0"
__author__ = "AI Agent Automation Hub Team"

# Test utilities
from .utils import (
    MockDiscordBot,
    MockDatabase, 
    MockAgent,
    MockInteraction,
    MockTaskManager,
    TestConfig,
    create_test_task,
    assert_task_created,
    assert_message_sent,
    wait_for_task_completion
)

__all__ = [
    "MockDiscordBot",
    "MockDatabase", 
    "MockAgent",
    "MockInteraction", 
    "MockTaskManager",
    "TestConfig",
    "create_test_task",
    "assert_task_created",
    "assert_message_sent", 
    "wait_for_task_completion"
]