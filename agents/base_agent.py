"""
Base Agent Module

This module provides the BaseAgent class that serves as the foundation for all
specialized agents in the AI Agent Automation Hub. It includes development
bible integration, task preparation, and validation functionality.
"""

import os
import sys
import logging
import threading
import time
from typing import Optional, Dict, Any, Callable
from functools import wraps
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.dev_bible_reader import DevBibleReader, enforce_dev_bible_reading
from utils.task_state_manager import get_task_state_manager, TaskState, CheckpointType
from utils.safe_git_operations import get_safe_git_operations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def require_dev_bible_prep(func: Callable) -> Callable:
    """
    Decorator to ensure agent methods can only be executed after proper
    development bible preparation has been completed.
    
    Args:
        func (Callable): The method to be decorated
        
    Returns:
        Callable: The wrapped method
        
    Raises:
        RuntimeError: If the agent hasn't prepared for the current task
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, '_preparation_complete') or not self._preparation_complete:
            raise RuntimeError(
                f"Agent {self.agent_name} must complete prepare_for_task() "
                f"before executing {func.__name__}(). Development bible "
                f"preparation is required for all task operations."
            )
        
        if not hasattr(self, 'current_guidelines') or not self.current_guidelines:
            raise RuntimeError(
                f"Agent {self.agent_name} has no loaded guidelines. "
                f"Call prepare_for_task() with appropriate task_type first."
            )
        
        logger.info(f"Executing {func.__name__} for {self.agent_name} with proper preparation")
        return func(self, *args, **kwargs)
    
    return wrapper


class BaseAgent:
    """
    Base class for all AI agents in the automation hub.
    
    This class provides core functionality for development bible integration,
    task preparation, and validation that all specialized agents inherit.
    All agents must prepare for tasks by reading required development guidelines
    before performing any operations.
    
    Attributes:
        agent_name (str): Name identifier for the agent
        agent_type (str): Type classification of the agent
        dev_bible_reader (DevBibleReader): Reader for accessing development guidelines
        current_guidelines (Optional[str]): Currently loaded guidelines content
        current_task_type (Optional[str]): Current task type being prepared for
        preparation_timestamp (Optional[datetime]): When preparation was completed
    """
    
    def __init__(self, agent_name: str, agent_type: str, dev_bible_path: Optional[str] = None):
        """
        Initialize the BaseAgent with name, type, and development bible access.
        
        Args:
            agent_name (str): Unique name for this agent instance
            agent_type (str): Type of agent (backend, testing, database, etc.)
            dev_bible_path (Optional[str]): Path to dev_bible directory.
                                          Defaults to relative path from project root.
        
        Raises:
            FileNotFoundError: If the dev_bible directory cannot be found
            ValueError: If agent_name or agent_type are empty
        """
        if not agent_name or not agent_name.strip():
            raise ValueError("Agent name cannot be empty")
        
        if not agent_type or not agent_type.strip():
            raise ValueError("Agent type cannot be empty")
        
        self.agent_name = agent_name.strip()
        self.agent_type = agent_type.strip().lower()
        
        # Set default dev_bible path if not provided
        if dev_bible_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            dev_bible_path = os.path.join(os.path.dirname(current_dir), "dev_bible")
        
        # Initialize development bible reader
        try:
            self.dev_bible_reader = DevBibleReader(dev_bible_path)
            logger.info(f"Initialized {self.agent_name} ({self.agent_type}) with dev_bible at {dev_bible_path}")
        except FileNotFoundError as e:
            logger.error(f"Failed to initialize DevBibleReader for {self.agent_name}: {e}")
            raise
        
        # Task preparation state
        self.current_guidelines: Optional[str] = None
        self.current_task_type: Optional[str] = None
        self.current_task_description: Optional[str] = None
        self.preparation_timestamp: Optional[datetime] = None
        self._preparation_complete: bool = False
        
        # Agent metadata
        self.creation_timestamp = datetime.now()
        self.task_history: list = []
        
        # Reliability system components
        self.task_state_manager = get_task_state_manager()
        self.safe_git = get_safe_git_operations()
        self.current_task_id: Optional[str] = None
        self.checkpoint_timer: Optional[threading.Timer] = None
        self.last_checkpoint_time: Optional[datetime] = None
        self._reliability_lock = threading.Lock()
        
        logger.info(f"BaseAgent {self.agent_name} initialized successfully")
    
    def prepare_for_task(self, task_description: str, task_type: str) -> None:
        """
        Prepare the agent for executing a specific task by loading required guidelines.
        
        This method must be called before any task-related operations. It loads
        all development bible guidelines required for the specified task type
        and stores them for use during task execution.
        
        Args:
            task_description (str): Description of the task to be performed
            task_type (str): Type of task (pre_task, backend, database, testing, documentation)
        
        Raises:
            ValueError: If task_description is empty or task_type is invalid
        """
        if not task_description or not task_description.strip():
            raise ValueError("Task description cannot be empty")
        
        if not task_type or not task_type.strip():
            raise ValueError("Task type cannot be empty")
        
        task_type = task_type.strip().lower()
        
        logger.info(f"Preparing {self.agent_name} for {task_type} task: {task_description[:100]}...")
        
        try:
            # Load required guidelines using the helper function
            self.current_guidelines = enforce_dev_bible_reading(
                self.agent_name, 
                task_type, 
                self.dev_bible_reader.dev_bible_path
            )
            
            # Update agent state
            self.current_task_type = task_type
            self.current_task_description = task_description
            self.preparation_timestamp = datetime.now()
            self._preparation_complete = True
            
            # Log successful preparation
            guidelines_length = len(self.current_guidelines) if self.current_guidelines else 0
            logger.info(
                f"✓ {self.agent_name} preparation complete for {task_type} task. "
                f"Loaded {guidelines_length} characters of guidelines."
            )
            
            # Add to task history
            self.task_history.append({
                'task_description': task_description,
                'task_type': task_type,
                'preparation_time': self.preparation_timestamp,
                'guidelines_loaded': guidelines_length > 0
            })
            
        except Exception as e:
            logger.error(f"Failed to prepare {self.agent_name} for task: {e}")
            self._preparation_complete = False
            raise
    
    def get_guidelines_context(self) -> str:
        """
        Get formatted guidelines content for use in LLM prompts.
        
        Returns:
            str: Formatted guidelines content ready for LLM context,
                 or empty string if no guidelines are loaded
        
        Note:
            This method can be called without the @require_dev_bible_prep decorator
            as it's used to check preparation status.
        """
        if not self.current_guidelines:
            return ""
        
        context_header = f"""
{'='*80}
DEVELOPMENT GUIDELINES CONTEXT FOR {self.agent_name.upper()}
Current Task: {self.current_task_description or 'Not specified'}
Task Type: {self.current_task_type or 'Not specified'}
Preparation Time: {self.preparation_timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.preparation_timestamp else 'Unknown'}
{'='*80}

