# agents/orchestrator/orchestrator.py
"""Core Orchestrator Agent implementation"""
import asyncio
import json
import logging
import uuid
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
        
        # Database session
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Performance metrics
        self.metrics = {
            "tasks_assigned": 0,
            "tasks_completed": 0,
            "average_response_time": 0.0,
            "errors_encountered": 0,
            "uptime_start": None
        }
        
        logger.info(f"🤖 Orchestrator Agent initialized: {self.name}")
    
    async def initialize(self):
        """Initialize the orchestrator agent"""
        try:
            self.metrics["uptime_start"] = datetime.now(timezone.utc)
            
            # Initialize Claude client
            await self.claude_client.initialize()
            
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
                task_id = await self._create_pending_task(
                    description, user_id, channel_id, priority, analysis, questions
                )
                return {
                    "success": True,
                    "task_id": str(task_id),
                    "requires_clarification": True,
                    "questions": questions,
                    "message": "Task created but requires clarification before assignment."
                }
            
            # Create and assign task
            task_id = await self._create_and_assign_task(
                description, user_id, channel_id, priority, analysis
            )
            
            self.metrics["tasks_assigned"] += 1
            
            return {
                "success": True,
                "task_id": str(task_id),
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
            # Get pending task
            task = db.query(Task).filter(Task.id == task_id).first()
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
            task.metadata.update(clarified_analysis.get("metadata", {}))
            task.assigned_at = datetime.now(timezone.utc)
            task.updated_at = datetime.now(timezone.utc)
            
            db.commit()
            
            await self._log_info(f"Task {task_id} clarified and assigned to {task.assigned_agent}")
            
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
            
            # Get agent statistics
            active_agents = db.query(Agent).filter(Agent.status == AgentStatus.ACTIVE).count()
            busy_agents = db.query(Agent).filter(Agent.status == AgentStatus.BUSY).count()
            
            # Calculate uptime
            uptime = None
            if self.metrics["uptime_start"]:
                uptime_delta = datetime.now(timezone.utc) - self.metrics["uptime_start"]
                uptime = str(uptime_delta).split('.')[0]  # Remove microseconds
            
            return {
                "orchestrator_status": self.status.value,
                "uptime": uptime,
                "tasks": {
                    "total": total_tasks,
                    "pending": pending_tasks,
                    "completed": completed_tasks,
                    "success_rate": f"{(completed_tasks / max(total_tasks, 1)) * 100:.1f}%"
                },
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
                metadata=analysis.get("metadata", {})
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
                metadata=analysis.get("metadata", {})
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
        await self._log_error(f"Task {task.id} escalated: {reason}")
        # TODO: Send Discord notification to human supervisor
    
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