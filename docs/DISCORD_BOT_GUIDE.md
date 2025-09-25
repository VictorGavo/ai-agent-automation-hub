# Discord Bot Documentation

## Overview

The AI Agent Automation Hub Discord Bot provides a comprehensive interface for managing and interacting with specialized AI agents through Discord. The bot integrates seamlessly with the existing agent system (OrchestratorAgent, BackendAgent, DatabaseAgent) to provide task assignment, monitoring, and approval workflows.

## Architecture

### Core Components

#### 1. DiscordBot Class (`bot/main.py`)
- Main bot implementation extending `discord.ext.commands.Bot`
- Manages specialized agent instances
- Handles Discord events and command routing
- Implements periodic status updates (every 30 minutes as per dev bible)

#### 2. Configuration System (`bot/config.py`)
- Environment variable management with validation
- Type-safe configuration using dataclasses
- Supports required and optional settings
- Runtime configuration validation

#### 3. Utilities (`bot/utils.py`)
- Embed creation helpers for consistent Discord message formatting
- Permission checking system for role-based access
- Task formatting and display utilities
- Async caching and rate limiting
- Paginated view components

#### 4. Startup Script (`bot/run_bot.py`)
- Production-ready bot launcher
- Comprehensive error handling and logging
- Signal handling for graceful shutdown
- Configuration validation before startup

## Features

### Slash Commands

#### `/assign-task [description] [task_type]`
- **Description**: Assigns a task to the appropriate agent via OrchestratorAgent
- **Parameters**:
  - `description` (required): Detailed description of the task
  - `task_type` (required): Type of task (backend, database, orchestration, testing, documentation)
- **Flow**:
  1. Command parsed by OrchestratorAgent
  2. Task broken down into manageable components
  3. Appropriate agent assigned based on task type
  4. Task ID generated and tracked
  5. Response embed sent with assignment details
- **Permissions**: All users with message permissions
- **Rate Limited**: 10 commands per minute per user

#### `/status`
- **Description**: Shows current status of all agents
- **Response**: Comprehensive embed showing:
  - Individual agent status (ready, busy, error, stopped)
  - Number of completed tasks per agent
  - Current active task for each agent
  - System-wide statistics
  - Emergency stop status
- **Permissions**: All users
- **Rate Limited**: 5 commands per minute per user

#### `/approve [task_id]`
- **Description**: Approves a pull request for merging
- **Parameters**:
  - `task_id` (required): ID of the task to approve
- **Flow**:
  1. Validates task exists and is in appropriate state
  2. Updates task status to 'approved'
  3. Triggers completion workflow
  4. Updates agent availability
  5. Logs approval action
- **Permissions**: Users with channel management permissions
- **Integration**: Would connect to GitHub API for real PR approval

#### `/agent-logs [agent_name]`
- **Description**: Shows recent logs for a specific agent
- **Parameters**:
  - `agent_name` (required): Name of agent (orchestrator, backend, database)
- **Response**: 
  - Recent activity summary
  - Current status and error information
  - Task completion statistics
  - Last update timestamp
- **Permissions**: Users with message management permissions

#### `/emergency-stop`
- **Description**: Halts all agent activity (ADMIN ONLY)
- **Flow**:
  1. Validates user has administrator permissions
  2. Sets emergency stop flag
  3. Halts all active tasks
  4. Updates all agent statuses to 'stopped'
  5. Disables new task assignments
  6. Sends critical alert to monitoring channels
- **Permissions**: Administrator role required
- **Logging**: Critical level logging with full audit trail

### Event Handlers

#### `on_ready()`
- Logs successful connection with bot details
- Updates bot presence/status
- Confirms guild connections
- Initializes periodic tasks

#### `on_command_error()`
- Comprehensive error handling for all command types
- User-friendly error messages
- Detailed logging for debugging
- Graceful degradation for missing permissions

#### Periodic Status Updates
- Runs every 30 minutes (configurable)
- Updates agent status tracking
- Sends status reports to configured monitoring channel
- Maintains system health metrics
- Automatic error recovery attempts

## Configuration

### Required Environment Variables