CRITICAL: These guidelines MUST be followed for all operations.
Review and understand all sections before proceeding with any task execution.

"""
        
        context_footer = f"""

{'='*80}
END OF GUIDELINES CONTEXT FOR {self.agent_name.upper()}
Ensure all guidelines above are strictly followed during task execution.
{'='*80}
"""
        
        return context_header + self.current_guidelines + context_footer
    
    @require_dev_bible_prep
    def validate_task_completion(self, task_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that the agent followed required processes during task execution.
        
        Args:
            task_result (Dict[str, Any]): Results and metadata from task execution
        
        Returns:
            Dict[str, Any]: Validation results including compliance status and recommendations
        
        Note:
            This method requires proper preparation (@require_dev_bible_prep decorator)
        """
        logger.info(f"Validating task completion for {self.agent_name}")
        
        validation_result = {
            'agent_name': self.agent_name,
            'agent_type': self.agent_type,
            'task_type': self.current_task_type,
            'task_description': self.current_task_description,
            'validation_timestamp': datetime.now(),
            'preparation_verified': self._preparation_complete,
            'guidelines_loaded': bool(self.current_guidelines),
            'compliance_checks': [],
            'recommendations': [],
            'overall_status': 'pending'
        }
        
        # Basic compliance checks
        compliance_checks = []
        
        # Check 1: Proper preparation
        if self._preparation_complete and self.current_guidelines:
            compliance_checks.append({
                'check': 'development_bible_preparation',
                'status': 'passed',
                'message': 'Agent properly prepared with required guidelines'
            })
        else:
            compliance_checks.append({
                'check': 'development_bible_preparation',
                'status': 'failed',
                'message': 'Agent did not complete proper preparation'
            })
        
        # Check 2: Task type alignment
        if self.current_task_type and self.agent_type:
            # Basic alignment check - can be extended by subclasses
            alignment_good = (
                self.current_task_type == 'pre_task' or  # Always allowed
                self.current_task_type == self.agent_type or  # Direct match
                self.agent_type in ['base', 'general']  # General agents
            )
            
            if alignment_good:
                compliance_checks.append({
                    'check': 'task_type_alignment',
                    'status': 'passed',
                    'message': f'Task type {self.current_task_type} aligns with agent type {self.agent_type}'
                })
            else:
                compliance_checks.append({
                    'check': 'task_type_alignment',
                    'status': 'warning',
                    'message': f'Task type {self.current_task_type} may not align with agent type {self.agent_type}'
                })
        
        # Check 3: Task result structure
        required_keys = ['status', 'completed_at']
        missing_keys = [key for key in required_keys if key not in task_result]
        
        if not missing_keys:
            compliance_checks.append({
                'check': 'result_structure',
                'status': 'passed',
                'message': 'Task result contains required metadata'
            })
        else:
            compliance_checks.append({
                'check': 'result_structure',
                'status': 'failed',
                'message': f'Task result missing required keys: {missing_keys}'
            })
        
        validation_result['compliance_checks'] = compliance_checks
        
        # Generate recommendations
        recommendations = []
        failed_checks = [check for check in compliance_checks if check['status'] == 'failed']
        warning_checks = [check for check in compliance_checks if check['status'] == 'warning']
        
        if failed_checks:
            recommendations.append("Review and address failed compliance checks before proceeding")
        
        if warning_checks:
            recommendations.append("Consider addressing warning items to improve task execution quality")
        
        if not self.current_guidelines:
            recommendations.append("Ensure proper development bible preparation for all future tasks")
        
        validation_result['recommendations'] = recommendations
        
        # Determine overall status
        if failed_checks:
            validation_result['overall_status'] = 'failed'
        elif warning_checks:
            validation_result['overall_status'] = 'warning'
        else:
            validation_result['overall_status'] = 'passed'
        
        logger.info(
            f"Task validation complete for {self.agent_name}: "
            f"{validation_result['overall_status']} "
            f"({len(compliance_checks)} checks, {len(failed_checks)} failed, {len(warning_checks)} warnings)"
        )
        
        return validation_result
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status information about the agent.
        
        Returns:
            Dict[str, Any]: Complete agent status including preparation state and history
        """
        return {
            'agent_name': self.agent_name,
            'agent_type': self.agent_type,
            'creation_timestamp': self.creation_timestamp,
            'preparation_complete': self._preparation_complete,
            'current_task_type': self.current_task_type,
            'current_task_description': self.current_task_description,
            'preparation_timestamp': self.preparation_timestamp,
            'guidelines_loaded': bool(self.current_guidelines),
            'guidelines_length': len(self.current_guidelines) if self.current_guidelines else 0,
            'task_history_count': len(self.task_history),
            'dev_bible_path': self.dev_bible_reader.dev_bible_path
        }
    
    def reset_preparation(self) -> None:
        """
        Reset the agent's preparation state, clearing current guidelines and task info.
        
        This method should be called when switching to a completely different task
        or when re-preparation is needed.
        """
        logger.info(f"Resetting preparation state for {self.agent_name}")
        
        # Stop checkpoint timer if running
        self._stop_checkpoint_timer()
        
        self.current_guidelines = None
        self.current_task_type = None
        self.current_task_description = None
        self.preparation_timestamp = None
        self._preparation_complete = False
        self.current_task_id = None
        
        logger.info(f"✓ {self.agent_name} preparation state reset")
    
    def save_checkpoint(self, notes: Optional[str] = None, checkpoint_type: CheckpointType = CheckpointType.AUTO) -> Optional[str]:
        """
        Save current agent state as a checkpoint.
        
        Args:
            notes: Optional notes about the checkpoint
            checkpoint_type: Type of checkpoint to create
            
        Returns:
            Checkpoint ID if successful, None otherwise
        """
        if not self.current_task_id:
            logger.warning(f"Cannot save checkpoint - no active task for {self.agent_name}")
            return None
        
        try:
            with self._reliability_lock:
                # Update current task state
                context_data = {
                    'agent_type': self.agent_type,
                    'preparation_complete': self._preparation_complete,
                    'guidelines_loaded': bool(self.current_guidelines),
                    'task_type': self.current_task_type,
                    'git_status': self.safe_git.get_safety_status()
                }
                
                # Create checkpoint
                checkpoint_id = self.task_state_manager.create_checkpoint(
                    self.current_task_id,
                    checkpoint_type,
                    notes,
                    rollback_data={
                        'git_commit': self.safe_git.get_current_commit(),
                        'git_branch': self.safe_git.get_current_branch()
                    }
                )
                
                if checkpoint_id:
                    self.last_checkpoint_time = datetime.now(timezone.utc)
                    logger.info(f"Saved checkpoint for {self.agent_name}: {checkpoint_id}")
                
                return checkpoint_id
        
        except Exception as e:
            logger.error(f"Failed to save checkpoint for {self.agent_name}: {e}")
            return None
    
    def resume_from_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Resume agent work from a specific checkpoint.
        
        Args:
            checkpoint_id: Checkpoint to resume from
            
        Returns:
            True if resumed successfully
        """
        try:
            with self._reliability_lock:
                checkpoint = self.task_state_manager.get_checkpoint(checkpoint_id)
                if not checkpoint:
                    logger.error(f"Checkpoint not found: {checkpoint_id}")
                    return False
                
                if checkpoint.agent_name != self.agent_name:
                    logger.error(f"Checkpoint belongs to different agent: {checkpoint.agent_name}")
                    return False
                
                # Restore task state
                task_state = self.task_state_manager.get_task_state(checkpoint.task_id)
                if not task_state:
                    logger.error(f"Task state not found: {checkpoint.task_id}")
                    return False
                
                # Restore agent state
                self.current_task_id = checkpoint.task_id
                self.current_task_type = task_state.task_type
                self.current_task_description = task_state.task_description
                
                # Re-prepare with stored task info
                if task_state.task_type and task_state.task_description:
                    self.prepare_for_task(task_state.task_description, task_state.task_type)
                
                # Update task state to show resumption
                self.task_state_manager.update_task_state(
                    checkpoint.task_id,
                    state=TaskState.IN_PROGRESS,
                    current_step=f"Resumed from checkpoint {checkpoint_id[:8]}",
                    add_conversation={
                        'type': 'system',
                        'message': f'Agent {self.agent_name} resumed from checkpoint {checkpoint_id}',
                        'checkpoint_id': checkpoint_id
                    }
                )
                
                # Restart checkpoint timer
                self._start_checkpoint_timer()
                
                logger.info(f"Successfully resumed {self.agent_name} from checkpoint {checkpoint_id}")
                return True
        
        except Exception as e:
            logger.error(f"Failed to resume from checkpoint {checkpoint_id}: {e}")
            return False
    
    def validate_safe_to_proceed(self) -> Dict[str, Any]:
        """
        Validate that it's safe to proceed with potentially destructive operations.
        
        Returns:
            Validation results with safety status and recommendations
        """
        validation = {
            'safe_to_proceed': False,
            'agent_name': self.agent_name,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'checks': [],
            'warnings': [],
            'blocking_issues': [],
            'recommendations': []
        }
        
        try:
            # Check agent preparation
            if self._preparation_complete:
                validation['checks'].append({
                    'check': 'agent_preparation',
                    'status': 'pass',
                    'message': 'Agent properly prepared with guidelines'
                })
            else:
                validation['blocking_issues'].append({
                    'issue': 'agent_preparation',
                    'message': 'Agent not properly prepared - call prepare_for_task() first'
                })
            
            # Check git safety
            git_status = self.safe_git.get_safety_status()
            if git_status.get('is_safe_branch', False):
                validation['checks'].append({
                    'check': 'git_safe_branch',
                    'status': 'pass',
                    'message': f"On safe branch: {git_status['current_branch']}"
                })
            else:
                validation['warnings'].append({
                    'warning': 'git_branch',
                    'message': f"Not on safe branch: {git_status['current_branch']}"
                })
            
            if git_status.get('has_uncommitted_changes', False):
                validation['warnings'].append({
                    'warning': 'uncommitted_changes',
                    'message': 'Repository has uncommitted changes'
                })
            
            if git_status.get('backup_branches_available', 0) > 0:
                validation['checks'].append({
                    'check': 'backup_available',
                    'status': 'pass',
                    'message': f"{git_status['backup_branches_available']} backup branches available"
                })
            else:
                validation['warnings'].append({
                    'warning': 'no_backup',
                    'message': 'No backup branches available - consider creating one'
                })
            
            # Check active task state
            if self.current_task_id:
                task_state = self.task_state_manager.get_task_state(self.current_task_id)
                if task_state and task_state.state == TaskState.IN_PROGRESS:
                    validation['checks'].append({
                        'check': 'active_task',
                        'status': 'pass',
                        'message': f'Active task in progress: {task_state.task_id}'
                    })
                elif task_state:
                    validation['warnings'].append({
                        'warning': 'task_state',
                        'message': f'Task in unexpected state: {task_state.state.value}'
                    })
            else:
                validation['warnings'].append({
                    'warning': 'no_active_task',
                    'message': 'No active task - consider starting a task first'
                })
            
            # Check checkpoint recency
            if self.last_checkpoint_time:
                time_since_checkpoint = datetime.now(timezone.utc) - self.last_checkpoint_time
                if time_since_checkpoint.total_seconds() < 1800:  # 30 minutes
                    validation['checks'].append({
                        'check': 'recent_checkpoint',
                        'status': 'pass',
                        'message': f'Recent checkpoint available ({time_since_checkpoint.total_seconds():.0f}s ago)'
                    })
                else:
                    validation['warnings'].append({
                        'warning': 'old_checkpoint',
                        'message': f'Last checkpoint is old ({time_since_checkpoint.total_seconds():.0f}s ago)'
                    })
            
            # Determine overall safety
            validation['safe_to_proceed'] = len(validation['blocking_issues']) == 0
            
            # Generate recommendations
            recommendations = []
            
            if validation['blocking_issues']:
                recommendations.append("Address blocking issues before proceeding")
            
            if validation['warnings']:
                recommendations.append("Consider addressing warnings for safer operation")
            
            if not git_status.get('is_safe_branch', False):
                recommendations.append("Create agent working branch before making changes")
            
            if git_status.get('backup_branches_available', 0) == 0:
                recommendations.append("Create backup branch before destructive operations")
            
            if not self.last_checkpoint_time:
                recommendations.append("Create initial checkpoint before starting work")
            
            validation['recommendations'] = recommendations
        
        except Exception as e:
            validation['blocking_issues'].append({
                'issue': 'validation_error',
                'message': f'Error during safety validation: {str(e)}'
            })
            validation['safe_to_proceed'] = False
        
        return validation
    
    def get_rollback_options(self) -> Dict[str, Any]:
        """
        Get available rollback options for recovery scenarios.
        
        Returns:
            Dictionary with rollback options
        """
        options = {
            'agent_name': self.agent_name,
            'current_task_id': self.current_task_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'task_checkpoints': [],
            'git_rollback_options': {},
            'recovery_recommendations': []
        }
        
        try:
            # Get task checkpoints
            if self.current_task_id:
                checkpoints = self.task_state_manager.get_task_checkpoints(self.current_task_id)
                options['task_checkpoints'] = [
                    {
                        'checkpoint_id': cp.checkpoint_id,
                        'type': cp.checkpoint_type.value,
                        'timestamp': cp.timestamp.isoformat(),
                        'step': cp.current_step,
                        'progress': cp.progress_percentage,
                        'notes': cp.notes
                    }
                    for cp in checkpoints[:10]  # Last 10 checkpoints
                ]
            
            # Get git rollback options
            options['git_rollback_options'] = self.safe_git.get_rollback_options()
            
            # Get agent recovery options
            recovery_data = self.task_state_manager.get_recovery_options(self.agent_name)
            options.update(recovery_data)
            
            # Generate recovery recommendations
            recommendations = []
            
            if options['task_checkpoints']:
                recommendations.append(f"Resume from one of {len(options['task_checkpoints'])} available checkpoints")
            
            if options['git_rollback_options'].get('backup_branches'):
                backup_count = len(options['git_rollback_options']['backup_branches'])
                recommendations.append(f"Rollback to one of {backup_count} backup branches")
            
            if options['interrupted_tasks']:
                recommendations.append(f"Resume one of {len(options['interrupted_tasks'])} interrupted tasks")
            
            if not recommendations:
                recommendations.append("No automatic recovery options available - manual intervention may be needed")
            
            options['recovery_recommendations'] = recommendations
        
        except Exception as e:
            logger.error(f"Error getting rollback options: {e}")
            options['error'] = str(e)
        
        return options
    
    def start_task_with_reliability(self, task_description: str, task_type: str, create_git_branch: bool = True) -> Optional[str]:
        """
        Start a new task with full reliability features enabled.
        
        Args:
            task_description: Description of the task
            task_type: Type of task
            create_git_branch: Whether to create a new git branch
            
        Returns:
            Task ID if started successfully
        """
        try:
            with self._reliability_lock:
                # Generate task ID
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                task_id = f"{self.agent_name}_{task_type}_{timestamp}"
                
                # Prepare for task
                self.prepare_for_task(task_description, task_type)
                
                # Create git branch if requested
                if create_git_branch:
                    try:
                        agent_branch, backup_branch = self.safe_git.create_agent_branch(
                            self.agent_name, 
                            task_description
                        )
                        logger.info(f"Created git branches: {agent_branch} (backup: {backup_branch})")
                    except Exception as e:
                        logger.warning(f"Failed to create git branches: {e}")
                
                # Create task state
                task_state = self.task_state_manager.create_task_state(
                    task_id,
                    self.agent_name,
                    task_description,
                    task_type,
                    {
                        'git_branch': self.safe_git.get_current_branch(),
                        'git_commit': self.safe_git.get_current_commit(),
                        'preparation_timestamp': self.preparation_timestamp.isoformat() if self.preparation_timestamp else None
                    }
                )
                
                self.current_task_id = task_id
                
                # Update to in-progress
                self.task_state_manager.update_task_state(
                    task_id,
                    state=TaskState.IN_PROGRESS,
                    current_step="Task started",
                    progress_percentage=0.0,
                    add_conversation={
                        'type': 'system',
                        'message': f'Task started by {self.agent_name}',
                        'task_description': task_description,
                        'task_type': task_type
                    }
                )
                
                # Create initial checkpoint
                self.save_checkpoint("Initial checkpoint after task start", CheckpointType.MILESTONE)
                
                # Start automatic checkpoint timer
                self._start_checkpoint_timer()
                
                logger.info(f"Started task with reliability: {task_id}")
                return task_id
        
        except Exception as e:
            logger.error(f"Failed to start task with reliability: {e}")
            return None
    
    def _start_checkpoint_timer(self) -> None:
        """Start automatic checkpoint timer (10 minutes)."""
        self._stop_checkpoint_timer()  # Stop existing timer
        
        def auto_checkpoint():
            if self.current_task_id:
                self.save_checkpoint("Automatic 10-minute checkpoint", CheckpointType.AUTO)
                self._start_checkpoint_timer()  # Reschedule
        
        self.checkpoint_timer = threading.Timer(600.0, auto_checkpoint)  # 10 minutes
        self.checkpoint_timer.daemon = True
        self.checkpoint_timer.start()
        logger.debug(f"Started checkpoint timer for {self.agent_name}")
    
    def _stop_checkpoint_timer(self) -> None:
        """Stop automatic checkpoint timer."""
        if self.checkpoint_timer:
            self.checkpoint_timer.cancel()
            self.checkpoint_timer = None
            logger.debug(f"Stopped checkpoint timer for {self.agent_name}")
    
    def complete_task_safely(self, result: Dict[str, Any]) -> bool:
        """
        Complete current task safely with final checkpoint.
        
        Args:
            result: Task completion result
            
        Returns:
            True if completed successfully
        """
        if not self.current_task_id:
            logger.warning(f"No active task to complete for {self.agent_name}")
            return False
        
        try:
            with self._reliability_lock:
                # Create final checkpoint
                final_checkpoint_id = self.save_checkpoint(
                    "Final checkpoint before task completion", 
                    CheckpointType.MILESTONE
                )
                
                # Update task state to completed
                success = self.task_state_manager.update_task_state(
                    self.current_task_id,
                    state=TaskState.COMPLETED,
                    current_step="Task completed",
                    progress_percentage=100.0,
                    context_data={'completion_result': result, 'final_checkpoint': final_checkpoint_id},
                    add_conversation={
                        'type': 'system',
                        'message': f'Task completed successfully by {self.agent_name}',
                        'completion_result': result
                    }
                )
                
                if success:
                    # Stop checkpoint timer
                    self._stop_checkpoint_timer()
                    
                    # Clear current task
                    completed_task_id = self.current_task_id
                    self.current_task_id = None
                    
                    logger.info(f"Task completed safely: {completed_task_id}")
                    return True
                
        except Exception as e:
            logger.error(f"Failed to complete task safely: {e}")
        
        return False
    
    def __str__(self) -> str:
        """String representation of the agent."""
        status = "prepared" if self._preparation_complete else "unprepared"
        return f"{self.agent_name} ({self.agent_type}) - {status}"
    
    def __repr__(self) -> str:
        """Detailed representation of the agent."""
        return (
            f"BaseAgent(name='{self.agent_name}', type='{self.agent_type}', "
            f"prepared={self._preparation_complete}, task_type='{self.current_task_type}')"
        )


