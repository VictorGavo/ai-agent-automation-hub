"""
DevBible Reader Module

This module provides functionality to read and manage development guidelines
from the dev_bible directory structure, ensuring agents have access to
required documentation based on their task types.
"""

import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class DevBibleReader:
    """
    A class to manage reading and accessing development bible guidelines
    based on agent task types and requirements.
    """
    
    def __init__(self, dev_bible_path: str):
        """
        Initialize the DevBibleReader with the path to the dev_bible directory.
        
        Args:
            dev_bible_path (str): Path to the dev_bible directory
            
        Raises:
            FileNotFoundError: If the dev_bible directory doesn't exist
        """
        self.dev_bible_path = os.path.abspath(dev_bible_path)
        if not os.path.exists(self.dev_bible_path):
            raise FileNotFoundError(f"Dev bible directory not found: {self.dev_bible_path}")
        
        # Define required reading mappings
        self._required_reading_map = {
            "pre_task": [
                "core/_agent_quick_start.md",
                "automation_hub/current_priorities.md"
            ],
            "backend": [
                "core/coding_standards.md",
                "core/workflow_process.md",
                "automation_hub/architecture.md"
            ],
            "database": [
                "core/security_rules.md",
                "automation_hub/architecture.md"
            ],
            "testing": [
                "core/coding_standards.md",
                "core/workflow_process.md"
            ],
            "documentation": [
                "core/communication.md",
                "core/workflow_process.md"
            ]
        }
    
    def get_required_reading(self, task_type: str) -> List[str]:
        """
        Get the list of required markdown files for a specific task type.
        
        Args:
            task_type (str): The type of task (pre_task, backend, database, testing, documentation)
            
        Returns:
            List[str]: List of relative file paths within the dev_bible directory
            
        Raises:
            ValueError: If the task_type is not recognized
        """
        if task_type not in self._required_reading_map:
            available_types = ", ".join(self._required_reading_map.keys())
            raise ValueError(f"Unknown task type '{task_type}'. Available types: {available_types}")
        
        return self._required_reading_map[task_type].copy()
    
    def read_guidelines(self, file_path: str) -> Optional[str]:
        """
        Read the content of a markdown file from the dev_bible directory.
        
        Args:
            file_path (str): Relative path to the markdown file within dev_bible
            
        Returns:
            Optional[str]: Content of the file, or None if file doesn't exist
            
        Note:
            Logs warnings if files are not found
        """
        full_path = os.path.join(self.dev_bible_path, file_path)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as file:
                content = file.read()
                logger.info(f"Successfully read guidelines from {file_path}")
                return content
        except FileNotFoundError:
            logger.warning(f"Guidelines file not found: {full_path}")
            return None
        except IOError as e:
            logger.error(f"Error reading guidelines file {full_path}: {e}")
            return None
    
    def validate_agent_prep(self, agent_name: str, task_type: str) -> None:
        """
        Print the required reading list for an agent preparing for a specific task type.
        
        Args:
            agent_name (str): Name of the agent
            task_type (str): Type of task the agent will perform
        """
        try:
            required_files = self.get_required_reading(task_type)
            
            print(f"\n{'='*60}")
            print(f"REQUIRED READING FOR {agent_name.upper()}")
            print(f"Task Type: {task_type.upper()}")
            print(f"{'='*60}")
            
            if not required_files:
                print("No specific guidelines required for this task type.")
                return
            
            print(f"\nThe following {len(required_files)} document(s) must be reviewed:")
            
            for i, file_path in enumerate(required_files, 1):
                full_path = os.path.join(self.dev_bible_path, file_path)
                status = "✓ Available" if os.path.exists(full_path) else "✗ Missing"
                print(f"{i:2d}. {file_path}")
                print(f"     Status: {status}")
            
            print(f"\n{'='*60}")
            print("Ensure all documents are reviewed before proceeding with task execution.")
            print(f"{'='*60}\n")
            
        except ValueError as e:
            print(f"Error: {e}")
    
    def get_all_guidelines_content(self, task_type: str) -> str:
        """
        Load all required guidelines content for a task type into a single string.
        
        Args:
            task_type (str): Type of task
            
        Returns:
            str: Combined content of all required guidelines
        """
        required_files = self.get_required_reading(task_type)
        combined_content = []
        
        combined_content.append(f"# Development Guidelines for {task_type.upper()} Tasks")
        combined_content.append("=" * 60)
        combined_content.append("")
        
        for file_path in required_files:
            content = self.read_guidelines(file_path)
            if content:
                combined_content.append(f"## Guidelines from {file_path}")
                combined_content.append("-" * 40)
                combined_content.append(content)
                combined_content.append("")
                combined_content.append("-" * 40)
                combined_content.append("")
            else:
                combined_content.append(f"## WARNING: Could not load {file_path}")
                combined_content.append("")
        
        return "\n".join(combined_content)


def enforce_dev_bible_reading(agent_name: str, task_type: str, 
                            dev_bible_path: str = None) -> str:
    """
    Helper function to load all required guidelines into a string for agent context.
    
    This function creates a DevBibleReader instance and loads all required
    guidelines for the specified task type into a formatted string that can
    be used as context for agent operations.
    
    Args:
        agent_name (str): Name of the agent requiring the guidelines
        task_type (str): Type of task the agent will perform
        dev_bible_path (str, optional): Path to dev_bible directory. 
                                       Defaults to relative path from current location.
    
    Returns:
        str: Formatted string containing all required guidelines content
        
    Example:
        >>> guidelines = enforce_dev_bible_reading("BackendAgent", "backend")
        >>> print(guidelines[:100])  # First 100 characters
    """
    if dev_bible_path is None:
        # Default to dev_bible directory relative to current working directory
        dev_bible_path = os.path.join(os.getcwd(), "dev_bible")
    
    try:
        reader = DevBibleReader(dev_bible_path)
        
        # Add header with agent and task information
        header = f"""
{'='*80}
DEVELOPMENT GUIDELINES CONTEXT
Agent: {agent_name}
Task Type: {task_type}
Generated: {os.path.basename(__file__)}
{'='*80}

IMPORTANT: These guidelines must be followed for all {task_type} tasks.
Review and understand all sections before proceeding.

"""
        
        guidelines_content = reader.get_all_guidelines_content(task_type)
        
        footer = f"""

{'='*80}
END OF DEVELOPMENT GUIDELINES
Agent: {agent_name} | Task Type: {task_type}
{'='*80}
"""
        
        return header + guidelines_content + footer
        
    except (FileNotFoundError, ValueError) as e:
        error_message = f"""
ERROR: Could not load development guidelines for {agent_name}
Task Type: {task_type}
Error: {str(e)}

Please ensure the dev_bible directory exists and contains the required files.
"""
        logger.error(f"Failed to enforce dev bible reading: {e}")
        return error_message


# Example usage and testing
if __name__ == "__main__":
    # Example usage of the DevBibleReader class
    try:
        # Initialize with dev_bible path
        reader = DevBibleReader("../dev_bible")
        
        # Validate agent preparation
        reader.validate_agent_prep("TestAgent", "backend")
        
        # Get required reading list
        backend_files = reader.get_required_reading("backend")
        print(f"Backend task requires: {backend_files}")
        
        # Load guidelines for agent context
        guidelines = enforce_dev_bible_reading("ExampleAgent", "pre_task")
        print(f"Guidelines loaded: {len(guidelines)} characters")
        
    except Exception as e:
        print(f"Example execution error: {e}")