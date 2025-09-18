"""
Orchestrator Client for Backend Agent Communication

This module provides the communication interface between the Backend Agent
and the Orchestrator Agent for task coordination and status management.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

# Import shared models and utilities
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database.models.task import Task, TaskStatus
from database.models.logs import Log, LogLevel
from database.models.base import SessionLocal


class NotificationPriority(Enum):
    """Priority levels for notifications to Orchestrator"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OrchestratorClient:
    """
    Handles communication between Backend Agent and Orchestrator Agent.
    
    Provides methods for:
    - Task status updates with progress tracking
    - Progress reporting with detailed metadata
    - Error escalation and clarification requests
    - Completion notifications with verification results
    """
    
    def __init__(self, agent_id: str, db_session_factory=SessionLocal):
        """
        Initialize the Orchestrator Client.
        
        Args:
            agent_id: Unique identifier for the backend agent
            db_session_factory: Database session factory for data persistence
        """
        self.agent_id = agent_id
        self.db_session_factory = db_session_factory
        self.logger = logging.getLogger(f"backend_agent.orchestrator_client.{agent_id}")
        
        # Communication statistics
        self.stats = {
            "updates_sent": 0,
            "clarifications_requested": 0,
            "completions_reported": 0,
            "errors_escalated": 0,
            "last_communication": None
        }
    
    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        metadata: Optional[Dict[str, Any]] = None,
        progress_percentage: Optional[int] = None,
        current_step: Optional[str] = None
    ) -> bool:
        """
        Update task status in database with progress information.
        
        Args:
            task_id: Unique task identifier
            status: New task status
            metadata: Additional task metadata
            progress_percentage: Completion percentage (0-100)
            current_step: Description of current execution step
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Prepare status update data
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow(),
                "agent_id": self.agent_id
            }
            
            # Add progress information if provided
            if progress_percentage is not None:
                update_data["progress_percentage"] = max(0, min(100, progress_percentage))
            
            if current_step:
                update_data["current_step"] = current_step
            
            # Merge additional metadata
            if metadata:
                if "metadata" not in update_data:
                    update_data["metadata"] = {}
                update_data["metadata"].update(metadata)
            
            # Update task in database
            session = self.db_session_factory()
            try:
                task = session.get(Task, task_id)
                if not task:
                    self.logger.error(f"Task {task_id} not found for status update")
                    return False
                
                # Update task fields
                for key, value in update_data.items():
                    if key == "metadata":
                        # Merge metadata dictionaries
                        current_metadata = task.metadata or {}
                        current_metadata.update(value)
                        task.metadata = current_metadata
                    else:
                        setattr(task, key, value)
                
                session.commit()
            finally:
                session.close()
            
            # Log the status update
            await self._log_communication(
                "STATUS_UPDATE",
                f"Updated task {task_id} to {status.value}",
                {
                    "task_id": task_id,
                    "status": status.value,
                    "progress": progress_percentage,
                    "step": current_step
                }
            )
            
            self.stats["updates_sent"] += 1
            self.stats["last_communication"] = datetime.utcnow()
            
            self.logger.info(
                f"Task {task_id} status updated to {status.value} "
                f"(Progress: {progress_percentage or 'N/A'}%)"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update task status: {str(e)}")
            await self._log_communication(
                "STATUS_UPDATE_ERROR",
                f"Failed to update task {task_id}: {str(e)}",
                {"task_id": task_id, "error": str(e)},
                LogLevel.ERROR
            )
            return False
    
    async def request_clarification(
        self,
        task_id: str,
        questions: List[str],
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Escalate to human via Orchestrator when task requirements are unclear.
        
        Args:
            task_id: Task requiring clarification
            questions: List of specific questions for human review
            priority: Urgency level for the clarification request
            context: Additional context for the clarification
            
        Returns:
            bool: True if escalation successful, False otherwise
        """
        try:
            # Prepare clarification request
            clarification_data = {
                "task_id": task_id,
                "agent_id": self.agent_id,
                "questions": questions,
                "priority": priority.value,
                "context": context or {},
                "requested_at": datetime.utcnow(),
                "type": "clarification_request"
            }
            
            # Update task status to indicate pending clarification
            await self.update_task_status(
                task_id,
                TaskStatus.PENDING,
                metadata={
                    "clarification_requested": True,
                    "questions": questions,
                    "clarification_priority": priority.value
                },
                current_step="Waiting for clarification"
            )
            
            # Log the clarification request
            await self._log_communication(
                "CLARIFICATION_REQUEST",
                f"Requested clarification for task {task_id}",
                clarification_data
            )
            
            # In a real implementation, this would send to Discord/Slack
            # For now, we'll simulate the notification process
            await self._simulate_discord_notification(
                f"🤔 Backend Agent needs clarification for task {task_id}",
                {
                    "Questions": questions,
                    "Priority": priority.value,
                    "Agent": self.agent_id,
                    "Context": context or "No additional context"
                }
            )
            
            self.stats["clarifications_requested"] += 1
            self.stats["last_communication"] = datetime.utcnow()
            
            self.logger.info(
                f"Clarification requested for task {task_id} with {len(questions)} questions"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to request clarification: {str(e)}")
            await self._log_communication(
                "CLARIFICATION_ERROR",
                f"Failed to request clarification for task {task_id}: {str(e)}",
                {"task_id": task_id, "error": str(e)},
                LogLevel.ERROR
            )
            return False
    
    async def report_completion(
        self,
        task_id: str,
        pr_url: str,
        test_results: Dict[str, Any],
        artifacts: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Notify Orchestrator of task completion with verification results.
        
        Args:
            task_id: Completed task identifier
            pr_url: GitHub Pull Request URL
            test_results: Test execution results and validation
            artifacts: Additional artifacts produced during task execution
            
        Returns:
            bool: True if completion reported successfully, False otherwise
        """
        try:
            # Prepare completion report
            completion_data = {
                "task_id": task_id,
                "agent_id": self.agent_id,
                "pr_url": pr_url,
                "test_results": test_results,
                "artifacts": artifacts or {},
                "completed_at": datetime.utcnow(),
                "type": "completion_report"
            }
            
            # Calculate completion quality score
            quality_score = self._calculate_quality_score(test_results)
            
            # Update task status to completed
            await self.update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                metadata={
                    "completion_reported": True,
                    "pr_url": pr_url,
                    "test_results": test_results,
                    "quality_score": quality_score,
                    "artifacts": artifacts or {}
                },
                progress_percentage=100,
                current_step="Completed - awaiting review"
            )
            
            # Log the completion report
            await self._log_communication(
                "COMPLETION_REPORT",
                f"Reported completion for task {task_id}",
                completion_data
            )
            
            # Send completion notification
            await self._simulate_discord_notification(
                f"✅ Backend Agent completed task {task_id}",
                {
                    "Pull Request": pr_url,
                    "Quality Score": f"{quality_score}/100",
                    "Tests Passed": test_results.get("tests_passed", 0),
                    "Tests Failed": test_results.get("tests_failed", 0),
                    "Agent": self.agent_id,
                    "Artifacts": len(artifacts) if artifacts else 0
                }
            )
            
            self.stats["completions_reported"] += 1
            self.stats["last_communication"] = datetime.utcnow()
            
            self.logger.info(
                f"Task {task_id} completion reported - PR: {pr_url}, "
                f"Quality: {quality_score}/100"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to report completion: {str(e)}")
            await self._log_communication(
                "COMPLETION_ERROR",
                f"Failed to report completion for task {task_id}: {str(e)}",
                {"task_id": task_id, "error": str(e)},
                LogLevel.ERROR
            )
            return False
    
    async def escalate_error(
        self,
        task_id: str,
        error_type: str,
        error_message: str,
        recovery_attempts: int = 0,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Escalate critical errors to Orchestrator for human intervention.
        
        Args:
            task_id: Task experiencing the error
            error_type: Category of error (e.g., "github_api", "code_generation")
            error_message: Detailed error description
            recovery_attempts: Number of automatic recovery attempts made
            context: Additional error context and debugging information
            
        Returns:
            bool: True if escalation successful, False otherwise
        """
        try:
            # Prepare error escalation data
            escalation_data = {
                "task_id": task_id,
                "agent_id": self.agent_id,
                "error_type": error_type,
                "error_message": error_message,
                "recovery_attempts": recovery_attempts,
                "context": context or {},
                "escalated_at": datetime.utcnow(),
                "type": "error_escalation"
            }
            
            # Determine priority based on error type and recovery attempts
            priority = self._determine_error_priority(error_type, recovery_attempts)
            
            # Update task status to error state
            await self.update_task_status(
                task_id,
                TaskStatus.FAILED,
                metadata={
                    "error_escalated": True,
                    "error_type": error_type,
                    "error_message": error_message,
                    "recovery_attempts": recovery_attempts,
                    "escalation_priority": priority.value
                },
                current_step=f"Error escalated: {error_type}"
            )
            
            # Log the error escalation
            await self._log_communication(
                "ERROR_ESCALATION",
                f"Escalated error for task {task_id}: {error_type}",
                escalation_data,
                LogLevel.ERROR
            )
            
            # Send error notification
            await self._simulate_discord_notification(
                f"🚨 Backend Agent error escalation for task {task_id}",
                {
                    "Error Type": error_type,
                    "Error Message": error_message,
                    "Recovery Attempts": recovery_attempts,
                    "Priority": priority.value,
                    "Agent": self.agent_id,
                    "Context": str(context) if context else "No additional context"
                }
            )
            
            self.stats["errors_escalated"] += 1
            self.stats["last_communication"] = datetime.utcnow()
            
            self.logger.error(
                f"Error escalated for task {task_id}: {error_type} "
                f"(Attempts: {recovery_attempts})"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to escalate error: {str(e)}")
            return False
    
    async def get_communication_stats(self) -> Dict[str, Any]:
        """
        Get communication statistics and health metrics.
        
        Returns:
            Dict containing communication statistics
        """
        return {
            **self.stats,
            "agent_id": self.agent_id,
            "health_status": "healthy" if self.stats["last_communication"] else "inactive"
        }
    
    # Private helper methods
    
    async def _log_communication(
        self,
        action: str,
        message: str,
        metadata: Dict[str, Any],
        level: LogLevel = LogLevel.INFO
    ):
        """Log communication event to database."""
        try:
            session = self.db_session_factory()
            try:
                log_entry = Log(
                    agent_name=self.agent_id,
                    level=level,
                    message=f"[ORCHESTRATOR_COMM] {action}: {message}",
                    log_metadata=str({
                        "action": action,
                        "communication_type": "orchestrator",
                        **metadata
                    })
                )
                session.add(log_entry)
                session.commit()
            finally:
                session.close()
        except Exception as e:
            self.logger.error(f"Failed to log communication: {str(e)}")
    
    def _calculate_quality_score(self, test_results: Dict[str, Any]) -> int:
        """Calculate quality score based on test results."""
        try:
            total_tests = test_results.get("total_tests", 0)
            passed_tests = test_results.get("tests_passed", 0)
            
            if total_tests == 0:
                return 50  # Default score when no tests
            
            base_score = int((passed_tests / total_tests) * 80)
            
            # Bonus points for additional quality metrics
            if test_results.get("code_coverage", 0) > 80:
                base_score += 10
            if test_results.get("lint_score", 0) > 8:
                base_score += 10
            
            return min(100, base_score)
            
        except Exception:
            return 50  # Default fallback score
    
    def _determine_error_priority(
        self,
        error_type: str,
        recovery_attempts: int
    ) -> NotificationPriority:
        """Determine escalation priority based on error characteristics."""
        # Critical errors that require immediate attention
        critical_errors = ["github_api_auth", "database_connection", "security_violation"]
        
        if error_type in critical_errors:
            return NotificationPriority.CRITICAL
        
        # High priority for multiple failed recovery attempts
        if recovery_attempts >= 3:
            return NotificationPriority.HIGH
        
        # Medium priority for most errors
        if recovery_attempts >= 1:
            return NotificationPriority.MEDIUM
        
        # Low priority for first-time errors
        return NotificationPriority.LOW
    
    async def _simulate_discord_notification(
        self,
        title: str,
        details: Dict[str, Any]
    ):
        """
        Simulate Discord notification (in real implementation, this would
        send actual Discord/Slack messages via webhooks).
        """
        self.logger.info(f"[DISCORD_NOTIFICATION] {title}")
        for key, value in details.items():
            self.logger.info(f"  {key}: {value}")


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    from unittest.mock import AsyncMock
    
    async def test_orchestrator_client():
        """Test the OrchestratorClient functionality."""
        from unittest.mock import Mock
        
        # Mock database session factory
        mock_session = Mock()
        mock_session.get.return_value = Mock(metadata={})
        mock_session.commit.return_value = None
        mock_session.close.return_value = None
        
        def mock_session_factory():
            return mock_session
        
        # Create client
        client = OrchestratorClient("backend-agent-001", mock_session_factory)
        
        print("Testing OrchestratorClient...")
        
        # Test status update
        success = await client.update_task_status(
            "task-123",
            TaskStatus.IN_PROGRESS,
            metadata={"step": "generating_code"},
            progress_percentage=45,
            current_step="Generating Flask route"
        )
        print(f"✅ Status update: {success}")
        
        # Test clarification request
        success = await client.request_clarification(
            "task-123",
            [
                "Should the API endpoint require authentication?",
                "What should be the rate limiting strategy?",
                "Are there specific validation rules for the input data?"
            ],
            priority=NotificationPriority.MEDIUM,
            context={"endpoint": "/api/users", "method": "POST"}
        )
        print(f"✅ Clarification request: {success}")
        
        # Test completion report
        success = await client.report_completion(
            "task-123",
            "https://github.com/repo/pull/42",
            {
                "total_tests": 15,
                "tests_passed": 14,
                "tests_failed": 1,
                "code_coverage": 85,
                "lint_score": 9
            },
            artifacts={"generated_files": 3, "test_files": 2}
        )
        print(f"✅ Completion report: {success}")
        
        # Test error escalation
        success = await client.escalate_error(
            "task-456",
            "github_api",
            "Failed to create pull request: API rate limit exceeded",
            recovery_attempts=2,
            context={"api_calls_made": 5000, "rate_limit_reset": "2023-09-18T15:30:00Z"}
        )
        print(f"✅ Error escalation: {success}")
        
        # Get communication stats
        stats = await client.get_communication_stats()
        print(f"✅ Communication stats: {stats}")
        
        print("\n🎉 OrchestratorClient test completed successfully!")
    
    # Run the test
    asyncio.run(test_orchestrator_client())