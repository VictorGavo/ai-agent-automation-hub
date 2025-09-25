# Automation Hub Architecture

## Technology Stack
- **Backend**: Python with Flask framework
- **Database**: PostgreSQL (both dev and production)
- **Containerization**: Docker for agent isolation
- **Version Control**: Git with GitHub integration
- **Communication**: Discord bot for command interface
- **External Access**: Tailscale VPN (no direct port forwarding)
- **LLM Service**: Anthropic Claude API (Sonnet model)

## System Components
### Core Agents
1. **Orchestrator Agent**: Task breakdown, delegation, monitoring
2. **Backend Agent**: Flask APIs, business logic, Python code
3. **Database Agent**: PostgreSQL schemas, migrations, SQLAlchemy models
4. **Frontend Agent**: HTML/CSS/JavaScript, Jinja2 templates
5. **Testing Agent**: pytest, integration tests, coverage reporting
6. **Documentation Agent**: README updates, living documentation

### Infrastructure
- **Raspberry Pi 5**: Primary hosting platform
- **Docker Containers**: Each agent runs in isolated container
- **PostgreSQL**: Central database for all data storage
- **Discord Bot**: Primary command and communication interface
- **Web Dashboard**: Pi-hosted monitoring interface

## Data Flow
1. Human assigns task via Discord
2. Orchestrator validates and delegates to appropriate agent
3. Agent creates feature branch and implements solution
4. Agent runs tests and creates Pull Request
5. Human reviews and approves via mobile (GitHub/Discord)
6. Changes merge to staging, then production after final approval

## Agent Communication
- Agents communicate through shared PostgreSQL database
- Status updates via Discord bot
- File system shared through Docker volumes
- No direct agent-to-agent communication

## Security Architecture
- All agents run with minimal necessary permissions
- API keys stored in environment variables
- VPN-only external access via Tailscale
- Comprehensive audit logging
- Human approval gates for all production changes