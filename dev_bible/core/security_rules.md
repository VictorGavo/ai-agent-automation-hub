# Security Rules (NON-NEGOTIABLE)

## Core Security Principles
- **Local-First**: All processing occurs on local infrastructure (Pi 5)
- **Zero External Data Exposure**: No personal data leaves local network
- **Encryption**: All sensitive data encrypted at rest and in transit
- **Compartmentalization**: Minimal necessary permissions only

## Data Handling Rules
### NEVER Do This
- Log passwords, API keys, tokens, or personal information
- Store sensitive data in plain text
- Send personal data to external services
- Hardcode credentials in source code
- Bypass authentication or authorization checks

### ALWAYS Do This
- Use environment variables for all credentials
- Validate and sanitize all inputs
- Use parameterized queries for database operations
- Implement proper error handling without exposing internals
- Log all actions for audit trail (but not sensitive data)

## API and Database Security
- Use connection pooling with timeout limits
- Implement rate limiting on all endpoints
- Validate all input parameters before processing
- Use TLS for all external communications
- Rotate credentials regularly (document in secure vault)

## Docker Container Security
- Run containers as non-root user
- Use minimal base images
- No unnecessary network ports exposed
- Mount only required volumes as read-only when possible
- Regular security updates for base images

## Emergency Procedures
- Immediate escalation for any suspected security breach
- Document all security-related decisions
- Human approval required for all security configuration changes
- Kill switches available for emergency shutdown

## Audit Requirements
- Log all database modifications with timestamps
- Track all API calls and responses (excluding sensitive data)
- Monitor resource usage and access patterns
- Regular security reviews of all code changes