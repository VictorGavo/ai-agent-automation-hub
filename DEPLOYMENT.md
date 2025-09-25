# AI Agent Automation Hub - Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the AI Agent Automation Hub on Raspberry Pi 5 using Docker and Docker Compose. The deployment includes PostgreSQL database, Discord bot, and optional agent services with proper security, monitoring, and backup configurations.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Raspberry Pi 5 Setup](#raspberry-pi-5-setup)
3. [Manual Installation](#manual-installation)
4. [Configuration](#configuration)
5. [Discord Bot Setup](#discord-bot-setup)
6. [Starting Services](#starting-services)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)
8. [Backup and Recovery](#backup-and-recovery)
9. [Troubleshooting](#troubleshooting)
10. [Security Considerations](#security-considerations)

## Prerequisites

### Hardware Requirements

- **Raspberry Pi 5** (recommended) with at least 8GB RAM
- **MicroSD Card**: 64GB+ Class 10 or better
- **Power Supply**: Official Raspberry Pi 5 power supply
- **Network**: Wired Ethernet connection recommended
- **Cooling**: Active cooling solution recommended for 24/7 operation

### Software Prerequisites

- **Raspberry Pi OS**: 64-bit Lite or Desktop (latest version)
- **Docker**: 20.10+ (installed by setup script)
- **Docker Compose**: 2.0+ (installed by setup script)
- **Internet Connection**: Required for initial setup and Discord connectivity

### Account Requirements

- **Discord Developer Account**: For bot token creation
- **GitHub Account**: (Optional) For repository integration
- **Anthropic/OpenAI Account**: (Optional) For AI model integration

## Raspberry Pi 5 Setup

### Option 1: Automated Setup (Recommended)

Use the provided setup script for a fully automated installation:

```bash
# Download and run the setup script
curl -fsSL https://raw.githubusercontent.com/VictorGavo/ai-agent-automation-hub/main/deploy/pi-setup.sh -o pi-setup.sh
chmod +x pi-setup.sh

# Run with sudo
sudo ./pi-setup.sh
```

The setup script will:
- ✅ Update system packages
- ✅ Install Docker and Docker Compose
- ✅ Create service user and directories
- ✅ Generate environment configuration
- ✅ Deploy application files
- ✅ Set up systemd service
- ✅ Configure monitoring and backups
- ✅ Set up firewall rules

### Option 2: Manual Installation

If you prefer manual control or need to troubleshoot issues:

#### Step 1: Update System

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git vim htop unzip ca-certificates gnupg lsb-release
```

#### Step 2: Install Docker

```bash
# Install Docker using convenience script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
rm get-docker.sh

# Install Docker Compose
COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d'"' -f4)
sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker
```

#### Step 3: Create Service User

```bash
sudo useradd -r -s /bin/bash -d /home/aiagent -m aiagent
sudo usermod -aG docker aiagent
```

#### Step 4: Setup Directory Structure

```bash
sudo mkdir -p /opt/automation-hub/{data/{postgres,backups,logs},config,workspace}
sudo chown -R aiagent:aiagent /opt/automation-hub
sudo mkdir -p /var/log/automation-hub
sudo chown aiagent:aiagent /var/log/automation-hub
```

#### Step 5: Clone Repository

```bash
cd /opt/automation-hub
sudo -u aiagent git clone https://github.com/VictorGavo/ai-agent-automation-hub.git app
cd app
```

## Configuration

### Environment Variables

Create and configure the environment file:

```bash
sudo cp /opt/automation-hub/app/.env.bot.template /opt/automation-hub/.env
sudo nano /opt/automation-hub/.env
```

#### Required Configuration

```bash
# REQUIRED: Discord Bot Token
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# Database (generated automatically)
POSTGRES_PASSWORD=your_generated_password
```

#### Optional Configuration

```bash
# Discord Settings
DISCORD_STATUS_CHANNEL_ID=123456789012345678    # Channel for status updates
DISCORD_ALLOWED_GUILDS=111111111,222222222      # Restrict to specific servers
DISCORD_ADMIN_ROLE=Admin                         # Admin role name

# Integration Tokens
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx           # For GitHub integration
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxx   # For Claude AI
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx          # For OpenAI GPT

# Bot Behavior
BOT_MAX_CONCURRENT_TASKS=10                      # Max simultaneous tasks
BOT_TASK_TIMEOUT_MINUTES=60                      # Task timeout
BOT_STATUS_UPDATE_INTERVAL=30                    # Status update frequency (minutes)
BOT_LOG_LEVEL=INFO                               # Logging level

# Service Ports
BOT_HEALTH_PORT=8080                             # Health check port
POSTGRES_PORT=5433                               # PostgreSQL port
```

### File Permissions

```bash
sudo chown aiagent:aiagent /opt/automation-hub/.env
sudo chmod 600 /opt/automation-hub/.env
sudo cp /opt/automation-hub/.env /opt/automation-hub/app/.env
```

## Discord Bot Setup

### Step 1: Create Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Enter application name: "AI Agent Automation Hub"
4. Save the application

### Step 2: Create Bot

1. Navigate to "Bot" section
2. Click "Add Bot"
3. **Copy the bot token** (you'll need this for `DISCORD_BOT_TOKEN`)
4. Enable necessary intents:
   - ✅ **Message Content Intent**
   - ✅ **Server Members Intent** (optional)
   - ✅ **Presence Intent** (optional)

### Step 3: Configure Bot Permissions

Set the following permissions for your bot:
- ✅ Send Messages
- ✅ Use Slash Commands
- ✅ Embed Links
- ✅ Read Message History
- ✅ Add Reactions
- ✅ Manage Messages (for admin features)
- ✅ View Channels

### Step 4: Generate Invite Link

1. Go to "OAuth2" > "URL Generator"
2. Select scopes:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Select bot permissions (as listed above)
4. Copy generated URL and invite bot to your server

### Step 5: Set Up Channels (Optional)

Create dedicated channels for bot interaction:
- `#ai-agents` - Main bot interaction channel
- `#agent-status` - Status updates channel (set `DISCORD_STATUS_CHANNEL_ID`)
- `#bot-logs` - Bot logging channel

## Starting Services

### Using Systemd (Recommended)

If you used the setup script, a systemd service was created:

```bash
# Start services
sudo systemctl start automation-hub

# Check status
sudo systemctl status automation-hub

# Enable auto-start on boot
sudo systemctl enable automation-hub

# View logs
sudo journalctl -u automation-hub -f
```

### Using Docker Compose Directly

```bash
cd /opt/automation-hub/app

# Start essential services (PostgreSQL + Discord Bot)
sudo -u aiagent docker-compose up -d postgres discord-bot

# Start all services including optional agents
sudo -u aiagent docker-compose --profile full up -d

# Check status
sudo -u aiagent docker-compose ps

# View logs
sudo -u aiagent docker-compose logs -f discord-bot
```

### Service Profiles

The docker-compose.yml supports different service profiles:

```bash
# Minimal deployment (PostgreSQL + Discord Bot only)
docker-compose up -d

# Full deployment (all agents + monitoring)
docker-compose --profile full up -d

# Specific profiles
docker-compose --profile orchestrator up -d    # Add orchestrator
docker-compose --profile backend up -d         # Add backend agent  
docker-compose --profile testing up -d         # Add testing agent
docker-compose --profile monitoring up -d      # Add monitoring
```

## Monitoring and Maintenance

### Health Checks

Run the built-in health check script:

```bash
cd /opt/automation-hub/app
./deploy/health-check.sh
```

Expected output:
```
🏥 Running AI Agent Automation Hub Health Check
================================================
🐳 Container Status:
✅ PostgreSQL: Container running
✅ Discord Bot: Container running

🗄️  Database Connectivity:
✅ PostgreSQL: Database accessible

🌐 Service Health Endpoints:
✅ Discord Bot: Health check passed

================================================
🎉 All services are healthy!
```

### Monitoring URLs

- **Bot Health**: `http://YOUR_PI_IP:8080`
- **Prometheus**: `http://YOUR_PI_IP:9090` (if monitoring enabled)
- **Container Stats**: `docker stats`

### Log Management

```bash
# View all logs
sudo -u aiagent docker-compose logs -f

# View specific service logs
sudo -u aiagent docker-compose logs -f discord-bot
sudo -u aiagent docker-compose logs -f postgres

# View systemd service logs
sudo journalctl -u automation-hub -f

# View application logs
tail -f /opt/automation-hub/data/logs/*.log
```

### Resource Monitoring

```bash
# Check Docker container resource usage
docker stats

# Check system resources
htop
df -h
free -h

# Check Docker disk usage
docker system df
```

## Backup and Recovery

### Automated Backups

The setup script creates an automated backup system:

```bash
# Manual backup
sudo -u aiagent /opt/automation-hub/backup.sh

# Check cron job
sudo crontab -u aiagent -l

# View backup logs
tail -f /var/log/automation-hub/backup.log
```

### Backup Contents

Daily backups include:
- PostgreSQL database dump
- Configuration files
- Development bible content
- Application logs

Backups are stored in: `/opt/automation-hub/data/backups/`

### Manual Backup Procedures

```bash
# Backup database
docker exec automation_hub_postgres pg_dump -U automation automation_hub | gzip > backup_$(date +%Y%m%d).sql.gz

# Backup configuration
tar -czf config_backup_$(date +%Y%m%d).tar.gz -C /opt/automation-hub .env

# Backup entire data directory
tar -czf full_backup_$(date +%Y%m%d).tar.gz -C /opt/automation-hub data config
```

### Recovery Procedures

```bash
# Stop services
sudo systemctl stop automation-hub

# Restore database
gunzip -c backup_20241224.sql.gz | docker exec -i automation_hub_postgres psql -U automation -d automation_hub

# Restore configuration
tar -xzf config_backup_20241224.tar.gz -C /opt/automation-hub/

# Restart services
sudo systemctl start automation-hub
```

## Troubleshooting

### Common Issues

#### 1. Bot Won't Start

**Symptoms**: Discord bot container keeps restarting

**Diagnosis**:
```bash
docker-compose logs discord-bot
```

**Solutions**:
- Check Discord token is set correctly in `.env`
- Verify bot has proper permissions in Discord server
- Check internet connectivity
- Ensure firewall allows outbound HTTPS (443)

#### 2. Database Connection Issues

**Symptoms**: "Database not accessible" in health check

**Diagnosis**:
```bash
docker-compose logs postgres
docker exec automation_hub_postgres pg_isready -U automation
```

**Solutions**:
- Check PostgreSQL container is running: `docker-compose ps`
- Verify database password in `.env` file
- Check disk space: `df -h`
- Restart PostgreSQL: `docker-compose restart postgres`

#### 3. Permission Errors

**Symptoms**: Permission denied errors in logs

**Solutions**:
```bash
# Fix data directory permissions
sudo chown -R aiagent:aiagent /opt/automation-hub

# Fix environment file permissions
sudo chown aiagent:aiagent /opt/automation-hub/.env
sudo chmod 600 /opt/automation-hub/.env
```

#### 4. Out of Disk Space

**Diagnosis**:
```bash
df -h
docker system df
```

**Solutions**:
```bash
# Clean up Docker
docker system prune -f

# Clean up old logs
sudo find /opt/automation-hub/data/logs -name "*.log" -mtime +7 -delete

# Clean up old backups
sudo find /opt/automation-hub/data/backups -mtime +30 -delete
```

#### 5. High Memory Usage

**Diagnosis**:
```bash
free -h
docker stats --no-stream
```

**Solutions**:
- Restart services: `sudo systemctl restart automation-hub`
- Reduce concurrent tasks in `.env`: `BOT_MAX_CONCURRENT_TASKS=5`
- Add swap space: `sudo fallocate -l 2G /swapfile`

### Debug Commands

```bash
# Check service status
sudo systemctl status automation-hub

# View recent logs
sudo journalctl -u automation-hub --since "1 hour ago"

# Check Docker daemon
sudo systemctl status docker

# Test Discord bot configuration
cd /opt/automation-hub/app
python examples/discord_bot_demo.py

# Test database connection
docker exec -it automation_hub_postgres psql -U automation -d automation_hub

# Check network connectivity
ping discord.com
curl -I https://discord.com

# Check container resource usage
docker stats --no-stream

# Inspect container configuration
docker inspect automation_hub_discord_bot
```

### Log Locations

- **Systemd service logs**: `journalctl -u automation-hub`
- **Docker container logs**: `docker-compose logs`
- **Application logs**: `/opt/automation-hub/data/logs/`
- **PostgreSQL logs**: `docker-compose logs postgres`
- **Backup logs**: `/var/log/automation-hub/backup.log`

## Security Considerations

### Network Security

```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 8080/tcp  # Bot health check

# Optional: Allow specific IPs only
# sudo ufw allow from YOUR_IP_ADDRESS to any port 8080
```

### File Permissions

```bash
# Secure environment files
sudo chmod 600 /opt/automation-hub/.env
sudo chown aiagent:aiagent /opt/automation-hub/.env

# Secure data directories
sudo chmod 755 /opt/automation-hub/data
sudo chown -R aiagent:aiagent /opt/automation-hub/data
```

### Docker Security

```bash
# Run containers as non-root user
# (Already configured in docker-compose.yml)

# Regular security updates
sudo apt update && sudo apt upgrade -y
docker-compose pull  # Update container images
```

### Secrets Management

- Store all secrets in `.env` file with proper permissions
- Use strong, unique passwords for database
- Rotate API tokens regularly
- Never commit secrets to version control

### Access Control

- Use SSH key authentication instead of passwords
- Disable root SSH access
- Configure fail2ban for SSH protection
- Use Discord role-based permissions for bot commands

## Advanced Configuration

### Custom Domain Setup

```bash
# Install nginx for reverse proxy
sudo apt install nginx

# Configure SSL with Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com

# Configure nginx proxy
sudo nano /etc/nginx/sites-available/automation-hub
```

### Monitoring with Grafana

```bash
# Add Grafana to monitoring stack
# Edit docker-compose.yml to include Grafana service

# Access Grafana at http://YOUR_PI_IP:3000
# Default login: admin/admin
```

### High Availability Setup

For production environments:
- Use external PostgreSQL database
- Set up multiple Pi instances behind load balancer
- Use shared storage for persistent data
- Implement database replication

## Maintenance Schedule

### Daily
- Check service status
- Review error logs
- Monitor disk space

### Weekly  
- Review backup logs
- Check resource usage
- Update Discord bot status

### Monthly
- Update system packages
- Rotate log files
- Test backup recovery
- Review security logs

### Quarterly
- Update container images
- Review and update API tokens
- Performance optimization
- Security audit

## Support and Updates

### Getting Updates

```bash
# Update application code
cd /opt/automation-hub/app
sudo -u aiagent git pull origin main

# Update container images
sudo -u aiagent docker-compose pull

# Restart services
sudo systemctl restart automation-hub
```

### Community Support

- **GitHub Issues**: Report bugs and request features
- **Discord Community**: Join for real-time support
- **Documentation**: Check latest docs for updates

### Professional Support

For enterprise deployments or custom modifications:
- Contact the development team
- Commercial support options available
- Custom feature development

---

## Quick Reference

### Essential Commands

```bash
# Service control
sudo systemctl start/stop/restart/status automation-hub

# Container management
docker-compose up -d / down / restart / ps / logs -f

# Health monitoring
./deploy/health-check.sh

# Backup
sudo -u aiagent /opt/automation-hub/backup.sh

# View logs
sudo journalctl -u automation-hub -f
```

### Important Paths

- **Application**: `/opt/automation-hub/app/`
- **Data**: `/opt/automation-hub/data/`
- **Configuration**: `/opt/automation-hub/.env`
- **Logs**: `/var/log/automation-hub/`
- **Backups**: `/opt/automation-hub/data/backups/`

### Default Ports

- **Discord Bot Health**: 8080
- **PostgreSQL**: 5433
- **Prometheus**: 9090
- **Orchestrator**: 8081
- **Backend Agent**: 8082
- **Testing Agent**: 8083