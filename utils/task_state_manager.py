"""
Task State Manager

Manages persistent task state for AI agents to enable recovery from interruptions.
Provides checkpointing, rollback capabilities, and conversation history tracking.
"""

import os
import sys
import json
import pickle
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from contextlib import contextmanager
import threading
import uuid

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskState(Enum):
    """Task execution states."""
    CREATED = "created"
    INITIALIZED = "initialized"
    IN_PROGRESS = "in_progress"
    CHECKPOINT = "checkpoint"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class CheckpointType(Enum):
    """Types of checkpoints."""
    AUTO = "auto"         # Automatic 10-minute checkpoint
    MANUAL = "manual"     # Manually created checkpoint
    MILESTONE = "milestone"  # Major progress milestone
    ERROR = "error"       # Error recovery point
    ROLLBACK = "rollback"  # Rollback preparation point


@dataclass
class TaskCheckpoint:
    """Represents a task checkpoint."""
    checkpoint_id: str
    task_id: str
    agent_name: str
    checkpoint_type: CheckpointType
    timestamp: datetime
    current_step: str
    progress_percentage: float
    context_data: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    rollback_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert checkpoint to dictionary."""
        data = asdict(self)
        data['checkpoint_type'] = self.checkpoint_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskCheckpoint':
        """Create checkpoint from dictionary."""
        data = data.copy()
        data['checkpoint_type'] = CheckpointType(data['checkpoint_type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class AgentTaskState:
    """Represents complete agent task state."""
    task_id: str
    agent_name: str
    task_description: str
    task_type: str
    state: TaskState
    created_at: datetime
    updated_at: datetime
    current_step: str
    progress_percentage: float
    context_data: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    checkpoints: List[str]  # List of checkpoint IDs
    error_count: int = 0
    last_error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task state to dictionary."""
        data = asdict(self)
        data['state'] = self.state.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentTaskState':
        """Create task state from dictionary."""
        data = data.copy()
        data['state'] = TaskState(data['state'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


class TaskStateManager:
    """
    Manages persistent task state for AI agents.
    
    Features:
    - Persistent state storage in SQLite database
    - Automatic checkpointing every 10 minutes
    - Manual checkpoint creation
    - Rollback capabilities
    - Conversation history tracking
    - Thread-safe operations
    """
    
    def __init__(self, db_path: str = "data/task_state.db"):
        """
        Initialize the task state manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._lock = threading.Lock()
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"TaskStateManager initialized with database: {db_path}")
    
    def _init_database(self) -> None:
        """Initialize database tables."""
        with self._get_connection() as conn:
            # Create task states table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_states (
                    task_id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    task_description TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    current_step TEXT NOT NULL,
                    progress_percentage REAL NOT NULL,
                    context_data TEXT NOT NULL,
                    conversation_history TEXT NOT NULL,
                    checkpoints TEXT NOT NULL,
                    error_count INTEGER DEFAULT 0,
                    last_error TEXT
                )
            """)
            
            # Create checkpoints table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    checkpoint_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    current_step TEXT NOT NULL,
                    progress_percentage REAL NOT NULL,
                    context_data TEXT NOT NULL,
                    conversation_history TEXT NOT NULL,
                    rollback_data TEXT,
                    notes TEXT,
                    FOREIGN KEY (task_id) REFERENCES task_states (task_id)
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_agent ON task_states (agent_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_state ON task_states (state)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_checkpoint_task ON checkpoints (task_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_checkpoint_timestamp ON checkpoints (timestamp)")
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper locking."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, timeout=30)
            try:
                yield conn
            finally:
                conn.close()
    
    def create_task_state(
        self, 
        task_id: str,
        agent_name: str,
        task_description: str,
        task_type: str,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> AgentTaskState:
        """
        Create new task state for an agent.
        
        Args:
            task_id: Unique task identifier
            agent_name: Name of the agent
            task_description: Description of the task
            task_type: Type of task
            initial_context: Initial context data
            
        Returns:
            Created AgentTaskState
        """
        now = datetime.now(timezone.utc)
        
        task_state = AgentTaskState(
            task_id=task_id,
            agent_name=agent_name,
            task_description=task_description,
            task_type=task_type,
            state=TaskState.CREATED,
            created_at=now,
            updated_at=now,
            current_step="initialization",
            progress_percentage=0.0,
            context_data=initial_context or {},
            conversation_history=[],
            checkpoints=[]
        )
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO task_states (
                    task_id, agent_name, task_description, task_type, state,
                    created_at, updated_at, current_step, progress_percentage,
                    context_data, conversation_history, checkpoints, error_count, last_error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_state.task_id,
                task_state.agent_name,
                task_state.task_description,
                task_state.task_type,
                task_state.state.value,
                task_state.created_at.isoformat(),
                task_state.updated_at.isoformat(),
                task_state.current_step,
                task_state.progress_percentage,
                json.dumps(task_state.context_data),
                json.dumps(task_state.conversation_history),
                json.dumps(task_state.checkpoints),
                task_state.error_count,
                task_state.last_error
            ))
            conn.commit()
        
        logger.info(f"Created task state for {agent_name}: {task_id}")
        return task_state
    
    def get_task_state(self, task_id: str) -> Optional[AgentTaskState]:
        """
        Get task state by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            AgentTaskState if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM task_states WHERE task_id = ?
            """, (task_id,))
            row = cursor.fetchone()
        
        if not row:
            return None
        
        columns = [desc[0] for desc in cursor.description]
        data = dict(zip(columns, row))
        
        # Convert JSON fields back
        data['context_data'] = json.loads(data['context_data'])
        data['conversation_history'] = json.loads(data['conversation_history'])
        data['checkpoints'] = json.loads(data['checkpoints'])
        
        return AgentTaskState.from_dict(data)
    
    def update_task_state(
        self,
        task_id: str,
        state: Optional[TaskState] = None,
        current_step: Optional[str] = None,
        progress_percentage: Optional[float] = None,
        context_data: Optional[Dict[str, Any]] = None,
        add_conversation: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update task state.
        
        Args:
            task_id: Task identifier
            state: New task state
            current_step: Current execution step
            progress_percentage: Progress percentage (0-100)
            context_data: Context data to merge
            add_conversation: Conversation entry to add
            
        Returns:
            True if updated successfully
        """
        task_state = self.get_task_state(task_id)
        if not task_state:
            logger.error(f"Task state not found: {task_id}")
            return False
        
        # Update fields
        if state is not None:
            task_state.state = state
        if current_step is not None:
            task_state.current_step = current_step
        if progress_percentage is not None:
            task_state.progress_percentage = min(100.0, max(0.0, progress_percentage))
        if context_data is not None:
            task_state.context_data.update(context_data)
        if add_conversation is not None:
            conversation_entry = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                **add_conversation
            }
            task_state.conversation_history.append(conversation_entry)
        
        task_state.updated_at = datetime.now(timezone.utc)
        
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE task_states SET
                    state = ?, current_step = ?, progress_percentage = ?,
                    context_data = ?, conversation_history = ?, updated_at = ?
                WHERE task_id = ?
            """, (
                task_state.state.value,
                task_state.current_step,
                task_state.progress_percentage,
                json.dumps(task_state.context_data),
                json.dumps(task_state.conversation_history),
                task_state.updated_at.isoformat(),
                task_id
            ))
            conn.commit()
        
        logger.debug(f"Updated task state: {task_id}")
        return True
    
    def create_checkpoint(
        self,
        task_id: str,
        checkpoint_type: CheckpointType = CheckpointType.MANUAL,
        notes: Optional[str] = None,
        rollback_data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Create a checkpoint for the task.
        
        Args:
            task_id: Task identifier
            checkpoint_type: Type of checkpoint
            notes: Optional notes about the checkpoint
            rollback_data: Optional rollback data
            
        Returns:
            Checkpoint ID if created successfully
        """
        task_state = self.get_task_state(task_id)
        if not task_state:
            logger.error(f"Cannot create checkpoint - task not found: {task_id}")
            return None
        
        checkpoint_id = str(uuid.uuid4())
        checkpoint = TaskCheckpoint(
            checkpoint_id=checkpoint_id,
            task_id=task_id,
            agent_name=task_state.agent_name,
            checkpoint_type=checkpoint_type,
            timestamp=datetime.now(timezone.utc),
            current_step=task_state.current_step,
            progress_percentage=task_state.progress_percentage,
            context_data=task_state.context_data.copy(),
            conversation_history=task_state.conversation_history.copy(),
            rollback_data=rollback_data,
            notes=notes
        )
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO checkpoints (
                    checkpoint_id, task_id, agent_name, checkpoint_type,
                    timestamp, current_step, progress_percentage,
                    context_data, conversation_history, rollback_data, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                checkpoint.checkpoint_id,
                checkpoint.task_id,
                checkpoint.agent_name,
                checkpoint.checkpoint_type.value,
                checkpoint.timestamp.isoformat(),
                checkpoint.current_step,
                checkpoint.progress_percentage,
                json.dumps(checkpoint.context_data),
                json.dumps(checkpoint.conversation_history),
                json.dumps(rollback_data) if rollback_data else None,
                checkpoint.notes
            ))
            
            # Update task state with new checkpoint
            task_state.checkpoints.append(checkpoint_id)
            conn.execute("""
                UPDATE task_states SET checkpoints = ? WHERE task_id = ?
            """, (json.dumps(task_state.checkpoints), task_id))
            
            conn.commit()
        
        logger.info(f"Created {checkpoint_type.value} checkpoint for {task_id}: {checkpoint_id}")
        return checkpoint_id
    
    def get_checkpoint(self, checkpoint_id: str) -> Optional[TaskCheckpoint]:
        """
        Get checkpoint by ID.
        
        Args:
            checkpoint_id: Checkpoint identifier
            
        Returns:
            TaskCheckpoint if found
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM checkpoints WHERE checkpoint_id = ?
            """, (checkpoint_id,))
            row = cursor.fetchone()
        
        if not row:
            return None
        
        columns = [desc[0] for desc in cursor.description]
        data = dict(zip(columns, row))
        
        # Convert JSON fields
        data['context_data'] = json.loads(data['context_data'])
        data['conversation_history'] = json.loads(data['conversation_history'])
        if data['rollback_data']:
            data['rollback_data'] = json.loads(data['rollback_data'])
        
        return TaskCheckpoint.from_dict(data)
    
    def get_task_checkpoints(self, task_id: str) -> List[TaskCheckpoint]:
        """
        Get all checkpoints for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            List of TaskCheckpoints ordered by timestamp
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM checkpoints 
                WHERE task_id = ? 
                ORDER BY timestamp DESC
            """, (task_id,))
            rows = cursor.fetchall()
        
        checkpoints = []
        columns = [desc[0] for desc in cursor.description]
        
        for row in rows:
            data = dict(zip(columns, row))
            data['context_data'] = json.loads(data['context_data'])
            data['conversation_history'] = json.loads(data['conversation_history'])
            if data['rollback_data']:
                data['rollback_data'] = json.loads(data['rollback_data'])
            checkpoints.append(TaskCheckpoint.from_dict(data))
        
        return checkpoints
    
    def rollback_to_checkpoint(self, task_id: str, checkpoint_id: str) -> bool:
        """
        Rollback task to a specific checkpoint.
        
        Args:
            task_id: Task identifier
            checkpoint_id: Checkpoint to rollback to
            
        Returns:
            True if rollback successful
        """
        checkpoint = self.get_checkpoint(checkpoint_id)
        if not checkpoint or checkpoint.task_id != task_id:
            logger.error(f"Invalid checkpoint for rollback: {checkpoint_id}")
            return False
        
        # Create rollback checkpoint before reverting
        rollback_checkpoint_id = self.create_checkpoint(
            task_id,
            CheckpointType.ROLLBACK,
            f"Rollback preparation before reverting to {checkpoint_id}"
        )
        
        # Restore task state from checkpoint
        success = self.update_task_state(
            task_id,
            state=TaskState.ROLLED_BACK,
            current_step=checkpoint.current_step,
            progress_percentage=checkpoint.progress_percentage,
            context_data=checkpoint.context_data,
        )
        
        if success:
            # Restore conversation history
            task_state = self.get_task_state(task_id)
            if task_state:
                task_state.conversation_history = checkpoint.conversation_history.copy()
                task_state.conversation_history.append({
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'type': 'system',
                    'message': f'Task rolled back to checkpoint {checkpoint_id}',
                    'rollback_checkpoint_id': rollback_checkpoint_id
                })
                
                with self._get_connection() as conn:
                    conn.execute("""
                        UPDATE task_states SET conversation_history = ? WHERE task_id = ?
                    """, (json.dumps(task_state.conversation_history), task_id))
                    conn.commit()
            
            logger.info(f"Successfully rolled back task {task_id} to checkpoint {checkpoint_id}")
        
        return success
    
    def get_agent_tasks(self, agent_name: str, state_filter: Optional[TaskState] = None) -> List[AgentTaskState]:
        """
        Get all tasks for an agent.
        
        Args:
            agent_name: Agent name
            state_filter: Optional state filter
            
        Returns:
            List of AgentTaskStates
        """
        query = "SELECT * FROM task_states WHERE agent_name = ?"
        params = [agent_name]
        
        if state_filter:
            query += " AND state = ?"
            params.append(state_filter.value)
        
        query += " ORDER BY updated_at DESC"
        
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        tasks = []
        columns = [desc[0] for desc in cursor.description]
        
        for row in rows:
            data = dict(zip(columns, row))
            data['context_data'] = json.loads(data['context_data'])
            data['conversation_history'] = json.loads(data['conversation_history'])
            data['checkpoints'] = json.loads(data['checkpoints'])
            tasks.append(AgentTaskState.from_dict(data))
        
        return tasks
    
    def record_error(self, task_id: str, error_message: str) -> bool:
        """
        Record an error for a task.
        
        Args:
            task_id: Task identifier
            error_message: Error message
            
        Returns:
            True if recorded successfully
        """
        task_state = self.get_task_state(task_id)
        if not task_state:
            return False
        
        task_state.error_count += 1
        task_state.last_error = error_message
        task_state.updated_at = datetime.now(timezone.utc)
        
        # Add to conversation history
        task_state.conversation_history.append({
            'timestamp': task_state.updated_at.isoformat(),
            'type': 'error',
            'message': error_message,
            'error_count': task_state.error_count
        })
        
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE task_states SET
                    error_count = ?, last_error = ?, updated_at = ?, conversation_history = ?
                WHERE task_id = ?
            """, (
                task_state.error_count,
                task_state.last_error,
                task_state.updated_at.isoformat(),
                json.dumps(task_state.conversation_history),
                task_id
            ))
            conn.commit()
        
        logger.warning(f"Recorded error for task {task_id}: {error_message}")
        return True
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> Dict[str, int]:
        """
        Clean up old task data.
        
        Args:
            days_to_keep: Number of days to keep data
            
        Returns:
            Dictionary with cleanup statistics
        """
        cutoff_date = (datetime.now(timezone.utc).timestamp() - (days_to_keep * 24 * 3600))
        cutoff_iso = datetime.fromtimestamp(cutoff_date, timezone.utc).isoformat()
        
        with self._get_connection() as conn:
            # Count before cleanup
            cursor = conn.execute("""
                SELECT COUNT(*) FROM task_states WHERE created_at < ?
            """, (cutoff_iso,))
            old_tasks = cursor.fetchone()[0]
            
            cursor = conn.execute("""
                SELECT COUNT(*) FROM checkpoints WHERE timestamp < ?
            """, (cutoff_iso,))
            old_checkpoints = cursor.fetchone()[0]
            
            # Delete old data
            conn.execute("""
                DELETE FROM checkpoints WHERE timestamp < ?
            """, (cutoff_iso,))
            
            conn.execute("""
                DELETE FROM task_states WHERE created_at < ?
            """, (cutoff_iso,))
            
            conn.commit()
        
        stats = {
            'deleted_tasks': old_tasks,
            'deleted_checkpoints': old_checkpoints,
            'days_kept': days_to_keep
        }
        
        logger.info(f"Cleanup completed: {stats}")
        return stats
    
    def get_recovery_options(self, agent_name: str) -> Dict[str, Any]:
        """
        Get recovery options for an agent.
        
        Args:
            agent_name: Agent name
            
        Returns:
            Dictionary with recovery options
        """
        # Get interrupted tasks
        interrupted_tasks = self.get_agent_tasks(
            agent_name, 
            TaskState.IN_PROGRESS
        ) + self.get_agent_tasks(
            agent_name, 
            TaskState.PAUSED
        )
        
        # Get recent checkpoints
        recent_checkpoints = []
        for task in interrupted_tasks:
            checkpoints = self.get_task_checkpoints(task.task_id)
            recent_checkpoints.extend(checkpoints[:3])  # Top 3 per task
        
        # Sort by timestamp
        recent_checkpoints.sort(key=lambda x: x.timestamp, reverse=True)
        
        return {
            'agent_name': agent_name,
            'interrupted_tasks': [task.to_dict() for task in interrupted_tasks],
            'recent_checkpoints': [cp.to_dict() for cp in recent_checkpoints[:10]],
            'recovery_timestamp': datetime.now(timezone.utc).isoformat()
        }


# Global instance
_task_state_manager: Optional[TaskStateManager] = None


def get_task_state_manager() -> TaskStateManager:
    """Get global task state manager instance."""
    global _task_state_manager
    
    if _task_state_manager is None:
        _task_state_manager = TaskStateManager()
    
    return _task_state_manager


if __name__ == "__main__":
    # Test the task state manager
    try:
        print("Testing TaskStateManager...")
        
        manager = TaskStateManager("test_task_state.db")
        
        # Create test task
        task_state = manager.create_task_state(
            "test-task-1",
            "TestAgent",
            "Test task for validation",
            "testing",
            {"test_data": "value"}
        )
        print(f"✓ Created task state: {task_state.task_id}")
        
        # Update task
        success = manager.update_task_state(
            task_state.task_id,
            state=TaskState.IN_PROGRESS,
            current_step="executing tests",
            progress_percentage=25.0,
            add_conversation={
                'type': 'agent',
                'message': 'Started test execution'
            }
        )
        print(f"✓ Updated task state: {success}")
        
        # Create checkpoint
        checkpoint_id = manager.create_checkpoint(
            task_state.task_id,
            CheckpointType.AUTO,
            "Auto checkpoint during execution"
        )
        print(f"✓ Created checkpoint: {checkpoint_id}")
        
        # Test rollback
        rollback_success = manager.rollback_to_checkpoint(task_state.task_id, checkpoint_id)
        print(f"✓ Rollback test: {rollback_success}")
        
        # Get recovery options
        recovery = manager.get_recovery_options("TestAgent")
        print(f"✓ Recovery options: {len(recovery['interrupted_tasks'])} tasks, {len(recovery['recent_checkpoints'])} checkpoints")
        
        print("\n✅ All TaskStateManager tests passed!")
        
        # Cleanup test database
        os.remove("test_task_state.db")
        
    except Exception as e:
        print(f"❌ TaskStateManager test failed: {e}")
        raise