# AI Agent Automation Hub - Reliability System

## Overview

The Reliability System provides comprehensive safety features for AI agent operations, enabling safe development directly from Discord. The system is designed with the assumption that things will go wrong and focuses on recovery mechanisms rather than preventing all failures.

## 🏗️ System Architecture

### Core Components

#### 1. Task State Manager (`utils/task_state_manager.py`)
- **Persistent State Storage**: SQLite database for agent task states
- **Automatic Checkpointing**: Saves progress every 10 minutes
- **Recovery Points**: Manual and milestone checkpoints
- **Conversation History**: Tracks agent decisions and interactions
- **Rollback Capability**: Restore to any previous checkpoint

#### 2. Safe Git Operations (`utils/safe_git_operations.py`)
- **Backup Branches**: Creates backup before any modifications
- **Atomic Operations**: All-or-nothing git commits
- **Git Hooks**: Prevents direct main branch modifications
- **One-Command Rollback**: Quick restore to last working state
- **Operation Logging**: Audit trail of all git operations

#### 3. Enhanced Base Agent (`agents/base_agent.py`)
- **Checkpoint Integration**: `save_checkpoint()` and `resume_from_checkpoint()`
- **Safety Validation**: `validate_safe_to_proceed()` checks
- **Recovery Options**: `get_rollback_options()` for troubleshooting
- **Reliable Task Lifecycle**: `start_task_with_reliability()`

#### 4. Safety Monitor (`safety_monitor.py`)
- **Error Monitoring**: Automatic recovery point creation
- **File Conflict Prevention**: Prevents simultaneous modifications
- **Resource Monitoring**: Pi overload detection and protection
- **Discord Alerts**: Notifications for manual intervention needs

#### 5. Discord Safety Commands (`bot/safety_commands.py`)
- **System Health**: `/system-health` command
- **Safe Mode Control**: `/safe-mode` command
- **Recovery Options**: `/rollback` command
- **Task Resumption**: `/resume-task` command

## 🚀 Quick Start

### 1. System Startup
```bash
# Start the complete reliability system
python start_reliability_system.py
```

### 2. Basic Discord Commands
```
/system-health              # Check overall system status
/safe-mode enable [reason]   # Pause all agents (emergency)
/assign-task [description]   # Create task with reliability features
/rollback show              # See available recovery options
```

## 📋 Discord Commands Reference

### System Monitoring
- **`/system-health`** - Comprehensive health report
  - System resources (CPU, Memory, Temperature)
  - Agent status and paused agents
  - Git safety status
  - Recent alerts and warnings

### Safety Controls
- **`/safe-mode enable [reason]`** - Activate emergency mode
  - Pauses all agent operations
  - Prevents new task execution
  - Requires manual intervention to resume

- **`/safe-mode disable`** - Deactivate safe mode
  - Resume normal operations
  - Clear all agent pauses

### Recovery Operations
- **`/rollback show [agent]`** - Display recovery options
  - Git backup branches
  - Task checkpoints
  - Recent commits

- **`/rollback git_backup`** - Rollback to latest backup branch
- **`/rollback task_checkpoint [agent]`** - Show agent checkpoints

### Task Management
- **`/resume-task [task_id] [checkpoint_id]`** - Resume interrupted work
- **`/pause-agent [name] [reason]`** - Pause specific agent
- **`/resume-agent [name]`** - Resume paused agent

## 🔧 Configuration

### Environment Variables
```bash
# Discord Configuration
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_GUILD_ID=your_guild_id_here

# Optional Safety Settings
SAFETY_MONITORING_INTERVAL=30    # seconds
SAFETY_ALERT_COOLDOWN=300        # seconds
SAFETY_DB_PATH=data/safety_monitor.db
```

### Safety Monitor Configuration
```python
safety_config = {
    'monitoring_interval': 30,        # Check system every 30 seconds
    'alert_cooldown': 300,           # 5-minute cooldown between alerts
    'db_path': 'data/safety_monitor.db',
    'discord_webhook_url': None      # Optional Discord webhook
}
```

## 🛡️ Safety Features

### Automatic Protections

#### Git Safety
- **Pre-commit Hook**: Prevents direct commits to main/master
- **Backup Branches**: Created before any agent work
- **Safe Branch Detection**: Ensures agents work on feature branches
- **Atomic Operations**: All git operations are reversible

