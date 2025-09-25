FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including build tools
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r automation && useradd -r -g automation automation

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs workspace && \
    chown -R automation:automation /app

USER automation

USER root
RUN mkdir -p /app/app/routes /app/tests && \
    chown -R automation:automation /app && \
    chmod -R 755 /app

USER automation
RUN git init /app && \
    cd /app && \
    git config user.name "Backend Agent" && \
    git config user.email "backend-agent@automation-hub.local" && \
    git remote add origin https://github.com/VictorGavo/ai-agent-automation-hub.git

WORKDIR /app


ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "agents/backend/main.py"]