# agents/backend/__init__.py
"""Backend Agent Module

This module contains the Backend Agent implementation for the AI Agent Automation Hub.
The Backend Agent is responsible for executing Flask development tasks assigned by the Orchestrator.
"""

from .backend_agent import BackendAgent
from .github_client import GitHubClient
from .task_executor import TaskExecutor

__all__ = ["BackendAgent", "GitHubClient", "TaskExecutor"]