#### System Protection
- **Resource Monitoring**: Tracks CPU, memory, disk, temperature
- **Overload Detection**: Automatically activates safe mode when overloaded
- **File Lock Management**: Prevents multiple agents modifying same files
- **Process Monitoring**: Tracks agent health and errors

#### Task Reliability
- **Checkpoint System**: Automatic saves every 10 minutes
- **State Persistence**: Survives bot restarts and crashes
- **Conversation History**: Tracks all agent decisions
- **Progress Tracking**: Detailed step and percentage completion

### Manual Controls
- **Emergency Stop**: Immediate halt of all operations
- **Selective Pausing**: Pause individual agents
- **Recovery Points**: Manual checkpoint creation
- **Rollback Options**: Multiple restore strategies

## 🔄 Recovery Scenarios

### Scenario 1: Bot Restart During Task
```
1. Bot crashes while agent is working
2. Restart: python start_reliability_system.py  
3. Use: /rollback show [agent_name]
4. Use: /resume-task [task_id] [checkpoint_id]
```

### Scenario 2: Code Changes Gone Wrong
```
1. Agent makes unwanted changes
2. Use: /safe-mode enable "Code issues"
3. Use: /rollback git_backup
4. Or: /rollback show for specific options
```

### Scenario 3: System Overload
```
1. Safety monitor detects overload
2. Automatic safe mode activation
3. Discord alert sent
4. Manual: /system-health to check status
5. Manual: /safe-mode disable when ready
```

### Scenario 4: File Conflicts
```
1. Multiple agents try to modify same file
2. File access tracker blocks conflicting operations
3. Alert generated for manual resolution
4. Use: /pause-agent to control specific agents
```

## 📊 Monitoring and Alerts

### System Metrics Tracked
- **CPU Usage**: Percentage and load averages
- **Memory Usage**: Available and used memory
- **Disk Usage**: Free space monitoring  
- **Temperature**: Raspberry Pi temperature (if available)
- **Agent Count**: Active and paused agents
- **Task Count**: In-progress and completed tasks

### Alert Levels
- **INFO**: General system information
- **WARNING**: Potential issues, system still functional
- **ERROR**: Problems requiring attention
- **CRITICAL**: System safety compromised, safe mode activated

### Alert Types
- **Agent Error**: Agent encountered an error
- **Resource Warning**: High resource usage
- **File Conflict**: Multiple agents accessing same file
- **System Overload**: Critical resource exhaustion
- **Manual Intervention**: Human action required

## 📁 Database Schema

### Task States Table
```sql
CREATE TABLE task_states (
    task_id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    task_description TEXT NOT NULL,
    task_type TEXT NOT NULL,
    state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    current_step TEXT NOT NULL,
    progress_percentage REAL NOT NULL,
    context_data TEXT NOT NULL,      -- JSON
    conversation_history TEXT NOT NULL, -- JSON
    checkpoints TEXT NOT NULL,       -- JSON array
    error_count INTEGER DEFAULT 0,
    last_error TEXT
);
```

### Checkpoints Table
```sql
CREATE TABLE checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    checkpoint_type TEXT NOT NULL,   -- auto, manual, milestone, error, rollback
    timestamp TEXT NOT NULL,
    current_step TEXT NOT NULL,
    progress_percentage REAL NOT NULL,
    context_data TEXT NOT NULL,      -- JSON
    conversation_history TEXT NOT NULL, -- JSON
    rollback_data TEXT,              -- JSON
    notes TEXT,
    FOREIGN KEY (task_id) REFERENCES task_states (task_id)
);
```

### Safety Alerts Table
```sql
CREATE TABLE safety_alerts (
    alert_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    level TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    agent_name TEXT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    data TEXT NOT NULL,              -- JSON
    resolved BOOLEAN DEFAULT FALSE,
    resolution_timestamp TEXT,
    resolution_notes TEXT
);
```

## 🔨 Development Workflow

### Starting New Agent Work
1. **Preparation**: Agent calls `prepare_for_task()`
2. **Safe Start**: Use `start_task_with_reliability()`
3. **Git Branch**: Automatic backup and working branch creation
4. **Initial Checkpoint**: Baseline checkpoint created
5. **Monitoring**: Automatic 10-minute checkpoints begin

