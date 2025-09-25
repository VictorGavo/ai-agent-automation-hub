# Coding Standards

## Python Standards
- Follow PEP 8 style guidelines strictly
- Use descriptive variable names (no single letters except for loops)
- Maximum line length: 88 characters (Black formatter standard)
- Use type hints for all function parameters and return values

## Code Quality Requirements
- All code must pass existing tests PLUS new tests you create
- 100% test pass rate before task completion (no exceptions)
- Use pytest for all testing
- Include docstrings for all functions and classes
- Handle errors gracefully with try/except blocks

## Performance Guidelines
- Database queries: Always use indexes for WHERE clauses, limit result sets
- No performance degradation >5% from changes
- Use profiling for any performance-critical code
- Implement caching where appropriate

## Security Requirements
- Validate all inputs before processing
- Never log sensitive data (passwords, tokens, personal info)
- Use parameterized queries for database operations
- Follow principle of least privilege for permissions

## Before Marking Task Complete
- [ ] All tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No security vulnerabilities introduced
- [ ] Performance impact assessed