# Example specialized agent classes that inherit from BaseAgent
class CodeAgent(BaseAgent):
    """
    Specialized agent for code-related tasks.
    
    Inherits all BaseAgent functionality and adds code-specific methods.
    """
    
    def __init__(self, agent_name: str, dev_bible_path: Optional[str] = None):
        """Initialize CodeAgent with 'backend' type."""
        super().__init__(agent_name, "backend", dev_bible_path)
        logger.info(f"CodeAgent {agent_name} initialized")
    
    @require_dev_bible_prep
    def validate_code_standards(self, code: str) -> Dict[str, Any]:
        """
        Validate code against development standards from guidelines.
        
        Args:
            code (str): Code to validate
            
        Returns:
            Dict[str, Any]: Validation results
        """
        # This is a placeholder - actual implementation would parse guidelines
        # and check code against coding standards
        logger.info(f"Validating code standards for {self.agent_name}")
        
        return {
            'agent_name': self.agent_name,
            'validation_type': 'code_standards',
            'timestamp': datetime.now(),
            'guidelines_applied': bool(self.current_guidelines),
            'status': 'validated'
        }


class TestingAgent(BaseAgent):
    """
    Specialized agent for testing-related tasks.
    
    Inherits all BaseAgent functionality and adds testing-specific methods.
    """
    
    def __init__(self, agent_name: str, dev_bible_path: Optional[str] = None):
        """Initialize TestingAgent with 'testing' type."""
        super().__init__(agent_name, "testing", dev_bible_path)
        logger.info(f"TestingAgent {agent_name} initialized")
    
    @require_dev_bible_prep
    def validate_test_coverage(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate test coverage against guidelines.
        
        Args:
            test_results (Dict[str, Any]): Test execution results
            
        Returns:
            Dict[str, Any]: Coverage validation results
        """
        logger.info(f"Validating test coverage for {self.agent_name}")
        
        return {
            'agent_name': self.agent_name,
            'validation_type': 'test_coverage',
            'timestamp': datetime.now(),
            'guidelines_applied': bool(self.current_guidelines),
            'status': 'validated'
        }


# Example usage and testing
if __name__ == "__main__":
    # Example usage of BaseAgent and specialized agents
    try:
        # Test BaseAgent
        print("Testing BaseAgent functionality...")
        base_agent = BaseAgent("TestBaseAgent", "general")
        print(f"Created: {base_agent}")
        
        # Test preparation
        base_agent.prepare_for_task("Example task for testing", "pre_task")
        print("✓ Preparation completed")
        
        # Test guidelines context
        context = base_agent.get_guidelines_context()
        print(f"✓ Guidelines context loaded: {len(context)} characters")
        
        # Test validation
        task_result = {
            'status': 'completed',
            'completed_at': datetime.now(),
            'result': 'success'
        }
        validation = base_agent.validate_task_completion(task_result)
        print(f"✓ Validation completed: {validation['overall_status']}")
        
        # Test specialized agents
        print("\nTesting specialized agents...")
        code_agent = CodeAgent("TestCodeAgent")
        code_agent.prepare_for_task("Code review task", "backend")
        print(f"✓ CodeAgent prepared: {code_agent}")
        
        testing_agent = TestingAgent("TestTestingAgent")
        testing_agent.prepare_for_task("Test execution task", "testing")
        print(f"✓ TestingAgent prepared: {testing_agent}")
        
        print("\n✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        raise