### During Agent Execution
1. **Safety Checks**: `validate_safe_to_proceed()` before major operations
2. **Progress Updates**: Regular task state updates
3. **Error Handling**: Automatic checkpoints on errors
4. **Resource Monitoring**: Continuous system health checks

### Task Completion
1. **Final Checkpoint**: Last progress point saved
2. **Safe Completion**: `complete_task_safely()`
3. **Cleanup**: Stop checkpoint timer
4. **Audit Trail**: Complete operation history preserved

## 🐛 Troubleshooting

### Common Issues

#### Bot Not Responding to Commands
```bash
# Check if bot is running
ps aux | grep python | grep bot

# Check logs
tail -f logs/discord_bot.log
tail -f logs/reliability_startup.log

# Restart system
python start_reliability_system.py
```

#### Git Hook Errors
```bash
# Check hook installation
ls -la .git/hooks/

# Reinstall hooks
python -c "from utils.safe_git_operations import get_safe_git_operations; get_safe_git_operations()._install_git_hooks()"
```

#### Database Corruption
```bash
# Check database integrity
sqlite3 data/task_state.db "PRAGMA integrity_check;"
sqlite3 data/safety_monitor.db "PRAGMA integrity_check;"

# Backup and reset if needed
cp data/task_state.db data/task_state.db.backup
rm data/task_state.db
# System will recreate on next startup
```

#### High Resource Usage
```
1. Use: /system-health
2. Check warnings in the output
3. Use: /safe-mode enable "High resource usage"
4. Investigate and resolve issues
5. Use: /safe-mode disable when resolved
```

### Debug Mode
```bash
# Enable debug logging
export BOT_LOG_LEVEL=DEBUG
python start_reliability_system.py
```

## 🧪 Testing

### Test Individual Components
```bash
# Test task state manager
python utils/task_state_manager.py

# Test safe git operations  
python utils/safe_git_operations.py

# Test safety monitor
python safety_monitor.py

# Test Discord commands (requires bot token)
python bot/main.py
```

### Integration Tests
```bash
# Test full system startup
python start_reliability_system.py

# In Discord, test command sequence:
# /system-health
# /safe-mode enable "Testing"
# /rollback show
# /safe-mode disable
```

## 📈 Performance Considerations

### Resource Usage
- **SQLite Databases**: ~1-10MB depending on usage
- **Memory**: ~50-100MB for monitoring processes
- **CPU**: <5% during normal operation
- **Disk I/O**: Minimal, periodic checkpoint writes

### Scaling Limits
- **Concurrent Agents**: Tested up to 10 agents
- **Checkpoint History**: Automatically pruned to last 100 operations
- **Database Size**: Auto-cleanup after 30 days
- **Pi Performance**: Monitoring prevents overload

### Optimization Tips
- Regular database cleanup: `safety_monitor.cleanup_old_data(days=7)`
- Prune old git branches: `safe_git.cleanup_old_branches(days=3)`  
- Monitor disk space for log files
- Adjust checkpoint frequency for long-running tasks

## 🔒 Security Considerations

### Access Control
- Discord commands require appropriate permissions
- Git hooks prevent unauthorized commits
- File access tracking prevents conflicts
- Safe mode provides emergency control

### Data Protection
- Local SQLite databases (no cloud dependency)
- Git operation audit trails
- Conversation history encryption (future enhancement)
- Secure token handling

### Best Practices
- Regular backups of critical data
- Monitor system logs for suspicious activity
- Use safe mode during maintenance
- Test recovery procedures regularly

---

## 🎯 Summary

The AI Agent Automation Hub Reliability System provides comprehensive safety features that enable confident use of AI agents for development work. The system is designed to fail gracefully and provide multiple recovery options when things go wrong.

**Key Benefits:**
- ✅ **Safe Development**: Backup branches and atomic operations
- ✅ **Always Recoverable**: Multiple checkpoint and rollback options  
- ✅ **Discord Control**: Complete management from Discord chat
- ✅ **System Protection**: Automatic overload detection and prevention
- ✅ **Audit Trail**: Complete history of all operations
- ✅ **Resource Aware**: Raspberry Pi optimized monitoring

**Quick Commands:**
- Emergency: `/safe-mode enable "emergency"`
- Status: `/system-health`
- Recovery: `/rollback show`
- Resume: `/resume-task [task_id]`

The system transforms AI agent operations from experimental to production-ready, providing the safety net needed for reliable autonomous development.