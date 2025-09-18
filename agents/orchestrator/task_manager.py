# agents/orchestrator/task_manager.py
"""Task management and queue handling for the Orchestrator Agent"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from sqlalchemy.orm import sessionmaker
from database.models.base import engine
from database.models.task import Task, TaskStatus

logger = logging.getLogger(__name__)

class TaskManager:
    """Manages task queue and lifecycle"""
    
    def __init__(self):
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.active_tasks = {}  # In-memory tracking for performance
    
    async def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks from queue"""
        db = self.SessionLocal()
        try:
            tasks = db.query(Task).filter(
                Task.status.in_([TaskStatus.PENDING, TaskStatus.ASSIGNED])
            ).order_by(Task.priority.desc(), Task.created_at.asc()).all()
            return tasks
        finally:
            db.close()
    
    async def update_task_status(self, task_id: str, status: TaskStatus, metadata: Optional[Dict] = None):
        """Update task status and metadata"""
        db = self.SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = status
                task.updated_at = datetime.now(timezone.utc)
                
                if status == TaskStatus.IN_PROGRESS and not task.started_at:
                    task.started_at = datetime.now(timezone.utc)
                elif status == TaskStatus.COMPLETED:
                    task.completed_at = datetime.now(timezone.utc)
                
                if metadata:
                    if hasattr(task, 'task_metadata') and task.task_metadata:
                        task.task_metadata.update(metadata or {})
                
                db.commit()
                logger.info(f"Task {task_id} status updated to {status.value}")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update task status: {e}")
        finally:
            db.close()

