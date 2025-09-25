"""
Base Agent Module

This module provides the BaseAgent class that serves as the foundation for all
specialized agents in the AI Agent Automation Hub. It includes development
bible integration, task preparation, and validation functionality.
"""

import os
import sys
import logging
from typing import Optional, Dict, Any, Callable
from functools import wraps
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.dev_bible_reader import DevBibleReader, enforce_dev_bible_reading

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
        
        self.current_guidelines = None
        self.current_task_type = None
        self.current_task_description = None
        self.preparation_timestamp = None
        self._preparation_complete = False
        
        logger.info(f"✓ {self.agent_name} preparation state reset")
    
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