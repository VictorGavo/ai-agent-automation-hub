"""
Pytest configuration and fixtures for the AI Agent Automation Hub tests.
"""

import asyncio
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from typing import AsyncGenerator, Generator

from tests.utils import (
    MockDiscordBot,
    MockDatabase,
    MockAgent,
    MockInteraction,
    MockTaskManager,
    TestConfig
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config() -> TestConfig:
    """Provide test configuration."""
    return TestConfig()


@pytest.fixture
async def mock_database() -> AsyncGenerator[MockDatabase, None]:
    """Provide a mock database for testing."""
    db = MockDatabase()
    await db.setup()
    yield db
    await db.cleanup()


@pytest.fixture
def mock_discord_bot() -> MockDiscordBot:
    """Provide a mock Discord bot for testing."""
    return MockDiscordBot()


@pytest.fixture
def mock_interaction() -> MockInteraction:
    """Provide a mock Discord interaction for testing."""
    return MockInteraction()


@pytest.fixture
def mock_backend_agent() -> MockAgent:
    """Provide a mock backend agent for testing."""
    return MockAgent("backend")


@pytest.fixture
def mock_testing_agent() -> MockAgent:
    """Provide a mock testing agent for testing."""
    return MockAgent("testing")


@pytest.fixture
def mock_orchestrator() -> MockAgent:
    """Provide a mock orchestrator agent for testing."""
    return MockAgent("orchestrator")


@pytest.fixture
async def mock_task_manager(mock_database) -> MockTaskManager:
    """Provide a mock task manager for testing."""
    return MockTaskManager(mock_database)


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory structure for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        
        # Create directory structure
        directories = [
            "agents/backend",
            "agents/testing", 
            "agents/orchestrator",
            "bot",
            "database/models",
            "database/migrations",
            "dev_bible/automation_hub",
            "dev_bible/core",
            "logs",
            "scripts",
            "config"
        ]
        
        for dir_path in directories:
            (project_root / dir_path).mkdir(parents=True, exist_ok=True)
        
        # Create essential files
        files_content = {
            "bot/main.py": "# Discord bot main file",
            "bot/config.py": "# Bot configuration",
            "agents/backend/backend_agent.py": "# Backend agent",
            "agents/testing/testing_agent.py": "# Testing agent", 
            "agents/orchestrator/orchestrator.py": "# Orchestrator agent",
            "database/models/base.py": "# Database models",
            "dev_bible/README.md": "# Development Bible",
            "dev_bible/automation_hub/architecture.md": "# Architecture Documentation",
            "dev_bible/automation_hub/agent_roles.md": "# Agent Roles Documentation",
            "dev_bible/core/coding_standards.md": "# Coding Standards",
            "dev_bible/core/workflow_process.md": "# Workflow Process",
            ".env": "DISCORD_TOKEN=test_token\nDATABASE_URL=postgresql://test:test@localhost/test"
        }
        
        for file_path, content in files_content.items():
            full_path = project_root / file_path
            full_path.write_text(content)
        
        yield project_root


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment variables."""
    test_env = {
        'APP_MODE': 'testing',
        'LOG_LEVEL': 'DEBUG',
        'DATABASE_URL': 'postgresql://test:test@localhost/test_db',
        'DISCORD_TOKEN': 'test_token_12345',
        'MAX_CONCURRENT_TASKS': '2',
        'ENABLE_BACKEND_AGENT': 'false',
        'ENABLE_TESTING_AGENT': 'false',
        'ENABLE_ORCHESTRATOR': 'false',
        'ENCRYPTION_KEY': 'test_encryption_key_for_testing'
    }
    
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)


# Pytest markers configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (slower, requires components)"
    )
    config.addinivalue_line(
        "markers", "discord: marks tests that require Discord API access"
    )
    config.addinivalue_line(
        "markers", "database: marks tests that require database access"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (may be skipped in fast test runs)"
    )


# Test collection customization
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file location."""
    for item in items:
        # Add markers based on test file location
        if "test_discord" in item.nodeid:
            item.add_marker(pytest.mark.discord)
        
        if "test_database" in item.nodeid:
            item.add_marker(pytest.mark.database)
        
        if "integration" in item.nodeid or item.get_closest_marker("integration"):
            item.add_marker(pytest.mark.integration)
        elif not item.get_closest_marker("integration"):
            item.add_marker(pytest.mark.unit)