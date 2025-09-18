#!/usr/bin/env python3
"""
Backend Agent Integration with OrchestratorClient

This file demonstrates how the BackendAgent integrates with the OrchestratorClient
for complete task management and communication workflow.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock

# Add the project root to the path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.backend.orchestrator_client import OrchestratorClient, NotificationPriority
from database.models.task import TaskStatus


class MockBackendAgent:
    """
    Mock Backend Agent showing integration with OrchestratorClient.
    In the real implementation, this would be the actual BackendAgent class.
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.orchestrator_client = OrchestratorClient(agent_id)
        self.logger = logging.getLogger(f"backend_agent.{agent_id}")
        
        # Task execution state
        self.current_task = None
        self.task_progress = 0
        
    async def execute_task(self, task_id: str, task_description: str) -> bool:
        """
        Execute a backend development task with full Orchestrator communication.
        
        Args:
            task_id: Unique task identifier
            task_description: Task requirements and description
            
        Returns:
            bool: True if task completed successfully, False if failed/escalated
        """
        self.current_task = task_id
        self.task_progress = 0
        
        try:
            self.logger.info(f"Starting task execution: {task_id}")
            
            # 1. Initialize task
            await self.orchestrator_client.update_task_status(
                task_id=task_id,
                status=TaskStatus.IN_PROGRESS,
                metadata={"task_description": task_description},
                progress_percentage=0,
                current_step="Initializing task execution"
            )
            
            # 2. Analyze requirements
            await self._update_progress(task_id, 10, "Analyzing task requirements")
            
            # Simulate requirement analysis
            if "unclear" in task_description.lower():
                # Request clarification for unclear requirements
                clarification_success = await self.orchestrator_client.request_clarification(
                    task_id=task_id,
                    questions=[
                        "Could you provide more specific requirements?",
                        "What should be the expected input/output format?",
                        "Are there any specific frameworks or libraries to use?"
                    ],
                    priority=NotificationPriority.MEDIUM,
                    context={"analysis_stage": "requirement_review"}
                )
                
                if clarification_success:
                    self.logger.info("Clarification requested - waiting for response")
                    return False  # Task paused for clarification
            
            # 3. Code generation phase
            await self._update_progress(task_id, 30, "Generating Flask application code")
            
            # Simulate code generation
            generated_files = await self._simulate_code_generation(task_id)
            
            # 4. Testing phase
            await self._update_progress(task_id, 70, "Running tests and validation")
            
            # Simulate testing
            test_results = await self._simulate_testing(task_id)
            
            # 5. GitHub operations
            await self._update_progress(task_id, 90, "Creating pull request")
            
            # Simulate GitHub PR creation
            pr_url = await self._simulate_github_operations(task_id)
            
            # 6. Report completion
            await self.orchestrator_client.report_completion(
                task_id=task_id,
                pr_url=pr_url,
                test_results=test_results,
                artifacts={
                    "generated_files": generated_files,
                    "test_coverage": test_results.get("code_coverage", 0),
                    "quality_metrics": {
                        "lint_score": test_results.get("lint_score", 0),
                        "security_score": test_results.get("security_score", 0)
                    }
                }
            )
            
            self.logger.info(f"Task {task_id} completed successfully")
            return True
            
        except Exception as e:
            # Escalate errors to Orchestrator
            await self.orchestrator_client.escalate_error(
                task_id=task_id,
                error_type="task_execution",
                error_message=str(e),
                recovery_attempts=0,
                context={
                    "current_step": f"progress_{self.task_progress}%",
                    "error_details": str(e)
                }
            )
            
            self.logger.error(f"Task {task_id} failed: {str(e)}")
            return False
    
    async def _update_progress(self, task_id: str, progress: int, step: str):
        """Update task progress with Orchestrator."""
        self.task_progress = progress
        await self.orchestrator_client.update_task_status(
            task_id=task_id,
            status=TaskStatus.IN_PROGRESS,
            progress_percentage=progress,
            current_step=step
        )
        
        # Simulate some work time
        await asyncio.sleep(0.1)
    
    async def _simulate_code_generation(self, task_id: str) -> list:
        """Simulate Flask code generation."""
        generated_files = [
            "app.py",
            "models/user.py",
            "routes/auth.py",
            "tests/test_auth.py",
            "requirements.txt"
        ]
        
        for i, file in enumerate(generated_files):
            progress = 30 + (i * 8)  # 30-70% range
            await self._update_progress(
                task_id,
                progress,
                f"Generating {file}"
            )
        
        return generated_files
    
    async def _simulate_testing(self, task_id: str) -> Dict[str, Any]:
        """Simulate test execution."""
        await self._update_progress(task_id, 75, "Running unit tests")
        await self._update_progress(task_id, 80, "Running integration tests")
        await self._update_progress(task_id, 85, "Analyzing code coverage")
        
        return {
            "total_tests": 18,
            "tests_passed": 17,
            "tests_failed": 1,
            "code_coverage": 85,
            "lint_score": 8.5,
            "security_score": 92
        }
    
    async def _simulate_github_operations(self, task_id: str) -> str:
        """Simulate GitHub operations."""
        await self._update_progress(task_id, 92, "Creating feature branch")
        await self._update_progress(task_id, 95, "Committing changes")
        await self._update_progress(task_id, 98, "Creating pull request")
        
        return f"https://github.com/team/project/pull/{hash(task_id) % 1000}"


