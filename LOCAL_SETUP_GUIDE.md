# Local Development Setup Guide

This guide helps you set up the AI Agent Automation Hub for local development and testing.

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+ (preferably 3.11)
- Git
- A Discord account for bot setup
- GitHub account (for optional GitHub integration)

### 2. Clone and Install

```bash
# Clone the repository
git clone https://github.com/VictorGavo/ai-agent-automation-hub.git
cd ai-agent-automation-hub

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### 3. Environment Setup

```bash
# Run the automated local setup
python setup_local_test.py
```

This will:
- ✅ Create necessary directories (`logs/`, `data/`, `workspace/`, etc.)
- ✅ Set up local SQLite database with sample data
- ✅ Validate all module imports
- ✅ Check environment variables
- ✅ Generate setup report

### 4. Configure Environment Variables

The setup script creates a `.env` file with placeholder values. You need to replace these:

#### Required Configuration

```bash
# Edit .env file
nano .env

# Update these values:
DISCORD_TOKEN=YOUR_ACTUAL_BOT_TOKEN_HERE
DISCORD_GUILD_ID=YOUR_DISCORD_SERVER_ID_HERE
DATABASE_URL=sqlite:///./data/local_test.db  # Already configured for local testing
APP_MODE=development  # Already set
```

#### Optional Configuration

```bash
# GitHub integration (optional)
GITHUB_TOKEN=YOUR_GITHUB_PERSONAL_ACCESS_TOKEN

# Specific Discord channels (optional)
DISCORD_CHANNEL_ID=YOUR_CHANNEL_ID
DISCORD_STATUS_CHANNEL_ID=YOUR_STATUS_CHANNEL_ID
```

### 5. Discord Bot Setup

Follow the detailed guide: [DISCORD_SETUP_GUIDE.md](./DISCORD_SETUP_GUIDE.md)

**Quick steps:**
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create new application → Add Bot
3. Copy bot token to `.env` file
4. Enable required permissions (Send Messages, Use Slash Commands, etc.)
5. Invite bot to your Discord server
6. Copy server ID to `.env` file

### 6. Validate Setup

```bash
# Run comprehensive validation
python scripts/validate_deployment.py --verbose

# Or use the make command
make validate-deployment
```

This checks:
- ✅ Environment variables
- ✅ File structure
- ✅ Database connectivity
- ✅ Agent initialization
- ✅ Discord bot configuration
- ✅ System health
- ✅ End-to-end workflow

## 🧪 Testing

### Run All Tests

```bash
# Run the full test suite
pytest tests/ -v

# Run with coverage
make test-coverage

# Run specific test categories
pytest tests/test_agents.py -v          # Agent tests
pytest tests/test_discord.py -v         # Discord bot tests
pytest tests/test_database.py -v        # Database tests
```

### Manual Testing

```bash
# Test individual components
python examples/discord_demo.py         # Test Discord integration
python examples/testing_agent_demo.py   # Test agent functionality
python examples/base_agent_integration_demo.py  # Test base agent system

# Test the deployment validation
python scripts/validate_deployment.py --json    # Get JSON report
```

### Start Development Services

```bash
# Start the orchestrator (main service)
python -m agents.orchestrator.main

# Or start individual agents
python -m agents.backend.main      # Backend agent
python -m agents.testing.main      # Testing agent

