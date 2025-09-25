# agents/backend/backend_agent.py
"""Backend Agent that executes Flask development tasks assigned by the Orchestrator"""

import asyncio
import logging
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

from github import Github, GithubException
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Import existing models and utilities
from database.models.base import engine, SessionLocal
from database.models.task import Task, TaskStatus, TaskCategory
from database.models.agent import Agent, AgentType, AgentStatus, BACKEND_CAPABILITIES, BACKEND_CONFIG
from database.models.logs import Log, LogLevel
from .github_client import GitHubClient, sanitize_branch_name, generate_pr_description
from .task_executor import TaskExecutor

logger = logging.getLogger(__name__)

class BackendAgent:
    """
    Backend development agent that:
    - Polls task queue for backend tasks
    - Creates GitHub branches automatically  
    - Implements Flask endpoints and business logic
    - Follows 4-hour task limit rule
    - Reports progress every 30 minutes
    - Creates pull requests when complete
    """
    
    def __init__(self):
        """Initialize the Backend Agent"""
        self.name = "backend-agent-alpha"
        self.type = AgentType.BACKEND
        self.status = AgentStatus.OFFLINE
        
        # Task tracking
        self.current_task = None
        self.start_time = None
        self.last_progress_report = None
        
        # GitHub client and repository
        self.github_client = GitHubClient()
        self.repo = None  # Will be set during GitHub initialization
        self.current_branch = None  # Current working branch
        
        # Task executor
        self.task_executor = TaskExecutor(self.name)
        
        # Database session
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Performance metrics - Use consistent naming (metrics is the main one)
        self.metrics = {
            "tasks_completed": 0,
            "tasks_assigned": 0,
            "tasks_failed": 0,
            "branches_created": 0,
            "prs_created": 0,
            "uptime_start": datetime.now(timezone.utc).isoformat(),  # Store as ISO string immediately
            "last_task_completed": None,
            "average_execution_time": 0.0,
            "total_execution_time": 0.0,
            "errors_encountered": 0
        }
        
        # Keep performance_metrics as alias for backward compatibility
        self.performance_metrics = self.metrics
        
        # Task execution configuration
        self.max_task_hours = BACKEND_CONFIG.get("task_timeout_hours", 4)
        self.progress_report_interval = BACKEND_CONFIG.get("progress_report_interval", 30)  # minutes
        self.poll_interval = 10  # seconds
        
        # Task polling control
        self.is_running = False
        self.polling_interval = 5  # seconds (backward compatibility)
        
        # Agent capabilities
        self.capabilities = BACKEND_CAPABILITIES.copy()
        
        logger.info(f"🔧 Backend Agent initialized: {self.name}")
    
    async def initialize(self):
        """Initialize the backend agent"""
        try:
            # Update uptime start time (already in ISO format from __init__)
            self.metrics["uptime_start"] = datetime.now(timezone.utc).isoformat()
            
            # Initialize GitHub client
            github_initialized = await self.github_client.initialize()
            if github_initialized:
                await self._log_info("GitHub client initialized successfully")
                # Store repository reference for convenience
                if hasattr(self.github_client, 'repo'):
                    self.repo = self.github_client.repo
            else:
                await self._log_error("GitHub client initialization failed - GitHub integration disabled")
            
            # Register agent in database
            await self.register_agent()
            
            # Start background tasks
            asyncio.create_task(self._heartbeat_loop())
            asyncio.create_task(self._progress_reporting_loop())
            
            # Start main task polling loop
            asyncio.create_task(self.poll_for_tasks())
            
            await self._log_info("Backend Agent initialized successfully")
            logger.info("✅ Backend Agent initialization complete")
            
        except Exception as e:
            await self._log_error(f"Backend Agent initialization failed: {e}")
            raise
    
    async def register_agent(self):
        """Register this agent in the database"""
        try:
            with self.SessionLocal() as db:
                # Check if agent already exists
                existing_agent = db.query(Agent).filter(Agent.name == self.name).first()
                
                # Prepare metrics for JSON storage - fix the datetime conversion
                json_safe_metrics = self.metrics.copy()
                
                # Only convert datetime to string if it's actually a datetime object
                if "uptime_start" in json_safe_metrics and json_safe_metrics["uptime_start"]:
                    if hasattr(json_safe_metrics["uptime_start"], 'isoformat'):
                        # It's a datetime object, convert it
                        json_safe_metrics["uptime_start"] = json_safe_metrics["uptime_start"].isoformat()
                    # If it's already a string, leave it as is
                
                # Handle last_task_completed similarly
                if "last_task_completed" in json_safe_metrics and json_safe_metrics["last_task_completed"]:
                    if hasattr(json_safe_metrics["last_task_completed"], 'isoformat'):
                        json_safe_metrics["last_task_completed"] = json_safe_metrics["last_task_completed"].isoformat()
                
                if existing_agent:
                    # Update existing agent
                    existing_agent.status = self.status  # Use enum not string value
                    existing_agent.performance_metrics = json_safe_metrics
                    existing_agent.updated_at = datetime.now(timezone.utc)
                    await self._log_info(f"Updated agent registration: {self.name}")
                else:
                    # Create new agent
                    new_agent = Agent(
                        name=self.name,
                        type=self.type,  # Use 'type' not 'agent_type'
                        status=self.status,  # Use enum not string value
                        capabilities=self.capabilities,
                        performance_metrics=json_safe_metrics
                    )
                    db.add(new_agent)
                    await self._log_info(f"Registered new agent: {self.name}")
                
                db.commit()
                logger.info(f"✅ Agent {self.name} registered successfully")
                
        except Exception as e:
            await self._log_error(f"Failed to register agent: {e}")
            logger.error(f"❌ Agent registration failed: {e}")
            raise
    
    async def poll_for_tasks(self):
        """Continuously check for backend tasks in ASSIGNED status"""
        await self._log_info("Starting task polling loop")
        
        while True:
            try:
                if self.current_task is None and self.status == AgentStatus.ACTIVE:
                    # Look for assigned backend tasks
                    db = self.SessionLocal()
                    try:
                        task = db.query(Task).filter(
                            Task.category == TaskCategory.BACKEND,
                            Task.status == TaskStatus.ASSIGNED,
                            Task.assigned_agent == self.name
                        ).first()
                        
                        if task:
                            await self._log_info(f"Found assigned task: {task.id}")
                            self.current_task = task
                            self.start_time = datetime.now(timezone.utc)
                            self.last_progress_report = self.start_time
                            
                            await self.update_status(AgentStatus.BUSY)
                            
                            # Execute task in background
                            asyncio.create_task(self.execute_task(task))
                        
                    finally:
                        db.close()
                
                await asyncio.sleep(self.poll_interval)
                
            except Exception as e:
                await self._log_error(f"Task polling error: {e}")
                await asyncio.sleep(self.poll_interval * 2)  # Longer delay on error
    
    async def execute_task(self, task: Task):
        """Main task execution method"""
        try:
            await self._log_info(f"Starting execution of task {task.id}: {task.title}")
            
            # Update task status to IN_PROGRESS
            await self._update_task_status(task.id, TaskStatus.IN_PROGRESS)
            
            # Parse task requirements and success criteria
            task_requirements = await self._parse_task_requirements(task)
            
            # Create GitHub branch
            branch_name = await self.create_github_branch(str(task.id), task.title)
            if branch_name:
                await self._update_task_metadata(task.id, {"github_branch": branch_name})
                self.current_branch = branch_name  # Store for file operations
            
            # Execute task using TaskExecutor
            if self._is_flask_endpoint_task(task_requirements):
                execution_result = await self.task_executor.execute_flask_endpoint(task)
            else:
                execution_result = await self._execute_general_backend_task_with_executor(task)
            
            # Handle execution results
            if execution_result["success"]:
                # Commit files to GitHub if available
                if branch_name and "implementation" in execution_result:
                    files = execution_result["implementation"]["files"]
                    commit_message = f"Implement: {task.title}"
                    
                    success = await self.github_client.commit_changes(
                        branch_name, files, commit_message
                    )
                    
                    if success:
                        await self._log_info(f"Committed {len(files)} files to branch {branch_name}")
                    else:
                        await self._log_error("Failed to commit files to GitHub")
                
                # Run tests if files were created
                if "implementation" in execution_result and execution_result["implementation"]["files"]:
                    test_results = await self.task_executor.run_tests(
                        list(execution_result["implementation"]["files"].keys())
                    )
                    await self._update_task_metadata(task.id, {"test_results": test_results})
            else:
                raise Exception(execution_result.get("error", "Task execution failed"))
            
            # Report completion
            await self.report_progress(str(task.id), 100.0, "Task completed successfully")
            
            # Create pull request
            if branch_name and self.repo:
                pr_url = await self.create_pull_request(branch_name, task)
                if pr_url:
                    await self._update_task_metadata(task.id, {"github_pr_url": pr_url})
            
            # Update task status
            await self._update_task_status(task.id, TaskStatus.REVIEW_READY)
            
            # Update metrics
            self.metrics["tasks_completed"] += 1
            execution_time = (datetime.now(timezone.utc) - self.start_time).total_seconds() / 3600
            self.metrics["total_execution_time"] += execution_time
            
            await self._log_info(f"Task {task.id} completed successfully in {execution_time:.2f} hours")
            
        except Exception as e:
            await self._log_error(f"Task execution failed: {e}")
            await self._update_task_status(task.id, TaskStatus.FAILED)
            self.metrics["tasks_failed"] += 1
            self.metrics["errors_encountered"] += 1
            
        finally:
            # Reset current task and status
            self.current_task = None
            self.start_time = None
            self.last_progress_report = None
            self.current_branch = None  # Reset branch reference
            await self.update_status(AgentStatus.ACTIVE)
    
    async def _execute_general_backend_task_with_executor(self, task: Task) -> Dict[str, Any]:
        """Execute general backend tasks using TaskExecutor"""
        try:
            await self._log_info("Executing general backend task with TaskExecutor")
            
            # For general tasks, we can still use the task executor's validation
            # and code generation capabilities
            task_requirements = await self._parse_task_requirements(task)
            
            # Generate basic implementation
            implementation_code = self._generate_general_implementation(task_requirements)
            
            # Validate the implementation
            validation_result = await self.task_executor.validate_implementation(task, implementation_code)
            
            # Determine file path
            file_path = f"app/backend_{task_requirements.get('task_id', 'implementation')}.py"
            
            # Create files dictionary
            files = {file_path: implementation_code}
            
            # Generate basic test if possible
            test_code = self._generate_basic_test(task_requirements)
            if test_code:
                test_file = f"tests/test_{task_requirements.get('function_name', 'backend')}.py"
                files[test_file] = test_code
            
            result = {
                "success": True,
                "implementation": {
                    "files": files,
                    "validation_passed": validation_result,
                    "task_type": "general_backend"
                },
                "message": "General backend implementation completed",
                "files_created": len(files)
            }
            
            return result
            
        except Exception as e:
            await self._log_error(f"General backend task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to execute general backend task: {str(e)[:100]}..."
            }
    
    async def create_flask_endpoint(self, endpoint_spec: Dict):
        """Specialized method for Flask endpoint creation using TaskExecutor"""
        try:
            await self._log_info("Creating Flask endpoint using TaskExecutor")
            
            # Create a temporary task object for the executor
            # In real usage, this would be the actual task from the database
            task_data = {
                "id": endpoint_spec.get("task_id", "temp-task"),
                "title": endpoint_spec.get("title", "Flask Endpoint Creation"),
                "description": endpoint_spec.get("description", "Create Flask endpoint"),
                "success_criteria": endpoint_spec.get("success_criteria", []),
                "task_metadata": endpoint_spec
            }
            
            # Execute using TaskExecutor
            execution_result = await self.task_executor.execute_flask_endpoint(
                type('Task', (), task_data)()  # Create a simple object with task attributes
            )
            
            if execution_result["success"]:
                # Commit files to GitHub if branch is available
                if hasattr(self, 'current_branch') and self.current_branch:
                    files = execution_result["implementation"]["files"]
                    commit_message = f"Implement {endpoint_spec.get('route', 'endpoint')}"
                    
                    await self.github_client.commit_changes(
                        self.current_branch, files, commit_message
                    )
                
                await self.report_progress(
                    str(self.current_task.id), 
                    80.0, 
                    f"Flask endpoint {execution_result['implementation']['route_path']} created"
                )
            else:
                await self._log_error(f"Flask endpoint creation failed: {execution_result.get('error', 'Unknown error')}")
                raise Exception(execution_result.get("error", "Task execution failed"))
            
        except Exception as e:
            await self._log_error(f"Flask endpoint creation failed: {e}")
            raise
    
    async def create_github_branch(self, task_id: str, description: str) -> Optional[str]:
        """Create feature branch: feature/backend-{task_id}-{description}"""
        try:
            # Sanitize description for branch name
            sanitized_desc = sanitize_branch_name(description)
            branch_name = f"feature/backend-{task_id[:8]}-{sanitized_desc}"
            
            # Create branch using GitHub client
            created_branch = await self.github_client.create_branch(branch_name)
            
            if created_branch:
                self.metrics["branches_created"] += 1
                await self._log_info(f"Created GitHub branch: {branch_name}")
                return branch_name
            else:
                await self._log_error(f"Failed to create GitHub branch: {branch_name}")
                return None
                
        except Exception as e:
            await self._log_error(f"GitHub branch creation failed: {e}")
            return None
    
    async def create_pull_request(self, branch_name: str, task: Task) -> Optional[str]:
        """Create PR with task summary and changes"""
        try:
            pr_title = f"Backend: {task.title}"
            
            # Calculate execution time
            execution_time = None
            if self.start_time:
                execution_time = (datetime.now(timezone.utc) - self.start_time).total_seconds() / 3600
            
            # Generate PR description using utility function
            pr_body = generate_pr_description(
                task_title=task.title,
                task_description=task.description,
                success_criteria=task.success_criteria or [],
                agent_name=self.name,
                execution_time=execution_time
            )
            
            # Create pull request using GitHub client
            pr_url = await self.github_client.create_pull_request(
                branch_name=branch_name,
                title=pr_title,
                description=pr_body
            )
            
            if pr_url:
                self.metrics["prs_created"] += 1
                await self._log_info(f"Created pull request: {pr_url}")
                return pr_url
            else:
                await self._log_error("Failed to create pull request")
                return None
                
        except Exception as e:
            await self._log_error(f"Pull request creation failed: {e}")
            return None
    
    async def report_progress(self, task_id: str, percentage: float, message: str):
        """Report progress to Orchestrator every 30 minutes"""
        try:
            # Update task metadata with progress
            await self._update_task_metadata(task_id, {
                "progress_percentage": percentage,
                "last_progress_update": datetime.now(timezone.utc).isoformat(),
                "current_status_message": message
            })
            
            await self._log_info(f"Progress report - Task {task_id}: {percentage}% - {message}")
            
        except Exception as e:
            await self._log_error(f"Progress reporting failed: {e}")
    
    async def update_status(self, status: AgentStatus):
        """Update agent status in database"""
        self.status = status
        db = self.SessionLocal()
        try:
            agent = db.query(Agent).filter(Agent.name == self.name).first()
            if agent:
                agent.status = status
                agent.last_heartbeat = datetime.now(timezone.utc)
                
                # Ensure performance_metrics contains only JSON-serializable data
                json_safe_metrics = self.metrics.copy()
                if "uptime_start" in json_safe_metrics and json_safe_metrics["uptime_start"] is not None:
                    if isinstance(json_safe_metrics["uptime_start"], datetime):
                        json_safe_metrics["uptime_start"] = json_safe_metrics["uptime_start"].isoformat()
                
                agent.performance_metrics = json_safe_metrics
                if self.current_task:
                    agent.current_task_id = self.current_task.id
                else:
                    agent.current_task_id = None
                db.commit()
                await self._log_info(f"Agent status updated to: {status.value}")
        except Exception as e:
            db.rollback()
            await self._log_error(f"Status update failed: {e}")
        finally:
            db.close()
    
    def _generate_general_implementation(self, requirements: Dict) -> str:
        """Generate general backend implementation code"""
        try:
            description = requirements.get("description", "")
            title = requirements.get("title", "Backend Task")
            task_id = requirements.get("task_id", "unknown")
            
            code = f'''
# Generated backend implementation
# Task: {title}
# Task ID: {task_id}
# Description: {description}

from datetime import datetime, timezone
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BackendImplementation:
    """
    Generated implementation for: {title}
    """
    
    def __init__(self):
        self.created_at = datetime.now(timezone.utc)
        self.task_id = "{task_id}"
        logger.info(f"Backend implementation initialized for task {{self.task_id}}")
    
    def execute(self) -> Dict[str, Any]:
        """
        Main execution method
        
        Returns:
            Dict containing execution results
        """
        try:
            logger.info(f"Executing backend implementation for task {{self.task_id}}")
            
            # TODO: Implement the actual business logic
            # This is a generated template - customize as needed
            # Task description: {description}
            
            result = {{
                "success": True,
                "message": "Backend implementation executed successfully",
                "task_id": self.task_id,
                "timestamp": self.created_at.isoformat(),
                "execution_time": (datetime.now(timezone.utc) - self.created_at).total_seconds()
            }}
            
            logger.info(f"Backend implementation completed successfully for task {{self.task_id}}")
            return result
            
        except Exception as e:
            logger.error(f"Backend implementation failed for task {{self.task_id}}: {{e}}")
            return {{
                "success": False,
                "error": str(e),
                "task_id": self.task_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }}
    
    def validate(self) -> bool:
        """
        Validate the implementation
        
        Returns:
            True if validation passes, False otherwise
        """
        try:
            # Basic validation checks
            checks = [
                self.task_id is not None,
                self.created_at is not None,
                hasattr(self, 'execute')
            ]
            
            return all(checks)
            
        except Exception as e:
            logger.error(f"Validation failed: {{e}}")
            return False

# Example usage
if __name__ == "__main__":
    implementation = BackendImplementation()
    
    # Validate implementation
    if implementation.validate():
        result = implementation.execute()
        print(f"Result: {{result}}")
    else:
        print("Implementation validation failed")
'''
            
            return code.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate general implementation: {e}")
            return f"# Error generating implementation: {str(e)}"
    
    def _generate_basic_test(self, requirements: Dict) -> Optional[str]:
        """Generate basic test code for general implementations"""
        try:
            function_name = requirements.get("function_name", "backend")
            task_id = requirements.get("task_id", "unknown")
            
            test_code = f'''
import pytest
from datetime import datetime, timezone
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_{function_name}_initialization():
    """Test backend implementation initialization"""
    from app.backend_{task_id} import BackendImplementation
    
    impl = BackendImplementation()
    assert impl.task_id == "{task_id}"
    assert impl.created_at is not None
    assert isinstance(impl.created_at, datetime)

def test_{function_name}_execution():
    """Test backend implementation execution"""
    from app.backend_{task_id} import BackendImplementation
    
    impl = BackendImplementation()
    result = impl.execute()
    
    assert isinstance(result, dict)
    assert "success" in result
    assert "task_id" in result
    assert result["task_id"] == "{task_id}"

def test_{function_name}_validation():
    """Test backend implementation validation"""
    from app.backend_{task_id} import BackendImplementation
    
    impl = BackendImplementation()
    assert impl.validate() is True

def test_{function_name}_error_handling():
    """Test error handling in backend implementation"""
    from app.backend_{task_id} import BackendImplementation
    
    impl = BackendImplementation()
    
    # The implementation should handle errors gracefully
    result = impl.execute()
    assert "success" in result
    assert "timestamp" in result
'''
            
            return test_code.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate basic test: {e}")
            return None
    
    async def _parse_task_requirements(self, task: Task) -> Dict[str, Any]:
        """Parse task description to extract requirements"""
        try:
            # Basic parsing logic - in production this would be more sophisticated
            description = task.description.lower()
            
            requirements = {
                "description": task.description,
                "title": task.title,
                "task_id": str(task.id),
                "success_criteria": task.success_criteria or [],
                "metadata": task.task_metadata or {}
            }
            
            # Extract route information
            if "endpoint" in description or "api" in description:
                # Look for route patterns
                route_match = re.search(r'/api/[\w/]+', task.description)
                if route_match:
                    requirements["route"] = route_match.group()
                
                # Look for HTTP method
                for method in ["POST", "GET", "PUT", "DELETE", "PATCH"]:
                    if method.lower() in description:
                        requirements["method"] = method
                        break
            
            # Extract function name from title
            function_name = re.sub(r'[^a-zA-Z0-9_]', '_', task.title.lower())
            requirements["function_name"] = function_name
            
            return requirements
            
        except Exception as e:
            await self._log_error(f"Task requirement parsing failed: {e}")
            return {"description": task.description, "title": task.title}
    
    def _is_flask_endpoint_task(self, requirements: Dict) -> bool:
        """Determine if task is a Flask endpoint creation task"""
        description = requirements.get("description", "").lower()
        return any(keyword in description for keyword in [
            "endpoint", "api", "route", "flask", "rest"
        ])
    
    async def _execute_general_backend_task(self, requirements: Dict):
        """Execute general backend development tasks"""
        try:
            await self._log_info("Executing general backend task")
            
            # For general tasks, create a basic implementation structure
            description = requirements.get("description", "")
            
            # Generate basic code structure
            code = f'''
# Generated backend implementation
# Task: {requirements.get("title", "Backend Task")}
# Description: {description}

from datetime import datetime, timezone
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BackendImplementation:
    """
    Generated implementation for: {requirements.get("title", "Backend Task")}
    """
    
    def __init__(self):
        self.created_at = datetime.now(timezone.utc)
        logger.info("Backend implementation initialized")
    
    def execute(self) -> Dict[str, Any]:
        """
        Main execution method
        
        Returns:
            Dict containing execution results
        """
        try:
            # TODO: Implement the actual business logic
            # This is a generated template - customize as needed
            
            result = {{
                "success": True,
                "message": "Backend implementation executed successfully",
                "timestamp": self.created_at.isoformat(),
                "task_id": "{requirements.get('task_id', 'unknown')}"
            }}
            
            logger.info("Backend implementation executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Backend implementation failed: {{e}}")
            return {{
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }}

# Example usage
if __name__ == "__main__":
    implementation = BackendImplementation()
    result = implementation.execute()
    print(result)
'''
            
            # Write to appropriate file
            file_path = f"app/backend_{requirements.get('task_id', 'implementation')}.py"
            await self._write_code_to_file(file_path, code, requirements)
            
            await self.report_progress(
                requirements.get("task_id"), 
                80.0, 
                "General backend implementation completed"
            )
            
        except Exception as e:
            await self._log_error(f"General backend task execution failed: {e}")
            raise
    
    async def _write_code_to_file(self, file_path: str, code: str, requirements: Dict):
        """Write generated code to file (simulated for this implementation)"""
        try:
            # In a real implementation, this would write to the actual file system
            # For this demo, we'll just log the action
            await self._log_info(f"Writing code to file: {file_path}")
            
            # Simulate file creation
            await asyncio.sleep(0.1)  # Simulate I/O operation
            
            await self._log_info(f"Code successfully written to {file_path}")
            
        except Exception as e:
            await self._log_error(f"Failed to write code to {file_path}: {e}")
            raise
    
    async def _update_task_status(self, task_id: str, status: TaskStatus):
        """Update task status in database"""
        db = self.SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = status
                task.updated_at = datetime.now(timezone.utc)
                
                if status == TaskStatus.IN_PROGRESS and not task.started_at:
                    task.started_at = datetime.now(timezone.utc)
                elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.REVIEW_READY]:
                    task.completed_at = datetime.now(timezone.utc)
                    if task.started_at:
                        actual_hours = (task.completed_at - task.started_at).total_seconds() / 3600
                        task.actual_hours = actual_hours
                
                db.commit()
                await self._log_info(f"Task {task_id} status updated to {status.value}")
        except Exception as e:
            db.rollback()
            await self._log_error(f"Task status update failed: {e}")
        finally:
            db.close()
    
    async def _update_task_metadata(self, task_id: str, metadata_update: Dict):
        """Update task metadata"""
        db = self.SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                if task.task_metadata is None:
                    task.task_metadata = {}
                task.task_metadata.update(metadata_update)
                task.updated_at = datetime.now(timezone.utc)
                db.commit()
        except Exception as e:
            db.rollback()
            await self._log_error(f"Task metadata update failed: {e}")
        finally:
            db.close()
    
    async def _heartbeat_loop(self):
        """Background heartbeat to update agent status"""
        while True:
            try:
                await self.update_status(self.status)
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")
                await asyncio.sleep(60)  # Longer delay on error
    
    async def _progress_reporting_loop(self):
        """Background progress reporting every 30 minutes during task execution"""
        while True:
            try:
                if (self.current_task and self.start_time and 
                    self.last_progress_report and
                    (datetime.now(timezone.utc) - self.last_progress_report).total_seconds() >= 1800):  # 30 minutes
                    
                    # Calculate progress based on time elapsed
                    elapsed_hours = (datetime.now(timezone.utc) - self.start_time).total_seconds() / 3600
                    estimated_hours = self.current_task.estimated_hours or 1.0
                    progress_percentage = min(90.0, (elapsed_hours / estimated_hours) * 100)
                    
                    await self.report_progress(
                        str(self.current_task.id),
                        progress_percentage,
                        f"In progress - {elapsed_hours:.1f}h elapsed of {estimated_hours}h estimated"
                    )
                    
                    self.last_progress_report = datetime.now(timezone.utc)
                    
                    # Check for task timeout
                    if elapsed_hours >= self.max_task_hours:
                        await self._log_error(f"Task {self.current_task.id} exceeded {self.max_task_hours}h limit")
                        await self._update_task_status(self.current_task.id, TaskStatus.FAILED)
                        self.current_task = None
                        await self.update_status(AgentStatus.ACTIVE)
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Progress reporting loop failed: {e}")
                await asyncio.sleep(600)  # Longer delay on error
    
    async def _log_info(self, message: str, task_id: Optional[str] = None):
        """Log info message to database"""
        await self._log(LogLevel.INFO, message, task_id)
    
    async def _log_error(self, message: str, task_id: Optional[str] = None):
        """Log error message to database"""
        await self._log(LogLevel.ERROR, message, task_id)
    
    async def _log(self, level: LogLevel, message: str, task_id: Optional[str] = None):
        """Log message to database"""
        db = self.SessionLocal()
        try:
            log_entry = Log(
                agent_name=self.name,
                task_id=task_id or (str(self.current_task.id) if self.current_task else None),
                level=level,
                message=message,
                context="backend_agent"
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log message: {e}")
        finally:
            db.close()
    
    def get_status_report(self) -> Dict[str, Any]:
        """Generate agent status report"""
        try:
            uptime = None
            if self.metrics["uptime_start"]:
                # Handle uptime_start as ISO string (convert back to datetime for calculation)
                if isinstance(self.metrics["uptime_start"], str):
                    try:
                        # Handle ISO format string and convert to timezone-aware datetime
                        uptime_start_str = self.metrics["uptime_start"]
                        if uptime_start_str.endswith('Z'):
                            uptime_start_str = uptime_start_str[:-1] + '+00:00'
                        uptime_start = datetime.fromisoformat(uptime_start_str)
                        if uptime_start.tzinfo is None:
                            uptime_start = uptime_start.replace(tzinfo=timezone.utc)
                    except (ValueError, AttributeError):
                        # Fallback if parsing fails
                        uptime_start = datetime.now(timezone.utc)
                else:
                    uptime_start = self.metrics["uptime_start"]
                uptime_delta = datetime.now(timezone.utc) - uptime_start
                uptime = str(uptime_delta).split('.')[0]  # Remove microseconds
            
            current_task_info = None
            if self.current_task:
                elapsed_time = None
                if self.start_time:
                    elapsed_delta = datetime.now(timezone.utc) - self.start_time
                    elapsed_time = str(elapsed_delta).split('.')[0]
                
                current_task_info = {
                    "task_id": str(self.current_task.id),
                    "title": self.current_task.title,
                    "elapsed_time": elapsed_time,
                    "estimated_hours": self.current_task.estimated_hours
                }
            
            return {
                "agent_name": self.name,
                "agent_type": self.type.value,
                "status": self.status.value,
                "uptime": uptime,
                "current_task": current_task_info,
                "capabilities": self.capabilities,
                "performance_metrics": self.metrics,
                "github_integration": self.github_client.get_stats(),
                "task_executor_stats": self.task_executor.get_stats(),
                "configuration": {
                    "max_task_hours": self.max_task_hours,
                    "progress_report_interval": self.progress_report_interval,
                    "poll_interval": self.poll_interval
                }
            }
            
        except Exception as e:
            return {"error": f"Failed to generate status report: {str(e)[:100]}..."}
    
    async def run(self):
        """Run the backend agent (keep it running indefinitely)"""
        try:
            # Update status to active
            await self.update_status(AgentStatus.ACTIVE)
            
            # Keep the agent running
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Backend Agent shutting down...")
            await self.update_status(AgentStatus.OFFLINE)
        except Exception as e:
            logger.error(f"Backend Agent crashed: {e}")
            await self.update_status(AgentStatus.ERROR)
            raise

# Entry point for running the backend agent
async def main():
    """Main entry point for Backend Agent"""
    try:
        agent = BackendAgent()
        await agent.initialize()
        
        # Keep the agent running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Backend Agent shutting down...")
    except Exception as e:
        logger.error(f"Backend Agent crashed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())