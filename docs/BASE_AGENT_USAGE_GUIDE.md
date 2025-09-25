# BaseAgent Class Usage Guide

## Overview

The `BaseAgent` class provides a foundation for all AI agents in the automation hub with integrated development bible functionality. It ensures agents follow required guidelines and processes before executing tasks.

## Key Features

- **Development Bible Integration**: Automatic loading of required guidelines based on task type
- **Task Preparation Validation**: Ensures agents are properly prepared before task execution
- **Decorator Protection**: `@require_dev_bible_prep` prevents unprepared method execution
- **Comprehensive Logging**: Full audit trail of agent operations
- **Extensible Design**: Easy to create specialized agents

## Quick Start

### 1. Basic Usage

```python
from agents.base_agent import BaseAgent

# Create an agent
agent = BaseAgent("MyAgent", "backend")

# Prepare for a task (required before any operations)
agent.prepare_for_task("Code review task", "backend")

# Now agent methods can be used safely
validation = agent.validate_task_completion({
    'status': 'completed',
    'completed_at': datetime.now()
})
```

### 2. Creating Specialized Agents

```python
from agents.base_agent import BaseAgent, require_dev_bible_prep

class MyCustomAgent(BaseAgent):
    def __init__(self, agent_name: str):
        super().__init__(agent_name, "backend")
    
    @require_dev_bible_prep
    def my_custom_method(self, data):
        # This method requires preparation first
        # Guidelines are available in self.current_guidelines
        return {"status": "processed"}
```

### 3. Using Pre-built Specialized Agents

```python
from agents.base_agent import CodeAgent, TestingAgent

# Code agent for backend tasks
code_agent = CodeAgent("BackendReviewer")
code_agent.prepare_for_task("Review API implementation", "backend")
code_agent.validate_code_standards("def my_function(): pass")

# Testing agent for test-related tasks
test_agent = TestingAgent("QAValidator") 
test_agent.prepare_for_task("Validate test coverage", "testing")
test_agent.validate_test_coverage({"coverage": 95.2})
```

## Task Types and Required Reading

| Task Type | Required Guidelines |
|-----------|-------------------|
| `pre_task` | `core/_agent_quick_start.md`, `automation_hub/current_priorities.md` |
| `backend` | `core/coding_standards.md`, `core/workflow_process.md`, `automation_hub/architecture.md` |
| `database` | `core/security_rules.md`, `automation_hub/architecture.md` |
| `testing` | `core/coding_standards.md`, `core/workflow_process.md` |
| `documentation` | `core/communication.md`, `core/workflow_process.md` |

## Core Methods

### `prepare_for_task(task_description, task_type)`
**Required before any task operations**
- Loads appropriate development bible guidelines
- Sets agent state to prepared
- Enables protected method execution

### `get_guidelines_context()`
Returns formatted guidelines for LLM prompts:
```python
context = agent.get_guidelines_context()
# Use in LLM prompt: f"Context: {context}\n\nUser request: ..."
```

### `validate_task_completion(task_result)`
Validates agent followed required processes:
```python
result = agent.validate_task_completion({
    'status': 'completed',
    'completed_at': datetime.now(),
    'result': 'success'
})
# Returns validation with compliance status
```

### `get_agent_status()`
Returns comprehensive agent status information:
```python
status = agent.get_agent_status()
print(f"Prepared: {status['preparation_complete']}")
print(f"Guidelines: {status['guidelines_length']} chars")
```

## Decorator Usage

The `@require_dev_bible_prep` decorator protects methods from execution without proper preparation:

```python
from agents.base_agent import require_dev_bible_prep

class MyAgent(BaseAgent):
    @require_dev_bible_prep
    def protected_method(self):
        # This will raise RuntimeError if agent not prepared
        return "success"
    
    def unprotected_method(self):
        # This can run without preparation
        return "always works"
```

## Error Handling

### Common Exceptions

- **`RuntimeError`**: Method called without proper preparation
- **`ValueError`**: Invalid task type or empty parameters
- **`FileNotFoundError`**: dev_bible directory not found

### Example Error Handling

```python
try:
    agent = BaseAgent("TestAgent", "backend")
    agent.prepare_for_task("Code review", "backend")
    result = agent.validate_task_completion(task_data)
except RuntimeError as e:
    print(f"Preparation required: {e}")
except ValueError as e:
    print(f"Invalid input: {e}")
```

## Integration with Existing Agents

### Updating Existing Agent Classes

1. **Inherit from BaseAgent**:
```python
# Before
class MyAgent:
    def __init__(self, name):
        self.name = name

# After  
class MyAgent(BaseAgent):
    def __init__(self, name):
        super().__init__(name, "backend")
```

2. **Add preparation requirement**:
```python
# Add decorator to methods that need guidelines
@require_dev_bible_prep
def execute_task(self, task_data):
    # Method now requires preparation
    guidelines = self.current_guidelines
    # ... implementation
```

3. **Update usage pattern**:
```python
# Before
agent = MyAgent("test")
agent.execute_task(data)

# After
agent = MyAgent("test")
agent.prepare_for_task("description", "backend")  # Required
agent.execute_task(data)
```

## Best Practices

1. **Always prepare before task execution**
2. **Use appropriate task types for your agent's domain**
3. **Handle preparation errors gracefully**
4. **Use guidelines context in LLM prompts**
5. **Validate task completion for compliance**
6. **Reset preparation when switching between different task types**

## Example: Complete Workflow

```python
from agents.base_agent import CodeAgent
from datetime import datetime

def complete_code_review_workflow():
    # 1. Create specialized agent
    agent = CodeAgent("ReviewerBot")
    
    # 2. Prepare for specific task
    agent.prepare_for_task(
        "Review authentication module implementation", 
        "backend"
    )
    
    # 3. Get guidelines for LLM context
    guidelines = agent.get_guidelines_context()
    
    # 4. Execute protected operations
    validation = agent.validate_code_standards("""
    def authenticate_user(username, password):
        # Secure implementation
        return True
    """)
    
    # 5. Validate completion
    completion_result = agent.validate_task_completion({
        'status': 'completed',
        'completed_at': datetime.now(),
        'code_reviewed': True
    })
    
    # 6. Check final status
    status = agent.get_agent_status()
    
    return {
        'agent_prepared': status['preparation_complete'],
        'validation_passed': validation['status'] == 'validated',
        'compliance_status': completion_result['overall_status']
    }
```

This ensures all agents follow development bible guidelines and maintain consistent, compliant operations across the automation hub.