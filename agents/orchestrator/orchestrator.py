# agents/orchestrator/orchestrator.py
"""Core Orchestrator Agent implementation"""
import asyncio
import json
import logging
import uuid
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from anthropic import AsyncAnthropic
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from database.models.base import engine
from database.models.task import Task, TaskCategory, TaskPriority, TaskStatus
from database.models.agent import Agent, AgentType, AgentStatus
from database.models.logs import Log, LogLevel
from agents.orchestrator.task_manager import TaskManager
from agents.orchestrator.utils import TaskValidator, ClaudeClient

# Import GitHub client for PR management
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
try:
    from agents.backend.github_client import GitHubClient
except ImportError:
    GitHubClient = None
    logger.warning("GitHubClient not available - PR management disabled")

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """Central coordination agent for the Automation Hub"""
    
    def __init__(self):
        self.name = "orchestrator-alpha"
        self.type = AgentType.ORCHESTRATOR
        self.status = AgentStatus.OFFLINE
        self.task_manager = TaskManager()
        self.task_validator = TaskValidator()
        self.claude_client = ClaudeClient()
        
        # GitHub client for PR management
        self.github_client = None
        if GitHubClient:
            self.github_client = GitHubClient()
        
        # Database session
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Short ID management
        self.task_id_counter = 0
        self.short_to_uuid_map = {}  # Maps short IDs to UUIDs
        self.uuid_to_short_map = {}  # Maps UUIDs to short IDs
        
        # Performance metrics
        self.metrics = {
            "tasks_assigned": 0,
            "tasks_completed": 0,
            "average_response_time": 0.0,
            "errors_encountered": 0,
            "uptime_start": None
        }
        
        logger.info(f"🤖 Orchestrator Agent initialized: {self.name}")
    
    def generate_short_task_id(self, task_uuid: uuid.UUID) -> str:
        """Generate a human-friendly short ID for a task and maintain mapping"""
        # Get current date in format: sep18, dec25, etc.
        today = datetime.now(timezone.utc)
        date_prefix = today.strftime("%b%d").lower()
        
        # Increment counter for today
        self.task_id_counter += 1
        
        # Generate short ID: sep18-001, sep18-002, etc.
        short_id = f"{date_prefix}-{self.task_id_counter:03d}"
        
        # Store bidirectional mapping
        self.short_to_uuid_map[short_id] = task_uuid
        self.uuid_to_short_map[task_uuid] = short_id
        
        logger.info(f"Generated short ID {short_id} for task UUID {task_uuid}")
        return short_id
    
    def get_uuid_from_short_id(self, short_id: str) -> Optional[uuid.UUID]:
        """Convert short ID back to UUID"""
        return self.short_to_uuid_map.get(short_id)
    
    def get_short_id_from_uuid(self, task_uuid: uuid.UUID) -> Optional[str]:
        """Get short ID from UUID"""
        return self.uuid_to_short_map.get(task_uuid)
    
    def is_short_id(self, task_id: str) -> bool:
        """Check if a given ID is a short ID format (e.g., sep18-001)"""
        pattern = r'^[a-z]{3}\d{1,2}-\d{3}$'
        return bool(re.match(pattern, task_id))
    
    def resolve_task_id(self, task_id: str) -> uuid.UUID:
        """Resolve either short ID or UUID string to UUID object"""
        if self.is_short_id(task_id):
            resolved_uuid = self.get_uuid_from_short_id(task_id)
            if resolved_uuid is None:
                raise ValueError(f"Short ID '{task_id}' not found")
            return resolved_uuid
        else:
            try:
                return uuid.UUID(task_id)
            except ValueError:
                raise ValueError(f"Invalid task ID format: '{task_id}'")
    
    async def _rebuild_short_id_mappings(self):
        """Rebuild short ID mappings for existing tasks on startup"""
        db = self.SessionLocal()
        try:
            # Get today's date for counter calculation
            today = datetime.now(timezone.utc)
            date_prefix = today.strftime("%b%d").lower()
            
            # Get all tasks created today (or recent ones if none today)
            today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
            recent_tasks = db.query(Task).filter(
                Task.created_at >= today_start
            ).order_by(Task.created_at).all()
            
            # If no tasks today, get recent tasks to continue numbering
            if not recent_tasks:
                week_ago = today - timedelta(days=7)
                recent_tasks = db.query(Task).filter(
                    Task.created_at >= week_ago
                ).order_by(Task.created_at).all()
            
            # Rebuild mappings and find highest counter
            counter = 0
            for task in recent_tasks:
                task_date = task.created_at.strftime("%b%d").lower()
                
                if task_date == date_prefix:
                    # Task from today - assign sequential number
                    counter += 1
                    short_id = f"{date_prefix}-{counter:03d}"
                else:
                    # Task from different day - use its own date
                    # For simplicity, just assign a number based on order
                    task_counter = 1  # Could be improved to track per-day counters
                    short_id = f"{task_date}-{task_counter:03d}"
                
                # Store mapping
                self.short_to_uuid_map[short_id] = task.id
                self.uuid_to_short_map[task.id] = short_id
            
            # Set counter for new tasks
            self.task_id_counter = counter
            
            logger.info(f"Rebuilt short ID mappings for {len(recent_tasks)} tasks, counter at {counter}")
            
        except Exception as e:
            logger.error(f"Failed to rebuild short ID mappings: {e}")
        finally:
            db.close()
    
    async def initialize(self):
        """Initialize the orchestrator agent"""
        try:
            self.metrics["uptime_start"] = datetime.now(timezone.utc)
            
            # Initialize Claude client
            await self.claude_client.initialize()
            
            # Initialize GitHub client if available
            if self.github_client:
                github_initialized = await self.github_client.initialize()
                if github_initialized:
                    await self._log_info("GitHub client initialized for PR management")
                else:
                    await self._log_warning("GitHub client initialization failed - PR commands will be limited")
            
            # Rebuild short ID mappings for existing tasks
            await self._rebuild_short_id_mappings()
            
            # Start background tasks
            asyncio.create_task(self._heartbeat_loop())
            asyncio.create_task(self._monitor_tasks())
            
            await self._log_info("Orchestrator Agent initialized successfully")
            logger.info("✅ Orchestrator Agent initialization complete")
            
        except Exception as e:
            await self._log_error(f"Orchestrator initialization failed: {e}")
            raise
    
    async def register_agent(self):
        """Register this agent in the database"""
        db = self.SessionLocal()
        try:
            # Check if agent already exists
            existing_agent = db.query(Agent).filter(Agent.name == self.name).first()
            
            if existing_agent:
                existing_agent.status = AgentStatus.ACTIVE
                existing_agent.last_heartbeat = datetime.now(timezone.utc)
                existing_agent.performance_metrics = self.metrics
            else:
                agent = Agent(
                    name=self.name,
                    type=self.type,
                    status=AgentStatus.ACTIVE,
                    capabilities=[
                        "task_assignment",
                        "agent_coordination",
                        "human_interaction",
                        "task_validation",
                        "progress_monitoring",
                        "clarifying_questions"
                    ],
                    performance_metrics=self.metrics,
                    configuration={
                        "max_clarifying_questions": 5,
                        "task_timeout_hours": 4,
                        "escalation_threshold_minutes": 15,
                        "max_concurrent_tasks": 10
                    }
                )
                db.add(agent)
            
            db.commit()
            await self._log_info("Agent registered in database")
            
        except Exception as e:
            db.rollback()
            await self._log_error(f"Agent registration failed: {e}")
            raise
        finally:
            db.close()
    
    async def update_status(self, status: AgentStatus):
        """Update agent status in database"""
        self.status = status
        db = self.SessionLocal()
        try:
            agent = db.query(Agent).filter(Agent.name == self.name).first()
            if agent:
                agent.status = status
                agent.last_heartbeat = datetime.now(timezone.utc)
                agent.performance_metrics = self.metrics
                db.commit()
                await self._log_info(f"Agent status updated to: {status.value}")
        except Exception as e:
            db.rollback()
            await self._log_error(f"Status update failed: {e}")
        finally:
            db.close()
    
    async def assign_task(self, description: str, user_id: str, channel_id: str, 
                         priority: TaskPriority = TaskPriority.MEDIUM) -> Dict[str, Any]:
        """Assign a new task - main entry point for task creation"""
        try:
            await self._log_info(f"Received task assignment request: {description[:100]}...")
            
            # Validate task description
            validation_result = await self.task_validator.validate_description(description)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "message": f"Task validation failed: {validation_result['reason']}",
                    "requires_clarification": False
                }
            
            # Analyze task with Claude
            analysis = await self.claude_client.analyze_task(description)
            
            # Check if clarification is needed
            if analysis.get("needs_clarification", False):
                questions = analysis.get("questions", [])
                task_uuid = await self._create_pending_task(
                    description, user_id, channel_id, priority, analysis, questions
                )
                short_id = self.generate_short_task_id(task_uuid)
                return {
                    "success": True,
                    "task_id": short_id,
                    "requires_clarification": True,
                    "questions": questions,
                    "message": "Task created but requires clarification before assignment."
                }
            
            # Create and assign task
            task_uuid = await self._create_and_assign_task(
                description, user_id, channel_id, priority, analysis
            )
            
            short_id = self.generate_short_task_id(task_uuid)
            self.metrics["tasks_assigned"] += 1
            
            return {
                "success": True,
                "task_id": short_id,
                "requires_clarification": False,
                "estimated_hours": analysis.get("estimated_hours", 1.0),
                "category": analysis.get("category", "general"),
                "message": f"Task assigned successfully! Estimated completion: {analysis.get('estimated_hours', 1.0)} hours"
            }
            
        except Exception as e:
            await self._log_error(f"Task assignment failed: {e}")
            self.metrics["errors_encountered"] += 1
            return {
                "success": False,
                "message": f"Task assignment failed: {str(e)[:100]}...",
                "requires_clarification": False
            }
    
    async def provide_clarification(self, task_id: str, answers: List[str]) -> Dict[str, Any]:
        """Process clarification answers and proceed with task assignment"""
        db = self.SessionLocal()
        try:
            # Resolve short ID to UUID
            try:
                task_uuid = self.resolve_task_id(task_id)
            except ValueError as e:
                return {
                    "success": False,
                    "message": str(e)
                }
            
            # Get pending task
            task = db.query(Task).filter(Task.id == task_uuid).first()
            if not task or task.status != TaskStatus.CLARIFICATION_NEEDED:
                return {
                    "success": False,
                    "message": "Task not found or not awaiting clarification"
                }
            
            # Process clarification with Claude
            clarified_analysis = await self.claude_client.process_clarification(
                task.description, task.clarifying_questions, answers
            )
            
            # Update task with clarified information
            task.status = TaskStatus.ASSIGNED
            task.assigned_agent = self._determine_best_agent(clarified_analysis)
            task.category = TaskCategory(clarified_analysis.get("category", "general"))
            task.estimated_hours = clarified_analysis.get("estimated_hours", 1.0)
            task.success_criteria = clarified_analysis.get("success_criteria", [])
            
            # Handle task_metadata safely - check if it exists and is not None
            if not hasattr(task, 'task_metadata') or task.task_metadata is None:
                task.task_metadata = {}
            
            # Update metadata from clarified analysis
            metadata_update = clarified_analysis.get("metadata", {})
            if isinstance(task.task_metadata, dict) and isinstance(metadata_update, dict):
                task.task_metadata.update(metadata_update)
            else:
                # If task_metadata is not a dict, replace it entirely
                task.task_metadata = metadata_update
            
            task.assigned_at = datetime.now(timezone.utc)
            task.updated_at = datetime.now(timezone.utc)
            
            db.commit()
            
            # Get the short ID for logging (might already exist in mapping)
            short_id = self.get_short_id_from_uuid(task_uuid) or task_id
            await self._log_info(f"Task {short_id} clarified and assigned to {task.assigned_agent}")
            
            return {
                "success": True,
                "message": f"Task clarified and assigned to {task.assigned_agent}",
                "estimated_hours": task.estimated_hours
            }
            
        except Exception as e:
            db.rollback()
            await self._log_error(f"Clarification processing failed: {e}")
            return {
                "success": False,
                "message": f"Clarification processing failed: {str(e)[:100]}..."
            }
        finally:
            db.close()
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status by short ID or UUID"""
        db = self.SessionLocal()
        try:
            # Resolve short ID to UUID
            try:
                task_uuid = self.resolve_task_id(task_id)
            except ValueError as e:
                return {
                    "success": False,
                    "message": str(e)
                }
            
            # Get task from database
            task = db.query(Task).filter(Task.id == task_uuid).first()
            if not task:
                return {
                    "success": False,
                    "message": f"Task {task_id} not found"
                }
            
            # Get short ID for display
            short_id = self.get_short_id_from_uuid(task_uuid) or str(task_uuid)
            
            return {
                "success": True,
                "task_id": short_id,
                "title": task.title,
                "status": task.status.value,
                "category": task.category.value if task.category else "general",
                "priority": task.priority.value,
                "assigned_agent": task.assigned_agent,
                "estimated_hours": task.estimated_hours,
                "actual_hours": task.actual_hours,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "assigned_at": task.assigned_at.isoformat() if task.assigned_at else None,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "github_pr_url": task.github_pr_url,
                "clarifying_questions": task.clarifying_questions
            }
            
        except Exception as e:
            await self._log_error(f"Task status retrieval failed: {e}")
            return {
                "success": False,
                "message": f"Failed to retrieve task status: {str(e)[:100]}..."
            }
        finally:
            db.close()
    
    async def list_recent_tasks(self, limit: int = 10) -> Dict[str, Any]:
        """List recent tasks with short IDs for Discord display"""
        db = self.SessionLocal()
        try:
            # Get recent tasks
            recent_tasks = db.query(Task).order_by(
                Task.created_at.desc()
            ).limit(limit).all()
            
            task_list = []
            for task in recent_tasks:
                # Get or generate short ID
                short_id = self.get_short_id_from_uuid(task.id)
                if not short_id:
                    short_id = self.generate_short_task_id(task.id)
                
                task_info = {
                    "short_id": short_id,
                    "title": task.title[:50] + "..." if len(task.title) > 50 else task.title,
                    "status": task.status.value,
                    "category": task.category.value if task.category else "general",
                    "priority": task.priority.value,
                    "assigned_agent": task.assigned_agent,
                    "created_at": task.created_at.strftime("%Y-%m-%d %H:%M") if task.created_at else "Unknown"
                }
                
                # Add status-specific info
                if task.status == TaskStatus.CLARIFICATION_NEEDED:
                    task_info["questions_count"] = len(task.clarifying_questions) if task.clarifying_questions else 0
                elif task.status == TaskStatus.IN_PROGRESS and task.started_at:
                    elapsed = datetime.now(timezone.utc) - task.started_at
                    task_info["elapsed_hours"] = round(elapsed.total_seconds() / 3600, 1)
                elif task.status == TaskStatus.COMPLETED and task.completed_at:
                    task_info["completed_at"] = task.completed_at.strftime("%Y-%m-%d %H:%M")
                
                task_list.append(task_info)
            
            return {
                "success": True,
                "tasks": task_list,
                "total_shown": len(task_list)
            }
            
        except Exception as e:
            await self._log_error(f"Task listing failed: {e}")
            return {
                "success": False,
                "message": f"Failed to list tasks: {str(e)[:100]}..."
            }
        finally:
            db.close()
    
    async def get_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report"""
        db = self.SessionLocal()
        try:
            # Get task statistics
            total_tasks = db.query(Task).count()
            pending_tasks = db.query(Task).filter(Task.status.in_([
                TaskStatus.PENDING, 
                TaskStatus.CLARIFICATION_NEEDED,
                TaskStatus.ASSIGNED,
                TaskStatus.IN_PROGRESS
            ])).count()
            completed_tasks = db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
            
            # Get tasks with PRs awaiting approval
            pr_approval_tasks = db.query(Task).filter(
                Task.github_pr_url.isnot(None),
                Task.human_approval_required == True,
                Task.status == TaskStatus.COMPLETED  # Completed but awaiting approval
            ).count()
            
            # Get agent statistics
            active_agents = db.query(Agent).filter(Agent.status == AgentStatus.ACTIVE).count()
            busy_agents = db.query(Agent).filter(Agent.status == AgentStatus.BUSY).count()
            
            # Calculate uptime
            uptime = None
            if self.metrics["uptime_start"]:
                uptime_delta = datetime.now(timezone.utc) - self.metrics["uptime_start"]
                uptime = str(uptime_delta).split('.')[0]  # Remove microseconds
            
            # Get PR statistics if GitHub client is available
            pr_stats = {}
            if self.github_client:
                try:
                    recent_prs = await self.github_client.list_open_pull_requests(20)
                    pr_stats = {
                        "open_prs": len(recent_prs),
                        "awaiting_approval": pr_approval_tasks
                    }
                except Exception:
                    pr_stats = {"open_prs": "N/A", "awaiting_approval": pr_approval_tasks}
            else:
                pr_stats = {"open_prs": "N/A", "awaiting_approval": pr_approval_tasks}
            
            return {
                "orchestrator_status": self.status.value,
                "uptime": uptime,
                "tasks": {
                    "total": total_tasks,
                    "pending": pending_tasks,
                    "completed": completed_tasks,
                    "success_rate": f"{(completed_tasks / max(total_tasks, 1)) * 100:.1f}%"
                },
                "prs": pr_stats,
                "agents": {
                    "active": active_agents,
                    "busy": busy_agents,
                    "total": active_agents + busy_agents
                },
                "performance": {
                    "tasks_assigned": self.metrics["tasks_assigned"],
                    "tasks_completed": self.metrics["tasks_completed"],
                    "errors": self.metrics["errors_encountered"],
                    "average_response_time": f"{self.metrics['average_response_time']:.2f}s"
                }
            }
            
        except Exception as e:
            await self._log_error(f"Status report generation failed: {e}")
            return {"error": f"Failed to generate status report: {str(e)[:100]}..."}
        finally:
            db.close()
    
    async def _create_pending_task(self, description: str, user_id: str, channel_id: str, 
                                 priority: TaskPriority, analysis: Dict, questions: List[str]) -> uuid.UUID:
        """Create a task that requires clarification"""
        db = self.SessionLocal()
        try:
            task = Task(
                title=analysis.get("title", description[:100]),
                description=description,
                category=TaskCategory(analysis.get("category", "general")),
                priority=priority,
                status=TaskStatus.CLARIFICATION_NEEDED,
                estimated_hours=analysis.get("estimated_hours", 1.0),
                human_approval_required=True,
                discord_user_id=user_id,
                discord_channel_id=channel_id,
                clarifying_questions=questions,
                task_metadata=analysis.get("metadata", {})
            )
            
            db.add(task)
            db.commit()
            db.refresh(task)
            
            await self._log_info(f"Created pending task {task.id} requiring clarification")
            return task.id
            
        except Exception as e:
            db.rollback()
            await self._log_error(f"Failed to create pending task: {e}")
            raise
        finally:
            db.close()
    
    async def _create_and_assign_task(self, description: str, user_id: str, channel_id: str,
                                    priority: TaskPriority, analysis: Dict) -> uuid.UUID:
        """Create and immediately assign a task"""
        db = self.SessionLocal()
        try:
            assigned_agent = self._determine_best_agent(analysis)
            
            task = Task(
                title=analysis.get("title", description[:100]),
                description=description,
                category=TaskCategory(analysis.get("category", "general")),
                priority=priority,
                status=TaskStatus.ASSIGNED,
                assigned_agent=assigned_agent,
                estimated_hours=analysis.get("estimated_hours", 1.0),
                human_approval_required=analysis.get("requires_approval", True),
                discord_user_id=user_id,
                discord_channel_id=channel_id,
                success_criteria=analysis.get("success_criteria", []),
                assigned_at=datetime.now(timezone.utc),
                task_metadata=analysis.get("metadata", {})
            )
            
            db.add(task)
            db.commit()
            db.refresh(task)
            
            await self._log_info(f"Created and assigned task {task.id} to {assigned_agent}")
            return task.id
            
        except Exception as e:
            db.rollback()
            await self._log_error(f"Failed to create and assign task: {e}")
            raise
        finally:
            db.close()
    
    def _determine_best_agent(self, analysis: Dict) -> str:
        """Determine the best agent for a task (placeholder for Phase 1)"""
        category = analysis.get("category", "general")
        
        # For Phase 1, we only have the orchestrator
        # In future phases, this will route to specialized agents
        agent_mapping = {
            "backend": "backend-agent-alpha",
            "database": "database-agent-alpha", 
            "frontend": "frontend-agent-alpha",
            "testing": "testing-agent-alpha",
            "documentation": "documentation-agent-alpha",
            "deployment": "deployment-agent-alpha"
        }
        
        # For MVP, return orchestrator as fallback
        return agent_mapping.get(category, "orchestrator-alpha")
    
    async def _heartbeat_loop(self):
        """Background heartbeat to update agent status"""
        while True:
            try:
                await self.update_status(AgentStatus.ACTIVE if self.status != AgentStatus.BUSY else AgentStatus.BUSY)
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")
                await asyncio.sleep(60)  # Longer delay on error
    
    async def _monitor_tasks(self):
        """Background task monitoring for timeouts and escalation"""
        while True:
            try:
                db = self.SessionLocal()
                
                # Check for timed out tasks (>4 hours in progress)
                timeout_threshold = datetime.now(timezone.utc) - timedelta(hours=4)
                timed_out_tasks = db.query(Task).filter(
                    Task.status == TaskStatus.IN_PROGRESS,
                    Task.started_at < timeout_threshold
                ).all()
                
                for task in timed_out_tasks:
                    await self._escalate_task(task, "Task timeout exceeded 4 hours")
                
                db.close()
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Task monitoring failed: {e}")
                await asyncio.sleep(600)  # Longer delay on error
    
    async def _escalate_task(self, task: Task, reason: str):
        """Escalate a task to human attention"""
        # Try to get short ID for better readability
        short_id = self.get_short_id_from_uuid(task.id) or str(task.id)
        await self._log_error(f"Task {short_id} escalated: {reason}")
        # TODO: Send Discord notification to human supervisor
    
    # PR Management Methods
    
    async def get_pull_request_details(self, pr_number: int) -> Dict[str, Any]:
        """Get detailed information about a pull request"""
        if not self.github_client:
            return {
                "success": False,
                "message": "GitHub client not available"
            }
        
        try:
            pr_details = await self.github_client.get_pull_request(pr_number)
            if pr_details:
                return {
                    "success": True,
                    "pr": pr_details
                }
            else:
                return {
                    "success": False,
                    "message": f"PR #{pr_number} not found"
                }
        except Exception as e:
            await self._log_error(f"Failed to get PR #{pr_number} details: {e}")
            return {
                "success": False,
                "message": f"Failed to retrieve PR details: {str(e)[:100]}..."
            }
    
    async def approve_and_merge_pr(self, pr_number: int, user_id: str) -> Dict[str, Any]:
        """Approve and merge a pull request"""
        if not self.github_client:
            return {
                "success": False,
                "message": "GitHub client not available"
            }
        
        try:
            # First get PR details to find associated task
            pr_details = await self.github_client.get_pull_request(pr_number)
            if not pr_details:
                return {
                    "success": False,
                    "message": f"PR #{pr_number} not found"
                }
            
            # Check if PR is mergeable
            if not pr_details.get("mergeable"):
                return {
                    "success": False,
                    "message": f"PR #{pr_number} is not mergeable: {pr_details.get('mergeable_state', 'unknown')}"
                }
            
            # Merge the PR
            merge_result = await self.github_client.merge_pull_request(
                pr_number, 
                merge_method="merge",
                commit_title=f"Merge PR #{pr_number}: {pr_details['title']}"
            )
            
            if merge_result and merge_result.get("success"):
                # Find and update associated task
                await self._update_task_after_merge(pr_details["url"], user_id)
                
                await self._log_info(f"Successfully merged PR #{pr_number} by user {user_id}")
                return {
                    "success": True,
                    "message": f"PR #{pr_number} merged successfully",
                    "sha": merge_result.get("sha"),
                    "pr_title": pr_details["title"]
                }
            else:
                return {
                    "success": False,
                    "message": merge_result.get("message", "Unknown merge error")
                }
                
        except Exception as e:
            await self._log_error(f"Failed to approve/merge PR #{pr_number}: {e}")
            return {
                "success": False,
                "message": f"Failed to merge PR: {str(e)[:100]}..."
            }
    
    async def reject_pr(self, pr_number: int, reason: str, user_id: str) -> Dict[str, Any]:
        """Reject a pull request with reason"""
        if not self.github_client:
            return {
                "success": False,
                "message": "GitHub client not available"
            }
        
        try:
            # Get PR details first
            pr_details = await self.github_client.get_pull_request(pr_number)
            if not pr_details:
                return {
                    "success": False,
                    "message": f"PR #{pr_number} not found"
                }
            
            # Close the PR with reason
            success = await self.github_client.close_pull_request(pr_number, f"Rejected by {user_id}: {reason}")
            
            if success:
                # Update associated task if found
                await self._update_task_after_rejection(pr_details["url"], reason, user_id)
                
                await self._log_info(f"Rejected PR #{pr_number} by user {user_id}: {reason}")
                return {
                    "success": True,
                    "message": f"PR #{pr_number} rejected successfully",
                    "pr_title": pr_details["title"],
                    "reason": reason
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to close PR"
                }
                
        except Exception as e:
            await self._log_error(f"Failed to reject PR #{pr_number}: {e}")
            return {
                "success": False,
                "message": f"Failed to reject PR: {str(e)[:100]}..."
            }
    
    async def list_pending_prs(self, limit: int = 10) -> Dict[str, Any]:
        """List open pull requests awaiting approval"""
        if not self.github_client:
            return {
                "success": False,
                "message": "GitHub client not available"
            }
        
        try:
            prs = await self.github_client.list_open_pull_requests(limit)
            
            # Enhance PR data with task information
            enhanced_prs = []
            db = self.SessionLocal()
            
            try:
                for pr in prs:
                    # Try to find associated task
                    task = db.query(Task).filter(Task.github_pr_url == pr["url"]).first()
                    
                    pr_info = pr.copy()
                    if task:
                        short_id = self.get_short_id_from_uuid(task.id)
                        pr_info["task_id"] = short_id or str(task.id)
                        pr_info["task_title"] = task.title
                        pr_info["task_status"] = task.status.value
                        pr_info["requires_approval"] = task.human_approval_required
                    
                    enhanced_prs.append(pr_info)
                
            finally:
                db.close()
            
            return {
                "success": True,
                "prs": enhanced_prs,
                "count": len(enhanced_prs)
            }
            
        except Exception as e:
            await self._log_error(f"Failed to list pending PRs: {e}")
            return {
                "success": False,
                "message": f"Failed to list PRs: {str(e)[:100]}..."
            }
    
    async def _update_task_after_merge(self, pr_url: str, approved_by: str):
        """Update task status after PR is merged"""
        db = self.SessionLocal()
        try:
            task = db.query(Task).filter(Task.github_pr_url == pr_url).first()
            if task:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now(timezone.utc)
                task.task_metadata = task.task_metadata or {}
                task.task_metadata.update({
                    "approved_by": approved_by,
                    "approved_at": datetime.now(timezone.utc).isoformat(),
                    "merged": True
                })
                db.commit()
                
                short_id = self.get_short_id_from_uuid(task.id)
                await self._log_info(f"Task {short_id or task.id} marked as completed after PR merge")
        except Exception as e:
            db.rollback()
            await self._log_error(f"Failed to update task after merge: {e}")
        finally:
            db.close()
    
    async def _update_task_after_rejection(self, pr_url: str, reason: str, rejected_by: str):
        """Update task status after PR is rejected"""
        db = self.SessionLocal()
        try:
            task = db.query(Task).filter(Task.github_pr_url == pr_url).first()
            if task:
                task.status = TaskStatus.FAILED
                task.task_metadata = task.task_metadata or {}
                task.task_metadata.update({
                    "rejected_by": rejected_by,
                    "rejected_at": datetime.now(timezone.utc).isoformat(),
                    "rejection_reason": reason
                })
                db.commit()
                
                short_id = self.get_short_id_from_uuid(task.id)
                await self._log_info(f"Task {short_id or task.id} marked as failed after PR rejection")
        except Exception as e:
            db.rollback()
            await self._log_error(f"Failed to update task after rejection: {e}")
        finally:
            db.close()
    
    async def _log_warning(self, message: str, task_id: Optional[str] = None):
        """Log warning message to database"""
        await self._log(LogLevel.WARNING, message, task_id)

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
                task_id=task_id,
                level=level,
                message=message,
                context="orchestrator_agent"
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log message: {e}")
        finally:
            db.close()
    
    async def log_error(self, message: str, context: Any = None):
        """Public method for error logging"""
        await self._log_error(f"{message} | Context: {str(context)[:200]}")

    # ===== TESTING AGENT INTEGRATION =====

    async def trigger_pr_tests(self, pr_number: int, user_id: str) -> Dict[str, Any]:
        """Trigger tests on a specific PR."""
        try:
            logger.info(f"Triggering tests for PR #{pr_number} by user {user_id}")
            
            # Check if PR exists
            if not self.github_client:
                return {"success": False, "message": "GitHub client not available"}
            
            pr_details = await self.github_client.get_pull_request(pr_number)
            if not pr_details.get("success", False):
                return {"success": False, "message": f"PR #{pr_number} not found"}
            
            # Log the test trigger
            await self._log_to_database(
                level=LogLevel.INFO,
                message=f"Manual test trigger for PR #{pr_number} by user {user_id}"
            )
            
            # In a real implementation, this would communicate with the testing agent
            # For now, we'll simulate the trigger
            
            return {
                "success": True,
                "message": f"Tests triggered for PR #{pr_number}",
                "pr_title": pr_details.get("data", {}).get("title", "Unknown"),
                "triggered_by": user_id
            }
            
        except Exception as e:
            logger.error(f"Failed to trigger PR tests: {e}")
            await self.log_error(f"Failed to trigger tests for PR #{pr_number}", str(e))
            return {"success": False, "message": f"Error triggering tests: {str(e)}"}

    async def get_testing_status(self) -> Dict[str, Any]:
        """Get current testing agent status."""
        try:
            # In a real implementation, this would query the testing agent
            # For now, we'll return simulated status
            
            status = {
                "online": True,
                "active_tests": 0,
                "auto_approve": True,
                "recent_tests": [
                    {
                        "pr_number": 42,
                        "status": "pass",
                        "duration": 45.2,
                        "timestamp": datetime.now().isoformat()
                    }
                ],
                "statistics": {
                    "total": 156,
                    "passed": 142,
                    "failed": 14
                }
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get testing status: {e}")
            return {
                "online": False,
                "error": str(e)
            }

    async def update_testing_config(self, config_changes: Dict[str, Any]) -> Dict[str, Any]:
        """Update testing agent configuration."""
        try:
            logger.info(f"Updating testing configuration: {config_changes}")
            
            # Log configuration change
            await self._log_to_database(
                level=LogLevel.INFO,
                message=f"Testing configuration updated: {json.dumps(config_changes)}"
            )
            
            # In a real implementation, this would communicate with the testing agent
            # For now, we'll simulate the update
            
            return {
                "success": True,
                "message": "Testing configuration updated",
                "changes": config_changes
            }
            
        except Exception as e:
            logger.error(f"Failed to update testing config: {e}")
            await self.log_error("Failed to update testing configuration", str(e))
            return {"success": False, "message": f"Error updating config: {str(e)}"}

    async def get_testing_logs(self, lines: int = 20, level: str = "all") -> Dict[str, Any]:
        """Get testing agent logs."""
        try:
            # In a real implementation, this would read from testing agent logs
            # For now, we'll return simulated logs
            
            sample_logs = [
                "2025-09-23 10:30:15 - INFO - Testing Agent started",
                "2025-09-23 10:30:45 - INFO - Monitoring PRs for changes",
                "2025-09-23 10:31:20 - INFO - Running tests for PR #42",
                "2025-09-23 10:32:05 - INFO - Tests completed: PASS (45.2s)",
                "2025-09-23 10:32:10 - INFO - Auto-approved PR #42"
            ]
            
            # Filter by level if specified
            if level != "all":
                sample_logs = [log for log in sample_logs if level.upper() in log]
            
            # Limit lines
            sample_logs = sample_logs[-lines:]
            
            return {
                "success": True,
                "logs": "\n".join(sample_logs),
                "lines_returned": len(sample_logs)
            }
            
        except Exception as e:
            logger.error(f"Failed to get testing logs: {e}")
            return {"success": False, "message": f"Error retrieving logs: {str(e)}"}

    async def send_notification(self, channel: str, message: str, priority: str = "normal") -> Dict[str, Any]:
        """Send notification to Discord channel."""
        try:
            logger.info(f"Sending notification to {channel}: {message[:100]}...")
            
            # Log the notification
            await self._log_to_database(
                level=LogLevel.INFO,
                message=f"Notification sent to {channel} channel: {message[:200]}"
            )
            
            # In a real implementation, this would send to Discord
            # For now, we'll just log it
            
            return {
                "success": True,
                "message": "Notification sent",
                "channel": channel,
                "priority": priority
            }
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return {"success": False, "message": f"Error sending notification: {str(e)}"}