async def test_backend_agent_integration():
    """
    Test the complete integration between BackendAgent and OrchestratorClient.
    """
    print("🔧 Backend Agent + OrchestratorClient Integration Test")
    print("=" * 55)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create backend agent
    agent = MockBackendAgent("backend-agent-integration-test")
    
    print("\n📋 Test Case 1: Successful Task Execution")
    print("-" * 45)
    
    success = await agent.execute_task(
        "task-success-123",
        "Create a Flask API endpoint for user authentication with JWT tokens"
    )
    
    print(f"✅ Task execution result: {'Success' if success else 'Failed/Paused'}")
    
    print("\n📋 Test Case 2: Task Requiring Clarification")
    print("-" * 45)
    
    success = await agent.execute_task(
        "task-unclear-456",
        "Create some unclear API thing that does stuff"
    )
    
    print(f"✅ Task execution result: {'Success' if success else 'Failed/Paused'}")
    
    print("\n📋 Test Case 3: Task with Error")
    print("-" * 35)
    
    # Simulate an error by modifying the agent
    original_method = agent._simulate_github_operations
    
    async def failing_github_operations(task_id: str) -> str:
        raise Exception("GitHub API rate limit exceeded")
    
    agent._simulate_github_operations = failing_github_operations
    
    success = await agent.execute_task(
        "task-error-789",
        "Create a Flask API with GitHub integration"
    )
    
    print(f"✅ Task execution result: {'Success' if success else 'Failed/Escalated'}")
    
    # Restore original method
    agent._simulate_github_operations = original_method
    
    print("\n📊 Communication Statistics")
    print("-" * 30)
    
    stats = await agent.orchestrator_client.get_communication_stats()
    print(f"Agent ID: {stats['agent_id']}")
    print(f"Health Status: {stats['health_status']}")
    print(f"Total Updates: {stats['updates_sent']}")
    print(f"Clarifications: {stats['clarifications_requested']}")
    print(f"Completions: {stats['completions_reported']}")
    print(f"Errors: {stats['errors_escalated']}")
    
    print("\n🎉 Integration test completed!")
    print("\nKey Features Demonstrated:")
    print("✅ Real-time progress tracking")
    print("✅ Automatic clarification requests")
    print("✅ Comprehensive completion reporting")
    print("✅ Intelligent error escalation")
    print("✅ Communication health monitoring")


async def test_priority_escalation_workflow():
    """
    Test the priority-based escalation workflow.
    """
    print("\n\n🚨 Priority Escalation Workflow Test")
    print("=" * 40)
    
    agent = MockBackendAgent("backend-agent-priority-test")
    
    # Test different error types and their priority escalation
    error_scenarios = [
        {
            "error_type": "github_api_auth",
            "description": "GitHub authentication failure",
            "expected_priority": "critical"
        },
        {
            "error_type": "code_generation", 
            "description": "Code generation logic error",
            "expected_priority": "medium"
        },
        {
            "error_type": "test_failure",
            "description": "Unit test failures",
            "expected_priority": "low"
        }
    ]
    
    for i, scenario in enumerate(error_scenarios, 1):
        print(f"\n{i}️⃣ Testing {scenario['error_type']} escalation...")
        
        await agent.orchestrator_client.escalate_error(
            task_id=f"priority-test-{i}",
            error_type=scenario["error_type"],
            error_message=scenario["description"],
            recovery_attempts=2,
            context={"scenario": "priority_testing"}
        )
    
    print("\n✅ Priority escalation workflow test completed!")


if __name__ == "__main__":
    async def main():
        await test_backend_agent_integration()
        await test_priority_escalation_workflow()
    
    asyncio.run(main())