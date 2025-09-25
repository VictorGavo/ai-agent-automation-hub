# AI Agent Automation Hub - Production Dockerfile
# Multi-stage build for optimized production image

# Stage 1: Build dependencies
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Add metadata labels
LABEL maintainer="AI Dev Team <team@example.com>" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="ai-agent-automation-hub" \
      org.label-schema.description="AI Agent Automation Hub with Discord Bot" \
      org.label-schema.url="https://github.com/VictorGavo/ai-agent-automation-hub" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/VictorGavo/ai-agent-automation-hub" \
      org.label-schema.vendor="AI Dev Team" \
      org.label-schema.version=$VERSION \
      org.label-schema.schema-version="1.0"

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Stage 2: Production image
FROM python:3.11-slim as production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN groupadd --gid 1001 aiagent && \
    useradd --uid 1001 --gid aiagent --shell /bin/bash --create-home aiagent

# Set working directory
WORKDIR /app

# Create directory structure with proper permissions
RUN mkdir -p /app/logs /app/data /app/workspace /app/config && \
    chown -R aiagent:aiagent /app

# Copy application code
COPY --chown=aiagent:aiagent . .

# Install application in development mode for proper imports
RUN pip install -e .

# Create startup script
RUN cat > /app/entrypoint.sh << 'EOF'
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
    from bot.main import DiscordBot
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
EOF

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER aiagent

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_MODE=bot \
    LOG_LEVEL=INFO \
    INIT_DB=false

# Expose Discord bot port (for health checks)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "
import sys, os
sys.path.insert(0, '/app')
try:
    from bot.config import get_config
    config = get_config()
    print('✅ Health check passed')
except:
    print('❌ Health check failed')
    sys.exit(1)
" || exit 1

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]