# AI Agent Automation Hub 🤖

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Discord.py](https://img.shields.io/badge/discord.py-2.3.2+-green.svg)](https://discordpy.readthedocs.io/)

# AI Agent Automation Hub

A comprehensive automation hub for AI-powered development agents with Discord integration, task management, and testing capabilities.

## 🚀 Quick Setup for Local Development

Get started in 3 simple steps:

```bash
# 1. Install dependencies
pip install -r requirements.txt && pip install -e .

# 2. Setup local environment
python setup_local_test.py

# 3. Validate setup
python scripts/validate_deployment.py
```

**Need Discord bot setup?** → See [DISCORD_SETUP_GUIDE.md](./DISCORD_SETUP_GUIDE.md)  
**Complete setup guide?** → See [LOCAL_SETUP_GUIDE.md](./LOCAL_SETUP_GUIDE.md)

## ✨ Features

### 🎯 Core Capabilities
- **Multi-Agent System**: Backend, Testing, and Orchestrator agents working in harmony
- **Discord Integration**: Slash commands, interactive buttons, rich embeds, and real-time status updates
- **Task Management**: Create, track, monitor, and manage development tasks seamlessly
- **Database Persistence**: PostgreSQL with connection pooling and migration support
- **Production Ready**: Docker deployment with monitoring, health checks, and automated backups

### 🚀 Discord Bot Features
- `/create-task` - Create and assign tasks to specialized agents
- `/task-status` - Check real-time task progress and results
- `/list-tasks` - View all tasks with filtering and pagination
- `/agent-status` - Monitor agent health and performance
- Interactive task management with buttons and dropdowns
- Rich embeds with progress tracking and error reporting

### 🔧 Specialized Agents
- **Backend Agent**: Code analysis, API development, database management
- **Testing Agent**: Automated testing, test generation, CI/CD integration
- **Orchestrator**: Task coordination, workflow management, resource allocation

### 📦 Deployment Options
- **Docker Compose**: Full stack deployment with PostgreSQL
- **Raspberry Pi 5**: Optimized for edge deployment with automated setup
- **Development Mode**: Local development with hot reloading
- **Production Mode**: Scalable deployment with monitoring and security

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Discord Bot Token ([Get one here](https://discord.com/developers/applications))
- PostgreSQL database (or use Docker Compose)

### 1. Installation

#### Option A: Using pip (Recommended)
```bash
pip install ai-agent-automation-hub
```

#### Option B: From Source
```bash
git clone https://github.com/VictorGavo/ai-agent-automation-hub.git
cd ai-agent-automation-hub
pip install -e .
```

### 2. Configuration
```bash
# Copy the example environment file
cp .env.example .env

# Edit the configuration (add your Discord token and database URL)
nano .env
```

### 3. Database Setup
```bash
# Using the built-in command
automation-hub-setup

# Or using make
make setup-db
```

### 4. Run the Bot
```bash
# Using the built-in command
automation-hub-bot

# Or using make
make run-bot

# Or with debug logging
automation-hub-bot --debug
```

## 🐳 Docker Deployment

### Quick Start with Docker Compose
```bash
# Clone the repository
git clone https://github.com/VictorGavo/ai-agent-automation-hub.git
cd ai-agent-automation-hub

# Configure environment
cp .env.example .env
# Edit .env with your Discord token and other settings

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f discord-bot
```

### Raspberry Pi 5 Deployment
```bash
# Run the automated setup script
sudo bash deploy/pi-setup.sh

# Or deploy remotely
make deploy-pi PI_HOST=pi@192.168.1.100
```

## 📚 Documentation

### Getting Started
- [Installation Guide](DEPLOYMENT.md#installation)
- [Discord Bot Setup](DEPLOYMENT.md#discord-bot-configuration)
- [Environment Configuration](.env.example)

### Development
- [Development Bible](dev_bible/README.md)
- [Architecture Overview](dev_bible/automation_hub/architecture.md)
- [Coding Standards](dev_bible/core/coding_standards.md)
- [Agent Roles](dev_bible/automation_hub/agent_roles.md)

### Deployment
- [Complete Deployment Guide](DEPLOYMENT.md)
- [Docker Configuration](docker-compose.yml)
- [Raspberry Pi Setup](deploy/pi-setup.sh)

### Examples
- [Basic Usage Examples](examples/)
- [Discord Bot Demo](examples/discord_demo.py)
- [Agent Integration](examples/backend_agent_integration.py)

## 🔧 Development

### Development Setup
```bash
# Clone and setup development environment
git clone https://github.com/VictorGavo/ai-agent-automation-hub.git
cd ai-agent-automation-hub

# Install development dependencies
make install-dev

# Setup pre-commit hooks
make dev-setup

# Run tests
make test

# Format code
make format

# Run linting
make lint
```

### Available Make Commands
```bash
make help                 # Show all available commands
make install              # Install package
make install-dev          # Install with dev dependencies
make test                 # Run tests
make format               # Format code (black, isort)
make lint                 # Run linting (flake8, mypy)
make docker-build         # Build Docker image
make docker-up            # Start Docker services
make run-bot              # Run Discord bot
make setup-db             # Initialize database
make health-check         # Check system health
```

## 🏗️ Architecture

```
ai-agent-automation-hub/
├── agents/                 # AI Agent implementations
│   ├── backend/           # Backend development agent
│   ├── orchestrator/      # Task coordination agent
│   └── testing/           # Testing and QA agent
├── bot/                   # Discord bot implementation
├── database/              # Database models and migrations
├── deploy/                # Deployment configurations
├── examples/              # Usage examples and demos
├── scripts/               # Utility and maintenance scripts
└── dev_bible/             # Development documentation
```

### Agent System
Each agent is a specialized AI system designed for specific tasks:

- **Backend Agent**: Handles code analysis, API development, database operations
- **Testing Agent**: Manages automated testing, test generation, CI/CD workflows
- **Orchestrator**: Coordinates tasks between agents, manages workflows and resources

### Discord Integration
The bot provides a user-friendly interface for:
- Creating and managing development tasks
- Real-time progress tracking with interactive elements
- Agent status monitoring and health checks
- Rich formatted responses with embeds and buttons

## 📊 Monitoring & Health Checks

### Built-in Health Monitoring
```bash
# Check overall system health
automation-hub-health

# Monitor specific components
make monitor

# Check agent status
make check-agents
```

### Docker Compose Profiles
- `minimal`: Basic bot and database
- `full`: All agents and services
- `monitoring`: Includes Prometheus and Grafana

```bash
# Start with monitoring
docker-compose --profile monitoring up -d

# Access Grafana dashboard
open http://localhost:3000
```

## 🔒 Security Features

- **Environment-based Configuration**: Sensitive data in environment variables
- **Database Connection Pooling**: Secure and efficient database access
- **Docker Security**: Non-root user, read-only filesystems, resource limits
- **Rate Limiting**: Built-in protection against abuse
- **Input Validation**: Comprehensive validation for all user inputs

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test categories
pytest -m unit                    # Unit tests only
pytest -m integration            # Integration tests only
pytest -m discord               # Discord-related tests

# Run with coverage
pytest --cov=. --cov-report=html
```

## 🤝 Contributing

We welcome contributions! Please see our [Development Bible](dev_bible/README.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following our [coding standards](dev_bible/core/coding_standards.md)
4. Run tests and linting (`make ci`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Full documentation](DEPLOYMENT.md)
- **Issues**: [GitHub Issues](https://github.com/VictorGavo/ai-agent-automation-hub/issues)
- **Discussions**: [GitHub Discussions](https://github.com/VictorGavo/ai-agent-automation-hub/discussions)

## 🎉 Acknowledgments

- Built with [Discord.py](https://discordpy.readthedocs.io/) for Discord integration
- Powered by [AsyncPG](https://github.com/MagicStack/asyncpg) for database operations
- Containerized with [Docker](https://www.docker.com/) for easy deployment
- Optimized for [Raspberry Pi 5](https://www.raspberrypi.org/) edge deployment

---

**Ready to automate your development workflow?** 🚀

```bash
pip install ai-agent-automation-hub
automation-hub-bot --help
```