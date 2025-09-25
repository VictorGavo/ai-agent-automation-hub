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

# Copy and set up entrypoint script
COPY --chown=aiagent:aiagent docker-entrypoint.sh /app/entrypoint.sh
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

# Copy health check script
COPY --chown=aiagent:aiagent health-check.py /app/health-check.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python /app/health-check.py

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]