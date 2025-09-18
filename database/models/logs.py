# database/models/logs.py
from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
import enum
from .base import Base

class LogLevel(enum.Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class Log(Base):
    __tablename__ = "logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(100), nullable=True)
    task_id = Column(UUID(as_uuid=True), nullable=True)
    
    level = Column(SQLEnum(LogLevel), nullable=False, default=LogLevel.INFO)
    message = Column(Text, nullable=False)
    
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Optional context data
    context = Column(String(255), nullable=True)  # function_name, module, etc.
    log_metadata = Column(String, nullable=True)  # JSON string for additional data
    
    def __repr__(self):
        return f"<Log(level='{self.level.value}', agent='{self.agent_name}', timestamp='{self.timestamp}')>"

# Create indexes for better query performance
Index('idx_logs_timestamp', Log.timestamp.desc())
Index('idx_logs_agent_name', Log.agent_name)
Index('idx_logs_task_id', Log.task_id)
Index('idx_logs_level', Log.level)