```bash
# Discord bot token from Discord Developer Portal
DISCORD_BOT_TOKEN=your_discord_bot_token_here
```

### Optional Environment Variables

```bash
# Discord Configuration
DISCORD_COMMAND_PREFIX=!                    # Default: !
DISCORD_STATUS_CHANNEL_ID=channel_id        # For periodic updates
DISCORD_ALLOWED_GUILDS=guild1,guild2        # Restrict bot to specific servers
DISCORD_ADMIN_ROLE=Admin                     # Name of admin role

# Bot Behavior
BOT_MAX_CONCURRENT_TASKS=10                  # Default: 10
BOT_TASK_TIMEOUT_MINUTES=60                  # Default: 60
BOT_STATUS_UPDATE_INTERVAL=30                # Default: 30 minutes

# Logging
BOT_LOG_LEVEL=INFO                           # DEBUG, INFO, WARNING, ERROR, CRITICAL
BOT_LOG_FILE=logs/discord_bot.log            # Log file path

# Integrations
GITHUB_TOKEN=your_github_token               # For PR operations
DATABASE_URL=postgresql://...                # For persistence
```

## Setup and Deployment

### 1. Prerequisites

```bash
# Ensure Discord.py is installed (already in requirements.txt)
pip install discord.py python-dotenv

# Or install all requirements
pip install -r requirements.txt
```

### 2. Discord Application Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Navigate to "Bot" section
4. Create a bot and copy the token
5. Enable necessary intents:
   - Message Content Intent (for command parsing)
   - Server Members Intent (for permission checking)

### 3. Bot Permissions

Required bot permissions:
- Send Messages
- Use Slash Commands
- Embed Links
- Read Message History
- Add Reactions
- Manage Messages (for admin features)

### 4. Environment Configuration

```bash
# Copy template and configure
cp .env.bot.template .env

# Edit .env with your Discord token and optional settings
nano .env
```

### 5. Start the Bot

```bash
# Using the startup script (recommended)
python bot/run_bot.py

# Or directly
python -m bot.main

# With logging
python bot/run_bot.py 2>&1 | tee logs/bot_startup.log
```

### 6. Invite Bot to Server

Generate an invite link with required permissions:
```
https://discord.com/oauth2/authorize?client_id=YOUR_BOT_CLIENT_ID&permissions=PERMISSION_INT&scope=bot%20applications.commands
```

## Integration with Agent System

### Agent Initialization

The bot automatically initializes and prepares all specialized agents:

```python
# Agents are initialized during bot setup
self.orchestrator_agent = OrchestratorAgent()
self.backend_agent = BackendAgent()
self.database_agent = DatabaseAgent()

# Agents are prepared for task execution
for agent in agents:
    agent.prepare_for_task('general')
```

### Task Routing

Tasks are routed through the OrchestratorAgent which delegates to appropriate specialists:

1. **Command Parsing**: OrchestratorAgent.parse_discord_command()
2. **Task Breakdown**: OrchestratorAgent.break_down_task()
3. **Agent Assignment**: OrchestratorAgent.assign_to_agent()
4. **Execution**: Appropriate agent executes the task
5. **Status Tracking**: Bot monitors and reports progress

### Development Bible Compliance

All agents maintain compliance with development bible requirements:
- Agents use `@require_dev_bible_prep` decorator
- Guidelines are loaded and validated before task execution
- Task types are mapped to appropriate bible sections
- Preparation requirements are enforced

## Monitoring and Logging

### Log Files

- `logs/discord_bot.log`: Main bot activity
- `logs/orchestrator.log`: Agent-specific logs
- Agent logs accessible via `/agent-logs` command

### Health Monitoring

- Periodic status updates every 30 minutes
- Agent availability tracking
- Task completion metrics
- Error rate monitoring
- Emergency stop status

### Metrics Tracking

```python
# Bot maintains metrics for:
- Active task count
- Tasks completed per agent
- Average task duration
- Error rates by agent
- Command usage statistics
```

## Error Handling

### Command Errors

- Missing arguments: User-friendly prompts
- Invalid permissions: Clear permission requirements
- Rate limiting: Cooldown information
- Agent unavailable: Status and recovery info

### System Errors

