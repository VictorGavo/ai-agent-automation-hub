"""
Testing Agent Module

Provides automated testing capabilities for AI agent development workflow.
Monitors PRs, runs comprehensive test suites, and reports results.
"""

from .testing_agent import TestingAgent
from .test_runner import TestRunner

__all__ = ['TestingAgent', 'TestRunner']