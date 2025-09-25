# Testing Agent Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional testing dependencies
RUN pip install --no-cache-dir \
    pytest>=7.0.0 \
    pytest-cov>=4.0.0 \
    pytest-xdist>=3.0.0 \
    pytest-asyncio>=0.21.0 \
    bandit>=1.7.0 \
    flake8>=5.0.0 \
    black>=22.0.0 \
    safety>=2.0.0 \
    mypy>=1.0.0 \
    pytest-benchmark>=4.0.0

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p /tmp/testing_workspace /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV TESTING_POLLING_INTERVAL=60
ENV TESTING_AUTO_APPROVE=true

# Expose port (if needed for web interface)
EXPOSE 8083

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8083/health')" || exit 1

# Run the testing agent
CMD ["python", "agents/testing/main.py"]