- Agent initialization failures: Detailed error messages
- Discord connection issues: Automatic retry logic
- Configuration errors: Startup validation prevents runtime issues
- Emergency scenarios: Graceful degradation and admin alerts

## Security Considerations

### Permission System

- Role-based access control
- Command-specific permission requirements
- Admin-only emergency functions
- Rate limiting to prevent abuse

### Data Protection

- No sensitive data in logs
- Environment variable protection
- Secure token handling
- Optional guild restrictions

### Audit Trail

- All administrative actions logged
- Task assignments tracked with user ID
- Approval workflow maintains complete history
- Emergency stop events receive critical logging

## Testing

### Run the Demo

```bash
# Test bot functionality without connecting to Discord
python examples/discord_bot_demo.py

# Test configuration loading
python bot/config.py
```

### Manual Testing

1. Start bot with test token
2. Use Discord's built-in slash command testing
3. Verify agent integration with simple tasks
4. Test permission system with different user roles
5. Validate error handling with invalid commands

## Troubleshooting

### Common Issues

#### Bot Won't Start
```bash
# Check configuration
python bot/config.py

# Verify token
echo $DISCORD_BOT_TOKEN

# Check logs
tail -f logs/discord_bot.log
```

#### Commands Not Appearing
- Verify bot has `applications.commands` scope
- Check bot permissions in server
- Ensure slash commands are synced (automatic on startup)

#### Agent Errors
- Check agent preparation requirements
- Verify development bible files are accessible
- Review agent-specific logs with `/agent-logs`

#### Permission Denied
- Verify user roles match configuration
- Check bot permissions in channel
- Review admin role name in configuration

### Debug Mode

```bash
# Start with debug logging
BOT_LOG_LEVEL=DEBUG python bot/run_bot.py

# Enable Discord library debug
export DISCORD_DEBUG=1
python bot/run_bot.py
```

## API Reference

### DiscordBot Class Methods

```python
async def setup_hook() -> None
    """Initialize agents and sync commands"""

async def on_ready() -> None
    """Handle bot connection event"""

async def on_command_error(ctx, error) -> None
    """Handle command errors gracefully"""

async def _prepare_agents() -> None
    """Prepare all agents for task execution"""

async def _create_status_embed() -> discord.Embed
    """Create comprehensive status embed"""
```

### Configuration API

```python
config = BotConfig.from_env()
validation = config.validate()
config_dict = config.to_dict()
```

### Utility Functions

```python
# Embed creation
embed = EmbedBuilder.success("Title", "Description")
embed = EmbedBuilder.error("Title", "Description", error="Details")

# Permission checking
is_admin = PermissionChecker.is_admin(member, "Admin")
can_manage = PermissionChecker.can_manage_tasks(member)

# Task formatting
task_embed = TaskFormatter.create_task_embed(task_data)
status_text = TaskFormatter.format_task_status("completed")
```

## Future Enhancements

### Planned Features

1. **Dashboard Integration**: Web dashboard for advanced monitoring
2. **Webhook Support**: Integration with external services
3. **Task Scheduling**: Cron-like task scheduling
4. **Advanced Metrics**: Performance analytics and reporting
5. **Multi-Server Support**: Cross-server task coordination
6. **AI Integration**: Enhanced natural language task parsing

### Extension Points

- Custom slash command registration
- Plugin system for specialized agents
- External service integrations
- Custom embed templates
- Advanced permission models

---

## Quick Reference

### Essential Commands

```bash
# Start bot
python bot/run_bot.py

# Test configuration  
python bot/config.py

# Run demo
python examples/discord_bot_demo.py

# Check logs
tail -f logs/discord_bot.log
```

### Discord Commands

- `/assign-task "Create API" backend` - Assign task
- `/status` - Show agent status  
- `/approve task_123` - Approve task
- `/agent-logs backend` - View agent logs
- `/emergency-stop` - Emergency halt (admin only)

### Key Files

- `bot/main.py` - Main bot implementation
- `bot/config.py` - Configuration management
- `bot/utils.py` - Helper functions and utilities
- `bot/run_bot.py` - Production startup script
- `.env.bot.template` - Environment configuration template