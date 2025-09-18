#!/usr/bin/env python3
"""
OrchestratorClient Usage Examples

This file demonstrates how to integrate the OrchestratorClient with the Backend Agent
for comprehensive task communication and status management.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Add the project root to the path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.backend.orchestrator_client import OrchestratorClient, NotificationPriority
from database.models.task import TaskStatus


async def example_backend_agent_workflow():
    """
    Example workflow showing how Backend Agent uses OrchestratorClient
    throughout a typical task execution cycle.
    """
    
    print("🚀 Backend Agent Workflow with OrchestratorClient Integration")
    print("=" * 60)
    
    # Initialize the orchestrator client
    # In real usage, this would be injected into the Backend Agent
    client = OrchestratorClient("backend-agent-001")
    
    task_id = "task-flask-api-123"
    
    print(f"\n📋 Starting task: {task_id}")
    
    # 1. Initial task status update
    print("\n1️⃣ Updating task status to IN_PROGRESS...")
    await client.update_task_status(
        task_id=task_id,
        status=TaskStatus.IN_PROGRESS,
        metadata={"task_type": "flask_api_creation"},
        progress_percentage=5,
        current_step="Analyzing task requirements"
    )
    
    # 2. Progress updates during task execution
    print("\n2️⃣ Reporting progress during code generation...")
    await client.update_task_status(
        task_id=task_id,
        status=TaskStatus.IN_PROGRESS,
        metadata={"files_created": 2, "current_file": "app.py"},
        progress_percentage=35,
        current_step="Generating Flask application code"
    )
    
    # 3. Clarification request (if needed)
    print("\n3️⃣ Requesting clarification for ambiguous requirements...")
    await client.request_clarification(
        task_id=task_id,
        questions=[
            "Should the API include authentication middleware?",
            "What database schema should be used for user storage?",
            "Are there specific CORS requirements for the frontend?"
        ],
        priority=NotificationPriority.MEDIUM,
        context={
            "api_endpoint": "/api/v1/users",
            "current_progress": "35%",
            "blocking_issue": "authentication_requirements_unclear"
        }
    )
    
    # 4. Continue after clarification (simulated)
    print("\n4️⃣ Continuing after clarification received...")
    await client.update_task_status(
        task_id=task_id,
        status=TaskStatus.IN_PROGRESS,
        metadata={"clarification_resolved": True},
        progress_percentage=60,
        current_step="Implementing authentication middleware"
    )
    
    # 5. Testing phase
    print("\n5️⃣ Running tests and validation...")
    await client.update_task_status(
        task_id=task_id,
        status=TaskStatus.IN_PROGRESS,
        metadata={"tests_running": True},
        progress_percentage=85,
        current_step="Running automated tests"
    )
    
    # 6. Successful completion
    print("\n6️⃣ Reporting successful completion...")
    await client.report_completion(
        task_id=task_id,
        pr_url="https://github.com/team/project/pull/42",
        test_results={
            "total_tests": 24,
            "tests_passed": 23,
            "tests_failed": 1,
            "code_coverage": 87,
            "lint_score": 9.2,
            "security_score": 95
        },
        artifacts={
            "generated_files": ["app.py", "models/user.py", "tests/test_auth.py"],
            "documentation": "API_DOCUMENTATION.md",
            "docker_image": "backend-api:v1.2.3"
        }
    )
    
    print("\n✅ Task completed successfully!")


async def example_error_handling_workflow():
    """
    Example workflow showing error escalation and recovery patterns.
    """
    
    print("\n\n🚨 Error Handling Workflow")
    print("=" * 40)
    
    client = OrchestratorClient("backend-agent-002")
    task_id = "task-error-example-456"
    
    # 1. Start task
    print("\n1️⃣ Starting task with potential issues...")
    await client.update_task_status(
        task_id=task_id,
        status=TaskStatus.IN_PROGRESS,
        progress_percentage=10,
        current_step="Initializing GitHub repository"
    )
    
    # 2. Encounter recoverable error
    print("\n2️⃣ Handling recoverable error...")
    await client.update_task_status(
        task_id=task_id,
        status=TaskStatus.IN_PROGRESS,
        metadata={"retry_attempt": 1},
        progress_percentage=15,
        current_step="Retrying GitHub API call after rate limit"
    )
    
    # 3. Critical error requiring escalation
    print("\n3️⃣ Escalating critical error...")
    await client.escalate_error(
        task_id=task_id,
        error_type="github_api_auth",
        error_message="GitHub API authentication failed: Invalid token or insufficient permissions",
        recovery_attempts=3,
        context={
            "api_endpoint": "https://api.github.com/repos/team/project",
            "error_code": 401,
            "token_scopes": ["repo", "write:packages"],
            "required_scopes": ["repo", "write:packages", "admin:org"]
        }
    )
    
    print("\n❌ Task escalated for human intervention")


async def example_communication_monitoring():
    """
    Example of monitoring communication health and statistics.
    """
    
    print("\n\n📊 Communication Monitoring")
    print("=" * 35)
    
    client = OrchestratorClient("backend-agent-003")
    
    # Simulate some communication activities
    await client.update_task_status("task-1", TaskStatus.IN_PROGRESS)
    await client.update_task_status("task-2", TaskStatus.COMPLETED)
    await client.request_clarification("task-3", ["Question 1", "Question 2"])
    
    # Get communication statistics
    stats = await client.get_communication_stats()
    
    print("\n📈 Communication Statistics:")
    print(f"  Agent ID: {stats['agent_id']}")
    print(f"  Health Status: {stats['health_status']}")
    print(f"  Updates Sent: {stats['updates_sent']}")
    print(f"  Clarifications Requested: {stats['clarifications_requested']}")
    print(f"  Completions Reported: {stats['completions_reported']}")
    print(f"  Errors Escalated: {stats['errors_escalated']}")
    print(f"  Last Communication: {stats['last_communication']}")


async def example_priority_based_notifications():
    """
    Example showing different notification priorities and their usage.
    """
    
    print("\n\n🔔 Priority-Based Notifications")
    print("=" * 40)
    
    client = OrchestratorClient("backend-agent-004")
    
    # Low priority clarification
    print("\n🟢 Low priority clarification...")
    await client.request_clarification(
        "task-low-priority",
        ["Should we use snake_case or camelCase for API responses?"],
        priority=NotificationPriority.LOW,
        context={"category": "code_style", "impact": "minimal"}
    )
    
    # Medium priority clarification
    print("\n🟡 Medium priority clarification...")
    await client.request_clarification(
        "task-medium-priority",
        ["What should be the API rate limiting strategy?", "Should we implement caching?"],
        priority=NotificationPriority.MEDIUM,
        context={"category": "architecture", "impact": "performance"}
    )
    
    # High priority error
    print("\n🟠 High priority error escalation...")
    await client.escalate_error(
        "task-high-priority",
        "database_connection",
        "Database connection pool exhausted - unable to process requests",
        recovery_attempts=5,
        context={"active_connections": 100, "max_connections": 100}
    )
    
    # Critical error
    print("\n🔴 Critical error escalation...")
    await client.escalate_error(
        "task-critical",
        "security_violation",
        "Potential SQL injection vulnerability detected in generated code",
        recovery_attempts=0,
        context={"vulnerability_type": "sql_injection", "affected_endpoint": "/api/search"}
    )


async def main():
    """Run all example workflows."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🎯 OrchestratorClient Usage Examples")
    print("===================================")
    
    try:
        # Run example workflows
        await example_backend_agent_workflow()
        await example_error_handling_workflow()
        await example_communication_monitoring()
        await example_priority_based_notifications()
        
        print("\n\n🎉 All examples completed successfully!")
        print("\nKey Integration Points:")
        print("✅ Task status updates with progress tracking")
        print("✅ Clarification requests with priority levels")
        print("✅ Completion reports with test results")
        print("✅ Error escalation with recovery context")
        print("✅ Communication health monitoring")
        
    except Exception as e:
        print(f"\n❌ Error during examples: {str(e)}")
        logging.exception("Error in examples")


if __name__ == "__main__":
    asyncio.run(main())