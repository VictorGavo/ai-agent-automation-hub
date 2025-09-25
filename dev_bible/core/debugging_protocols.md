# Debugging Protocols

This document establishes debugging protocols and best practices for both human developers and AI agents working on the automation hub system.

## 1. DEBUGGING RULES (for humans and agents)

### Core Principles
- **Create debug branch before modifying working systems**
  - Never debug directly on main/production branches
  - Use naming convention: `debug/issue-description` or `fix/specific-problem`
  - Ensure you can quickly return to working state

- **Document current working state before troubleshooting**
  - Record what functions correctly vs what's broken
  - Capture current configurations, environment variables, and system state
  - Take screenshots/logs of working features before changes

- **Fix ONE specific issue at a time, don't rebuild**
  - Identify the exact symptom and root cause
  - Resist urge to "improve while you're there"
  - Complete one fix before addressing next issue

- **Test incrementally - don't change multiple components simultaneously**
  - Make small, testable changes
  - Verify each change works before proceeding
  - If change breaks something, you know exactly what caused it

- **Keep a "last known good" backup before debugging sessions**
  - Commit working state before starting debug session
  - Create system snapshots for critical environments
  - Document exact steps to restore working configuration

## 2. SCOPE BOUNDARIES

### What NOT to do (Common Anti-patterns)

❌ **Discord sync issue ≠ rebuild entire bot**
- Problem: One command not syncing
- Wrong approach: Rewrite command registration system
- Right approach: Check specific command configuration and sync that command

❌ **Missing command ≠ rewrite command system**
- Problem: New command not appearing
- Wrong approach: Rebuild entire command framework  
- Right approach: Verify command file exists, check imports, validate registration

❌ **Environment variable issue ≠ recreate environment**
- Problem: Bot token not loading
- Wrong approach: Delete and recreate entire environment
- Right approach: Check .env file, verify variable names, test loading mechanism

### Critical Question
**Always ask: "Am I fixing the specific problem or rebuilding everything?"**

If you're tempted to rewrite/rebuild, step back and identify the minimal change needed.

## 3. ROLLBACK TRIGGERS

Immediately stop debugging and rollback when:

### Time-based Triggers
- **If debugging session exceeds 30 minutes without progress**
  - You're likely addressing symptoms, not root cause
  - Step back, reassess the problem definition
  - Consider getting fresh perspective or escalating

### Scope-based Triggers  
- **If "simple fix" requires changing >3 files**
  - Simple fixes should be localized
  - Multiple file changes suggest architectural issue
  - May need design discussion before proceeding

### Complexity Triggers
- **If new errors appear while fixing original issue**
  - You're introducing regressions
  - Current approach is creating more problems than solving
  - Rollback to last working state immediately

### Functionality Triggers
- **If functionality is lost during troubleshooting**
  - Working features should never break during debugging
  - Indicates changes are too broad or poorly understood
  - Restore working state, narrow scope significantly

## 4. STATE DOCUMENTATION REQUIREMENTS

### Before Debugging
Document the following:
```markdown
## Pre-Debug State Assessment
- **What works correctly:** [List all functioning features]
- **What's broken:** [Specific symptoms, error messages, expected vs actual behavior]
- **Environment:** [OS, Python version, key dependencies, environment variables]
- **Recent changes:** [What was modified recently that might be related]
- **Last known good state:** [When did this last work? What changed since then?]
```

### During Debugging
Maintain a debug log:
```markdown
## Debug Session Log
**Time:** [timestamp]
**Change:** [What you modified]
**Reason:** [Why you made this change]
**Result:** [What happened]
**Status:** [Fixed/No change/New issue/Rollback needed]
```

### After Debugging
Verify and document:
```markdown
## Post-Debug Verification
- **Original issue status:** [Fixed/Partially fixed/Not fixed]
- **All original functionality verified:** [Yes/No - list any regressions]
- **New issues introduced:** [List any new problems]
- **Configuration changes made:** [Document all changes for future reference]
- **Lessons learned:** [What would you do differently?]
```

## Examples: Good vs Bad Debugging Decisions

### Example 1: Discord Command Not Syncing

**❌ Bad Approach:**
```
Problem: `/help` command not appearing in Discord
Decision: "The whole sync system is probably broken, let me rewrite it"
Result: Spend 3 hours rebuilding command sync, break other working commands
```

**✅ Good Approach:**
```
Problem: `/help` command not appearing in Discord
Decision: "Let me check if this specific command is properly registered"
Steps: 
1. Verify help.py exists and is imported
2. Check command decorator syntax
3. Test sync for just this command
4. Check Discord permissions for this guild
Result: Found missing @app_commands.describe() - 5 minute fix
```

### Example 2: Database Connection Issue

**❌ Bad Approach:**
```
Problem: "Database connection failed" error on startup
Decision: "Let me migrate to a different database system"
Result: Spend days rebuilding data layer, lose existing data
```

**✅ Good Approach:**
```
Problem: "Database connection failed" error on startup  
Decision: "Let me verify the connection string and database state"
Steps:
1. Check if database service is running
2. Verify connection credentials
3. Test connection manually
4. Check recent configuration changes
Result: Found typo in DATABASE_URL - 30 second fix
```

### Example 3: Agent Not Responding

**❌ Bad Approach:**
```
Problem: Backend agent not processing tasks
Decision: "The whole agent system needs refactoring"
Result: Spend weeks rewriting agent architecture, break orchestrator
```

**✅ Good Approach:**
```
Problem: Backend agent not processing tasks
Decision: "Let me check what's different about this agent's setup"
Steps:
1. Check agent logs for errors
2. Verify agent registration with orchestrator
3. Test with simple task
4. Compare config with working agents
Result: Found missing environment variable - 2 minute fix
```

## Escalation Procedures

### When to Escalate
1. **After hitting rollback trigger** - Need fresh perspective
2. **Issue affects multiple systems** - May need architectural discussion  
3. **Problem persists after proper debugging** - May need deeper investigation
4. **Security implications discovered** - Escalate immediately

### How to Escalate
1. **Document everything** using templates above
2. **Provide minimal reproduction case** 
3. **List what you've already tried**
4. **Specify what help you need** (review, pair debugging, architectural guidance)

### Escalation Channels
- **Technical issues:** Create detailed GitHub issue with debug documentation
- **Architectural questions:** Schedule design discussion with team
- **Security concerns:** Follow security incident response procedures
- **Urgent production issues:** Follow emergency escalation procedures

## Quick Reference Checklist

Before starting any debug session:
- [ ] Created debug branch
- [ ] Documented current working state  
- [ ] Identified ONE specific issue to fix
- [ ] Set 30-minute progress checkpoint
- [ ] Have rollback plan ready

During debugging:
- [ ] Making incremental changes
- [ ] Testing each change immediately
- [ ] Logging each modification and result
- [ ] Checking for new issues after each change

After debugging:
- [ ] Verified original functionality still works
- [ ] Documented all changes made
- [ ] Updated relevant documentation
- [ ] Committed clean, focused changes

Remember: **Debugging is detective work, not construction work.** Find the minimal change that solves the specific problem.