# Start Discord bot
python -m bot.main
```

## 📁 Project Structure

```
ai-agent-automation-hub/
├── .env                     # Your local environment variables
├── .env.example            # Template with all options
├── setup_local_test.py     # Local setup automation script
├── DISCORD_SETUP_GUIDE.md  # Discord bot setup guide
├── 
├── agents/                 # Agent implementations
│   ├── base_agent.py      # Base agent class
│   ├── backend/           # Backend automation agent
│   ├── orchestrator/      # Agent coordination
│   └── testing/          # Testing automation agent
├── 
├── bot/                   # Discord bot implementation
│   ├── main.py           # Bot entry point
│   ├── commands/         # Slash commands
│   └── events.py         # Discord event handlers
├── 
├── database/             # Database models and migrations
├── scripts/              # Utility and validation scripts
├── tests/               # Test suite
├── examples/            # Demo and example code
├── docs/               # Documentation
├── data/               # Local database and data files
└── logs/              # Application and setup logs
```

## 🔧 Development Commands

### Using Make (Recommended)

```bash
make help                    # Show all available commands
make install                 # Install dependencies
make test                    # Run tests
make validate-deployment     # Validate setup
make lint                    # Code linting
make format                  # Code formatting
make clean                   # Clean temporary files
```

### Direct Python Commands

```bash
# Development validation
python setup_local_test.py                    # Setup local environment
python scripts/validate_deployment.py         # Validate deployment

# Run components
python -m agents.orchestrator.main            # Start orchestrator
python -m bot.main                            # Start Discord bot

# Testing
pytest tests/ -v                              # Run tests
python examples/discord_demo.py               # Test Discord integration
```

## 📊 Monitoring and Logs

### Log Files

```bash
# View logs
tail -f logs/orchestrator.log              # Orchestrator logs
tail -f logs/local_setup.log               # Setup logs
tail -f logs/deployment_validation.log     # Validation logs
```

### Setup Reports

After running `setup_local_test.py`:
- 📄 **Setup Report**: `logs/local_setup_report.txt`
- 📊 **Detailed Results**: `logs/local_setup_results.json`

### Validation Reports

After running `validate_deployment.py`:
- 📋 **Human Report**: Console output with ✅/❌/⚠️ indicators
- 📊 **JSON Report**: Use `--json` flag for machine-readable output

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Reinstall dependencies
   pip install -r requirements.txt
   pip install -e .
   ```

2. **Database Issues**
   ```bash
   # Reset local database
   rm data/local_test.db
   python setup_local_test.py
   ```

3. **Discord Bot Not Responding**
   - Check bot token in `.env`
   - Verify bot permissions in Discord
   - Check server ID is correct
   - See [DISCORD_SETUP_GUIDE.md](./DISCORD_SETUP_GUIDE.md)

4. **Environment Variable Issues**
   ```bash
   # Re-run setup to check variables
   python setup_local_test.py
   
   # Check current environment
   cat .env
   ```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python -m agents.orchestrator.main

# Or set in .env file
echo "LOG_LEVEL=DEBUG" >> .env
```

### Getting Help

1. **Check Setup Reports**: `logs/local_setup_report.txt`
2. **Run Validation**: `python scripts/validate_deployment.py --verbose`
3. **Check Discord Setup**: Follow [DISCORD_SETUP_GUIDE.md](./DISCORD_SETUP_GUIDE.md)
4. **Review Examples**: Run scripts in `examples/` directory
5. **Check Documentation**: Browse `docs/` directory

## 🚀 Next Steps

Once your local setup is complete:

1. **Learn the System**: Read documentation in `docs/`
2. **Try Examples**: Run demo scripts in `examples/`
3. **Test Discord Commands**: Use `/help`, `/assign-task`, `/status`
4. **Develop Features**: Create new agents or extend existing ones
5. **Run Tests**: Ensure everything works with `make test`

## 📚 Additional Resources

- 📖 [Project Documentation](./docs/)
- 🤖 [Agent Development Guide](./docs/BASE_AGENT_USAGE_GUIDE.md)
- 🔗 [Discord Integration Guide](./docs/DISCORD_BOT_GUIDE.md)
- 🧪 [Testing Guide](./docs/TESTING_AGENT_DOCUMENTATION.md)
- 🐳 [Docker Deployment](./DEPLOYMENT.md)
- 🔧 [Validation Guide](./docs/VALIDATION.md)

---

**🎉 Happy Development!** Your local AI Agent Automation Hub environment is ready to go!