# Agent Roles and Responsibilities

## Orchestrator Agent (Task Manager)
**Primary Role**: Coordinate all development work and agent communication

### Responsibilities
- Parse human requests from Discord
- Break down complex tasks into agent-specific work
- Assign tasks based on agent capabilities and workload
- Monitor progress and handle escalations
- Create approval workflows for human review

### Decision Authority
- Task assignment and delegation
- Work prioritization and scheduling
- Agent coordination and communication
- Escalation to human when needed

### Technologies
- Discord API for communication
- PostgreSQL for task queue management
- Git for branch and PR coordination

## Backend Agent (Python Developer)
**Primary Role**: Flask application development and Python backend code

### Responsibilities
- Create Flask routes and API endpoints
- Implement business logic and data processing
- Write Python backend code following PEP 8 standards
- Integration with PostgreSQL database
- Error handling and logging implementation

### Decision Authority
- Implementation approach for backend features
- Code structure and organization
- Flask configuration and middleware choices

### Technologies
- Python, Flask, SQLAlchemy
- PostgreSQL database integration
- pytest for testing backend code

## Database Agent (Data Architect)
**Primary Role**: PostgreSQL schema design and database operations

### Responsibilities
- Design database schemas and relationships
- Create and manage database migrations
- Optimize queries and database performance
- Ensure data integrity and consistency
- Handle database security and access controls

### Decision Authority
- Schema design decisions
- Migration strategies
- Query optimization approaches
- Database indexing decisions

### Technologies
- PostgreSQL, SQLAlchemy ORM
- Alembic for database migrations
- Database performance monitoring tools

## Testing Agent (Quality Assurance)
**Primary Role**: Automated testing and quality validation

### Responsibilities
- Create pytest unit and integration tests
- Ensure 100% test pass rate before completion
- Run automated test suites on all code changes
- Generate test coverage reports
- Validate success criteria for all tasks

### Decision Authority
- Test strategy and approach
- Test data setup and teardown
- Coverage requirements and standards

### Technologies
- pytest, coverage.py
- Testing databases and fixtures
- Continuous integration tools

## Documentation Agent (Technical Writer)
**Primary Role**: Maintain living documentation and project knowledge

### Responsibilities
- Update README files when functionality changes
- Create and maintain Architecture Decision Records (ADRs)
- Ensure documentation reflects current system state
- Generate API documentation and usage examples

### Decision Authority
- Documentation structure and format
- Content organization and presentation
- Documentation standards and templates

### Technologies
- Markdown, Git documentation
- Automated documentation generation
- Knowledge management systems