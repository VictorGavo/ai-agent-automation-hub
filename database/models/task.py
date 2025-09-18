# database/models/task.py
from sqlalchemy import Column, String, Text, DateTime, Boolean, Float, JSON, Enum as SQLEnum, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
import enum
from .base import Base

class TaskCategory(enum.Enum):
    BACKEND = "backend"
    DATABASE = "database"
    FRONTEND = "frontend"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    GENERAL = "general"

class TaskPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatus(enum.Enum):
    PENDING = "pending"
    CLARIFICATION_NEEDED = "clarification_needed"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    REVIEW_READY = "review_ready"
    APPROVED = "approved"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(SQLEnum(TaskCategory), nullable=False, default=TaskCategory.GENERAL)
    priority = Column(SQLEnum(TaskPriority), nullable=False, default=TaskPriority.MEDIUM)
    status = Column(SQLEnum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    
    assigned_agent = Column(String(100), nullable=True)
    estimated_hours = Column(Float, nullable=True, default=1.0)
    actual_hours = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    human_approval_required = Column(Boolean, nullable=False, default=True)
    github_branch = Column(String(255), nullable=True)
    github_pr_url = Column(String(255), nullable=True)
    
    task_metadata = Column(JSON, nullable=True, default=dict)
    clarifying_questions = Column(JSON, nullable=True)
    success_criteria = Column(JSON, nullable=True)
    
    # Discord-specific fields
    discord_user_id = Column(String(50), nullable=False)
    discord_channel_id = Column(String(50), nullable=False)
    discord_message_id = Column(String(50), nullable=True)
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status.value}')>"