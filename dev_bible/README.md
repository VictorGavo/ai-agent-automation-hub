# Dev Bible - Agent Guidelines and Standards

## 🚀 Quick Start for Agents
**ALWAYS read `core/_agent_quick_start.md` FIRST before any task!**

## 📚 Documentation Structure

### Core Guidelines (80% - Universal)
Read these for ALL tasks:
- **`core/_agent_quick_start.md`** ← START HERE
- **`core/coding_standards.md`** - Python standards, testing, quality gates
- **`core/workflow_process.md`** - Development workflow, branching, approvals
- **`core/security_rules.md`** - Security requirements (NON-NEGOTIABLE)
- **`core/communication.md`** - Reporting, escalation, Discord protocols

### Project-Specific (20% - Automation Hub)
Read these for project context:
- **`automation_hub/architecture.md`** - Tech stack, system design
- **`automation_hub/current_priorities.md`** - What to focus on NOW
- **`automation_hub/agent_roles.md`** - Your specific responsibilities

## 🎯 How to Use This Documentation

### Before Starting Any Task
1. Read `_agent_quick_start.md` (2 minutes)
2. Check `current_priorities.md` for project focus
3. Review relevant core guidelines based on task type
4. Scan your role in `agent_roles.md`

### During Development
- Query specific sections as needed
- Re-read guidelines for tasks >2 hours
- Follow escalation procedures if blocked >15 minutes
- Update documentation if you modify functionality

### Task Type → Required Reading
- **Backend Development**: coding_standards + workflow_process + architecture
- **Database Work**: security_rules + architecture + workflow_process  
- **Testing Tasks**: coding_standards + workflow_process
- **Documentation**: communication + workflow_process
- **Any Blocking Issues**: communication (escalation procedures)

## ⚠️ Critical Rules (Never Violate)
- Maximum 4 hours per task
- Ask for clarification if unclear (don't assume)
- Report progress every 30 minutes during work
- Escalate if blocked >15 minutes
- 100% test pass rate required
- Human approval required for ALL main branch merges
- Follow all security rules without exception

## 🆘 Emergency Contacts
- **Blocked >15 minutes**: Escalate to human via Discord #agent-escalation
- **Security concerns**: IMMEDIATE escalation to human
- **Unclear requirements**: Ask in Discord #task-clarification
- **System issues**: Report in Discord #agent-status

---
*This Dev Bible is your source of truth. When in doubt, follow these guidelines and escalate quickly.*