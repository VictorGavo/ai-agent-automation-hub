# Specialized Agents Documentation

## Overview

This document describes the specialized agent classes that inherit from `BaseAgent` and provide domain-specific functionality for the AI Agent Automation Hub.

## Specialized Agent Classes

### 1. OrchestratorAgent (`agents/orchestrator_agent.py`)

**Purpose**: Manages task coordination, Discord command parsing, and agent assignment.

**Key Methods**:
- `parse_discord_command(discord_message)` - Parses Discord commands and extracts task information
- `break_down_task(task_description)` - Decomposes complex tasks into manageable subtasks
- `assign_to_agent(subtasks)` - Assigns subtasks to appropriate agents based on capabilities
- `validate_task_complexity(task_description)` - Assesses task complexity and generates clarification questions

**Example Usage**:
```python
orchestrator = OrchestratorAgent("MainOrchestrator")
orchestrator.prepare_for_task("Coordinate development workflow", "pre_task")

# Parse Discord command
command_result = orchestrator.parse_discord_command(
    "!create api endpoint for user authentication with database integration"
)

# Break down and assign tasks
subtasks = orchestrator.break_down_task(command_result['task_description'])
assignments = orchestrator.assign_to_agent(subtasks)
```

### 2. BackendAgent (`agents/backend_agent.py`)

**Purpose**: Specializes in Flask API development, business logic implementation, and Git integration.

**Key Methods**:
- `create_flask_endpoint()` - Creates Flask endpoints following coding standards
- `implement_business_logic()` - Implements business logic functions with proper validation
- `run_tests()` - Executes comprehensive test suites with coverage analysis
- `create_git_branch()` - Creates Git branches for development work
- `submit_pull_request()` - Submits PRs with proper formatting

**Example Usage**:
```python
backend_agent = BackendAgent("APIBuilder")
backend_agent.prepare_for_task("Implement user authentication API", "backend")

# Create endpoint
endpoint_result = backend_agent.create_flask_endpoint(
    endpoint_name="user_login",
    route="/api/v1/auth/login",
    methods=["POST"],
    auth_required=False
)

# Implement business logic
logic_result = backend_agent.implement_business_logic(
    function_name="authenticate_user",
    requirements="Validate credentials and return JWT token",
    input_parameters={"username": "str", "password": "str"},
    return_type="Dict[str, Any]",
    database_operations=True
)

# Run tests
test_result = backend_agent.run_tests(test_type="unit", coverage_threshold=85.0)
```

### 3. DatabaseAgent (`agents/database_agent.py`)

**Purpose**: Manages PostgreSQL operations, schema design, migrations, and query optimization.

**Key Methods**:
- `design_schema()` - Designs database schemas following PostgreSQL best practices
- `create_migration()` - Creates database migrations with rollback capabilities
- `optimize_queries()` - Analyzes and optimizes SQL queries for performance
- `validate_database_changes()` - Validates changes before applying to ensure safety

**Example Usage**:
```python
db_agent = DatabaseAgent("DBArchitect")
db_agent.prepare_for_task("Design user authentication schema", "database")

# Design schema
schema_result = db_agent.design_schema(
    table_name="users",
    columns={
        "id": "SERIAL PRIMARY KEY",
        "username": "VARCHAR(50) UNIQUE NOT NULL",
        "email": "VARCHAR(255) UNIQUE NOT NULL",
        "password_hash": "VARCHAR(255) NOT NULL",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    },
    indexes=[
        {"name": "idx_users_email", "columns": ["email"]},
        {"name": "idx_users_username", "columns": ["username"]}
    ]
)

# Create migration
migration_result = db_agent.create_migration(
    migration_name="add_users_table",
    operations=[schema_result]
)

# Optimize queries
optimization_result = db_agent.optimize_queries([
    "SELECT * FROM users WHERE email = 'user@example.com'"
])
```

## Inherited Functionality

All specialized agents inherit the following from `BaseAgent`:

### Core Methods
- `prepare_for_task(task_description, task_type)` - **Required before any operations**
- `get_guidelines_context()` - Returns formatted guidelines for LLM prompts
- `validate_task_completion(task_result)` - Validates compliance with guidelines
- `get_agent_status()` - Returns comprehensive agent status
- `reset_preparation()` - Resets preparation state

### Decorator Protection
All task methods use `@require_dev_bible_prep` decorator to ensure proper preparation.

## Agent Type Mappings

| Agent Class | Agent Type | Required Guidelines |
|-------------|------------|-------------------|
| OrchestratorAgent | "orchestrator" | pre_task guidelines |
| BackendAgent | "backend" | coding_standards.md, workflow_process.md, architecture.md |
| DatabaseAgent | "database" | security_rules.md, architecture.md |
| CodeAgent | "backend" | coding_standards.md, workflow_process.md, architecture.md |
| TestingAgent | "testing" | coding_standards.md, workflow_process.md |

## Integration Patterns

### 1. Complete Workflow Integration

```python
# Initialize orchestrator
orchestrator = OrchestratorAgent("MainOrchestrator")
orchestrator.prepare_for_task("Coordinate development", "pre_task")

# Parse and break down task
command = orchestrator.parse_discord_command("!create user management system")
subtasks = orchestrator.break_down_task(command['task_description'])
assignments = orchestrator.assign_to_agent(subtasks)

# Initialize specialized agents
db_agent = DatabaseAgent("DBDesigner")
backend_agent = BackendAgent("APIBuilder")

# Prepare agents for specific work
db_agent.prepare_for_task("Design user schema", "database")
backend_agent.prepare_for_task("Build user API", "backend")

# Execute coordinated work
schema = db_agent.design_schema("users", user_columns)
migration = db_agent.create_migration("add_users", [schema])
endpoint = backend_agent.create_flask_endpoint("get_users", "/api/users")
tests = backend_agent.run_tests("unit")

# Validate completion
for agent in [db_agent, backend_agent]:
    validation = agent.validate_task_completion({
        'status': 'completed',
        'completed_at': datetime.now()
    })
```

### 2. Error Handling Pattern

```python
try:
    agent = BackendAgent("APIBuilder")
    agent.prepare_for_task("API development", "backend")
    
    result = agent.create_flask_endpoint("test", "/test")
    
except RuntimeError as e:
    # Handle preparation requirement errors
    print(f"Preparation required: {e}")
    
except ValueError as e:
    # Handle invalid input errors
    print(f"Invalid input: {e}")
```

### 3. Guidelines Context for LLM Integration

```python
agent = DatabaseAgent("DBDesigner") 
agent.prepare_for_task("Schema design", "database")

# Get guidelines context for LLM
context = agent.get_guidelines_context()

# Use in LLM prompt
llm_prompt = f"""
{context}

Based on the guidelines above, design a database schema for user management.
Requirements: user authentication, profile storage, activity tracking.
"""
```

## Best Practices

1. **Always prepare agents** before task execution
2. **Use appropriate agent types** for specific domains
3. **Handle preparation errors** gracefully
4. **Validate task completion** for compliance
5. **Use guidelines context** in LLM prompts
6. **Reset preparation** when switching task types

## Files Created

- `agents/orchestrator_agent.py` - OrchestratorAgent implementation
- `agents/backend_agent.py` - BackendAgent implementation  
- `agents/database_agent.py` - DatabaseAgent implementation
- `agents/__init__.py` - Updated package exports
- `examples/specialized_agents_demo.py` - Integration demonstration

All specialized agents are production-ready and provide comprehensive functionality for coordinated development workflows with full development bible integration.