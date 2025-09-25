# Communication Protocols

## Progress Reporting (MANDATORY)
- **Frequency**: Every 30 minutes during active work
- **Format**: Brief summary with percentage completion
- **Channel**: Discord with structured updates
- **Example**: "Backend Agent: Task #1234 - 60% complete. Implemented user authentication, working on password reset feature."

## Escalation Procedures
### Immediate Escalation Triggers
- Blocked for >15 minutes
- Unclear task requirements or scope
- Security concerns discovered
- Critical errors encountered
- Performance degradation detected

### Escalation Format
🚨 ESCALATION - [Agent Name]
Task: #ID - Brief Description
Issue: Clear description of the problem
Context: What was being attempted
Attempted Solutions: What you tried
Next Steps Needed: What you need to proceed

## Inter-Agent Communication
- Use structured Discord messages for coordination
- Tag relevant agents when requesting information
- Document decisions in shared channels
- No direct agent-to-agent communication without logging

## Error Reporting Format
- Always include full context and error messages
- Specify exact steps to reproduce
- Include relevant code snippets
- Suggest potential solutions if known

## Discord Commands for Agents
- Report status updates in #agent-status channel
- Request clarification in #task-clarification channel
- Escalate issues in #agent-escalation channel
- Log completed work in #work-completed channel