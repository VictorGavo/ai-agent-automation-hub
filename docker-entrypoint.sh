#!/bin/bash
set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Health check function
health_check() {
    python -c "
import sys
import os
sys.path.insert(0, '/app')

try:
    # Test basic imports
    from bot.main import FullDiscordBot
    from agents.orchestrator_agent import OrchestratorAgent
    from agents.backend_agent import BackendAgent
    from agents.database_agent import DatabaseAgent
    from utils.dev_bible_reader import DevBibleReader
    
    # Test configuration loading
    from bot.config import get_config
    config = get_config()
    
    print('✅ All imports successful')
    print('✅ Configuration loaded')
    exit(0)
    
except Exception as e:
    print(f'❌ Health check failed: {e}')
    exit(1)
"
}

log "Starting AI Agent Automation Hub..."

# Verify environment
log "Checking environment variables..."
if [ -z "$DISCORD_BOT_TOKEN" ]; then
    log "WARNING: DISCORD_BOT_TOKEN not set"
fi

# Run health check
log "Running health check..."
if ! health_check; then
    log "ERROR: Health check failed"
    exit 1
fi

# Initialize database if needed
if [ "$INIT_DB" = "true" ]; then
    log "Initializing database..."
    python scripts/init_database.py || log "WARNING: Database initialization failed"
fi

# Start the application based on mode
case "$APP_MODE" in
    "bot")
        log "Starting Discord Bot..."
        exec python bot/run_bot.py
        ;;
    "orchestrator")
        log "Starting Orchestrator Agent..."
        exec python agents/orchestrator/main.py
        ;;
    "backend")
        log "Starting Backend Agent..."
        exec python agents/backend/main.py
        ;;
    "testing")
        log "Starting Testing Agent..."
        exec python agents/testing/main.py
        ;;
    *)
        log "Starting Discord Bot (default)..."
        exec python bot/run_bot.py
        ;;
esac