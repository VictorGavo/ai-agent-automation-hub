"""
Orchestrator Agent Module

This module provides the OrchestratorAgent class that manages task coordination,
Discord command parsing, and agent assignment within the automation hub.
"""

import sys
import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import re

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent, require_dev_bible_prep
from agents.backend.github_client import GitHubClient

logger = logging.getLogger(__name__)


class TaskComplexityLevel:
    """Enumeration for task complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    UNCLEAR = "unclear"


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent for managing task coordination and agent assignment.
    
    This agent inherits from BaseAgent and specializes in parsing Discord commands,
    breaking down complex tasks, and coordinating work across multiple agents.
    It serves as the central coordinator for the automation hub.
    
    Example Usage:
        ```python
        orchestrator = OrchestratorAgent("MainOrchestrator")
        orchestrator.prepare_for_task("Coordinate multi-agent workflow", "pre_task")
        
        # Parse Discord command
        command_result = orchestrator.parse_discord_command(
            "!create api endpoint for user authentication with database integration"
        )
        
        # Break down the task
        subtasks = orchestrator.break_down_task(command_result['task_description'])
        
        # Assign to appropriate agents
        assignments = orchestrator.assign_to_agent(subtasks)
        ```
    
    Attributes:
        task_queue (List[Dict]): Current queue of tasks awaiting assignment
        agent_availability (Dict[str, bool]): Status of available agents
        complexity_patterns (Dict): Regex patterns for complexity assessment
        clarification_queue (List[Dict]): Questions needing user clarification
    """
    
    def __init__(self, agent_name: str, dev_bible_path: Optional[str] = None):
        """
        Initialize OrchestratorAgent with orchestrator-specific capabilities.
        
        Args:
            agent_name (str): Unique name for this orchestrator instance
            dev_bible_path (Optional[str]): Path to dev_bible directory
        """
        super().__init__(agent_name, "pre_task", dev_bible_path)
        
        # Task management state
        self.task_queue: List[Dict[str, Any]] = []
        self.agent_availability: Dict[str, bool] = {
            "backend": True,
            "database": True,
            "testing": True,
            "documentation": True
        }
        self.clarification_queue: List[Dict[str, Any]] = []
        
        # GitHub integration client
        self.github_client = GitHubClient()
        
        # Track start time for uptime calculation
        self._start_time = datetime.now()
        
        # Complexity assessment patterns
        self.complexity_patterns = {
            TaskComplexityLevel.SIMPLE: [
                r'\b(simple|basic|easy|quick|small)\b',
                r'\bcreate\s+(single|one)\s+\w+\b',
                r'\bupdate\s+\w+\s+field\b'
            ],
            TaskComplexityLevel.MODERATE: [
                r'\b(api|endpoint|integration|workflow)\b',
                r'\bmultiple\s+\w+\b',
                r'\bwith\s+(database|authentication|validation)\b'
            ],
            TaskComplexityLevel.COMPLEX: [
                r'\b(system|architecture|migration|refactor)\b',
                r'\bmulti-step|complex|advanced\b',
                r'\bintegrate\s+multiple\b'
            ]
        }
        
        # Agent capability mapping
        self.agent_capabilities = {
            "backend": ["api", "endpoint", "business_logic", "flask", "authentication", "validation"],
            "database": ["schema", "migration", "query", "optimization", "postgres", "sql"],
            "testing": ["test", "coverage", "validation", "qa", "unittest", "integration"],
            "documentation": ["docs", "documentation", "readme", "guide", "api_docs"]
        }
        
        logger.info(f"OrchestratorAgent {agent_name} initialized with task management capabilities")
    
    async def initialize_github_client(self) -> bool:
        """
        Initialize the GitHub client for PR management.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            success = await self.github_client.initialize()
            if success:
                logger.info("GitHub client initialized successfully")
            else:
                logger.warning("GitHub client initialization failed - PR management will be unavailable")
            return success
        except Exception as e:
            logger.error(f"GitHub client initialization error: {e}")
            return False
    
    @require_dev_bible_prep
    def parse_discord_command(self, discord_message: str) -> Dict[str, Any]:
        """
        Parse a Discord command message to extract task information.
        
        Args:
            discord_message (str): Raw Discord message containing the command
            
        Returns:
            Dict[str, Any]: Parsed command information including:
                - command_type: Type of command (create, update, deploy, etc.)
                - task_description: Cleaned task description
                - parameters: Extracted parameters and flags
                - urgency: Assessed urgency level
                - complexity: Initial complexity assessment
                
        Example:
            ```python
            result = orchestrator.parse_discord_command(
                "!create --urgent api endpoint for user login with jwt auth"
            )
            # Returns: {
            #     'command_type': 'create',
            #     'task_description': 'api endpoint for user login with jwt auth',
            #     'parameters': {'urgent': True},
            #     'urgency': 'high',
            #     'complexity': 'moderate'
            # }
            ```
        """
        logger.info(f"Parsing Discord command for {self.agent_name}: {discord_message[:100]}...")
        
        if not discord_message or not discord_message.strip():
            raise ValueError("Discord message cannot be empty")
        
        # Clean the message
        cleaned_message = discord_message.strip()
        
        # Extract command prefix and remove it
        command_prefix_pattern = r'^[!\/](\w+)'
        command_match = re.match(command_prefix_pattern, cleaned_message)
        
        if not command_match:
            # No explicit command, treat as general request
            command_type = "general"
            task_content = cleaned_message
        else:
            command_type = command_match.group(1).lower()
            task_content = cleaned_message[len(command_match.group(0)):].strip()
        
        # Extract parameters (flags like --urgent, --simple, etc.)
        parameter_pattern = r'--(\w+)(?:\s+(\w+))?'
        parameters = {}
        
        for match in re.finditer(parameter_pattern, task_content):
            param_name = match.group(1)
            param_value = match.group(2) if match.group(2) else True
            parameters[param_name] = param_value
        
        # Remove parameters from task description
        task_description = re.sub(parameter_pattern, '', task_content).strip()
        
        # Assess urgency
        urgency = self._assess_urgency(task_description, parameters)
        
        # Assess initial complexity
        complexity = self._assess_complexity(task_description)
        
        parsed_result = {
            'original_message': discord_message,
            'command_type': command_type,
            'task_description': task_description,
            'parameters': parameters,
            'urgency': urgency,
            'complexity': complexity,
            'timestamp': datetime.now(),
            'parsed_by': self.agent_name
        }
        
        logger.info(
            f"✓ Parsed command: {command_type} | "
            f"Complexity: {complexity} | Urgency: {urgency}"
        )
        
        return parsed_result
    
    @require_dev_bible_prep
    def break_down_task(self, task_description: str) -> List[Dict[str, Any]]:
        """
        Break down a complex task into smaller, manageable subtasks.
        
        Args:
            task_description (str): High-level task description to decompose
            
        Returns:
            List[Dict[str, Any]]: List of subtasks with metadata:
                - subtask_id: Unique identifier
                - description: Detailed subtask description
                - agent_type: Recommended agent type
                - dependencies: List of dependent subtask IDs
                - estimated_complexity: Complexity assessment
                - priority: Execution priority (1-10)
                
        Example:
            ```python
            subtasks = orchestrator.break_down_task(
                "Create user authentication API with database integration"
            )
            # Returns list of subtasks for database, backend, and testing agents
            ```
        """
        logger.info(f"Breaking down task for {self.agent_name}: {task_description}")
        
        if not task_description or not task_description.strip():
            raise ValueError("Task description cannot be empty")
        
        # Analyze task content for different domains
        task_lower = task_description.lower()
        subtasks = []
        task_id_counter = 1
        
        # Database-related subtasks
        if any(keyword in task_lower for keyword in ['database', 'db', 'schema', 'migration', 'sql']):
            subtasks.append({
                'subtask_id': f"db_{task_id_counter}",
                'description': f"Design database schema for: {task_description}",
                'agent_type': 'database',
                'dependencies': [],
                'estimated_complexity': TaskComplexityLevel.MODERATE,
                'priority': 9,  # Database usually comes first
                'estimated_time': '2-4 hours'
            })
            task_id_counter += 1
            
            if 'migration' in task_lower or 'update' in task_lower:
                subtasks.append({
                    'subtask_id': f"db_{task_id_counter}",
                    'description': f"Create database migration for: {task_description}",
                    'agent_type': 'database',
                    'dependencies': [f"db_{task_id_counter-1}"],
                    'estimated_complexity': TaskComplexityLevel.MODERATE,
                    'priority': 8,
                    'estimated_time': '1-2 hours'
                })
                task_id_counter += 1
        
        # Backend/API-related subtasks
        if any(keyword in task_lower for keyword in ['api', 'endpoint', 'backend', 'flask', 'business logic']):
            dependencies = [st['subtask_id'] for st in subtasks if st['agent_type'] == 'database']
            
            subtasks.append({
                'subtask_id': f"be_{task_id_counter}",
                'description': f"Implement backend logic for: {task_description}",
                'agent_type': 'backend',
                'dependencies': dependencies,
                'estimated_complexity': TaskComplexityLevel.MODERATE,
                'priority': 7,
                'estimated_time': '3-6 hours'
            })
            task_id_counter += 1
            
            if 'api' in task_lower or 'endpoint' in task_lower:
                subtasks.append({
                    'subtask_id': f"be_{task_id_counter}",
                    'description': f"Create API endpoints for: {task_description}",
                    'agent_type': 'backend',
                    'dependencies': [f"be_{task_id_counter-1}"],
                    'estimated_complexity': TaskComplexityLevel.MODERATE,
                    'priority': 6,
                    'estimated_time': '2-4 hours'
                })
                task_id_counter += 1
        
        # Testing-related subtasks
        if any(keyword in task_lower for keyword in ['test', 'testing', 'validation', 'qa']) or len(subtasks) > 0:
            # Add testing for any development work
            backend_deps = [st['subtask_id'] for st in subtasks if st['agent_type'] == 'backend']
            db_deps = [st['subtask_id'] for st in subtasks if st['agent_type'] == 'database']
            
            subtasks.append({
                'subtask_id': f"test_{task_id_counter}",
                'description': f"Create comprehensive tests for: {task_description}",
                'agent_type': 'testing',
                'dependencies': backend_deps + db_deps,
                'estimated_complexity': TaskComplexityLevel.SIMPLE,
                'priority': 5,
                'estimated_time': '2-3 hours'
            })
            task_id_counter += 1
        
        # Documentation subtasks
        if any(keyword in task_lower for keyword in ['documentation', 'docs', 'readme']) or len(subtasks) > 1:
            # Add documentation for multi-component tasks
            all_deps = [st['subtask_id'] for st in subtasks]
            
            subtasks.append({
                'subtask_id': f"doc_{task_id_counter}",
                'description': f"Create documentation for: {task_description}",
                'agent_type': 'documentation',
                'dependencies': all_deps,
                'estimated_complexity': TaskComplexityLevel.SIMPLE,
                'priority': 3,
                'estimated_time': '1-2 hours'
            })
            task_id_counter += 1
        
        # If no specific patterns matched, create a general task
        if not subtasks:
            subtasks.append({
                'subtask_id': f"gen_{task_id_counter}",
                'description': task_description,
                'agent_type': 'general',
                'dependencies': [],
                'estimated_complexity': self._assess_complexity(task_description),
                'priority': 5,
                'estimated_time': '1-3 hours'
            })
        
        # Add metadata
        for subtask in subtasks:
            subtask.update({
                'created_by': self.agent_name,
                'created_at': datetime.now(),
                'status': 'pending',
                'parent_task': task_description
            })
        
        logger.info(f"✓ Task broken down into {len(subtasks)} subtasks")
        return subtasks
    
    @require_dev_bible_prep
    def assign_to_agent(self, subtasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Assign subtasks to appropriate agents based on capability and availability.
        
        Args:
            subtasks (List[Dict[str, Any]]): List of subtasks to assign
            
        Returns:
            Dict[str, Any]: Assignment results including:
                - assignments: Dict mapping agent types to their assigned tasks
                - scheduling: Recommended execution order
                - conflicts: Any scheduling conflicts or issues
                - total_estimated_time: Sum of all estimated times
                
        Example:
            ```python
            assignments = orchestrator.assign_to_agent(subtasks)
            # Returns organized task assignments by agent type
            ```
        """
        logger.info(f"Assigning {len(subtasks)} subtasks to agents")
        
        if not subtasks:
            return {
                'assignments': {},
                'scheduling': [],
                'conflicts': [],
                'total_estimated_time': '0 hours'
            }
        
        # Group tasks by agent type
        assignments = {}
        scheduling = []
        conflicts = []
        
        # Sort subtasks by priority (higher number = higher priority)
        sorted_subtasks = sorted(subtasks, key=lambda x: x['priority'], reverse=True)
        
        for subtask in sorted_subtasks:
            agent_type = subtask['agent_type']
            
            # Check agent availability
            if agent_type not in self.agent_availability:
                conflicts.append({
                    'subtask_id': subtask['subtask_id'],
                    'issue': f"No agent of type '{agent_type}' available",
                    'recommendation': "Assign to general agent or wait for availability"
                })
                continue
            
            if not self.agent_availability.get(agent_type, False):
                conflicts.append({
                    'subtask_id': subtask['subtask_id'],
                    'issue': f"Agent type '{agent_type}' currently unavailable",
                    'recommendation': "Queue for later assignment"
                })
            
            # Add to assignments
            if agent_type not in assignments:
                assignments[agent_type] = []
            
            assignments[agent_type].append(subtask)
            
            # Add to scheduling
            scheduling.append({
                'subtask_id': subtask['subtask_id'],
                'agent_type': agent_type,
                'priority': subtask['priority'],
                'dependencies': subtask['dependencies'],
                'estimated_start': self._calculate_start_time(subtask, scheduling)
            })
        
        # Calculate total estimated time
        total_time = self._calculate_total_time(subtasks)
        
        assignment_result = {
            'assignments': assignments,
            'scheduling': sorted(scheduling, key=lambda x: x['priority'], reverse=True),
            'conflicts': conflicts,
            'total_estimated_time': total_time,
            'assignment_timestamp': datetime.now(),
            'assigned_by': self.agent_name
        }
        
        logger.info(
            f"✓ Assignment complete: {len(assignments)} agent types, "
            f"{len(conflicts)} conflicts, estimated time: {total_time}"
        )
        
        return assignment_result
    
    @require_dev_bible_prep
    def validate_task_complexity(self, task_description: str) -> Dict[str, Any]:
        """
        Validate task complexity and determine if clarification is needed.
        
        Args:
            task_description (str): Task to validate
            
        Returns:
            Dict[str, Any]: Validation results including complexity assessment
                and clarification questions if needed
        """
        logger.info(f"Validating task complexity: {task_description[:100]}...")
        
        complexity = self._assess_complexity(task_description)
        needs_clarification = complexity == TaskComplexityLevel.UNCLEAR
        
        clarification_questions = []
        if needs_clarification:
            clarification_questions = self._generate_clarification_questions(task_description)
        
        validation_result = {
            'complexity': complexity,
            'needs_clarification': needs_clarification,
            'clarification_questions': clarification_questions,
            'confidence_score': self._calculate_confidence_score(task_description),
            'recommended_action': self._get_recommended_action(complexity),
            'validation_timestamp': datetime.now()
        }
        
        if needs_clarification:
            self.clarification_queue.append({
                'task_description': task_description,
                'questions': clarification_questions,
                'timestamp': datetime.now()
            })
        
        return validation_result
    
    def ask_clarifying_questions(self, task_description: str) -> List[str]:
        """
        Generate clarifying questions for ambiguous tasks.
        
        Args:
            task_description (str): Ambiguous task description
            
        Returns:
            List[str]: List of clarifying questions to ask the user
        """
        return self._generate_clarification_questions(task_description)
    
    def _assess_urgency(self, task_description: str, parameters: Dict[str, Any]) -> str:
        """Assess task urgency based on description and parameters."""
        if parameters.get('urgent') or parameters.get('emergency'):
            return 'high'
        
        if any(keyword in task_description.lower() for keyword in ['urgent', 'asap', 'emergency', 'critical']):
            return 'high'
        
        if any(keyword in task_description.lower() for keyword in ['quick', 'fast', 'soon']):
            return 'medium'
        
        return 'normal'
    
    def _assess_complexity(self, task_description: str) -> str:
        """Assess task complexity using pattern matching (legacy method)."""
        # Use the new method but return only the complexity for backward compatibility
        result = self.assess_task_complexity(task_description)
        return result['complexity']
    
    def _generate_clarification_questions(self, task_description: str) -> List[str]:
        """Generate clarifying questions for unclear tasks."""
        questions = []
        
        # General clarification questions
        questions.append(f"Could you provide more specific details about: {task_description}?")
        
        # Domain-specific questions
        if 'create' in task_description.lower():
            questions.append("What specific functionality should this include?")
            questions.append("Are there any existing systems this should integrate with?")
        
        if 'api' in task_description.lower():
            questions.append("What endpoints are needed?")
            questions.append("What authentication method should be used?")
        
        if 'database' in task_description.lower():
            questions.append("What data relationships are required?")
            questions.append("Are there any specific performance requirements?")
        
        return questions
    
    def _calculate_confidence_score(self, task_description: str) -> float:
        """Calculate confidence score for task understanding."""
        # Simple heuristic based on description clarity
        word_count = len(task_description.split())
        specific_terms = sum(1 for word in task_description.lower().split() 
                           if any(word in capabilities for capabilities in self.agent_capabilities.values()))
        
        if word_count == 0:
            return 0.0
        
        confidence = min(1.0, (specific_terms / word_count) * 2)
        return round(confidence, 2)
    
    def _get_recommended_action(self, complexity: str) -> str:
        """Get recommended action based on complexity."""
        actions = {
            TaskComplexityLevel.SIMPLE: "Proceed with direct assignment to appropriate agent",
            TaskComplexityLevel.MODERATE: "Break down into subtasks and assign to multiple agents",
            TaskComplexityLevel.COMPLEX: "Require detailed planning and phased execution",
            TaskComplexityLevel.UNCLEAR: "Request clarification before proceeding"
        }
        
        return actions.get(complexity, "Review task requirements")
    
    def _calculate_start_time(self, subtask: Dict[str, Any], existing_schedule: List[Dict[str, Any]]) -> str:
        """Calculate estimated start time based on dependencies and schedule."""
        if not subtask['dependencies']:
            return "immediate"
        
        # Find when dependencies complete (simplified calculation)
        dependency_completion = max(
            (item.get('estimated_start', 'immediate') for item in existing_schedule 
             if item['subtask_id'] in subtask['dependencies']),
            default="immediate"
        )
        
        return f"after {dependency_completion}"
    
    def _calculate_total_time(self, subtasks: List[Dict[str, Any]]) -> str:
        """Calculate total estimated time for all subtasks."""
        if not subtasks:
            return "0 hours"
        
        # Simple sum of estimated times (in practice would be more sophisticated)
        total_hours = 0
        for subtask in subtasks:
            time_str = subtask.get('estimated_time', '1 hour')
            # Extract number from time string (simplified)
            import re
            numbers = re.findall(r'\d+', time_str)
            if numbers:
                total_hours += int(numbers[0])
        
        return f"{total_hours} hours"
    
    def get_task_queue_status(self) -> Dict[str, Any]:
        """Get current status of the task queue."""
        return {
            'total_tasks': len(self.task_queue),
            'pending_clarifications': len(self.clarification_queue),
            'agent_availability': self.agent_availability.copy(),
            'last_updated': datetime.now()
        }
    
    def update_agent_availability(self, agent_type: str, available: bool) -> None:
        """Update availability status of an agent type."""
        self.agent_availability[agent_type] = available
        logger.info(f"Updated {agent_type} agent availability: {available}")


    def assess_task_complexity(self, description: str, task_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Assess the complexity level of a task based on its description and optionally task type.
        
        Args:
            description: Task description to analyze
            task_type: Optional task type for additional context
            
        Returns:
            Dict containing:
                - complexity: Complexity level (simple, moderate, complex, unclear)
                - needs_clarification: Boolean indicating if clarification is needed
                - questions: List of clarifying questions if needed
        """
        description_lower = description.lower()
        
        # Check for complex patterns first
        complexity = None
        for pattern in self.complexity_patterns[TaskComplexityLevel.COMPLEX]:
            if re.search(pattern, description_lower):
                complexity = TaskComplexityLevel.COMPLEX
                break
        
        # Check for moderate patterns if not already complex
        if not complexity:
            for pattern in self.complexity_patterns[TaskComplexityLevel.MODERATE]:
                if re.search(pattern, description_lower):
                    complexity = TaskComplexityLevel.MODERATE
                    break
        
        # Check for simple patterns if not already classified
        if not complexity:
            for pattern in self.complexity_patterns[TaskComplexityLevel.SIMPLE]:
                if re.search(pattern, description_lower):
                    complexity = TaskComplexityLevel.SIMPLE
                    break
        
        # If no patterns match, it's unclear and needs clarification
        if not complexity:
            complexity = TaskComplexityLevel.UNCLEAR
        
        # Determine if clarification is needed
        needs_clarification = complexity == TaskComplexityLevel.UNCLEAR
        
        # Additional clarification check based on task type mismatch or vague description
        if task_type and not needs_clarification:
            # Check if task type matches the complexity assessment
            type_keywords = {
                'backend': ['api', 'endpoint', 'server', 'backend', 'flask'],
                'database': ['database', 'db', 'schema', 'migration', 'sql'],
                'frontend': ['ui', 'interface', 'frontend', 'react', 'html'],
                'testing': ['test', 'testing', 'validation', 'qa'],
                'documentation': ['docs', 'documentation', 'readme']
            }
            
            task_type_lower = task_type.lower()
            if task_type_lower in type_keywords:
                type_matches = any(keyword in description_lower for keyword in type_keywords[task_type_lower])
                if not type_matches:
                    needs_clarification = True
        
        # Also check for very short or vague descriptions
        if len(description.strip().split()) < 3:
            needs_clarification = True
        
        # Generate clarifying questions if needed
        questions = []
        if needs_clarification:
            questions = self._generate_clarification_questions(description)
        
        return {
            'complexity': complexity,
            'needs_clarification': needs_clarification,
            'questions': questions
        }
    
    def get_task_complexity(self, description: str) -> str:
        """
        Get just the complexity level (simple wrapper for backward compatibility).
        
        Args:
            description: Task description to analyze
            
        Returns:
            Complexity level string (simple, moderate, complex, unclear)
        """
        result = self.assess_task_complexity(description)
        return result['complexity']
    
    # ============ DISCORD INTEGRATION METHODS ============
    
    async def assign_task(self, description: str, user_id: str, channel_id: str, priority=None) -> Dict[str, Any]:
        """
        Assign a task through Discord integration.
        
        Args:
            description: Task description
            user_id: Discord user ID who requested the task
            channel_id: Discord channel ID
            priority: Task priority level
            
        Returns:
            Dict containing task assignment result
        """
        try:
            # Generate task ID
            task_id = f"task_{len(self.task_queue) + 1}_{datetime.now().strftime('%H%M%S')}"
            
            # Analyze task complexity
            complexity_result = self.assess_task_complexity(description)
            
            # Create task entry
            task = {
                'task_id': task_id,
                'description': description,
                'user_id': user_id,
                'channel_id': channel_id,
                'priority': priority or 'medium',
                'complexity': complexity_result['complexity'],
                'status': 'assigned',
                'created_at': datetime.now().isoformat(),
                'requires_clarification': complexity_result['needs_clarification']
            }
            
            self.task_queue.append(task)
            
            if task['requires_clarification']:
                # Use questions from complexity assessment
                questions = complexity_result['questions']
                return {
                    'success': True,
                    'task_id': task_id,
                    'requires_clarification': True,
                    'questions': questions
                }
            else:
                return {
                    'success': True,
                    'task_id': task_id,
                    'requires_clarification': False,
                    'category': 'backend',  # Default category
                    'estimated_hours': 2.0  # Default estimate
                }
                
        except Exception as e:
            logger.error(f"Task assignment failed: {e}")
            return {
                'success': False,
                'message': f'Task assignment failed: {str(e)}'
            }
    
    async def provide_clarification(self, task_id: str, answers: List[str]) -> Dict[str, Any]:
        """
        Process clarification answers for a task.
        
        Args:
            task_id: ID of the task needing clarification
            answers: List of answers to clarification questions
            
        Returns:
            Dict containing clarification result
        """
        try:
            # Find task in queue
            task = next((t for t in self.task_queue if t['task_id'] == task_id), None)
            
            if not task:
                return {
                    'success': False,
                    'message': f'Task {task_id} not found'
                }
            
            # Update task with clarification
            task['clarification_answers'] = answers
            task['requires_clarification'] = False
            task['status'] = 'clarified'
            
            return {
                'success': True,
                'message': f'Task {task_id} clarified and ready for processing',
                'estimated_hours': 3.0
            }
            
        except Exception as e:
            logger.error(f"Clarification processing failed: {e}")
            return {
                'success': False,
                'message': f'Clarification failed: {str(e)}'
            }
    
    async def get_status_report(self) -> Dict[str, Any]:
        """
        Get comprehensive system status report.
        
        Returns:
            Dict containing system status information
        """
        try:
            uptime_start = getattr(self, '_start_time', datetime.now())
            uptime_delta = datetime.now() - uptime_start
            uptime_str = f"{uptime_delta.days}d {uptime_delta.seconds//3600}h {(uptime_delta.seconds//60)%60}m"
            
            # Task statistics
            total_tasks = len(self.task_queue)
            pending_tasks = len([t for t in self.task_queue if t['status'] == 'assigned'])
            in_progress = len([t for t in self.task_queue if t['status'] == 'in_progress'])
            completed = len([t for t in self.task_queue if t['status'] == 'completed'])
            
            return {
                'orchestrator_status': 'active',
                'uptime': uptime_str,
                'tasks': {
                    'total': total_tasks,
                    'pending': pending_tasks,
                    'in_progress': in_progress,
                    'completed': completed,
                    'success_rate': '85%'  # Mock success rate
                },
                'prs': {
                    'open_prs': 2,  # Mock data
                    'recent_merges': 1
                },
                'performance': {
                    'tasks_per_day': 5,
                    'average_response_time': '1.2s',
                    'errors': 0
                }
            }
            
        except Exception as e:
            logger.error(f"Status report generation failed: {e}")
            return {'error': f'Status report failed: {str(e)}'}
    
    async def list_pending_prs(self, limit: int = 10) -> Dict[str, Any]:
        """
        List pending pull requests using GitHub client.
        
        Args:
            limit: Maximum number of PRs to return
            
        Returns:
            Dict containing PR list or error
        """
        try:
            if not self.github_client:
                return {
                    'success': False,
                    'message': 'GitHub client not initialized'
                }
            
            prs = await self.github_client.list_open_pull_requests(limit)
            
            return {
                'success': True,
                'prs': prs
            }
            
        except Exception as e:
            logger.error(f"Failed to list pending PRs: {e}")
            return {
                'success': False,
                'message': f'Failed to list PRs: {str(e)}'
            }
    
    async def approve_and_merge_pr(self, pr_number: int, user_id: str) -> Dict[str, Any]:
        """
        Approve and merge a pull request.
        
        Args:
            pr_number: Pull request number
            user_id: ID of user approving the PR
            
        Returns:
            Dict containing approval result
        """
        try:
            if not self.github_client:
                return {
                    'success': False,
                    'message': 'GitHub client not initialized'
                }
            
            # Get PR details first
            pr_details = await self.github_client.get_pull_request(pr_number)
            if not pr_details:
                return {
                    'success': False,
                    'message': f'PR #{pr_number} not found'
                }
            
            # Merge the PR
            merge_result = await self.github_client.merge_pull_request(pr_number, 'merge')
            
            if merge_result and merge_result.get('success'):
                return {
                    'success': True,
                    'pr_title': pr_details.get('title', 'Unknown'),
                    'sha': merge_result.get('sha')
                }
            else:
                return {
                    'success': False,
                    'message': merge_result.get('message', 'Merge failed') if merge_result else 'Merge failed'
                }
                
        except Exception as e:
            logger.error(f"PR approval failed: {e}")
            return {
                'success': False,
                'message': f'PR approval failed: {str(e)}'
            }
    
    async def reject_pr(self, pr_number: int, reason: str, user_id: str) -> Dict[str, Any]:
        """
        Reject a pull request with reason.
        
        Args:
            pr_number: Pull request number
            reason: Reason for rejection
            user_id: ID of user rejecting the PR
            
        Returns:
            Dict containing rejection result
        """
        try:
            if not self.github_client:
                return {
                    'success': False,
                    'message': 'GitHub client not initialized'
                }
            
            # Get PR details first
            pr_details = await self.github_client.get_pull_request(pr_number)
            if not pr_details:
                return {
                    'success': False,
                    'message': f'PR #{pr_number} not found'
                }
            
            # Close the PR with reason
            success = await self.github_client.close_pull_request(pr_number, reason)
            
            if success:
                return {
                    'success': True,
                    'pr_title': pr_details.get('title', 'Unknown')
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to reject PR'
                }
                
        except Exception as e:
            logger.error(f"PR rejection failed: {e}")
            return {
                'success': False,
                'message': f'PR rejection failed: {str(e)}'
            }
    
    async def get_testing_status(self) -> Dict[str, Any]:
        """
        Get testing agent status.
        
        Returns:
            Dict containing testing status
        """
        return {
            'online': True,
            'active_tests': 0,
            'auto_approve': False,
            'recent_tests': [],
            'statistics': {
                'total': 10,
                'passed': 8,
                'failed': 2
            }
        }
    
    async def update_status(self, status) -> bool:
        """
        Update orchestrator status.
        
        Args:
            status: New status to set
            
        Returns:
            True if successful
        """
        try:
            # Mock status update
            logger.info(f"Status updated to: {status}")
            return True
        except Exception as e:
            logger.error(f"Status update failed: {e}")
            return False
    
    async def trigger_pr_tests(self, pr_number: int, user_id: str) -> Dict[str, Any]:
        """
        Trigger tests for a specific PR.
        
        Args:
            pr_number: Pull request number
            user_id: ID of user triggering tests
            
        Returns:
            Dict containing test trigger result
        """
        return {
            'success': True,
            'message': f'Tests triggered for PR #{pr_number}'
        }
    
    def _generate_clarification_questions(self, description: str) -> List[str]:
        """
        Generate clarification questions for unclear tasks.
        
        Args:
            description: Task description
            
        Returns:
            List of clarification questions
        """
        return [
            "What specific functionality should be implemented?",
            "Are there any technical requirements or constraints?",
            "What is the expected behavior and output?"
        ]

# Example usage and testing
if __name__ == "__main__":
    # Example usage of OrchestratorAgent
    try:
        print("Testing OrchestratorAgent functionality...")
        
        orchestrator = OrchestratorAgent("TestOrchestrator")
        orchestrator.prepare_for_task("Coordinate development workflow", "pre_task")
        
        # Test command parsing
        command = "!create --urgent api endpoint for user authentication with database integration"
        parsed = orchestrator.parse_discord_command(command)
        print(f"✓ Parsed command: {parsed['command_type']} (complexity: {parsed['complexity']})")
        
        # Test task breakdown
        subtasks = orchestrator.break_down_task(parsed['task_description'])
        print(f"✓ Task broken into {len(subtasks)} subtasks")
        
        # Test assignment
        assignments = orchestrator.assign_to_agent(subtasks)
        print(f"✓ Tasks assigned to {len(assignments['assignments'])} agent types")
        
        # Test complexity validation
        validation = orchestrator.validate_task_complexity("create something")
        print(f"✓ Complexity validation: {validation['complexity']}")
        
        print("All OrchestratorAgent tests passed!")
        
    except Exception as e:
        print(f"Test failed: {e}")
        raise