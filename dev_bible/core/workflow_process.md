# Development Workflow Process

## Task Execution Protocol
### Before Starting (MANDATORY)
1. Read entire task specification completely
2. Validate prerequisites are available
3. Understand success criteria clearly
4. Check environment and tools ready
5. Plan implementation approach
6. Ask for clarification immediately if anything is unclear

### During Development
1. Create feature branch: `feature/TASK-ID-description`
2. Work in 15-30 minute chunks with validation checkpoints
3. Report progress every 30 minutes via Discord
4. Focus on simplest solution that meets requirements
5. Update documentation immediately as you proceed
6. Run tests continuously, not just at the end

### Before Completion
1. Run all automated tests (must pass 100%)
2. Verify all success criteria met
3. Update relevant README sections if functionality changed
4. Generate required deliverables and validation artifacts
5. Create Pull Request with summary of changes

## Branch Strategy
- `main`: Production deployment
- `staging`: Integration testing  
- `feature/TASK-ID-description`: Your work branch

## Escalation Rules
- Blocked >15 minutes = Escalate immediately
- Unclear requirements = Ask for clarification immediately
- Security concerns = Escalate to human immediately
- Performance issues = Document and escalate

## Human Approval Gates
- ALL merges to main branch require human approval
- Critical architectural decisions require human review
- Security-related changes require human approval
- NO exceptions to approval workflow