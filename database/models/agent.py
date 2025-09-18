# database/models/agent.py
from sqlalchemy import Column, String, DateTime, JSON, Enum as SQLEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
import enum
from .base import Base

class AgentType(enum.Enum):
    ORCHESTRATOR = "orchestrator"
    BACKEND = "backend"
    DATABASE = "database"
    FRONTEND = "frontend"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"

class AgentStatus(enum.Enum):
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"

# Backend-specific capabilities
BACKEND_CAPABILITIES = [
    "flask_development",
    "api_endpoints", 
    "business_logic",
    "database_integration",
    "error_handling",
    "testing",
    "github_integration"
]

# Backend agent configuration
BACKEND_CONFIG = {
    "max_concurrent_tasks": 1,
    "task_timeout_hours": 4,
    "progress_report_interval": 30,  # minutes
    "supported_categories": ["backend", "api", "general"]
}

# Agent capability constants for other agent types
ORCHESTRATOR_CAPABILITIES = [
    "task_assignment",
    "agent_coordination",
    "human_interaction",
    "task_validation",
    "progress_monitoring",
    "clarifying_questions"
]

ORCHESTRATOR_CONFIG = {
    "max_clarifying_questions": 5,
    "task_timeout_hours": 4,
    "escalation_threshold_minutes": 15,
    "max_concurrent_tasks": 10
}

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    type = Column(SQLEnum(AgentType), nullable=False)
    status = Column(SQLEnum(AgentStatus), nullable=False, default=AgentStatus.OFFLINE)
    
    capabilities = Column(JSON, nullable=True, default=list)
    current_task_id = Column(UUID(as_uuid=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    last_task_completed = Column(DateTime(timezone=True), nullable=True)
    
    performance_metrics = Column(JSON, nullable=True, default=dict)
    configuration = Column(JSON, nullable=True, default=dict)
    
    is_active = Column(Boolean, nullable=False, default=True)
    max_concurrent_tasks = Column(String(10), nullable=False, default="1")
    
    def setup_agent_defaults(self):
        """Set up default capabilities and configuration based on agent type"""
        if self.type == AgentType.BACKEND:
            self.capabilities = BACKEND_CAPABILITIES.copy()
            self.configuration = BACKEND_CONFIG.copy()
        elif self.type == AgentType.ORCHESTRATOR:
            self.capabilities = ORCHESTRATOR_CAPABILITIES.copy()
            self.configuration = ORCHESTRATOR_CONFIG.copy()
        else:
            # Default configuration for other agent types
            self.capabilities = []
            self.configuration = {
                "max_concurrent_tasks": 1,
                "task_timeout_hours": 4
            }
    
    def __repr__(self):
        return f"<Agent(name='{self.name}', type='{self.type.value}', status='{self.status.value}')>"